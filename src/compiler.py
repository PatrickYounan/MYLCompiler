from token import TokenType, Token
from enum import Enum
import os


class Opcode(Enum):
    START_PROC = 0
    END_PROC = 1
    MOV_IMMI = 2
    MOV_IMMS = 3
    STORE_INT = 4
    LOAD_CONST = 5
    BINARY_OP = 6
    CALL = 7
    EXTERN = 8
    PUSH_ARG = 9
    ALLOC_BYTES = 10
    RES_STACK_PTR = 11


class StackValueType(Enum):
    INT = 0,
    REF = 1


class StackValue:
    def __init__(self, val_type, value):
        self.val_type = val_type
        self.value = value
        self.ptr = 0
        self.name = ""


class Variable:
    def __init__(self, name, ptr, value, line):
        self.ptr = ptr
        self.name = name
        self.value = value
        self.line = line
        self.using = False
        self.used_lines = []


class Instruction:
    def __init__(self, opcode, token=None, value=""):
        self.opcode = opcode
        self.token = token
        self.value = value


class Compiler:

    def __init__(self, asm_path, parser):
        self.instructions = []
        self.parser = parser
        self.asm_path = asm_path
        self.stack = []
        self.registers = ["r9", "r8", "rdx", "rcx"]
        self.scope = -1

    @staticmethod
    def write_section(file, data):
        for string in data:
            file.write(string)
        file.write("\n")

    def reset_registers(self):
        self.registers = ["r9", "r8", "rdx", "rcx"]

    def compile(self):
        while True:
            node = self.parser.parse_statement()
            if node is None:
                break
            node.compile(self)

        file = open(self.asm_path, "w")
        file.write("bits 64\n")

        text = [
            "section .text\n",
            "global main\n",
            "extern ExitProcess\n",
        ]
        code = [
            "main:\n",
            " call boot\n"
            " call ExitProcess\n"
        ]
        stack_alloc_line = 0
        stack_dealloc_line = 0
        data = []

        strings = {}
        constants = 0
        local_vars = {}
        local_pos = 0

        for instruction in self.instructions:
            if instruction.opcode == Opcode.START_PROC:
                local_pos = 0
                local_vars.clear()
                code.append("%s:\n" % instruction.value)
                code.append(" push rbp\n")
                code.append(" mov rbp, rsp\n")

            elif instruction.opcode == Opcode.END_PROC:
                # We will now start optimizations on the current function.
                local_pos = 0
                marked = []

                for variable in local_vars:
                    var = local_vars[variable]
                    if not var.using:
                        code[var.line] = ""
                    else:
                        marked.append(variable)

                for variable in marked:
                    var = local_vars[variable]
                    local_pos += 8
                    code[var.line] = code[var.line].replace("#", "%s" % hex(local_pos))

                    # Loop the lines that the variable is used at and update them.
                    for line in var.used_lines:
                        code[line] = code[line].replace("#", "%s" % hex(local_pos))

                code[stack_alloc_line] = code[stack_alloc_line].replace("#", "%s" % hex(32 + local_pos))
                code[stack_dealloc_line] = code[stack_dealloc_line].replace("#", "%s" % hex(32 + local_pos))

                code.append(" leave\n")
                code.append(" ret\n")

            elif instruction.opcode == Opcode.RES_STACK_PTR:
                stack_dealloc_line = len(code)
                code.append(" add rsp, #\n")  # Deallocate shadowspace.

            elif instruction.opcode == Opcode.ALLOC_BYTES:
                stack_alloc_line = len(code)
                code.append(" sub rsp, #\n")  # Allocate shadowspace.

            elif instruction.opcode == Opcode.EXTERN:
                text.append("extern %s\n" % instruction.value)

            elif instruction.opcode == Opcode.BINARY_OP:
                b = self.stack.pop()
                a = self.stack.pop()

                if instruction.token.type == TokenType.TOKEN_PLUS:
                    self.stack.append(StackValue(StackValueType.INT, int(a.value) + int(b.value)))
                elif instruction.token.type == TokenType.TOKEN_DASH:
                    self.stack.append(StackValue(StackValueType.INT, int(a.value) - int(b.value)))
                elif instruction.token.type == TokenType.TOKEN_STAR:
                    self.stack.append(StackValue(StackValueType.INT, int(a.value) * int(b.value)))
                elif instruction.token.type == TokenType.TOKEN_SLASH:
                    self.stack.append(StackValue(StackValueType.INT, int(a.value) / int(b.value)))

            elif instruction.opcode == Opcode.MOV_IMMI:
                self.stack.append(StackValue(StackValueType.INT, instruction.value))

            elif instruction.opcode == Opcode.STORE_INT:
                local_pos += 8
                variable = Variable(instruction.value, local_pos, 0, len(code))
                if self.stack:
                    stack_value = self.stack.pop()
                    code.append(" mov dword [rbp - #], %s ; int %s\n" % (hex(int(stack_value.value)), variable.name))
                    variable.value = stack_value.value
                local_vars[instruction.value] = variable
                self.reset_registers()

            elif instruction.opcode == Opcode.MOV_IMMS:
                if not strings.__contains__(instruction.value):
                    string_const = "lc%s" % constants
                    strings[instruction.value] = string_const
                    data.append("%s: db `%s`, 0\n" % (string_const, instruction.value))
                    register = self.registers.pop()
                    code.append(" mov %s, %s\n" % (register, string_const))
                    constants += 1
                else:
                    string_const = strings[instruction.value]
                    register = self.registers.pop()
                    code.append(" mov %s, %s\n" % (register, string_const))

            elif instruction.opcode == Opcode.LOAD_CONST:
                const = StackValue(StackValueType.REF, local_vars[instruction.value].value)
                const.ptr = local_vars[instruction.value].ptr
                const.name = instruction.value
                self.stack.append(const)

            elif instruction.opcode == Opcode.CALL:
                code.append(" call %s\n" % instruction.value)
                self.reset_registers()

            elif instruction.opcode == Opcode.PUSH_ARG:
                # Only push argument if its on the stack. This will account for numbers.
                if self.stack:
                    stack_value = self.stack.pop()
                    if stack_value.val_type == StackValueType.REF:
                        local_vars[stack_value.name].using = True
                        local_vars[stack_value.name].used_lines.append(len(code))
                        code.append(" mov %s, [rbp - #] ; %s\n" % (self.registers.pop(), local_vars[stack_value.name].name))
                    else:
                        code.append(" mov %s, %s\n" % (self.registers.pop(), hex(int(stack_value.value))))

        if len(data) > 0:
            file.write("section .data\n")
            self.write_section(file, data)

        self.write_section(file, text)
        self.write_section(file, code)
        file.close()

        obj_path = self.asm_path.replace(".asm", ".obj")

        os.system("nasm -fwin64 %s | gcc -o program %s" % (self.asm_path, obj_path))
        os.system("program")
