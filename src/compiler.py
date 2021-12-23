from token import TokenType, Token
from enum import Enum
import os


class Opcode(Enum):
    START_PROC = 0,
    END_PROC = 1,
    MOV_IMMI = 2,
    MOV_IMMS = 3,
    STORE_INT = 4,
    LOAD_CONST = 5,
    BINARY_OP = 6,
    CALL = 7


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
        self.registers = ["r9", "r8", "rdx", "rcx"]
        self.used_registers = []

    @staticmethod
    def write_section(file, data):
        for string in data:
            file.write(string)
        file.write("\n")

    def reset_registers(self):
        self.registers = ["r9", "r8", "rdx", "rcx"]

    def get_register(self):
        register = self.registers.pop()
        self.used_registers.append(register)
        return register

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
            "extern printf\n",
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
                code.append(" sub rsp, 32\n")
            elif instruction.opcode == Opcode.END_PROC:
                code.append(" add rsp, 32\n")
                code.append(" leave\n")
                code.append(" ret\n")
            elif instruction.opcode == Opcode.BINARY_OP:
                b = self.used_registers.pop()
                a = self.used_registers.pop()
                if instruction.token.type == TokenType.TOKEN_PLUS:
                    code.append(" add %s, %s\n" % (b, a))
                    self.used_registers.append(b)  # add b when adding.
                    self.reset_registers()
                    self.registers.append(a)  # add a to available registers.
                elif instruction.token.type == TokenType.TOKEN_DASH:
                    code.append(" sub %s, %s\n" % (a, b))
                    self.used_registers.append(a)  # add a when subtracting.
                    self.reset_registers()
                    self.registers.append(b)  # add b to available registers.
            elif instruction.opcode == Opcode.MOV_IMMI:
                code.append(" mov %s, %s\n" % (self.get_register(), instruction.value))
            elif instruction.opcode == Opcode.STORE_INT:
                local_pos += 4
                local_vars[instruction.value] = local_pos
                code.append(" mov [rsp - %s], %s\n" % (local_pos, self.used_registers.pop()))
                self.reset_registers()
            elif instruction.opcode == Opcode.MOV_IMMS:
                if not strings.__contains__(instruction.value):
                    string_const = "lc%s" % len(strings)
                    strings[instruction.value] = string_const
                    data.append("%s: db `%s`, 0\n" % (string_const, instruction.value))
                    code.append(" mov %s, %s\n" % (self.get_register(), string_const))
                else:
                    string_const = strings[instruction.value]
                    code.append(" mov %s, %s\n" % (self.get_register(), string_const))
            elif instruction.opcode == Opcode.LOAD_CONST:
                code.append(" mov %s, [rsp - %s]\n" % (self.get_register(), local_vars[instruction.value]))
            elif instruction.opcode == Opcode.CALL:
                code.append(" call %s\n" % instruction.value)
                self.reset_registers()

        if len(data) > 0:
            file.write("section .data\n")
            self.write_section(file, data)
        self.write_section(file, text)
        self.write_section(file, code)
        file.close()

        obj_path = self.asm_path.replace(".asm", ".obj")

        os.system("nasm -fwin64 %s | gcc -o program %s" % (self.asm_path, obj_path))
        os.system("program")
