import os, sys, math, json, re, time , argparse, csv, ast   
import secrets 


import numpy as np 
from sympy import ntt , intt

sys.path += ['./','../']

from conf.groupparam  import * 
from decimal import *


from charm.toolbox.eccurve import secp112r1, secp128r1, secp160k1, secp256k1, sect283k1,secp384r1
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



def client_message_gen(nid, vec_length, no_of_slots, FRAGMENTS):

    message_ele = int(2)

    filename = "./PREPROCESSED_PRF/n"+str(NODES)+"/bits_"+str(bits)+"_nid_"+str(nid)+".txt"
    with open(filename, 'r') as f:
        prf_evaluations = ast.literal_eval(f.read())

    slot_messages = []
    slot_msg = int(1)
    for i in range(no_of_slots*FRAGMENTS):
        slot_msg = slot_msg * message_ele 
        slot_msg = slot_msg % p
        msg_to_append =  (int(prf_evaluations[i])+int(1000*slot_msg)) % q  # in group 283
        #msg_to_append = group_zq.init(ZR, (int(prf_evaluations[i])+int(1000*slot_msg)) ) # in group 283
        slot_messages.append(msg_to_append)

    return slot_messages 


if __name__=="__main__":

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
    global v, p, q , pqratio, qvratio, bits, ring_v   

    NODES = args.nodes 

    bits = args.bits 
    group_zv = group384

    if bits == 256:
        group_zq = group283
        group_zp = group256
        share_vector_length = 8192
        p = group_zp.order()
        ring_v = (262 * (2 ** 360)) + 1 

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
        ring_v = ( 57 * (2 ** 96)) + 1 

    v = group_zv.order()
    q = group_zq.order()

    getcontext().prec = 571 
    qvratio = Decimal(int(q)) / Decimal(int(ring_v))


    num_of_slots = num_of_nodes 

    client_slot_messages = []

    FRAGMENTS = 1

    #Clients compute and forward the equation system 
    for i in range(num_of_nodes):
        client_slot_messages.append(client_message_gen(str(i) , share_vector_length, num_of_nodes, FRAGMENTS))
    #print("client_slot_messages:", client_slot_messages)

    #Compute summation for each slot
    relay_messages = []
    for i in range(num_of_nodes):
        relay_msg_of_slot = int(0)
        for j in range(num_of_nodes):
            relay_msg_of_slot = (relay_msg_of_slot + client_slot_messages[j][i]) % q
        relay_messages.append(relay_msg_of_slot)

    #relay_share = [1] * share_vector_length


    filename = "./PREPROCESSED_PRF/n"+str(NODES)+"/RELAY/bits_"+str(bits)+".txt"
    with open(filename, 'r') as f:
        local_prf_evaluations = ast.literal_eval(f.read())

    #subtract the prf evaluation from message received 
    final_equations = []
    for i in range(num_of_slots):
        val = round(int(relay_messages[i] - local_prf_evaluations[i])/1000) % q
        val_in_grp = int(val % p) 
        final_equations.append(val_in_grp)

    print("final equation sums:", final_equations)

    output = solve(final_equations)
    print(output)
