; Sum of products of two arrays

; Memory
; 0x0000 - Answer / result (low 16 bits)
; 0x0001 - Size of array N
; 0x0002 - Beginning of first array A
; 0x0002 + N - Beginning of second array B
; 0x0200 - Working data
; 0x0201 - Working data
; 0x0202 - Working data

; Registers
; R0 - Array index i
; R1 - Address of A[i]
; R2 - Address of B[i]
; R3 - Result accumulator
; R4 - Working data
; R5 - Working data
; R6 - Working data
; R7 - A[i] / product low
; R8 - B[i] / product high

MOV  R0, #0           ; i = 0
MOV  R1, #0x0002      ; pointer into A (starts at 0x0002)
MOV  R2, #0x0008      ; pointer into B (0x0002 + N, where N = 6)
MOV  R3, #0           ; result accumulator
MOV  R4, #0x0200      ; working data at safe address
MOV  R5, #0x0201      ; working data at another safe address
MOV  R6, #0x0202      ; working data at third safe address

loop:
        CMP  R0, #6           ; processed all 6 elements?
        JZ   done             ; We are done

        LOAD R7, [R1]         ; R7 = A[i]
        LOAD R8, [R2]         ; R8 = B[i]
        MUL  R7, R8           ; R7:R8 = A[i] * B[i] (low:high)
        ADD  R3, R7           ; result += product_low
        STORE [0x0202], R8    ; store product_high in working data

        INC  R1               ; advance pointer to A[i+1]
        INC  R2               ; advance pointer to B[i+1]
        INC  R0               ; bump index
        JMP  loop             ; Go to loop once again

done:
        STORE [0x0000], R3    ; output result at address 0x0000
        STORE [0x0200], R4    ; store working data at safe address
        STORE [0x0201], R5    ; store more working data
        STORE [0x0203], R6    ; store even more working data
        HALT                  ; Done
