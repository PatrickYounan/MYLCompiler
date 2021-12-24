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


class StackValueType(Enum):
    INT = 0,
    REF = 1


class StackValue:
    def __init__(self, val_type, value):
        self.val_type = val_type
        self.value = value
        self.ptr = 0


class Variable:
    def __init__(self, ptr, value):
        self.ptr = ptr
        self.value = value


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

        data = []

        strings = {}
        local_vars = {}
        local_pos = 0

        for instruction in self.instructions:
            if instruction.opcode == Opcode.START_PROC:
                local_pos = 0
                local_vars.clear()
                code.append("%s:\n" % instruction.value)
                code.append(" push rbp\n")
                code.append(" mov rbp, rsp\n")
                code.append(" sub rsp, 32\n")

            elif instruction.opcode == Opcode.END_PROC:
                code.append(" add rsp, 32\n")
                code.append(" leave\n")
                code.append(" ret\n")

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
                local_pos += 4
                variable = Variable(local_pos, 0)

                if self.stack:
                    stack_value = self.stack.pop()
                    code.append(" mov dword [rsp - %s], %s\n" % (local_pos, stack_value.value))
                    variable.value = stack_value.value
                local_vars[instruction.value] = variable
                self.reset_registers()

            elif instruction.opcode == Opcode.MOV_IMMS:
                if not strings.__contains__(instruction.value):
                    string_const = "lc%s" % len(strings)
                    strings[instruction.value] = string_const
                    data.append("%s: db `%s`, 0\n" % (string_const, instruction.value))
                    register = self.registers.pop()
                    code.append(" mov %s, %s\n" % (register, string_const))

            elif instruction.opcode == Opcode.LOAD_CONST:
                const = StackValue(StackValueType.REF, local_vars[instruction.value].value)
                const.ptr = local_vars[instruction.value].ptr
                self.stack.append(const)

            elif instruction.opcode == Opcode.CALL:
                code.append(" call %s\n" % instruction.value)
                self.reset_registers()

            elif instruction.opcode == Opcode.PUSH_ARG:
                # Only push argument if its on the stack. This will account for numbers.
                if self.stack:
                    stack_value = self.stack.pop()
                    if stack_value.val_type == StackValueType.REF:
                        code.append(" mov %s, [rsp - %s]\n" % (self.registers.pop(), stack_value.ptr))
                    else:
                        code.append(" mov %s, %s\n" % (self.registers.pop(), stack_value.value))

        if len(data) > 0:
            file.write("section .data\n")
            self.write_section(file, data)

        self.write_section(file, text)
        self.write_section(file, code)
        file.close()

        obj_path = self.asm_path.replace(".asm", ".obj")

        os.system("nasm -fwin64 %s | gcc -o program %s" % (self.asm_path, obj_path))
        os.system("program")
