#!/usr/bin/env python3
"""
Complete working example for GUI testing with real data.
This script loads actual test data and runs the programs.
"""

from pathlib import Path
from src.assembler.parser import assemble_file
from src.cpu.cpu import CPU

def setup_find_max_test():
    """Setup find_max.asm with real test data."""
    print("=== Setting up FIND MAX test ===")
    
    # Create CPU instance
    cpu = CPU()
    
    # Load the program
    program_path = Path('src/programs/find_max.asm')
    words = assemble_file(program_path)
    cpu.load_program(words)
    print(f"Loaded {program_path.name} ({len(words)} words)")
    
    # Load REAL test data into memory
    test_array = [6] + [10, 45, 2, 65535, 8, 3]  # Size=6, elements=[10,45,2,65535,8,3]
    cpu.load_data(0x100, test_array)
    print(f"Loaded test array: {test_array}")
    print(f"Array size at 0x100: {cpu.dmem[0x100]}")
    print(f"Array elements at 0x101-0x106: {cpu.dmem[0x101:0x107]}")
    
    return cpu

def setup_convolution_test():
    """Setup convolution.asm with real test data."""
    print("\n=== Setting up CONVOLUTION test ===")
    
    # Create CPU instance
    cpu = CPU()
    
    # Load the program
    program_path = Path('src/programs/convolution_fixed.asm')
    words = assemble_file(program_path)
    cpu.load_program(words)
    print(f"Loaded {program_path.name} ({len(words)} words)")
    
    # Load REAL test data for both arrays
    array_a = [6] + [10, 20, 30, 40, 50, 60]    # 6 elements at 0x101+
    array_b = [6] + [1, 2, 3, 4, 5, 6]          # 6 elements at 0x201+
    
    cpu.load_data(0x100, array_a)  # Array A base address
    cpu.load_data(0x200, array_b)  # Array B base address
    print(f"Array A: {array_a}")
    print(f"Array B: {array_b}")
    
    return cpu

def run_cpu_test(cpu, program_name):
    """Run CPU test and show results."""
    print(f"\n=== Running {program_name} ===")
    
    # Show initial state
    print("Initial registers:", [f"R{i}=0x{reg:04X}" for i, reg in enumerate(cpu.regs)])
    print("Initial flags: ZF=0, CF=0, SF=0")
    
    # Run the program
    steps = cpu.run()
    
    # Show final state
    print(f"\nExecution completed in {steps} steps")
    print(f"CPU halted: {cpu.halted}")
    print(f"Final PC: 0x{cpu.pc:03X} ({cpu.pc})")
    print(f"Final IR: 0x{cpu.ir:04X} ({cpu.ir})")
    print(f"Final flags: ZF={cpu.ZF}, CF={cpu.CF}, SF={cpu.SF}")
    
    # Show results
    if program_name == "find_max":
        result = cpu.dmem[0x200]
        print(f"\n🎯 FIND MAX RESULT:")
        print(f"Maximum value: {result} (0x{result:04X})")
        expected = max([10, 45, 2, 65535, 8, 3])  # Should be 65535
        print(f"Expected: {expected} (0x{expected:04X})")
        print(f"✅ CORRECT!" if result == expected else "❌ WRONG!")
        
    elif program_name == "convolution":
        result_low = cpu.dmem[0x300]
        result_mid = cpu.dmem[0x301] 
        result_high = cpu.dmem[0x302]
        result = result_low + (result_mid << 16) + (result_high << 32)
        print(f"\n🎯 CONVOLUTION RESULT:")
        print(f"Low word:  {result_low} (0x{result_low:04X})")
        print(f"Mid word:  {result_mid} (0x{result_mid:04X})") 
        print(f"High word: {result_high} (0x{result_high:04X})")
        print(f"Full result: {result} (0x{result:X})")
        
        # Manual calculation for verification
        a = [10, 20, 30, 40, 50, 60]
        b = [1, 2, 3, 4, 5, 6]
        expected = sum(a[i] * b[j] for i in range(6) for j in range(6))
        print(f"Expected: {expected} (0x{expected:X})")
        print(f"✅ CORRECT!" if result == expected else "❌ WRONG!")

def main():
    """Run complete tests with real data."""
    print("🚀 ADCR2R8 Complete Working Tests")
    print("=" * 50)
    
    # Test 1: Find Maximum
    cpu1 = setup_find_max_test()
    run_cpu_test(cpu1, "find_max")
    
    # Test 2: Convolution  
    cpu2 = setup_convolution_test()
    run_cpu_test(cpu2, "convolution")
    
    print("\n" + "=" * 50)
    print("✅ ALL TESTS COMPLETED!")
    print("\n💡 To use in GUI:")
    print("1. Run: python main.py")
    print("2. Use the CPU instances above to manually load data")
    print("3. Then load .asm files and run")

if __name__ == "__main__":
    main()