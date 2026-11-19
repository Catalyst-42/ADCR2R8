#!/usr/bin/env python3
"""
Simple working convolution test to verify the concept.
"""

from pathlib import Path
from src.assembler.parser import assemble_file
from src.cpu.cpu import CPU

def simple_convolution_test():
    """Test convolution with a very simple approach."""
    print("=== SIMPLE CONVOLUTION TEST ===")
    
    # Create CPU instance
    cpu = CPU()
    
    # Create a simple convolution program using proper encoding
    # MOV R3, #0 -> 0x0301 (opcode=0, Rd=3, Rs=0, mode=1), then 0x0000 (immediate value)
    # MOV R4, #1 -> 0x0401, then 0x0001
    # MOV R5, #2 -> 0x0501, then 0x0002
    # MUL R4, R5 -> 0x1543 (opcode=7, Rd=4, Rs=5, mode=0)
    # ADD R3, R4 -> 0x7453 (opcode=3, Rd=3, Rs=4, mode=0)
    # HALT -> 0x007F
    
    simple_program = [
        0x0301,  # MOV R3, #0      ; word 1: opcode=0, Rd=3, Rs=0, mode=1
        0x0000,  # word 2: immediate value 0
        0x0401,  # MOV R4, #1      ; word 1: opcode=0, Rd=4, Rs=0, mode=1
        0x0001,  # word 2: immediate value 1
        0x0501,  # MOV R5, #2      ; word 1: opcode=0, Rd=5, Rs=0, mode=1
        0x0002,  # word 2: immediate value 2
        0x1543,  # MUL R4, R5      ; R4:R5 = 1*2 = 2
        0x7453,  # ADD R3, R4      ; result += 2 (R3 = 0 + 2 = 2)
        0x007F,  # HALT
    ]
    
    cpu.load_program(simple_program)
    
    # Run and check result
    steps = cpu.run()
    print(f"Execution completed in {steps} steps")
    print(f"Final R3: {cpu.regs[3]} (expected: 2)")
    print(f"Final R4: {cpu.regs[4]} (should be 0)")
    print(f"Final R5: {cpu.regs[5]} (should be 0)")
    print(f"CPU halted: {cpu.halted}")
    
    if cpu.regs[3] == 2:
        print("✅ SIMPLE TEST PASSED!")
    else:
        print("❌ SIMPLE TEST FAILED!")
        print("This indicates an issue with the CPU implementation or encoding.")

if __name__ == "__main__":
    simple_convolution_test()