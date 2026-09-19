"""Headless demonstration: python -m src.cpu.demo."""
from pathlib import Path
from src.assembler.parser import assemble_file
from src.cpu.cpu import CPU


def main():
    programs = Path(__file__).resolve().parents[1] / 'programs'
    for name in ('find_max', 'convolution'):
        cpu = CPU()
        words = assemble_file(programs / f'{name}.asm', mem_size=None)
        cpu.load_program(words)
        cpu.load_data(0x100, [6] + [65535] * 6)
        if name == 'convolution':
            cpu.load_data(0x200, [6] + [65535] * 6)
        count = cpu.run()
        if not cpu.halted:
            raise RuntimeError('Instruction limit reached before HALT')
        result = (cpu.dmem[0x200] if name == 'find_max' else
                  sum(cpu.dmem[0x300 + i] << (16 * i) for i in range(3)))
        print(f'{name}:')
        print(' '.join(f'0x{word:04X}' for word in words))
        print(f'Result: {result} (0x{result:X}); steps: {count}; halted: {cpu.halted}')


if __name__ == '__main__':
    main()
