; Task 1: find the maximum element in array A (unsigned)
; A[0] size N is at 0x100, elements at 0x101..0x100+N
; result written to 0x200

        LOAD R0, [0x100]      ; R0 = N (array length)
        MOV  R1, #1           ; R1 = index, start at 1 (element 0 already taken as initial max)
        MOV  R2, #0x101       ; R2 = pointer to current element (address)
        LOAD R3, [R2]         ; R3 = current max = A[0]

loop:   CMP  R1, R0           ; index == N ?
        JZ   done
        INC  R2               ; advance pointer to A[index]
        LOAD R4, [R2]         ; R4 = A[index]
        CMP  R3, R4           ; R3 - R4  (CF=1 if R3 < R4, unsigned)
        JNC  skip             ; if R3 >= R4, keep current max
        MOV  R3, R4           ; else new max found
skip:   INC  R1
        JMP  loop

done:   STORE [0x200], R3     ; write result
        HALT
