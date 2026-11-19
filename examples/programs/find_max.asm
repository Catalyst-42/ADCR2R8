; Find maximum of array
;
; Memory
; 0x0000 - Answer
; 0x0001 - Size of array
; 0x0002 - Values of an array

LOAD R0, [0x0001]      ; R0 = N (array length from 0x0001)
MOV  R3, #0            ; empty array returns 0
CMP  R0, #0
JZ   done

MOV  R1, #2           ; R1 = index, start at 2 (element 0 at 0x0002 already taken as initial max)
MOV  R2, #0x0002      ; R2 = pointer to current element (address)
LOAD R3, [R2]         ; R3 = current max = A[0]

loop:   CMP  R1, R0           ; if index is n 
        JZ   done
        INC  R2               ; advance pointer to A[index]
        LOAD R4, [R2]         ; R4 = A[index]
        CMP  R3, R4           ; R3 - R4  (CF=1 if R3 < R4, unsigned)
        JNC  skip             ; if R3 >= R4, keep current max
        MOV  R3, R4           ; else new max found

skip:   INC  R1
        JMP  loop

done:   STORE [0x0000], R3
        HALT
