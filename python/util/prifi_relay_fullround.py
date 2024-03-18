from conf.includefiles import *
from multiprocessing import Process, Queue
import select
import queue
from util.solver_flint.my_sol_frag import *
import random
debug = 0


def DPRINT(*args, **kwargs):
    if debug:
        print(*args, **kwargs)


message_queues = {}

def server_socket(params):
    print("server socket")
    client_threads = []
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setblocking(0)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_address = ('localhost', 10000)
    print('starting up on %s port %s' % server_address)
    server.bind(server_address)
    # server.bind(('localhost', MY_PORT))

    num_of_clients = params['node_params']['N_CLIENTS']
    relay_ip = params['node_params']['RELAY_IP']

    # check for inputs
    inputs = [server]
    client_sockets = []
    # base_records = [{}] * num_of_clients  # Total round history - currently 10 rounds
    bulk_records = [{}] * num_of_clients
    key_records = [{}] * num_of_clients

    sent_status = [{}, {}]
    # message_queues = {}
    outs = []
    server.listen(num_of_clients)

    while True:

        # print("waiting using select")
        readable, writable, exceptional = select.select(inputs, outs, inputs, 0)
        # readable, writable, exceptional = select.select(inputs, outputs, [], 0)
        for s in readable:
            if s is server:
                print("got new connection")
                connection, client_address = s.accept()

                # re-check this step
                connection.setblocking(0)
                inputs.append(connection)
                client_sockets.append(connection)

                # allocating a variable to check for outputs
                # output_conn[connection] = 0
                # Give the connection a queue for data we want to send
                message_queues[connection] = queue.Queue()
            else:
                try:
                    data_recvd = recv_data(s)
                    if data_recvd:
                        data_received = json.loads(data_recvd)

                        handle_client_thread = threading.Thread(target=handle_client,
                                                                args=(
                                                                    data_received, key_records, bulk_records,
                                                                    client_sockets, sent_status, params))
                        handle_client_thread.start()
                        client_threads.append(handle_client_thread)
                    else:
                        # Stop listening for input on the connection
                        if s in outs:
                            outs.remove(s)
                        inputs.remove(s)
                        s.close()

                        # Remove message queue
                        del message_queues[s]


                except KeyboardInterrupt:
                    print("[!] Keyboard Interrupted!")
                    server.shutdown(socket.SHUT_RDWR)
                    server.close()
                    for th in client_threads:
                        th.join()
                        break

                except Exception as e:
                    continue

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
        # clear and populate afresh
        for con in message_queues:
            # check for all outputs who have a message
            if not message_queues[con].empty():
                outs.append(con)


    return


def handle_client(data_received, key_records, bulk_records, client_sockets, sent_status, params):
    pid = data_received["my_id"]

    num_of_clients = params['node_params']['N_CLIENTS']

    if data_received["msg_type"] == "HELLO":
        DPRINT("Hello received from:", pid)
        print("Hello received from:", pid)
        return

    if data_received["msg_type"] == "CLIENT_BULK_MSG":

        round_no = data_received["round_no"]
        DPRINT("Received bulk message for round")
        serial_client_msg = data_received['slot_messages']
        serial_client_key = data_received['keys']
        client_msg = ast.literal_eval(serial_client_msg)
        client_key = json.loads(serial_client_key)

        print("Bulk round - length of received slot values from client:", len(client_msg))

        bulk_records[round_no][pid] = client_msg
        key_records[round_no][pid] = client_key

        if len(bulk_records[round_no]) == num_of_clients and round_no not in sent_status[1]:
            # print("Not sent yet")

            # Once all the messages are received for the bulk round, compute the messages for slots

            compute_message(bulk_records[round_no], key_records[round_no], params)

            sent_status[1][round_no] = 1  # index 1 is bulk round
            data_to_send = {
                'round_no': round_no,
                'msg_type': "BULK_PROTOCOL_REPLY"}
            data = json.dumps(data_to_send)
            for sock in client_sockets:
                message_queues[sock].put(data)
                # send_data(sock, data)

        print("returning")
        return


def compute_message(client_slot_messages, key_slot_messages, params):
    print("RELAY FUNCTION")

    '''
    clients = params['node_params']['N_CLIENTS']
    bulk_p = params['bulk_params']['P']
    bulk_q = params['bulk_params']['Q']
    bits = params['bulk_params']['BITS']
    share_vector_length = params['bulk_params']['VECTOR_LENGTH']
    '''

    num_of_slots = params['node_params']['N_CLIENTS']
    num_of_nodes = num_of_slots
    total_guards = params['node_params']['N_GUARDS']

    n_bits = 1024

    prgs = [random.getrandbits(n_bits) for _ in range(total_guards)]

    for i in range(num_of_slots):
        xored_val = int(client_slot_messages[i][0])
        xored_prg = 0
        for j in range(2, num_of_nodes):
            xored_val = xored_val ^ int(client_slot_messages[j][i])
        for k in range(2, total_guards):
            xored_prg ^= prgs[k]
        xored_val ^= xored_prg
    # xored_val = 0
    # rand_val = rand_zq

    '''
    for i in range(num_of_slots):
    # for i in range(1):
        #for adding ki_s
        key = 0
        xored_val = client_slot_messages[str(i)][0]
        for j in range(2,num_of_nodes):
            xored_val = xored_val ^ int(client_slot_messages[str(j)][i])
            # xored_val = fast_xor(xored_val, client_slot_messages[str(j)][i])
            #guard_xored_val = guard_xored_val ^ guard_val
            #guard_sigma_val = guard_sigma_val + guard_sigma
            key = key + key_slot_messages[j][i]
        #relay_messages.append(xored_val)
        #message_ele_decrypted  = STD_symcrypt.decrypt(STD_enc)
        #X = "somethingsomething"
        #H = group_zq.hash(X, target_type=ZR)
    '''

