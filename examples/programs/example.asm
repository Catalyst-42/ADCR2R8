; Calculate sum of 11 and 31

; Memory
; 0x0000 - Answer

; Registers
; R2 - First operand
; R8 - Second operand

MOV R2, #11         ; Load 11 to R2
MOV R8, #31         ; Load 31 to R8
ADC R2, R8          ; The project number goes from there

STORE [0x0000], R2  ; Store total to memory
HALT
