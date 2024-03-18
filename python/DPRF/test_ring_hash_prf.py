import os, sys, math, json, re, time, argparse, csv, ast
import secrets

import numpy as np
from sympy import ntt, intt

sys.path += ['./', '../']

from conf.groupparam import *
from decimal import *

from charm.toolbox.eccurve import secp112r1, secp128r1, secp160k1, secp256k1, sect283k1, secp384r1
from util.solver_flint.my_sol_frag import *

from Crypto.Hash import SHA512

group112 = ECGroup(secp112r1)
group128 = ECGroup(secp128r1)
group160 = ECGroup(secp160k1)
group192 = ECGroup(prime192v1)
group256 = ECGroup(secp256k1)
group283 = ECGroup(sect283k1)
group384 = ECGroup(secp384r1)

u = 1
NODES = 0


def generate_sum_shares(no_of_clients, modulus, sum_val):
    # generate additive shares that sum upto 0.
    # The modulus should be less than 571 bit number 
    cumulative_sum = 0
    shares = []

    modulus_bitlength = len(bin(modulus))

    for i in range(no_of_clients - 1):
        # rand_share = int(group_zv.random(ZR)) % modulus
        rand_share = secrets.randbits(modulus_bitlength) % modulus
        shares.append(rand_share)
        cumulative_sum = (cumulative_sum + rand_share) % modulus
    # final_share = zero571 - cum_sum
    final_share = (sum_val - cumulative_sum) % modulus  # sum of shares mod modulus gives the sum_val
    shares.append(final_share)
    # serialized_shares = [group_zv.serialize(x) for x in shares]
    return shares


def compute_hash(slot_number, vec_length, ring_v):
    hash_vector = []
    X = str(slot_number)
    for j in range(vec_length):
        X = X + str(j)
        h = (SHA512.new(data=X.encode())).hexdigest()
        H = int(h, 16) % ring_v
        # H = int(group_zv.hash(X, target_type=ZR)) % ring_v
        hash_vector.append(H)
    return hash_vector


def prf_ring(RING_HASH_VEC, RING_SHARE_ROWS, ring_v, qvratio):
    ntt_product = np.multiply(RING_HASH_VEC, RING_SHARE_ROWS)
    ring_product = intt(ntt_product, ring_v)
    # round down
    prf_output = [int(x * qvratio) for x in ring_product]
    # inttout2  = np.polydiv(inttout, xN_1)[1]
    return prf_output


def client_message_gen(nid, vec_length, no_of_slots, FRAGMENTS):
    keyfilename = "./tmp/node" + str(nid) + "ShareList.txt"
    keystrings = []
    with open(keyfilename) as f:
        keystrings = [next(f) for x in range(u)]

    share_rows = []  # Holds u rows, each row indicates one 'share'
    for i in range(len(keystrings)):
        ele = ast.literal_eval(keystrings[0])
        share_rows.append(ele)
    share_rows = share_rows[0]

    message_ele = int(2)
    # pre-process hash computations

    # global HASH_VECTOR, SHARE_ROWS
    # global RING_HASH_VEC, RING_SHARE_ROWS

    HASH_VECTOR = compute_hash(0, vec_length, ring_v)
    SHARE_ROWS = share_rows

    RING_HASH_VEC = np.array(ntt(HASH_VECTOR, ring_v))
    RING_SHARE_ROWS = np.array(ntt(SHARE_ROWS, ring_v))

    prf_evaluations = []

    start = time.time()

    prf_evaluations = prf_ring(RING_HASH_VEC, RING_SHARE_ROWS, ring_v, qvratio)

    end = time.time()
    print("prf time:", end - start)

    filename = "./PREPROCESSED_PRF/n" + str(NODES) + "/bits_" + str(bits) + "_nid_" + str(nid) + ".txt"
    # with open(filename, 'w') as f:
    #    f.write(str(prf_evaluations))

    # print("bits:", bits)
    # print("nid:", nid)
    # print("nodes:", NODES)

    slot_messages = []
    slot_msg = int(1)
    for i in range(no_of_slots * FRAGMENTS):
        slot_msg = slot_msg * message_ele
        slot_msg = slot_msg % p
        msg_to_append = (int(prf_evaluations[i]) + int(1000 * slot_msg)) % q  # in group 283
        # msg_to_append = group_zq.init(ZR, (int(prf_evaluations[i])+int(1000*slot_msg)) ) # in group 283
        slot_messages.append(msg_to_append)

    return slot_messages


