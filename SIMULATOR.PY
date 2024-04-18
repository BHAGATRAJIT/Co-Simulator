import sys
import os

# Constants for opcodes
R_OPCODE = "0110011"
I_OPCODE = ["0000011", "0010011", "1100111"]
S_OPCODE = "0100011"
B_OPCODE = "1100011"
U_OPCODE = ["0010111", "0110111"]
JAL_OPCODE = "1101111"

# Helper functions
def sign_extend(imm):
    # Sign extend immediate to 32 bits
    if imm[0] == '1':
        return imm.ljust(32, imm[0])
    else:
        return imm.rjust(32, imm[0])

def decimal_to_binary(num):
    # Convert decimal to binary with 32 bits
    binary = bin(num & 0xFFFFFFFF)[2:]
    return binary.zfill(32)

def binary_to_decimal(binary):
    # Convert binary to decimal
    return int(binary, 2)

# R-type instructions
def execute_r_type(inst, pc, reg_dic):
    ti = inst[::-1]
    rd = ti[7:12][::-1]
    rs1 = ti[15:20][::-1]
    rs2 = ti[20:25][::-1]
    funct3 = ti[12:15][::-1]
    funct7 = inst[:7]

    if (funct3 == "000") and (funct7 == "0000000"):
        reg_dic[rd] = decimal_to_binary(binary_to_decimal(reg_dic[rs1]) + binary_to_decimal(reg_dic[rs2]))
    elif (funct3 == "000") and (funct7 == "0100000"):
        reg_dic[rd] = decimal_to_binary(binary_to_decimal(reg_dic[rs1]) - binary_to_decimal(reg_dic[rs2]))
    elif (funct3 == "010") and (funct7 == "0000000"):
        if binary_to_decimal(reg_dic[rs1]) < binary_to_decimal(reg_dic[rs2]):
            reg_dic[rd] = "00000000000000000000000000000001"
        else:
            reg_dic[rd] = "00000000000000000000000000000000"
    elif (funct3 == "011") and (funct7 == "0000000"):
        if binary_to_decimal(reg_dic[rs1]) < binary_to_decimal(reg_dic[rs2]):
            reg_dic[rd] = "00000000000000000000000000000001"
        else:
            reg_dic[rd] = "00000000000000000000000000000000"
    elif (funct3 == "100") and (funct7 == "0000000"):
        reg_dic[rd] = decimal_to_binary(binary_to_decimal(reg_dic[rs1]) ^ binary_to_decimal(reg_dic[rs2]))
    elif (funct3 == "001") and (funct7 == "0000000"):
        reg_dic[rd] = decimal_to_binary(binary_to_decimal(reg_dic[rs1]) << binary_to_decimal(reg_dic[rs2][-5:]))
    elif (funct3 == "101") and (funct7 == "0000000"):
        reg_dic[rd] = decimal_to_binary(binary_to_decimal(reg_dic[rs1]) >> binary_to_decimal(reg_dic[rs2][-5:]))
    elif (funct3 == "110") and (funct7 == "0000000"):
        reg_dic[rd] = decimal_to_binary(binary_to_decimal(reg_dic[rs1]) | binary_to_decimal(reg_dic[rs2]))
    elif (funct3 == "111") and (funct7 == "0000000"):
        reg_dic[rd] = decimal_to_binary(binary_to_decimal(reg_dic[rs1]) & binary_to_decimal(reg_dic[rs2]))        
    return pc + 4

# I-type instructions
def execute_i_type(inst, pc, reg_dic, mem_dic):
    ti = inst[::-1]
    imm = inst[:12]
    imm = sign_extend(imm)
    imm = binary_to_decimal(imm)

    rd = ti[7:12][::-1]
    rs1 = ti[15:20][::-1] 
    funct3 = ti[12:15][::-1]
    opcode = inst[-7:]

    if (funct3 == "010") and (opcode == "0000011"):
        rs1_val = binary_to_decimal(reg_dic[rs1])
        mem_addr = decimal_to_binary(rs1_val + imm)
        mem_addr_hex = hex(binary_to_decimal(mem_addr))[2:].zfill(8)
        reg_dic[rd] = mem_dic.get(mem_addr_hex, "00000000000000000000000000000000")
    elif funct3 == "000" and (opcode == "0010011"):
        rs1_val = binary_to_decimal(reg_dic[rs1])
        reg_dic[rd] = decimal_to_binary(rs1_val + imm)
    elif funct3 == "000" and (opcode == "1100111"):
        reg_dic[rd] = decimal_to_binary(pc + 4)
        pc = binary_to_decimal(reg_dic[rs1]) + imm
    return pc

# S-type instructions
def execute_s_type(inst, pc, reg_dic, mem_dic, reg_opc_to_mem_add):
    ti = inst[::-1]
    imm = inst[:7] + inst[20:25]
    imm = sign_extend(imm)
    imm = binary_to_decimal(imm)

    rs1 = ti[15:20][::-1]
    rs1_val = binary_to_decimal(reg_dic[rs1])
    mem_addr = decimal_to_binary(rs1_val + imm)
    mem_addr_hex = hex(binary_to_decimal(mem_addr))[2:].zfill(8)

    rs2 = ti[20:25][::-1]
    mem_dic[mem_addr_hex] = reg_dic[rs2]

    return pc + 4

