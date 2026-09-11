"""
test_cpu.py — CPU core tests. (TODO once src/cpu/cpu.py is implemented)

Planned coverage once CPU.step() exists:
    - each opcode (MOV/LOAD/STORE/ADD/.../NOT) updates regs/dmem correctly
    - flags (ZF/CF/SF) update as expected after arithmetic
    - MUL writes low word to Rd and high word to Rd+1, leaves CF unchanged
    - DIV by zero raises an exception
    - jumps (JMP/JZ/JNZ/JC/JNC/JS/JNS) branch on the correct flag
    - HALT sets cpu.halted and stops run()
    - end-to-end: assemble + run src/programs/find_max.asm and
      src/programs/convolution.asm against known input arrays, check dmem
"""
