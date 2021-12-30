from enum import Enum
from token import *

compiled_files = {}


class Opcode(enum.IntEnum):
    START_PROC = 0
    END_PROC = 1
    MOV_IMMI = 2
    MOV_IMMS = 3
    STORE_INT = 4
    LOAD_CONST = 5
    BINARY_OP = 6
    COMPARE_OP = 7
    CALL = 8
    EXTERN = 9
    MOV_TO_REG = 10
    ALLOC_BYTES = 11
    RES_STACK_PTR = 12
    INCLUDE = 13
    ENDIF = 14
    LABEL = 15


class StackValueType(enum.IntEnum):
    INT = 0,
    REF = 1,
    BOOL = 2


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
        self.branch_stack = []
        self.registers = ["r9", "r8", "rdx", "rcx"]
        self.scope = -1

    @staticmethod
    def write_section(file, data):
        for string in data:
            file.write(string)
        file.write("\n")

    def reset_registers(self):
        self.registers = ["r9", "r8", "rdx", "rcx"]

    def walk_tree(self):
        while True:
            node = self.parser.parse_statement()
            if node is None:
                break
            node.compile(self)

    def append_cmp_op(self, cmp_op, a, b):

        if cmp_op == TokenType.TOKEN_ISEQ:
            self.stack.append(StackValue(StackValueType.BOOL, int(a.value) == int(b.value)))

    def append_bin_op(self, bin_op, a, b):

        if bin_op == TokenType.TOKEN_PLUS:
            self.stack.append(StackValue(StackValueType.INT, int(a.value) + int(b.value)))

        elif bin_op == TokenType.TOKEN_DASH:
            self.stack.append(StackValue(StackValueType.INT, int(a.value) - int(b.value)))

        elif bin_op == TokenType.TOKEN_STAR:
            self.stack.append(StackValue(StackValueType.INT, int(a.value) * int(b.value)))

        elif bin_op == TokenType.TOKEN_SLASH:
            self.stack.append(StackValue(StackValueType.INT, int(a.value) / int(b.value)))

    def compile(self, path):

        if compiled_files.__contains__(path):
            return
        self.walk_tree()

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
        labels = 0

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
                code.append("L%s:\n" % labels)
                stack_dealloc_line = len(code)
                code.append(" add rsp, #\n")  # Deallocate shadowspace.

            elif instruction.opcode == Opcode.ALLOC_BYTES:
                stack_alloc_line = len(code)
                code.append(" sub rsp, #\n")  # Allocate shadowspace.

            elif instruction.opcode == Opcode.EXTERN:
                text.append("extern %s\n" % instruction.value)

            elif instruction.opcode == Opcode.ENDIF:
                if_ip = self.branch_stack.pop()
                label = "L%s" % labels
                code[if_ip] = code[if_ip].replace("#", label)

            elif instruction.opcode == Opcode.COMPARE_OP:
                code.append(" cmp rcx, rdx\n")
                label = "L%s" % labels
                if instruction.token.tok_type == TokenType.TOKEN_ISEQ:
                    code.append(" je %s\n" % label)
                self.branch_stack.append(len(code))
                code.append(" jmp #\n")
                self.reset_registers()

            elif instruction.opcode == Opcode.LABEL:
                code.append("L%s:\n" % labels)
                labels += 1

            elif instruction.opcode == Opcode.BINARY_OP:
                b = self.stack.pop()
                a = self.stack.pop()

                bin_op = instruction.token.tok_type
                self.append_bin_op(bin_op, a, b)

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

            elif instruction.opcode == Opcode.INCLUDE:
                if not compiled_files.__contains__("%s.myl" % instruction.value):
                    include_path = "%s.myl" % instruction.value

                    parser = Parser(Lexer("%s" % include_path))
                    parser.parse_advance()

                    compiler = Compiler(include_path.replace(".myl", ".asm"), parser)
                    compiler.compile(include_path)

                data.append("%include \"%s.asm\"" % instruction.value)

            elif instruction.opcode == Opcode.MOV_TO_REG:
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

        compiled_files[path] = True