if __name__ == "__main__":

    description = ""

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-n", "--nodes", default=4, type=int, help="number of nodes"
    )

    parser.add_argument(
        "-b", "--bits", default=96, type=int, help="bit length \eta_p of message output"
    )

    args = parser.parse_args()
    num_of_nodes = args.nodes
    print("Number of clients:", num_of_nodes)

    global group_zv, group_zq, group_zp
    global v, p, q, pqratio, qvratio, bits, ring_v

    NODES = args.nodes

    bits = args.bits
    group_zv = group384

    if bits == 256:
        group_zq = group283
        group_zp = group256
        share_vector_length = 8192
        p = group_zp.order()
        ring_v = (262 * (2 ** 360)) + 1

    if bits == 226:
        group_zq = group256
        share_vector_length = 8192
        p = 2 ** 226 - 5
        ring_v = (7 * (2 ** 290)) + 1

    elif bits == 128:
        group_zq = group160
        group_zp = group128
        share_vector_length = 4096
        p = group_zp.order()
        ring_v = (102 * (2 ** 256)) + 1

    elif bits == 64:
        group_zq = group112
        p = 2 ** 64 - 59
        share_vector_length = 2048
        ring_v = (102 * (2 ** 256)) + 1

    elif bits == 32:
        group_zq = group112
        p = 2 ** 32 - 5
        share_vector_length = 2048
        ring_v = (57 * (2 ** 96)) + 1

    v = group_zv.order()
    q = group_zq.order()

    if bits == 32:
        q = 2 ** 56 - 5

    getcontext().prec = 571
    qvratio = Decimal(int(q)) / Decimal(int(ring_v))

    num_of_slots = num_of_nodes

    node_shares = [[] for _ in range(num_of_nodes)]
    # clear old files
    for node_id in range(num_of_nodes):
        filename = "./tmp/node" + str(node_id) + "ShareList.txt"
        f = open(filename, 'w')
        f.close()

    # generate client shares 
    for i in range(share_vector_length):
        # shares , serial_shares = generate_one_sum_shares(num_of_nodes, ring_v)
        shares = generate_sum_shares(num_of_nodes, ring_v, 1)
        for j in range(len(shares)):
            node_shares[j].append(shares[j])

    # write shares to file
    for node_id in range(num_of_nodes):
        filename = "./tmp/node" + str(node_id) + "ShareList.txt"
        f = open(filename, 'a')
        f.write(str(node_shares[node_id]))
        f.close()

    client_slot_messages = []

    FRAGMENTS = 1

    # Clients compute and forward the equation system
    for i in range(num_of_nodes):
        client_slot_messages.append(client_message_gen(str(i), share_vector_length, num_of_nodes, FRAGMENTS))
    # print("client_slot_messages:", client_slot_messages)

    # Compute summation for each slot
    relay_messages = []
    for i in range(num_of_nodes):
        relay_msg_of_slot = group_zq.init(ZR, int(0))
        for j in range(num_of_nodes):
            relay_msg_of_slot = relay_msg_of_slot + client_slot_messages[j][i]
        relay_messages.append(relay_msg_of_slot % q)

    relay_share = [1] * share_vector_length

    relay_prf_start = time.time()

    # hash
    RELAY_HASH = compute_hash(0, share_vector_length, ring_v)
    RING_HASH_VEC = np.array(ntt(RELAY_HASH, ring_v))
    RING_SHARE_ROWS = np.array(ntt(relay_share, ring_v))

    ring_hash_vec_ = ntt(RELAY_HASH, ring_v)
    ring_share_rows_ = ntt(relay_share, ring_v)

    PRF_VECTORS = {
            "RELAY_HASH": RELAY_HASH, 
            "ring_hash_vec_":ring_hash_vec_, 
            "ring_share_rows_": ring_share_rows_, 
            "ring_v" : ring_v, 
            #"qvratio" : qvratio,
            "bits" : bits 
            }
    filename = "./PRF_VECTORS_bits_" + str(bits) + ".txt"
    with open(filename, 'w') as f:
        f.write(json.dumps(PRF_VECTORS))


    local_prf_evaluations = prf_ring(RING_HASH_VEC, RING_SHARE_ROWS, ring_v, qvratio)

    print("relay prf time:", time.time() - relay_prf_start)


    filename = "./PREPROCESSED_PRF/n" + str(NODES) + "/RELAY/bits_" + str(bits) + ".txt"
    # with open(filename, 'w') as f:
    #    f.write(str(local_prf_evaluations))

    # subtract the prf evaluation from message received
    final_equations = []
    for i in range(num_of_slots):
        val = round(int(relay_messages[i] - local_prf_evaluations[i]) / 1000) % q
        val_in_grp = int(val % p)
        final_equations.append(val_in_grp)

    print("final equation sums:", final_equations)

    output = solve(final_equations)
    print(output)
