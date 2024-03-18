import logging, time, argparse, csv 


from lib_solver import ffi, lib

from charm.toolbox.ecgroup import ECGroup, ZR, G
from charm.toolbox.eccurve import secp256k1

from charm.toolbox.eccurve import secp112r1, secp128r1, secp160k1, secp256k1, sect283k1,secp384r1

group128 = ECGroup(secp128r1)
group256 = ECGroup(secp256k1)

def int2hexbytes(n):
    return bytes(hex(n), "ascii")[2:]


#P = int(group256.order())
#print("_HEX_P:", _HEX_P)

_C_RET_INVALID = 1
_C_RET_INTERNAL_ERROR = 100
_C_RET_INPUT_ERROR = 101


def solve(dc_sums):
    """
    Solve function from protocol specification.

    Solves the following equation system:
    forall 0 <= i < size(dc_sums)
        sum_{j=0}^{size(dc_sums)-1)} messages[j]^{i+1} = dc_sums[i]

    In the finite prime field F_P for messages checks if my_message is in the solution.
    Assumes that size(dc_sums) >= 2.

    Returns a list of messages as solution (sorted in ascending numerial order)
    in case of success. Returns None if dc_sums is not a proper list of power sums,
    or if my_message is not a solution.
    """

    ffi_sums = [ffi.new("char[]", int2hexbytes(s)) for s in dc_sums]
    # Allocate result buffers (size of P in hex + 1 null char)
    ffi_messages = [ffi.new("char[]", len(_HEX_P) + 1) for _ in dc_sums]

    res = lib.solve(ffi_messages, _HEX_P, ffi_sums, len(dc_sums))

    if res == 0:
        return [int(ffi.string(m), 16) for m in ffi_messages]
    elif res == _C_RET_INVALID:
        logging.info("[ERROR]: Invalid code returned from C++ solver.")
        return None
    elif res == _C_RET_INPUT_ERROR:
        raise ValueError
    else:
        raise RuntimeError



if __name__ == "__main__":

    description=""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-n", "--nodes", default=4, type=int, help="number of ndoes"
    )   

    parser.add_argument(
        "-b", "--bits", default=128, type=int, help="number of input message bits "
    )   


    global bits, P, _HEX_P  


    args = parser.parse_args()
    bits = args.bits 
    input_length = args.nodes
    
    if bits == 256:
        group_zp = group256
        P = int(group_zp.order())
    elif bits == 128:
        group_zp = group128
        P = int(group_zp.order())
    elif bits == 96:
        P = 2 ** 96 - 17
    elif bits == 64:
        P = 2 ** 64 - 59 
    elif bits == 32:
        P = 2 ** 32 - 5 

    _HEX_P = int2hexbytes(P)

    print("number of messages/equations:", input_length)

    input_variables = []
    for i in range(input_length):
        if bits == 96 or bits == 64 or bits == 32:
            x = group128.random(ZR)
            x = int(int(x) % P)
        else:
            x = group_zp.random(ZR)
        input_variables.append(x)

    #print("input_variables:", input_variables)

    dc_sums = []
    for j in range(len(input_variables)):
        dc_sum = sum([x ** (j+1) for x in input_variables])
        dc_sums.append(int(dc_sum))


    start = time.time()
    start_process_time = time.process_time()

    output = solve(dc_sums)

    end = time.time()
    end_process_time = time.process_time()

    time_to_solve = end-start 
    process_time_to_solve = end_process_time - start_process_time 

    solve_timing = [time_to_solve, process_time_to_solve]

    print("time to solve:", end-start)
    print("process time to solve:", end_process_time - start_process_time)

    output_set = set(output)
    input_set = set([int(x) for x in input_variables])

    if output_set == input_set:
        print("yes, it works ")

    timingfilename = "./tmp/"+ str(bits)+ "equ_solve_timing_n_"+str(input_length)+".csv"
    with open(timingfilename, "a") as f:
        writer = csv.writer(f)
        writer.writerow(solve_timing)
