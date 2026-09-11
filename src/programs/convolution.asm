; Task 2: convolution (sum of products) of two 6-element unsigned arrays
; A[0] size is at 0x100, elements at 0x101..0x106
; B[0] size is at 0x200, elements at 0x201..0x206
; result (32-bit) written to 0x300 (low word) / 0x301 (high word)

        MOV  R0, #0           ; i = 0
        MOV  R1, #0x101       ; pointer into A
        MOV  R2, #0x201       ; pointer into B
        MOV  R3, #0           ; result low word
        MOV  R4, #0           ; result high word

loop:   CMP  R0, #6           ; processed all 6 elements?
        JZ   done
        LOAD R5, [R1]         ; A[i]
        LOAD R7, [R2]         ; B[i]
        MUL  R5, R7           ; R5:R6 = A[i] * B[i]  (low:high)
        ADD  R3, R5           ; result_low  += product_low   (sets CF on overflow)
        ADC  R4, R6           ; result_high += product_high + CF
        INC  R1
        INC  R2
        INC  R0
        JMP  loop

done:   STORE [0x300], R3     ; low word of result
        STORE [0x301], R4     ; high word of result
        HALT
