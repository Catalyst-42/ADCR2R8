#!/usr/bin/env python3
"""
Debug the convolution step by step.
"""

from pathlib import Path
from src.assembler.parser import assemble_file
from src.cpu.cpu import CPU

def debug_convolution():
    """Debug convolution step by step."""
    print("=== DEBUG CONVOLUTION ===")
    
    # Create CPU instance
    cpu = CPU()
    
    # Load the final program
    program_path = Path('src/programs/convolution_final.asm')
    words = assemble_file(program_path)
    cpu.load_program(words)
    print(f"Loaded {program_path.name}")
    
    # Load simple test data - smaller arrays to debug
    array_a = [2] + [10, 20]      # Size=2, elements=[10,20]
    array_b = [2] + [1, 2]        # Size=2, elements=[1,2]
    
    cpu.load_data(0x100, array_a)  # Array A base address
    cpu.load_data(0x200, array_b)  # Array B base address
    
    print(f"Array A: {array_a}")
    print(f"Array B: {array_b}")
    
    # Manual calculation for 2x2 case
    manual_result = 0
    print("\nManual calculation:")
    for i in range(2):
        for j in range(2):
            product = array_a[1+i] * array_b[1+j]
            manual_result += product
            print(f"  A[{i}] * B[{j}] = {array_a[1+i]} * {array_b[1+j]} = {product}")
    print(f"Manual total: {manual_result}")
    
    # Run step by step and track
    print(f"\nInitial memory state:")
    print(f"  dmem[0x100] = {cpu.dmem[0x100]} (size A)")
    print(f"  dmem[0x101] = {cpu.dmem[0x101]} (A[0])")
    print(f"  dmem[0x102] = {cpu.dmem[0x102]} (A[1])")
    print(f"  dmem[0x200] = {cpu.dmem[0x200]} (size B)")
    print(f"  dmem[0x201] = {cpu.dmem[0x201]} (B[0])")
    print(f"  dmem[0x202] = {cpu.dmem[0x202]} (B[1])")
    
    # Reset and run step by step
    cpu.reset()
    print(f"\nStep-by-step execution:")
    
    step_count = 0
    while not cpu.halted and step_count < 50:
        # Show current state
        print(f"Step {step_count}: PC=0x{cpu.pc:03X}, IR=0x{cpu.ir:04X}")
        print(f"  R0={cpu.regs[0]:04X}, R8={cpu.regs[8]:04X}, R9={cpu.regs[9]:04X}, R10={cpu.regs[10]:04X}")
        
        # Execute one step
        instruction = cpu.step()
        step_count += 1
        
        if instruction is not None:
            print(f"  Executed: {instruction.assembly}")
        else:
            print("  HALT")
            break
            
        # Check memory at result location periodically
        if step_count % 10 == 0:
            print(f"  Result so far: dmem[0x300]={cpu.dmem[0x300]}, dmem[0x301]={cpu.dmem[0x301]}, dmem[0x302]={cpu.dmem[0x302]}")
    
    print(f"\nFinal result:")
    result_low = cpu.dmem[0x300]
    result_mid = cpu.dmem[0x301] 
    result_high = cpu.dmem[0x302]
    result = result_low + (result_mid << 16) + (result_high << 32)
    print(f"Low: {result_low}, Mid: {result_mid}, High: {result_high}")
    print(f"Total: {result}")
    print(f"Expected: {manual_result}")

if __name__ == "__main__":
    debug_convolution()