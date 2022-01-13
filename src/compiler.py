from token import *
import ctypes


class Opcode(enum.IntEnum):
    START_PROC = 0
    START_PUB_PROC = 1
    END_PROC = 2,
    MOV_INT_CONST = 3
    MOV_UNSIGNED_INT_CONST = 4
    NEGATE = 5
    NOT = 6
    RETURN = 7
    STORE_INT8 = 8
    STORE_INT16 = 9
    STORE_INT32 = 10
    STORE_INT64 = 11
    SETUP_STACK = 12
    CLOSE_STACK = 13
    LOAD_VAR = 14
    CALL = 15
    EXTERN = 16
    LOAD_STRING = 17
    PUSH_ARGUMENT = 18
    ADD = 19
    SUB = 20
    MUL = 21
    DIV = 22
    STORE_FLOAT64 = 23
    MOV_FLOAT_CONST = 24
    CMP = 25
    IF = 26
    ENDIF = 27
    JMPEQ = 28
    JMP = 29
    ELSE = 30


class StackValueType(enum.IntEnum):
    INT_CONST = 0
    INT8_VAR = 1
    INT16_VAR = 2
    INT32_VAR = 3
    INT64_VAR = 4
    STRING_CONST = 5
    REGISTER8 = 6
    REGISTER16 = 7
    REGISTER32 = 8
    REGISTER64 = 9
    FLOAT_VAR = 10
    FLOAT_CONST = 11


class StackValue:
    def __init__(self, kind, value="", ptr=0):
        self.kind = kind
        self.value = value
        self.ptr = ptr


class Instruction:
    def __init__(self, opcode, token=None, value="", state=""):
        self.token = token
        self.value = value
        self.opcode = opcode
        self.state = state


class Variable:
    def __init__(self, name, ptr, kind, cur_value):
        self.name = name
        self.ptr = ptr
        self.kind = kind
        self.cur_value = cur_value


class Function:
    def __init__(self, name, kind):
        self.name = name
        self.kind = kind
        self.has_return_value = False


