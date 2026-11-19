; Find maximum of array

; Memory
; 0x0000 - Answer
; 0x0001 - Size of array
; 0x0002 - Beginning of array values

; Registers
; R0 - Array length
; R1 - Index of array
; R2 - Address of array value
; R3 - Current maximum of array
; R4 - Ongoing comparsion element

LOAD R0, [0x0001]           ; Load array length
MOV  R3, #0                 ; Load default answer value
CMP  R0, #0                 ; If array length is zero
    JZ   done               ; Then jump on done

LOAD R3, [0x0002]           ; Set first array element as current max
MOV  R2, #0x0002            ; Load first element address to comparsion pointer
MOV  R1, #1                 ; Increment index to second element because first one is already accounted

loop:
    CMP  R0, R1             ; If array index equal to n
        JZ   done           ; We are done

    INC  R2                 ; Increment R2 to next index
    LOAD R4, [R2]           ; Load next comparsion value from array
    CMP  R3, R4             ; If max greater or equal to R4
        JNC  skip           ; Then skip updating
                            ; Otherwise
    MOV  R3, R4             ; Set max from R4

skip:
    INC  R1                 ; Bump index
    JMP  loop               ; Go to loop once again

done:
    STORE [0x0000], R3      ; Dump maximum value from R3 to answer memory slot
    HALT                    ; Done
