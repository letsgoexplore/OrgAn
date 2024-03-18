import json
import time

from conf.includefiles import *
from multiprocessing import Process
import multiprocessing
import select
import queue

debug = 0

message_queues = {}
base_msgs_rcvd = 0
bulk_msgs_rcvd = 0

TIMING = {}
BULK_SEND_TIME = 0
BULK_RECEIVE_TIME = 0


def DPRINT(*args, **kwargs):
    if debug:
        print(*args, **kwargs)


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


def handle_reply(nid, data_received, base_records, bulk_records, relay_socket, params):
    if data_received["msg_type"] == "BASE_PROTOCOL_REPLY":
        params['base_msgs_rcvd'] += 1

        round_no = data_received["round_no"]
        base_records[round_no] = 1
        client_message_bulk(nid, params, round_no, relay_socket)
        return

    if data_received["msg_type"] == "BULK_PROTOCOL_REPLY":

        global BULK_RECEIVE_TIME
        BULK_RECEIVE_TIME = time.time()

        total_clients = params['node_params']['N_CLIENTS']
        filename = "bulk_rtt_client_" + str(params['node_params']['N_CLIENTS']) + str("_") + str(nid) + "_.csv"
        with open(filename, "a") as f:
            writer = csv.writer(f)
            writer.writerow([total_clients, nid, (BULK_RECEIVE_TIME - BULK_SEND_TIME)])

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

        round_no = data_received["round_no"]
        bulk_records[round_no] = 1
        return


def client_message_base(nid, params, round_no, relaysock):
    base_start_time = time.time()

    total_clients = params['node_params']['N_CLIENTS']
    no_of_slots = total_clients
    base_p = params['base_params']['P']
    base_q = params['base_params']['Q']
    bits = params['base_params']['BITS']
    fragments = params['slot_params']['FRAGMENTS']

    message_ele = int(nid) + 1

    bits = 32
    filename = "../DPRF/PREPROCESSED_PRF/n" + str(total_clients) + "/bits_" + str(bits) + "_nid_" + str(nid) + ".txt"
    with open(filename, 'r') as f:
        # prf_evaluations = ast.literal_eval(f.read())
        prf_evaluations = json.loads(f.read())

    slot_messages = []
    slot_msg = int(1)

    DPRINT("num_of_slots:", no_of_slots)
    DPRINT("evaluations:", prf_evaluations[:5])

    for i in range(no_of_slots):
        slot_msg = slot_msg * message_ele
        slot_msg = slot_msg % base_p
        msg_to_append = int((int(prf_evaluations[i]) + int(1000 * slot_msg)) % base_q)
        slot_messages.append(msg_to_append)

    DPRINT("slot_messages:", slot_messages)

    data_to_send = {
        'msg_type': "CLIENT_BASE_MSG",
        'my_id': nid,
        'slot_messages': json.dumps(slot_messages),
        'slots_needed': fragments,
        'round_no': round_no
    }
    data = json.dumps(data_to_send)
    message_queues[relaysock].put(data)

    base_protocol_time = time.time() - base_start_time
    delayfilename = "./client_base_delay_" + str(nid) + ".csv"
    with open(delayfilename, "a") as f:
        writer = csv.writer(f)
        writer.writerow([round_no, total_clients, base_protocol_time])
    return


def client_message_bulk(nid, params, round_no, relaysock):
    bulk_start_time = time.time()

    total_clients = params['node_params']['N_CLIENTS']
    bulk_q = params['bulk_params']['Q']
    message_ele = int(nid + 1)
    # bits = 226

    # bits = params['bulk_params']['BITS']
    # vec_length = params['bulk_params']['VECTOR_LENGTH']

    # TODO: change this back to 'bits'
    n_bits = 226

    filename = "../DPRF/PREPROCESSED_PRF/n" + str(total_clients) + "/bits_" + str(n_bits) + "_nid_" + str(nid) + ".txt"
    with open(filename, 'r') as f:
        prf_evaluations = json.loads(f.read())

    # vec_length = 37 * total_clients

    DPRINT("bulk round length of prf evaluations:", len(prf_evaluations))

    slot_messages = []
    slot_msg = int(1)

    # TODO: Below is for 1 KB packet
    vec_length = 37 * total_clients
    slots_per_client = 37

    # slots_per_client = int(vec_length / total_clients)
    my_slot_index_start = int(nid) * slots_per_client
    my_slot_index_end = (int(nid) + 1) * slots_per_client

    for i in range(my_slot_index_start, my_slot_index_end):
        prf_evaluations[i] = int((prf_evaluations[i] + 1000 * message_ele) % bulk_q)

    data_to_send = {'msg_type': "CLIENT_BULK_MSG",
                    'my_id': nid,
                    'round_no': round_no,
                    'slot_messages': json.dumps(prf_evaluations)
                    }
    data = json.dumps(data_to_send)

    # sleep(0.01 * nid)

    message_queues[relaysock].put(data)

    bulk_protocol_time = time.time() - bulk_start_time
    delayfilename = "./client_bulk_delay_" + str(nid) + ".csv"
    with open(delayfilename, "a") as f:
        writer = csv.writer(f)
        writer.writerow([round_no, vec_length, bulk_protocol_time])

    global BULK_SEND_TIME
    BULK_SEND_TIME = time.time()

    return
