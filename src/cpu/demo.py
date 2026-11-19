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
        cpu.load_data(0x0001, [6] + [2342] * 6)

        if name == 'convolution':
            cpu.load_data(0x0002 + 6, [6] + [2342] * 6)

        count = cpu.run()

        if not cpu.halted:
            raise RuntimeError('Instruction limit reached before HALT')

        # Use simple data structure: result is at 0x0000 (single word)
        result = cpu.dmem[0x0000]

        print(f'{name}:')
        print(' '.join(f'0x{word:04X}' for word in words))
        print(f'Result: {result} (0x{result:X}); steps: {count}; halted: {cpu.halted}')


if __name__ == '__main__':
    main()
