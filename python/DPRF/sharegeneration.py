import os, sys, math, json, re, time , argparse, csv, ast   
import secrets 
sys.path += ['./','../']

from conf.groupparam  import * 


from charm.toolbox.eccurve import secp112r1, secp128r1, secp160k1, secp256k1, sect283k1,secp384r1, prime192v2

from Crypto.Hash import SHA512, SHA256
from charm.schemes.pksig.pksig_schnorr91 import SchnorrSig
from charm.schemes.pksig.pksig_ecdsa import ECDSA
from charm.schemes.pkenc.pkenc_rsa import RSA_Enc, RSA_Sig
#from charm.toolbox.integergroup import integer



group112 = ECGroup(secp112r1)
group128 = ECGroup(secp128r1)
group160 = ECGroup(secp160k1)
group192 = ECGroup(prime192v1)
group256 = ECGroup(secp256k1)
group283 = ECGroup(sect283k1)
group384 = ECGroup(secp384r1)

u = 1
NODES = 0

g = group384.encode(decoded_g384)
h = group384.encode(decoded_h384)


def deserializeElements_zv(objects):
    object_byte_strings = re.findall(r"'(.*?)'", objects , re.DOTALL)
    object_strings  = [ str.encode(a) for a in object_byte_strings]
    elements = [group_zv.deserialize(a) for a in object_strings]
    return elements


def generate_sum_shares(no_of_clients, modulus, sum_val):
    #generate additive shares that sum upto 0. 
    # The modulus should be less than 571 bit number 
    cumulative_sum = 0
    shares = []

    modulus_bitlength = len(bin(modulus))

    for i in range(no_of_clients-1):
        #rand_share = int(group_zv.random(ZR)) % modulus 
        rand_share = secrets.randbits(modulus_bitlength) % modulus 
        shares.append(rand_share)
        cumulative_sum = (cumulative_sum + rand_share)  % modulus
    #final_share = zero571 - cum_sum
    final_share = (sum_val - cumulative_sum) % modulus # sum of shares mod modulus gives the sum_val 
    shares.append(final_share)
    #serialized_shares = [group_zv.serialize(x) for x in shares]
    return shares


if __name__=="__main__":

    description = ""

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-n", "--nodes", default=4, type=int, help="number of nodes"
    )

    parser.add_argument(
        "-b", "--bits", default=32, type=int, help="bit length \eta_p of message output"
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

    if bits == 226:
        group_zq = group256
        share_vector_length = 8192
        p = 2**226 - 5 
        ring_v = (7*(2**290))+1

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

    if bits == 32: 
         q = 2 ** 56 - 5 

    getcontext().prec = 571 
    qvratio = Decimal(int(q)) / Decimal(int(ring_v))

    num_of_slots = num_of_nodes 
    node_shares = [[] for _ in range(num_of_nodes)]
    #clear old files 
    for node_id in range(num_of_nodes):
        filename = "./tmp/node"+str(node_id)+"ShareList.txt"
        f = open(filename,'w')
        f.close()

    share_gen_start = time.time()

    if bits == 32:
        group384 = group256
        g = group256.encode(decoded_g256)
        h = group256.encode(decoded_h256)


    # generate client shares 
    for i in range(share_vector_length):
        #shares , serial_shares = generate_one_sum_shares(num_of_nodes, ring_v)
        shares = generate_sum_shares(num_of_nodes, ring_v, 1)
        for j in range(len(shares)):
            node_shares[j].append(shares[j])

    share_gen_end = time.time()
    print("share length:", share_vector_length)

    print("share gen time:", share_gen_end - share_gen_start)