class Compiler:

    def __init__(self, parser):
        self.parser = parser
        self.instructions = []
        self.stack = []
        self.state = ""
        self.vars = {}
        self.stack_offset = 0
        self.var_address_ptr = 0
        self.registers_64bit = ["r9", "r8", "rdx", "rcx"]
        self.registers_32bit = ["r9d", "r8d", "edx", "ecx"]
        self.functions = {}
        self.code = ["SECTION .text\n"]
        self.setup = []
        self.data = []
        self.labels = 0
        self.last_type = None

    def error(self, message):
        raise Exception(message)

    def add(self, instr):
        self.instructions.append(instr)

    def pop_32bit_arg_register(self):
        return self.registers_32bit.pop()

    def pop_64bit_arg_register(self):
        return self.registers_64bit.pop()

    def reset_registers(self):
        self.registers_64bit = ["r9", "r8", "rdx", "rcx"]
        self.registers_32bit = ["r9d", "r8d", "edx", "ecx"]

    # This function pops every registers for each bit size but chooses the one we require.
    def pop_register(self, required):
        if not self.registers_32bit or not self.registers_64bit:
            return "rax" if required == 64 else "eax"
        bit32 = self.pop_32bit_arg_register()
        bit64 = self.pop_64bit_arg_register()
        return bit64 if required == 64 else bit32

    def movq(self, a, b):
        if a == b:
            return
        self.code.append(" movq %s, %s\n" % (a, b))

    def mov(self, a, b):
        if a == b:
            return
        self.code.append(" mov %s, %s\n" % (a, b))

    def movss(self, a, b):
        if a == b:
            return
        self.code.append(" movss %s, %s\n" % (a, b))

    def pop_stack(self) -> StackValue:
        stack_value = self.stack.pop()

        if stack_value.kind == StackValueType.INT8_VAR:
            return StackValue(StackValueType.INT8_VAR, "byte [rsp - %s]" % stack_value.value, stack_value.ptr)
        elif stack_value.kind == StackValueType.INT16_VAR:
            return StackValue(StackValueType.INT16_VAR, "word [rsp - %s]" % stack_value.value, stack_value.ptr)
        elif stack_value.kind == StackValueType.INT32_VAR:
            return StackValue(StackValueType.INT32_VAR, "dword [rsp - %s]" % stack_value.value, stack_value.ptr)
        elif stack_value.kind == StackValueType.INT64_VAR:
            return StackValue(StackValueType.INT64_VAR, "qword [rsp - %s]" % stack_value.value, stack_value.ptr)
        elif stack_value.kind == StackValueType.FLOAT_VAR:
            return StackValue(StackValueType.FLOAT_VAR, "dword [rsp - %s]" % stack_value.value, stack_value.ptr)
        return stack_value

    def emit_mov(self, register="?"):
        stack_value = self.pop_stack()
        value = stack_value.value

        if stack_value.kind == StackValueType.INT8_VAR:
            register = self.pop_register(32)
            self.mov("al", value)
            self.code.append(" movzx %s, al\n" % register)
            return register

        elif stack_value.kind == StackValueType.INT16_VAR:
            register = self.pop_register(32)
            self.mov("ax", value)
            self.code.append(" movzx %s, ax\n" % register)
            return register

        elif stack_value.kind == StackValueType.FLOAT_VAR and register != "rax":
            register = self.pop_register(64)
            self.code.append(" cvtss2sd xmm0, %s\n" % value)
            self.movq(register, "xmm0")
            return register

        elif (stack_value.kind == StackValueType.INT32_VAR) and register != "eax" and register != "32":
            register = self.pop_register(32)

        elif (stack_value.kind == StackValueType.INT64_VAR or stack_value.kind == StackValueType.STRING_CONST) and register != "rax" and register != "64":
            register = self.pop_register(64)

        elif stack_value.kind == StackValueType.INT_CONST:
            if register == "64":
                register = self.pop_register(64)
            elif register == "32":
                register = self.pop_register(32)

        self.mov(register, value)
        return register

    def emit_var(self, name, byte_amount, stack_kind, var_kind):
        stack_value = self.pop_stack()
        self.var_address_ptr += byte_amount

        if stack_value.kind == StackValueType.INT_CONST:
            value = stack_value.value
            stack_value.value = ctypes.c_int64(int(value)).value

        self.stack_offset += 8
        if "FLOAT" in stack_kind.name:
            self.movss("%s [rsp - %s]" % (var_kind, self.var_address_ptr), stack_value.value)
        else:
            self.mov("%s [rsp - %s]" % (var_kind, self.var_address_ptr), stack_value.value)

        self.vars[name] = Variable(name, self.var_address_ptr, stack_kind, stack_value)

    def walk_tree(self):
        while True:
            node = self.parser.parse_statement()
            if node is None:
                break
            node.eval(self)

    def add_int_consts(self, a, b):
        self.stack.append(StackValue(StackValueType.INT_CONST, str(int(a.value) + int(b.value))))

    def get_register_for_type(self, value):
        if value.kind == StackValueType.INT32_VAR:
            return self.pop_register(32)
        elif value.kind == StackValueType.INT64_VAR:
            return self.pop_register(64)
        elif value.kind == StackValueType.INT_CONST:
            return value.value
        raise Exception("Unsupported kind.")

    def add_i8(self, a, b):
        self.mov("ah", a.value)
        self.mov("dh", b.value)
        self.code.append(" add ah, dh\n")
        self.stack.append(StackValue(StackValueType.REGISTER8, "ah"))

    def add_i16(self, a, b):
        self.mov("ax", a.value)
        self.mov("dx", b.value)
        self.code.append(" add ax, dx\n")
        self.stack.append(StackValue(StackValueType.REGISTER16, "ax"))

    def add_i32(self, a, b):
        self.mov("eax", a.value)
        self.mov("edx", b.value)
        self.code.append(" add eax, edx\n")
        self.stack.append(StackValue(StackValueType.REGISTER32, "eax"))

    def add_i64(self, a, b):
        self.mov("rax", a.value)
        self.mov("rdx", b.value)
        self.code.append(" add rax, rdx\n")
        self.stack.append(StackValue(StackValueType.REGISTER64, "rax"))

    def sub_int_consts(self, a, b):
        self.stack.append(StackValue(StackValueType.INT_CONST, str(int(a.value) - int(b.value))))

    def sub_i8(self, a, b):
        self.mov("ah", a.value)
        self.mov("dh", b.value)
        self.code.append(" sub ah, dh\n")
        self.stack.append(StackValue(StackValueType.REGISTER8, "ah"))

    def sub_i16(self, a, b):
        self.mov("ax", a.value)
        self.mov("dx", b.value)
        self.code.append(" sub ax, dx\n")
        self.stack.append(StackValue(StackValueType.REGISTER16, "ax"))

    def sub_i32(self, a, b):
        self.mov("eax", a.value)
        self.mov("edx", b.value)
        self.code.append(" sub eax, edx\n")
        self.stack.append(StackValue(StackValueType.REGISTER32, "eax"))

    def sub_i64(self, a, b):
        self.mov("rax", a.value)
        self.mov("rdx", b.value)
        self.code.append(" sub rax, rdx\n")
        self.stack.append(StackValue(StackValueType.REGISTER64, "rax"))

    def mul_int_consts(self, a, b):
        self.stack.append(StackValue(StackValueType.INT_CONST, str(int(a.value) * int(b.value))))

    def mul_i8(self, a, b):
        self.mov("al", a.value)
        self.mov("bl", b.value)
        self.code.append(" imul bl\n")
        self.stack.append(StackValue(StackValueType.REGISTER8, "al"))

    def mul_i16(self, a, b):
        self.mov("ax", a.value)
        self.mov("bx", b.value)
        self.code.append(" imul bx\n")
        self.stack.append(StackValue(StackValueType.REGISTER16, "ax"))

    def mul_i32(self, a, b):
        self.mov("eax", a.value)
        self.mov("ebx", b.value)
        self.code.append(" imul ebx\n")
        self.stack.append(StackValue(StackValueType.REGISTER32, "eax"))

    def mul_i64(self, a, b):
        self.mov("rax", a.value)
        self.mov("rdx", b.value)
        self.code.append(" imul rdx\n")
        self.stack.append(StackValue(StackValueType.REGISTER64, "rax"))

    def div_int_consts(self, a, b):
        self.stack.append(StackValue(StackValueType.INT_CONST, str(int(a.value) / int(b.value))))

    def div_i8(self, a, b):
        self.mov("al", a.value)
        self.code.append(" cbw\n")
        self.mov("bl", b.value)
        self.code.append(" idiv bl\n")
        self.stack.append(StackValue(StackValueType.REGISTER8, "al"))

    def div_i16(self, a, b):
        self.mov("ax", a.value)
        self.code.append(" cwd\n")
        self.mov("bx", b.value)
        self.code.append(" idiv bx\n")
        self.stack.append(StackValue(StackValueType.REGISTER16, "ax"))

    def div_i32(self, a, b):
        self.mov("eax", a.value)
        self.code.append(" cdq\n")
        self.mov("ebx", b.value)
        self.code.append(" idiv ebx\n")
        self.stack.append(StackValue(StackValueType.REGISTER32, "eax"))

    def div_i64(self, a, b):
        self.mov("rax", a.value)
        self.code.append(" cdq\n")
        self.mov("rbx", b.value)
        self.code.append(" idiv rbx\n")
        self.stack.append(StackValue(StackValueType.REGISTER64, "rax"))

    def emit_cmp(self, a, b):
        register_a = self.get_register_for_type(a)
        register_b = self.get_register_for_type(b)
        self.mov(register_a, a.value)
        self.mov(register_b, b.value)
        self.code.append(" cmp %s, %s\n" % (register_a, register_b))

    def compile_div_op(self, a, b):
        if a.kind == StackValueType.INT_CONST:
            if b.kind == StackValueType.INT_CONST:
                self.div_int_consts(a, b)
            elif b.kind == StackValueType.INT8_VAR:
                self.div_i8(a, b)
            elif b.kind == StackValueType.INT16_VAR:
                self.div_i16(a, b)
            elif b.kind == StackValueType.INT32_VAR:
                self.div_i32(a, b)
            elif b.kind == StackValueType.INT64_VAR:
                self.div_i64(a, b)
        elif a.kind == StackValueType.REGISTER8 or a.kind == StackValueType.INT8_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT8_VAR or b.kind == StackValueType.REGISTER8:
                self.div_i8(a, b)
            else:
                self.error("An I8 can only be divided by another I8 or Int Constant.")
        elif a.kind == StackValueType.REGISTER16 or a.kind == StackValueType.INT16_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT16_VAR or b.kind == StackValueType.REGISTER16:
                self.div_i16(a, b)
            else:
                self.error("An I16 can only be divided by another I16 or Int Constant.")
        elif a.kind == StackValueType.REGISTER32 or a.kind == StackValueType.INT32_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT32_VAR or b.kind == StackValueType.REGISTER32:
                self.div_i32(a, b)
            else:
                self.error("An I32 can only be divided by another I32 or Int Constant.")
        elif a.kind == StackValueType.REGISTER64 or a.kind == StackValueType.INT64_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT64_VAR or b.kind == StackValueType.REGISTER64:
                self.div_i64(a, b)
            else:
                self.error("An I64 can only be divided by another I64 or Int Constant.")

    def compile_sub_op(self, a, b):
        if a.kind == StackValueType.INT_CONST:
            if b.kind == StackValueType.INT_CONST:
                self.sub_int_consts(a, b)
            elif b.kind == StackValueType.INT8_VAR:
                self.sub_i8(a, b)
            elif b.kind == StackValueType.INT16_VAR:
                self.sub_i16(a, b)
            elif b.kind == StackValueType.INT32_VAR:
                self.sub_i32(a, b)
            elif b.kind == StackValueType.INT64_VAR:
                self.sub_i64(a, b)
        elif a.kind == StackValueType.REGISTER8 or a.kind == StackValueType.INT8_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT8_VAR or b.kind == StackValueType.REGISTER8:
                self.sub_i8(a, b)
            else:
                self.error("An I8 can only be subtracted by another I8 or Int Constant.")
        elif a.kind == StackValueType.REGISTER16 or a.kind == StackValueType.INT16_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT16_VAR or b.kind == StackValueType.REGISTER16:
                self.sub_i16(a, b)
            else:
                self.error("An I16 can only be subtracted by another I16 or Int Constant.")
        elif a.kind == StackValueType.REGISTER32 or a.kind == StackValueType.INT32_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT32_VAR or b.kind == StackValueType.REGISTER32:
                self.sub_i32(a, b)
            else:
                self.error("An I32 can only be subtracted by another I32 or Int Constant.")
        elif a.kind == StackValueType.REGISTER64 or a.kind == StackValueType.INT64_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT64_VAR or b.kind == StackValueType.REGISTER64:
                self.sub_i64(a, b)
            else:
                self.error("An I64 can only be subtracted by another I64 or Int Constant.")

    def compile_add_op(self, a, b):
        if a.kind == StackValueType.INT_CONST:
            if b.kind == StackValueType.INT_CONST:
                self.add_int_consts(a, b)
            elif b.kind == StackValueType.INT8_VAR:
                self.add_i8(a, b)
            elif b.kind == StackValueType.INT16_VAR:
                self.add_i16(a, b)
            elif b.kind == StackValueType.INT32_VAR:
                self.add_i32(a, b)
            elif b.kind == StackValueType.INT64_VAR:
                self.add_i64(a, b)

        elif a.kind == StackValueType.REGISTER8 or a.kind == StackValueType.INT8_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT8_VAR or b.kind == StackValueType.REGISTER8:
                self.add_i8(a, b)
            else:
                self.error("An I8 can only be added to another I8 or Int Constant.")

        elif a.kind == StackValueType.REGISTER16 or a.kind == StackValueType.INT16_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT16_VAR or b.kind == StackValueType.REGISTER16:
                self.add_i16(a, b)
            else:
                self.error("An I16 can only be added to another I16 or Int Constant.")

        elif a.kind == StackValueType.REGISTER32 or a.kind == StackValueType.INT32_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT32_VAR or b.kind == StackValueType.REGISTER32:
                self.add_i32(a, b)
            else:
                self.error("An I32 can only be added to another I32 or Int Constant.")

        elif a.kind == StackValueType.REGISTER64 or a.kind == StackValueType.INT64_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT64_VAR or b.kind == StackValueType.REGISTER64:
                self.add_i64(a, b)
            else:
                self.error("An I64 can only be added to another I64 or Int Constant.")

    def compile_mul_op(self, a, b):
        if a.kind == StackValueType.INT_CONST:
            if b.kind == StackValueType.INT_CONST:
                self.mul_int_consts(a, b)
            elif b.kind == StackValueType.INT8_VAR:
                self.mul_i8(a, b)
            elif b.kind == StackValueType.INT16_VAR:
                self.mul_i16(a, b)
            elif b.kind == StackValueType.INT32_VAR:
                self.mul_i32(a, b)
            elif b.kind == StackValueType.INT64_VAR:
                self.mul_i64(a, b)
        elif a.kind == StackValueType.REGISTER8 or a.kind == StackValueType.INT8_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT8_VAR or b.kind == StackValueType.REGISTER8:
                self.mul_i8(a, b)
            else:
                self.error("An I8 can only be multiplied by another I8 or Int Constant.")
        elif a.kind == StackValueType.REGISTER16 or a.kind == StackValueType.INT16_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT16_VAR or b.kind == StackValueType.REGISTER16:
                self.mul_i16(a, b)
            else:
                self.error("An I16 can only be multiplied by another I16 or Int Constant.")
        elif a.kind == StackValueType.REGISTER32 or a.kind == StackValueType.INT32_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT32_VAR or b.kind == StackValueType.REGISTER32:
                self.mul_i32(a, b)
            else:
                self.error("An I32 can only be multiplied by another I32 or Int Constant.")
        elif a.kind == StackValueType.REGISTER64 or a.kind == StackValueType.INT64_VAR:
            if b.kind == StackValueType.INT_CONST or b.kind == StackValueType.INT64_VAR or b.kind == StackValueType.REGISTER64:
                self.mul_i64(a, b)
            else:
                self.error("An I64 can only be multiplied by another I64 or Int Constant.")

    def gen_label(self):
        label = "L%s" % self.labels
        self.labels += 1
        return label

    def compile(self, path):
        self.walk_tree()
        file = open(path, "w")

        setup_stack_idx = 0
        strings = {}
        floats = {}
        string_count = 0
        float_count = 0
        calling_stack_offset = 0
        function = None

        for ip in range(0, len(self.instructions)):
            instr = self.instructions[ip]

            if instr.opcode == Opcode.START_PROC:
                self.vars.clear()
                self.stack_offset = 0
                self.var_address_ptr = 0
                self.code.append("%s:\n" % instr.value)
                function = self.functions[instr.value]

            elif instr.opcode == Opcode.START_PUB_PROC:
                self.code.append("%s:\n" % instr.value)
                self.setup.append("global %s\n" % instr.value)
                function = self.functions[instr.value]

            elif instr.opcode == Opcode.SETUP_STACK:
                setup_stack_idx = len(self.code)
                self.code.append(" push rbp\n")
                self.mov("rbp", "rsp")
                self.code.append(" sub rsp, #\n")

            elif instr.opcode == Opcode.CLOSE_STACK:
                if self.stack_offset <= 0:
                    for i in range(0, 3):
                        self.code.pop(setup_stack_idx)
                    continue
                sub_idx = setup_stack_idx + 2
                self.code[sub_idx] = self.code[sub_idx].replace("#", "%s" % hex(32 + self.stack_offset))
                self.code.append(" add rsp, %s\n" % hex(32 + self.stack_offset))
                self.code.append(" leave\n")

            elif instr.opcode == Opcode.MOV_INT_CONST:
                self.stack.append(StackValue(StackValueType.INT_CONST, instr.value))

            elif instr.opcode == Opcode.MOV_FLOAT_CONST:
                float_name = ""
                if instr.value not in floats:
                    float_name = "float%s" % float_count
                    self.data.append("%s: dd %s\n" % (float_name, instr.value))
                    floats[instr.value] = float_name
                    float_count += 1
                else:
                    float_name = floats[instr.value]
                self.movss("xmm0", "dword [%s]" % float_name)
                self.stack.append(StackValue(StackValueType.FLOAT_CONST, "xmm0"))

            elif instr.opcode == Opcode.MOV_UNSIGNED_INT_CONST:
                self.stack.append(StackValue(StackValueType.INT_CONST, int("-%s" % instr.value) + 2 ** 32))

            elif instr.opcode == Opcode.NOT:
                stack_value = int(self.pop_stack().value)
                self.stack.append(
                    StackValue(StackValueType.INT_CONST, str(0 if stack_value < 0 or stack_value > 0 else 1)))

            elif instr.opcode == Opcode.ADD:
                b = self.pop_stack()
                a = self.pop_stack()
                print("%s %s" % (a.value, b.value))
                self.compile_add_op(a, b)

            elif instr.opcode == Opcode.JMPEQ:
                self.code.append(" je %s\n" % instr.value)

            elif instr.opcode == Opcode.JMP:
                self.code.append(" jmp %s\n" % instr.value)

            elif instr.opcode == Opcode.IF:
                self.code.append("%s:\n" % instr.value)

            elif instr.opcode == Opcode.ELSE:
                self.code.append("%s:\n" % instr.value)

            elif instr.opcode == Opcode.ENDIF:
                self.code.append("%s:\n" % instr.value)

            elif instr.opcode == Opcode.SUB:
                b = self.pop_stack()
                a = self.pop_stack()
                self.compile_sub_op(a, b)

            elif instr.opcode == Opcode.MUL:
                b = self.pop_stack()
                a = self.pop_stack()
                self.compile_mul_op(a, b)

            elif instr.opcode == Opcode.DIV:
                b = self.pop_stack()
                a = self.pop_stack()
                self.compile_div_op(a, b)

            elif instr.opcode == Opcode.CMP:
                b = self.pop_stack()
                a = self.pop_stack()
                self.emit_cmp(a, b)
                self.reset_registers()

            elif instr.opcode == Opcode.RETURN:
                if self.stack:
                    if function.kind is None:
                        self.error("Function has no returning value.")
                    if function.kind == TokenType.TOKEN_INT64:
                        self.emit_mov("rax")
                    elif function.kind == TokenType.TOKEN_INT32:
                        self.emit_mov("eax")
                    elif function.kind == TokenType.TOKEN_INT16:
                        self.emit_mov("ax")
                    elif function.kind == TokenType.TOKEN_INT8:
                        self.emit_mov("al")
                    function.has_return_value = True
                else:
                    self.code.append(" ret\n")

            elif instr.opcode == Opcode.STORE_INT8:
                self.emit_var(instr.value, 1, StackValueType.INT8_VAR, "byte")

            elif instr.opcode == Opcode.STORE_INT16:
                self.emit_var(instr.value, 2, StackValueType.INT16_VAR, "word")

            elif instr.opcode == Opcode.STORE_INT32:
                self.emit_var(instr.value, 4, StackValueType.INT32_VAR, "dword")

            elif instr.opcode == Opcode.STORE_FLOAT64:
                self.emit_var(instr.value, 4, StackValueType.FLOAT_VAR, "dword")

            elif instr.opcode == Opcode.STORE_INT64:
                self.emit_var(instr.value, 8, StackValueType.INT64_VAR, "qword")

            elif instr.opcode == Opcode.LOAD_STRING:
                if instr.value not in strings:
                    string = "str%s" % string_count
                    self.data.append("%s: db `%s`, 0\n" % (string, instr.value))
                    strings[instr.value] = string
                    self.stack.append(StackValue(StackValueType.STRING_CONST, string))
                    string_count += 1
                else:
                    string = strings[instr.value]
                    self.stack.append(StackValue(StackValueType.STRING_CONST, string))

            elif instr.opcode == Opcode.EXTERN:
                self.setup.append("extern %s\n" % instr.value)

            elif instr.opcode == Opcode.CALL:
                self.code.append(" call %s\n" % instr.value)

                if instr.value in self.functions and self.functions[instr.value].kind is not None:
                    kind = self.functions[instr.value].kind
                    if kind == TokenType.TOKEN_INT8:
                        self.stack.append(StackValue(StackValueType.REGISTER8, "al"))
                    elif kind == TokenType.TOKEN_INT16:
                        self.stack.append(StackValue(StackValueType.REGISTER16, "ax"))
                    elif kind == TokenType.TOKEN_INT32:
                        self.stack.append(StackValue(StackValueType.REGISTER32, "eax"))
                    elif kind == TokenType.TOKEN_INT64:
                        self.stack.append(StackValue(StackValueType.REGISTER64, "rax"))

                self.reset_registers()
                calling_stack_offset = 0

            elif instr.opcode == Opcode.LOAD_VAR:
                var = self.vars[instr.value]
                self.stack.append(StackValue(var.kind, var.ptr, var.ptr))

            elif instr.opcode == Opcode.PUSH_ARGUMENT:
                register = self.emit_mov()

                # Move the arguments on the stack.
                if register == "rax" or register == "eax":
                    self.mov("[rsp + %s]" % hex(32 + calling_stack_offset), register)
                    calling_stack_offset += 8

            elif instr.opcode == Opcode.END_PROC:

                # Check if the function requires a return value.
                if function.kind is not None and not function.has_return_value:
                    self.error("Function %s requires a return value." % function.name)

                # If the last code was 'ret', don't emit ret again.
                if "ret" not in self.code[len(self.code) - 1]:
                    self.code.append(" ret\n")

        file.writelines(self.setup)
        file.write("\n")

        if len(self.data) > 0:
            file.write("SECTION .data\n")
            file.writelines(self.data)
            file.write("\n")

        file.writelines(self.code)
        file.write("\n")
        file.close()