# B-type instructions
def execute_b_type(inst, pc, reg_dic):
    ti = inst[::-1]
    imm = inst[0] + ti[12:20][::-1] + ti[11] + inst[1:11]
    imm = sign_extend(imm)
    imm = binary_to_decimal(imm)

    rs1 = ti[15:20][::-1]
    rs2 = ti[20:25][::-1]
    funct3 = ti[12:15][::-1]

    if funct3 == "000":
        if binary_to_decimal(reg_dic[rs1]) == binary_to_decimal(reg_dic[rs2]):
            pc += imm
    elif funct3 == "001":
        if binary_to_decimal(reg_dic[rs1]) != binary_to_decimal(reg_dic[rs2]):
            pc += imm
    elif funct3 == "100":
        if binary_to_decimal(reg_dic[rs1]) < binary_to_decimal(reg_dic[rs2]):
            pc += imm
    elif funct3 == "101":
        if binary_to_decimal(reg_dic[rs1]) >= binary_to_decimal(reg_dic[rs2]):
            pc += imm

    return pc

# U-type instructions
def execute_u_type(inst, pc, reg_dic):
    ti = inst[::-1]
    imm = inst[:20]
    imm = sign_extend(imm)
    imm = binary_to_decimal(imm)

    rd = ti[7:12][::-1]
    reg_dic[rd] = decimal_to_binary(imm)
    return pc + 4

# JAL-type instructions
def execute_jal_type(inst, pc, reg_dic):
    ti = inst[::-1]
    imm = inst[0] + inst[12:20] + inst[11] + inst[1:11]
    imm = sign_extend(imm)
    imm = binary_to_decimal(imm)

    rd = ti[7:12][::-1]
    reg_dic[rd] = decimal_to_binary(pc + 4)

    return pc + imm

# Main simulation function
def simulator(reg_dic, mem_dic, pc_dic, reg_opc_to_mem_add):
    pc = 0
    while pc <= 252:
        inst = pc_dic[pc]
        opc = inst[-7:]

        if inst == "00000000000000000000000001100011":
            break

        if opc == R_OPCODE:
            pc = execute_r_type(inst, pc, reg_dic)
        elif opc in I_OPCODE:
            pc = execute_i_type(inst, pc, reg_dic, mem_dic)
        elif opc == S_OPCODE:
            pc = execute_s_type(inst, pc, reg_dic, mem_dic, reg_opc_to_mem_add)
        elif opc == B_OPCODE:
            pc = execute_b_type(inst, pc, reg_dic)
        elif opc in U_OPCODE:
            pc = execute_u_type(inst, pc, reg_dic)
        elif opc == JAL_OPCODE:
            pc = execute_jal_type(inst, pc, reg_dic)

        reg_dic["program"] = decimal_to_binary(pc)
        output.append(" ".join([f"{k}:{v}" if k != "program" else f"{k}={v}" for k, v in reg_dic.items()]))

# Initialization
reg_dic = {'program': '0' * 32, '00000': '0' * 32, '00001': '0' * 32, '00010': '0' * 32, '00011': '0' * 32, '00100': '0' * 32, '00101': '0' * 32, '00110': '0' * 32, '00111': '0' * 32, '01000': '0' * 32, '01001': '0' * 32, '01010': '0' * 32, '01011': '0' * 32, '01100': '0' * 32, '01101': '0' * 32, '01110': '0' * 32, '01111': '0' * 32, '10000': '0' * 32, '10001': '0' * 32, '10010': '0' * 32, '10011': '0' * 32, '10100': '0' * 32, '10101': '0' * 32, '10110': '0' * 32, '10111': '0' * 32, '11000': '0' * 32, '11001': '0' * 32, '11010': '0' * 32, '11011': '0' * 32, '11100': '0' * 32, '11101': '0' * 32, '11110': '0' * 32, '11111': '0' * 32}
mem_dic = {'0x00010000': '0' * 32, '0x00010004': '0' * 32, '0x00010008': '0' * 32, '0x0001000c': '0' * 32, '0x00010010': '0' * 32, '0x00010014': '0' * 32, '0x00010018': '0' * 32, '0x0001001c': '0' * 32, '0x00010020': '0' * 32, '0x00010024': '0' * 32, '0x00010028': '0' * 32, '0x0001002c': '0' * 32, '0x00010030': '0' * 32, '0x00010034': '0' * 32, '0x00010038': '0' * 32, '0x0001003c': '0' * 32, '0x00010040': '0' * 32, '0x00010044': '0' * 32, '0x00010048': '0' * 32, '0x0001004c': '0' * 32, '0x00010050': '0' * 32, '0x00010054': '0' * 32, '0x00010058': '0' * 32, '0x0001005c': '0' * 32, '0x00010060': '0' * 32, '0x00010064': '0' * 32, '0x00010068': '0' * 32, '0x0001006c': '0' * 32, '0x00010070': '0' * 32, '0x00010074': '0' * 32, '0x00010078': '0' * 32, '0x0001007c': '0' * 32}
pc_dic = {0: '00000000000000000000000001100011', 4: '00000000000000000000000001100011', 8: '00000000000000000000000001100011', 12: '00000000000000000000000001100011', 16: '00000000000000000000000001100011', 20: '00000000000000000000000001100011'}

output = []

# Run the simulator
simulator(reg_dic, mem_dic, pc_dic, None)

# Print the output
for line in output:
    print(line)