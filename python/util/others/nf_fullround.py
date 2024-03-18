import json

from conf.includefiles import *
from multiprocessing import Process
import multiprocessing
import select
import queue

debug = 0
N_NODES = 5
CLIENTS = 5
u = 1

def DPRINT(*args, **kwargs):
    if debug:
        print(*args, **kwargs)

def serverSock(MY_IP, MY_PORT, nid, params):
    print("server socket")
    all_client_threads = []
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)
    # server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ('localhost', 10000)
    print('starting up on %s port %s' % server_address)
    server.bind(server_address)
    # server.bind(('localhost', MY_PORT))

    # check for inputs
    inputs = [server]
    outputs = []
    client_socks = []
    base_records = [{}] * 10  # Total round history - currently 10 rounds
    bulk_records = [{}] * 10
    message_queues = {}
    server.listen(50)
    while True:

        # print("waiting using select")
        readable, writable, exceptional = select.select(inputs, outputs, inputs)
        for s in readable:
            if s is server:
                print("got new connection")
                connection, client_address = s.accept()
                connection.setblocking(0)
                inputs.append(connection)
                # Give the connection a queue for data we want to send
                message_queues[connection] = queue.Queue()
            else:
                try:
                    data_recvd = recv_data(s)
                    data_received = json.loads(data_recvd)

                    if data_received:
                        print('received "%s" from %s' % (data_received, s.getpeername()))

                    if s not in client_socks:
                        client_socks.append(s)

                    handle_client_thread = threading.Thread(target=handle_client,
                                                            args=(data_received, base_records, bulk_records))
                    handle_client_thread.start()
                    all_client_threads.append(handle_client_thread)

                except KeyboardInterrupt:
                    print("[!] Keyboard Interrupted!")
                    server.shutdown(socket.SHUT_RDWR)
                    server.close()
                    for thread in all_client_threads:
                        thread.join()
                        break
                except Exception as e:

                    print(e)

    DPRINT("***Exiting the loop")
    for thread in all_client_threads:
        thread.join()
    return

def sendId2relay(relaysock, nid):
    data_to_send = {'msg_type': "HELLO",
                    'my_id': nid}
    data = json.dumps(data_to_send)
    # DPRINT("Sending Hello to relay:", pid)
    send_data(relaysock, data)
    return

def handle_client(data_received, base_records, bulk_records):
    pid = data_received["my_id"]

    if data_received["msg_type"] == "HELLO":
        DPRINT("Hello received from:", pid)
        print("Hello received from:", pid)
        return

    if data_received["msg_type"] == "CLIENT_BASE_MSG":
        round_no = data_received["round_no"]
        DPRINT("Received base message for round")
        serial_client_msg = data_received['slot_messages']
        client_msg = ast.literal_eval(serial_client_msg)
        base_records[round_no][pid] = client_msg

        if len(base_records[round_no]) == N_NODES:
            slot_permutation = solve_equation(base_records[round_no], round_no)
            data = json.loads(slot_permutation)

            # TODO: send round number as well

            for sock in client_sockets:
                send_data(sock, data)
        return

    if data_received["msg_type"] == "CLIENT_BULK_MSG":
        print("Received ping reply")
        print("ping reply at:", time.time())
        round_no = data_received["round_no"]
        DPRINT("Received base message for round")
        serial_client_msg = data_received['slot_messages']
        client_msg = ast.literal_eval(serial_client_msg)
        bulk_records[round_no][pid] = client_msg

        if len(bulk_records[round_no]) == N_NODES:

            data = "REPLY"

            # TODO: send round number as well

            for sock in client_sockets:
                send_data(sock, data)
        return

def solve_equation(record, round_no):
    relay_messages = []
    getcontext().prec = 100

    num_of_slots = len(record)
    num_of_nodes = len(record)

    # compute messages of each block
    relay_messages = []
    for i in range(num_of_slots):
        relay_msg_of_slot = int(0)

        for j in range(1, num_of_nodes + 1):
            relay_msg_of_slot = (relay_msg_of_slot + record[j][i]) % q
        relay_messages.append(relay_msg_of_slot)

    print("share_vector_length:", share_vector_length)

    # load pre-processed prf values
    filename = "../DPRF/PREPROCESSED_PRF/n" + str(CLIENTS) + "/RELAY/bits_" + str(bits) + ".txt"
    with open(filename, 'r') as f:
        local_prf_evaluations = ast.literal_eval(f.read())

    # subtract the prf evaluation from message received
    final_equations = []
    for i in range(num_of_slots):
        val = round(int(relay_messages[i] - local_prf_evaluations[i]) / 1000) % q
        val_in_grp = int(val % p)
        final_equations.append(val_in_grp)

    print("final_equations:", final_equations)

    # DPRINT("solving dc sums")
    output = solve(final_equations)
    print(output)
    DPRINT(output)
    return output
