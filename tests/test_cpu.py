"""Run all core and parser tests with python -m unittest discover -s tests -v."""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.cpu.cpu import CPU, CPUError
from src.assembler.parser import assemble_source, assemble_file
from src.assembler.errors import AsmError

PROGRAMS = Path(__file__).resolve().parents[1] / 'src' / 'programs'


class CoreTests(unittest.TestCase):
    def cpu(self, source):
        cpu = CPU()
        cpu.load_program(assemble_source(source))
        return cpu

    def test_raw_machine_words_and_steps(self):
        c = CPU()
        c.load_program([0x0101, 7, 0x0201, 5, 0x0310, 0x3320, 0x007F])
        self.assertEqual(c.step().assembly, 'MOV R1, #0x0007')
        self.assertEqual((c.pc, c.ir), (2, 0x0101))
        self.assertEqual(c.run(), 4)
        self.assertEqual(c.regs[3], 12)
        state = c.snapshot()
        self.assertIsNone(c.step())
        self.assertEqual(c.run(), 0)
        self.assertEqual(c.snapshot(), state)

    def test_all_source_modes_and_memory_isolation(self):
        c = self.cpu('MOV R0, #10\nMOV R1, R0\nSTORE [100], R1\nMOV R2, #100\nLOAD R3, [R2]\nADD R3, [100]\nADD R3, [R2]\nSTORE [R2], R3\nLOAD R4, [100]\nHALT')
        code = c.imem.copy()
        c.run()
        self.assertEqual(c.regs[4], 30)
        self.assertEqual(c.dmem[100], 30)
        self.assertEqual(c.imem, code)

    def test_arithmetic_flags(self):
        cases = [('ADD', 65535, 1, False, 0, True),
                 ('ADC', 65535, 0, True, 0, True),
                 ('SUB', 0, 1, False, 65535, True),
                 ('SBB', 0, 65535, True, 0, True),
                 ('DIV', 203, 4, True, 50, False),
                 ('AND', 0xAAAA, 0x5555, True, 0, False),
                 ('OR', 0xAAAA, 0x5555, True, 65535, False),
                 ('XOR', 0xAAAA, 0xAAAA, True, 0, False)]
        for op, a, b, carry, result, cf in cases:
            with self.subTest(op=op):
                c = self.cpu(f'{op} R0, R1')
                c.regs[:2] = [a, b]
                c.CF = carry
                c.step()
                self.assertEqual((c.regs[0], c.CF, c.ZF, c.SF),
                                 (result, cf, result == 0, bool(result & 0x8000)))

    def test_unary_and_cmp(self):
        c = self.cpu('INC R0\nDEC R0\nNOT R0\nCMP R0, #0')
        c.regs[0] = 65535
        c.step()
        self.assertEqual((c.regs[0], c.ZF, c.CF), (0, True, True))
        c.step()
        self.assertEqual((c.regs[0], c.SF, c.CF), (65535, True, True))
        c.step()
        self.assertEqual((c.regs[0], c.ZF, c.CF), (0, True, False))
        c.step()
        self.assertEqual((c.regs[0], c.ZF), (0, True))

    def test_multiply_aliases_and_carry(self):
        for rd, rs in [(0, 0), (0, 1), (14, 15)]:
            for carry in (False, True):
                c = self.cpu(f'MUL R{rd}, R{rs}')
                c.regs[rd] = c.regs[rs] = 65535
                c.CF = carry
                c.step()
                self.assertEqual(c.regs[rd:rd+2], [1, 65534])
                self.assertEqual((c.CF, c.ZF, c.SF), (carry, False, True))

    def test_multiply_flags_use_the_full_product(self):
        for a, b, words, zero in [
            (256, 256, [0, 1], False),
            (0, 65535, [0, 0], True),
        ]:
            with self.subTest(a=a, b=b):
                cpu = self.cpu('MUL R0, R1')
                cpu.regs[:2] = [a, b]
                cpu.step()
                self.assertEqual(cpu.regs[:2], words)
                self.assertEqual((cpu.ZF, cpu.SF), (zero, False))

    def test_indirect_address_uses_register_before_write(self):
        for source, expected in [
            ('LOAD R1, [R1]', 42),
            ('ADD R1, [R1]', 142),
            ('STORE [R1], R1', 100),
        ]:
            with self.subTest(source=source):
                cpu = self.cpu(source)
                cpu.regs[1] = 100
                cpu.load_data(100, [42])
                cpu.step()
                result = cpu.dmem[100] if source.startswith('STORE') else cpu.regs[1]
                self.assertEqual(result, expected)

    def test_moves_preserve_flags(self):
        c = self.cpu('MOV R0, #4\nSTORE [100], R0\nLOAD R1, [100]\nHALT')
        c.ZF = c.CF = c.SF = True
        c.run()
        self.assertEqual((c.ZF, c.CF, c.SF), (True, True, True))

    def test_every_branch_taken_and_not_taken(self):
        for name, flag, polarity in [('JZ', 'ZF', True), ('JNZ', 'ZF', False),
                                      ('JC', 'CF', True), ('JNC', 'CF', False),
                                      ('JS', 'SF', True), ('JNS', 'SF', False)]:
            for taken in (False, True):
                with self.subTest(name=name, taken=taken):
                    c = self.cpu(f'{name} 4\nMOV R0, #1\nHALT')
                    setattr(c, flag, polarity if taken else not polarity)
                    c.step()
                    self.assertEqual(c.pc, 4 if taken else 2)
        c = self.cpu('JMP 0')
        self.assertEqual(c.run(20), 20)
        self.assertEqual(c.pc, 0)
        self.assertFalse(c.halted)

    def test_decode_snapshot_reset_reload(self):
        c = self.cpu('MOV R0, #1\nHALT')
        before = c.snapshot()
        self.assertEqual(c.decode().length, 2)
        self.assertEqual(c.snapshot(), before)
        c.load_data(100, [42])
        c.run()
        c.reset()
        self.assertEqual((c.pc, c.regs[0], c.halted, c.dmem[100]), (0, 0, False, 42))
        c.load_program([0x007F])
        self.assertEqual(c.imem[1:4], [0, 0, 0])
        snapshot = c.snapshot()
        snapshot['regs'][0] = 999
        snapshot['dmem'][100] = 0
        self.assertEqual((c.regs[0], c.dmem[100]), (0, 42))

    def test_invalid_program_load_is_atomic(self):
        c = self.cpu('HALT')
        for words in [[-1], [65536], ['0x007F'], [True], [1.2], [0] * 4097]:
            state = c.snapshot()
            with self.assertRaises(CPUError):
                c.load_program(words)
            self.assertEqual(c.snapshot(), state)
        for address, values in [(4095, [1, 2]), (-1, [1]), (0, [1, -1])]:
            state = c.snapshot()
            with self.assertRaises(CPUError):
                c.load_data(address, values)
            self.assertEqual(c.snapshot(), state)

    def test_faults_are_atomic(self):
        for words, error in [([0x8010], ZeroDivisionError), ([0x7F00], CPUError),
                             ([0x0004], CPUError), ([0x008F], CPUError),
                             ([0x1000], CPUError), ([0x000F, 4096], CPUError),
                             ([0x1002, 4096], CPUError), ([0x9010], CPUError)]:
            with self.subTest(words=words):
                c = CPU()
                c.load_program(words)
                state = c.snapshot()
                with self.assertRaises(error):
                    c.step()
                self.assertEqual(c.snapshot(), state)
        c = self.cpu('LOAD R0, [R1]')
        c.regs[1] = 65535
        state = c.snapshot()
        with self.assertRaises(CPUError):
            c.step()
        self.assertEqual(c.snapshot(), state)

    def test_memory_boundary_and_limits(self):
        c = CPU()
        c.pc = 4095
        c.imem[4095] = 0x0001
        state = c.snapshot()
        with self.assertRaises(CPUError):
            c.step()
        self.assertEqual(c.snapshot(), state)
        c.imem[4095] = 0x007F
        c.step()
        self.assertTrue(c.halted)
        for limit in [-1, 1.5, True]:
            with self.assertRaises(CPUError):
                c.run(limit)
        self.assertEqual(c.run(0), 0)

    def test_find_max(self):
        rng = random.Random(17)
        for values in [[], [65535], [0] * 6, [3, 65535, 7, 32768, 2, 9]] + [
                [rng.randrange(65536) for _ in range(n)] for n in range(6, 16)]:
            c = CPU()
            c.load_program(assemble_file(PROGRAMS / 'find_max.asm'))
            c.load_data(0x100, [len(values)] + values)
            c.run()
            self.assertTrue(c.halted)
            self.assertEqual(c.dmem[0x200], max(values, default=0))

    def test_convolution_full_precision(self):
        rng = random.Random(19)
        pairs = [([0] * 6, [0] * 6), ([65535] * 6, [65535] * 6),
                 ([1, 2, 3, 4, 5, 6], [6, 5, 4, 3, 2, 1])]
        pairs += [([rng.randrange(65536) for _ in range(6)],
                   [rng.randrange(65536) for _ in range(6)]) for _ in range(25)]
        for a, b in pairs:
            c = CPU()
            c.load_program(assemble_file(PROGRAMS / 'convolution.asm'))
            c.load_data(0x100, [6] + a)
            c.load_data(0x200, [6] + b)
            c.run()
            self.assertTrue(c.halted)
            actual = sum(c.dmem[0x300 + i] << (16 * i) for i in range(3))
            self.assertEqual(actual, sum(x * y for x, y in zip(a, b)))

    def test_parser_rejects_unsupported_forms(self):
        for source in ['HALT R0', 'MUL R15, R0', 'LOAD R0, #1', 'STORE R0, R1', 'LOAD R0, [4096]']:
            with self.subTest(source=source), self.assertRaises(AsmError):
                assemble_source(source)


if __name__ == '__main__':
    unittest.main()
