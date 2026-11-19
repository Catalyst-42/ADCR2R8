; Task 2: convolution (sum of products) of two 6-element unsigned arrays
; Full convolution: result = sum_{i=0 to 5} sum_{j=0 to 5} A[i] * B[j]
; A[0] size is at 0x100, elements at 0x101..0x106
; B[0] size is at 0x200, elements at 0x201..0x206
; result (48-bit container): 0x300 low, 0x301 middle, 0x302 high

        MOV  R0, #0           ; outer loop counter i
        MOV  R8, #0           ; result low word
        MOV  R9, #0           ; result middle word  
        MOV  R10, #0          ; result high word

outer:  MOV  R1, #0           ; inner loop counter j
        MOV  R2, #0x101       ; pointer into A
        MOV  R3, #0x201       ; pointer into B

inner:  LOAD R4, [R2]        ; A[i]
        LOAD R5, [R3]        ; B[j]
        MUL  R4, R5          ; R4:R5 = A[i] * B[j]
        ADD  R8, R4          ; add low word
        ADC  R9, R5          ; add high word + carry
        ADC  R10, #0         ; preserve carry beyond 32 bits
        INC  R3              ; next B element
        INC  R1              ; increment inner counter
        CMP  R1, #6
        JNZ  inner           ; jump to inner loop (0x00E)

        INC  R2              ; next A element  
        INC  R0              ; increment outer counter
        CMP  R0, #6
        JNZ  outer           ; jump to outer loop (0x008)

done:   STORE [0x300], R8     ; low word of result
        STORE [0x301], R9     ; middle word of result
        STORE [0x302], R10    ; high word of result
        HALT