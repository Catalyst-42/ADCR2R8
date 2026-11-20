; Sum of products of two arrays

; Memory
; 0x0000 - Answer
; 0x0001 - First value of array A
; 0x0007 - First value of array B

; Registers
; R0 - Result
; R1 - Index for array A
; R2 - Index for array B
; R3 - A[R1]
; R4 - B[R2]

MOV  R0, #0                 ; Init zero result
MOV  R1, #0x0001            ; Set R1 point to A[0]
MOV  R2, #0x0007            ; Set R2 point to B[0]

loop:
    CMP  R1, #0x0007        ; If we got begin of array B on index of A
        JZ   done           ; Then we are done

    LOAD R3, [R1]           ; Load A[R1]
    LOAD R4, [R2]           ; Load B[R2]

    MUL  R3, R4             ; Multiply A[i] * B[i]
    ADD  R0, R3             ; Sum product with result

    INC  R1                 ; Bump pointers and loop once again
    INC  R2
    JMP  loop

done:
    STORE [0x0000], R0      ; Dump sum of products to answer memory slot
    HALT
