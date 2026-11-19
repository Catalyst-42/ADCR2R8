; Task 2: convolution (sum of products) of two unsigned arrays
; Task 2: convolution (sum of products) of two unsigned arrays
; Using SIMPLE data structure:
; dmem[0x0000] = output/result (low 16 bits)
; dmem[0x0001] = array size N
; dmem[0x0002+] = first array A[0]..A[N-1]
; dmem[0x0002+N+] = second array B[0]..B[N-1]
; Working data uses safe available addresses

        MOV  R0, #0           ; i = 0
        MOV  R1, #2           ; pointer into A (starts at 0x0002)
        MOV  R2, #8           ; pointer into B (starts at 0x0002+N, where N=6)
        MOV  R3, #0           ; result accumulator
        MOV  R4, #0x0200      ; working data at safe address (past arrays)
        MOV  R5, #0x0201      ; working data at another safe address
        MOV  R6, #0x0202      ; working data at third safe address

loop:    CMP  R0, #6           ; processed all 6 elements?
        JZ   done
        LOAD R7, [R1]         ; A[i]
        LOAD R8, [R2]         ; B[i]
        MUL  R7, R8           ; R7:R8 = A[i] * B[i]  (low:high)
        ADD  R3, R7           ; result += product_low
        STORE [0x0202], R8    ; store product_high in working data
        INC  R1
        INC  R2
        INC  R0
        JMP  loop

done:   STORE [0x0000], R3     ; output result at address 0x0000
        STORE [0x0200], R4    ; store working data at safe addresses
        STORE [0x0201], R5    ; store more working data
        STORE [0x0203], R6    ; store even more working data
        HALT
