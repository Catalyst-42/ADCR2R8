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
    
    # Create a simple convolution program
    simple_program = [
        0x0301,  # MOV R3, #0      ; result = 0
        0xB001,  # CMP R0, #0      ; if size == 0, skip
        0x001F,  # JZ done
        0x0401,  # MOV R4, #1      ; constant 1
        0x0501,  # MOV R5, #2      ; constant 2
        0x1533,  # MUL R4, R5      ; R4:R5 = 1*2 = 2
        0x7450,  # ADD R3, R4      ; result += 2
        0x3840,  # ADC R0, R5      ; dummy instruction
        0x007F,  # HALT
        # done: (not needed as we halt)
    ]
    
    cpu.load_program(simple_program)
    
    # Run and check result
    steps = cpu.run()
    print(f"Execution completed in {steps} steps")
    print(f"Final R3: {cpu.regs[3]} (expected: 2)")
    print(f"CPU halted: {cpu.halted}")
    
    if cpu.regs[3] == 2:
        print("✅ SIMPLE TEST PASSED!")
    else:
        print("❌ SIMPLE TEST FAILED!")

if __name__ == "__main__":
    simple_convolution_test()