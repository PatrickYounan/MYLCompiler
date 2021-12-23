from token import TokenType, Token
from enum import Enum
import os


class Opcode(Enum):
    START_PROC = 0,
    END_PROC = 1,
    PUSHI = 2,
    PUSHS = 3,
    STOREI = 4,
    LOAD_CONST = 5,
    CALL = 5


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

    @staticmethod
    def write_section(file, data):
        for string in data:
            file.write(string)
        file.write("\n")

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
            "extern ExitProcess\n"
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
            elif instruction.opcode == Opcode.END_PROC:
                code.append(" leave\n")
                code.append(" ret\n")
            elif instruction.opcode == Opcode.PUSHI:
                code.append(" mov rax, %s\n" % instruction.value)
            elif instruction.opcode == Opcode.STOREI:
                local_pos += 4
                local_vars[instruction.value] = local_pos
                code.append(" mov [rsp - %s], rax\n" % local_pos)
            elif instruction.opcode == Opcode.PUSHS:
                if not strings.__contains__(instruction.value):
                    string_const = "lc%s" % len(strings)
                    strings[instruction.value] = string_const
                    data.append("%s: db \"%s\", 0\n" % (string_const, instruction.value))
                    code.append(" push %s\n" % string_const)
                else:
                    string_const = strings[instruction.value]
                    code.append(" push %s\n" % string_const)
            elif instruction.opcode == Opcode.LOAD_CONST:
                code.append(" mov rax, [rsp - %s]\n" % local_vars[instruction.value])
                code.append(" push rax\n")
            elif instruction.opcode == Opcode.CALL:
                code.append(" call %s\n" % instruction.value)

        if len(data) > 0:
            file.write("section .data\n")
            self.write_section(file, data)
        self.write_section(file, text)
        self.write_section(file, code)
        file.close()

        obj_path = self.asm_path.replace(".asm", ".obj")

        os.system("nasm -fwin64 %s | gcc -o program %s" % (self.asm_path, obj_path))
        os.system("program")
