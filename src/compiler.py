import llvmlite.binding as llvm
from llvmlite import ir


class Compiler:

    def __init__(self):
        llvm.initialize()
        llvm.initialize_native_target()
        llvm.initialize_native_asmprinter()

        self.target = llvm.Target.from_default_triple()
        self.target_machine = self.target.create_target_machine()
        self.backing_mod = llvm.parse_assembly("")
        self.engine = llvm.create_mcjit_compiler(self.backing_mod, self.target_machine)
        self.mod_ref = None
