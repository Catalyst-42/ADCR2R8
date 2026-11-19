; GUI smoke test for ADCR2R8
; Expected after HALT:
;   R1 = 0x000C
;   R3 = 0x000C
;   dmem[0x350] = 0x000C
;   dmem[0x351] = 0x1234
;
; Use it with:
;   python main.py src/programs/test_gui.asm
; Press Step to execute one instruction at a time, or Run.

        MOV  R1, #5          ; R1 = 5
        MOV  R2, #7          ; R2 = 7
        ADD  R1, R2          ; R1 = 12
        STORE [0x350], R1    ; save the result to data memory
        LOAD  R3, [0x350]    ; load it back into R3
        CMP   R3, #12        ; ZF = 1 when the result is correct
        JNZ   fail           ; go to fail if the result is not 12
        MOV   R4, #0x1234
        STORE [0x351], R4    ; success marker
        HALT

fail:   MOV   R4, #0xFFFF
        STORE [0x351], R4    ; failure marker
        HALT
