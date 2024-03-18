import logging, time, argparse, csv, threading, sys

sys.path += ['./', '../', '../../']

from util.solver_flint.lib_solver import ffi, lib

from charm.toolbox.ecgroup import ECGroup, ZR, G
from charm.toolbox.eccurve import secp256k1

from charm.toolbox.eccurve import secp112r1, secp128r1, secp160k1, secp256k1, sect283k1, secp384r1

group128 = ECGroup(secp128r1)
group256 = ECGroup(secp256k1)


def int2hexbytes(n):
    return bytes(hex(n), "ascii")[2:]


# P = int(group256.order())
# print("_HEX_P:", _HEX_P)

_C_RET_INVALID = 1
_C_RET_INTERNAL_ERROR = 100
_C_RET_INPUT_ERROR = 101


def solve_with_return(dc_sums, qu):
    return_dict = qu.get()
    out = solve(dc_sums)
    # print("out of solution:", out)
    return_dict['output'] = out
    qu.put(return_dict)

    #return


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
    P = 2 ** 32 - 5
    _HEX_P = int2hexbytes(P)
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

    description = ""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-n", "--nodes", default=4, type=int, help="number of nodes"
    )

    parser.add_argument(
        "-b", "--bits", default=128, type=int, help="number of input message bits "
    )

    parser.add_argument(
        "-f", "--fragments", type=int, default=10, help="number of fragments/ threads  "
    )

    global bits, P, _HEX_P

    args = parser.parse_args()
    bits = args.bits
    input_length = args.nodes
    frag = args.fragments

    # TODO: P is hard coded to be 32 bit, other values do not work for this code

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
            x = int(i)
        else:
            x = group_zp.random(ZR)
        input_variables.append(x)

    print("input_variables:", input_variables)

    dc_sums = []
    for j in range(len(input_variables)):
        if bits == 96 or bits == 64 or bits == 32:
            dc_sum = sum([(x ** (j + 1)) % P for x in input_variables])
            dc_sum = dc_sum % P
            dc_sums.append(int(dc_sum))
        else:
            dc_sum = sum([(x ** (j + 1)) % P for x in input_variables])
            dc_sum = dc_sum % P
            dc_sums.append(int(dc_sum))

    start = time.time()
    start_process_time = time.process_time()

    output = solve(dc_sums)
    print(output)

    end = time.time()
    end_process_time = time.process_time()

    time_to_solve = end - start
    process_time_to_solve = end_process_time - start_process_time

    solve_timing = [time_to_solve, process_time_to_solve]

    print("time to solve:", end - start)
    # print("process time to solve:", end_process_time - start_process_time)

    output_set = set(output)
    input_set = set([int(x) for x in input_variables])

    if output_set == input_set:
        print("yes, it works ")

    initial_time = time.time()
    start_process_time = time.process_time()

    all_client_threads = []
    thread_count = 0

    # while ((time.time() - initial_time) < 0.1):
    while (thread_count < frag):
        handle_peer_thread = threading.Thread(target=solve, args=(dc_sums,))
        handle_peer_thread.start()
        all_client_threads.append(handle_peer_thread)
        thread_count += 1

    for thread in all_client_threads:
        thread.join()

    exit_time = time.time()
    end_process_time = time.process_time()

    total_threads_time = exit_time - initial_time
    print("time for", frag, " threads", total_threads_time)

    process_time_to_solve = end_process_time - start_process_time

    solve_timing = [total_threads_time, process_time_to_solve]

    timingfilename = "./tmp/" + str(bits) + "frag_equ_solve_timing_n_" + str(input_length) + ".csv"
    with open(timingfilename, "a") as f:
        writer = csv.writer(f)
        writer.writerow(solve_timing)
