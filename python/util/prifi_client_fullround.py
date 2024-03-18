import json

from conf.includefiles import *
from multiprocessing import Process
import multiprocessing
import select
import queue
import random
from charm.core.math.pairing import hashPair as sha2
# from charm.toolbox.symcrypto import SymmetricCryptoAbstraction
from charm.toolbox.pairinggroup import PairingGroup, GT
from hashlib import sha256

debug = 0
message_queues = {}
TIMING = {}


def DPRINT(*args, **kwargs):
    if debug:
        print(*args, **kwargs)


'''
def server_socket(nid, params, relay_socket):
    # check for inputs
    inputs = [relay_socket]
    base_records = {}  # Total round history
    bulk_records = {}
    all_threads = []
    while True:

        # print("waiting using select")
        readable, _, _ = select.select(inputs, [], [], 0)
        for s in readable:
            try:
                data_recvd = recv_data(s)
                data_received = json.loads(data_recvd)

                if data_received:
                    print('received "%s" from %s' % (data_received, s.getpeername()))
                handle_reply_thread = threading.Thread(target=handle_reply,
                                                       args=(nid, data_received, base_records, bulk_records,
                                                             relay_socket, params))
                handle_reply_thread.start()
                all_threads.append(handle_reply_thread)

            except KeyboardInterrupt:
                print("[!] Keyboard Interrupted!")
                relay_socket.close()
                for th in all_threads:
                    th.join()
                return
            except Exception as e:
                print(e)
                continue

    DPRINT("***Exiting the loop")
'''


def server_socket(nid, params, relay_socket):
    # check for inputs
    inputs = [relay_socket]
    base_records = {}  # Total round history
    bulk_records = {}
    all_threads = []
    outs = []
    message_queues[relay_socket] = queue.Queue()
    while True:

        # print("waiting using select")
        readable, writable, exceptional = select.select(inputs, outs, inputs, 0)
        for s in readable:
            try:
                data_recvd = recv_data(s)
                data_received = json.loads(data_recvd)

                if data_received:
                    print('received "%s" from %s' % (data_received, s.getpeername()))
                handle_reply_thread = threading.Thread(target=handle_reply,
                                                       args=(data_received, bulk_records, params))
                handle_reply_thread.start()
                all_threads.append(handle_reply_thread)

            except KeyboardInterrupt:
                print("[!] Keyboard Interrupted!")
                relay_socket.close()
                for th in all_threads:
                    th.join()
                return
            except Exception as e:
                inputs.remove(s)
                if s in outs:
                    outs.remove(s)
                s.close()
                del message_queues[s]
                print(e)

        for s in writable:
            try:
                next_msg = message_queues[s].get_nowait()
            except queue.Empty:
                outs.remove(s)
            else:
                send_data(s, next_msg)

        for s in exceptional:
            inputs.remove(s)
            if s in outs:
                outs.remove(s)
            s.close()
            del message_queues[s]

        outs = []
        if not message_queues[relay_socket].empty():
            outs = [relay_socket]

    DPRINT("***Exiting the loop")


def handle_reply(data_received, bulk_records, params):

    if data_received["msg_type"] == "BULK_PROTOCOL_REPLY":
        round_no = data_received["round_no"]
        bulk_records[round_no] = 1

        params['bulk_msgs_rcvd'] += 1
        rounds = params['node_params']['rounds']
        if params['bulk_msgs_rcvd'] == rounds:
            TIMING['END_TIME'] = time.time()
            print("End time:", TIMING['END_TIME'])
            timingfilename = "./organ_timing_n_" + str(params['node_params']['N_CLIENTS']) + ".csv"
            with open(timingfilename, "a") as f:
                writer = csv.writer(f)
                writer.writerow([TIMING['START_TIME'], TIMING['END_TIME'], TIMING['END_TIME'] - TIMING['START_TIME']])
            print("timings:",
                  [rounds, TIMING['START_TIME'], TIMING['END_TIME'], TIMING['END_TIME'] - TIMING['START_TIME']])
    return


def client_message_bulk(nid, params, round_no, relaysock):
    total_clients = params['node_params']['N_CLIENTS']
    total_guards = params['node_params']['N_GUARDS']
    no_of_slots = total_clients

    n_bits = 1024 * 8 # 1 KB

    # n_bits = int(1024)
    message_bits = random.getrandbits(n_bits)
    message = str(int(message_bits))

    # Compute PRG using a seed -- here generating random bits
    # prg_bits = random.getrandbits(n_bits)
    # 10 guard nodes
    prgs = [random.getrandbits(n_bits) for _ in range(total_guards)]

    groupObj = PairingGroup('SS512')
    # a = SymmetricCryptoAbstraction(sha2(groupObj.random(GT)))

    # TODO: Encrypt the message
    # Symmetric key encrypt the message
    # message_enc = a.encrypt(message)
    message_enc = int(message)

    message_enc = message_enc ^ prgs[0]
    for i in range(2, total_guards):
        message_enc ^= prgs[i]

    '''
    # Compute keys for each slot 
    for i in range(no_of_slots):
        gamma_i = int(group256.init(ZR))
        h_int = 0 
        h = sha256()
        for j in range(total_guards):
            h_hex = h.digest(str(prg[i]))
            h_int += int(h_hex, 16)
        keys.append(gamma_i + h_int)
    '''

    slot_messages = []
    keys = []
    for i in range(no_of_slots):
        slot_messages.append(message)
        gamma_i = int(group256.init(ZR))  # keep it as gamma_i
        keys.append(gamma_i)

    data_to_send = {'msg_type': "CLIENT_BULK_MSG",
                    'my_id': nid,
                    'slot_messages': json.dumps(slot_messages),
                    'keys': json.dumps(keys),
                    'round_no': round_no,
                    'cipher': json.dumps(message_enc)
                    }
    data = json.dumps(data_to_send)
    send_data(relaysock, data)
    return
