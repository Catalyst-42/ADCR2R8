; Sum of products of two arrays

; Memory
; 0x0000 - Answer
; 0x0001 - Answer
; 0x0002 - Answer
; 0x0003 - First value of array A
; 0x0009 - First value of array B

; Registers
; R0 - High part of result
; R1 - Mid part of result
; R2 - Low part of result
; R3 - Product
; R4 - Product
; R5 - Pointer to array A
; R6 - Pointer to array B

MOV  R0, #0                 ; Init answer with zero
MOV  R1, #0
MOV  R2, #0
MOV  R5, #0x0003            ; Init pointers
MOV  R6, #0x0009

loop:
    CMP  R5, #0x0009        ; If pointer of A reach the begin of B
        JZ   done           ; Then we are done

    LOAD R3, [R5]           ; Get A[R5] and B[R6] for multiplication
    LOAD R4, [R6]

    MUL  R3, R4             ; Multiply values
    ADD  R2, R3             ; Sum up product with account of carry
    ADC  R1, R4
    ADC  R0, #0

    INC  R5                 ; Move pointers step next
    INC  R6
    JMP  loop

done:
    STORE [0x0000], R0      ; Dump sum of products to memory
    STORE [0x0001], R1
    STORE [0x0002], R2
    HALT
