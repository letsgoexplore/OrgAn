import multiprocessing
import threading

from conf.includefiles import *
from multiprocessing import Process, Queue
import select
import queue
from util.solver_flint.my_sol_frag import *
from multiprocessing import Process, Manager
from sympy import ntt, intt

debug = 0

# inputs = []
# output_conn = {}
message_queues = {}


def DPRINT(*args, **kwargs):
    if debug:
        print(*args, **kwargs)


def prf_ring(RING_HASH_VEC, RING_SHARE_ROWS, ring_v, qvratio):
    ntt_product = np.multiply(RING_HASH_VEC, RING_SHARE_ROWS)
    ring_product = intt(ntt_product, ring_v)
    # round down
    prf_output = [int(x * qvratio) for x in ring_product]
    # inttout2  = np.polydiv(inttout, xN_1)[1]
    return prf_output


def compute_hash(slot_number, vec_length, ring_v_):
    hash_vector = []
    X = str(slot_number)
    for j in range(vec_length):
        X = X + str(j)
        h = (SHA512.new(data=X.encode())).hexdigest()
        H = int(h, 16) % ring_v_
        # H = int(group_zv.hash(X, target_type=ZR)) % ring_v
        hash_vector.append(H)
    return hash_vector


def server_socket(params):
    print("server socket")
    client_threads = []
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # server.setblocking(0)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    if AWS:
        server_address = (RELAY_IP, RELAY_PORT)
    else:
        server_address = ('localhost', 10000)
    print('starting up on %s port %s' % server_address)
    server.bind(server_address)
    # server.bind(('localhost', MY_PORT))

    num_of_clients = params['node_params']['N_CLIENTS']
    relay_ip = params['node_params']['RELAY_IP']
    rounds = params['node_params']['rounds']
    print("number of rounds:", rounds)

    # check for inputs
    inputs = [server]

    # --------
    '''
    manager = Manager()
    client_sockets = manager.list()
    base_records = manager.list()
    bulk_records = manager.list()
    for i in range(rounds):
        base_records.append(manager.dict())
        bulk_records.append(manager.dict())
    sent_status = manager.list([manager.dict(), manager.dict()])
    params = manager.dict(params)
    message_queues = manager.dict()
     outs = manager.list()
    '''

    add_to_socket = {}
    socket_to_addr = {}

    '''
    base_records = [manager.dict() for i in range(rounds)]  # Total round history - currently 10 rounds
    bulk_records = [{}] * rounds
    sent_status = [{}, {}]
    # -----
    '''

    client_sockets = []
    base_records = [{}] * rounds  # Total round history - currently 10 rounds
    bulk_records = [{}] * rounds
    sent_status = [{}, {}]
    # message_queues = {}
    outs = []

    # outputs = []

    # for con in g_outputs:
    #    if g_outputs[con] > 0:
    #        outputs.append

    # param = json.dumps(params)

    server.listen(50)
    while True:

        # print("waiting using select")
        readable, writable, exceptional = select.select(inputs, outs, inputs, 0)
        # readable, writable, exceptional = select.select(inputs, outputs, [], 0)
        for s in readable:
            if s is server:
                # print("got new connection")
                connection, client_address = s.accept()

                # re-check this step
                # connection.setblocking(0)
                inputs.append(connection)
                client_sockets.append(client_address)
                add_to_socket[client_address] = connection
                socket_to_addr[connection] = client_address

                # allocating a variable to check for outputs
                # output_conn[connection] = 0
                # Give the connection a queue for data we want to send
                # message_queues[connection] = manager.Queue()
                message_queues[client_address] = queue.Queue()

            else:
                try:
                    data_recvd = recv_data(s)
                    if data_recvd:
                        data_received = json.loads(data_recvd)
                        # print('received data of length "%s" from %s' % (len(data_received), s.getpeername()))

                        # if data_received:
                        # print('received data of length "%s" from %s' % (len(data_received), s.getpeername()))

                        '''
                        handle_client_thread = multiprocessing.Process(target=handle_client,
                                                                       args=(data_received, base_records, bulk_records,
                                                                             client_sockets, sent_status, params,
                                                                             message_queues))
                        '''

                        handle_client_thread = threading.Thread(target=handle_client,
                                                                args=(
                                                                    data_received, base_records, bulk_records,
                                                                    client_sockets, sent_status, params))

                        handle_client_thread.start()
                        client_threads.append(handle_client_thread)
                    else:
                        # Stop listening for input on the connection
                        if s in outs:
                            outs.remove(s)
                        inputs.remove(s)
                        # s.close()

                        # Remove message queue
                        # del message_queues[s]


                except KeyboardInterrupt:
                    print("[!] Keyboard Interrupted!")
                    server.shutdown(socket.SHUT_RDWR)
                    server.close()
                    for th in client_threads:
                        th.join()
                        break

                except Exception as e:
                    print(e)
                    '''
                    inputs.remove(s)
                    if s in outs:
                        outs.remove(s)
                    s.close()
                    del message_queues[s]
                    '''

        for s in writable:
            try:
                next_msg = message_queues[socket_to_addr[s]].get_nowait()
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

        # replace this with connection of a corresponding address
        outs = []
        # clear and populate afresh
        for addr in message_queues.keys():
            # check for all outputs who have a message
            if not message_queues[addr].empty():
                outs.append(add_to_socket[addr])
    return


def handle_client(data_received, base_records, bulk_records, client_sockets, sent_status, params):
    '''
    data_recvd = recv_data(s)
    if data_recvd:
        data_received = json.loads(data_recvd)
    '''
    # data_received = json.loads(data_received)
    # params = json.loads(params)
    # print("inside handle client")

    pid = data_received["my_id"]

    num_of_clients = params['node_params']['N_CLIENTS']

    if data_received["msg_type"] == "HELLO":
        DPRINT("Hello received from:", pid)
        DPRINT("Hello received from:", pid)
        return

    if data_received["msg_type"] == "CLIENT_BASE_MSG":

        base_start_time = time.time()

        round_no = data_received["round_no"]
        DPRINT("round_no:", round_no)

        DPRINT("Received base message for round")
        serial_client_msg = data_received['slot_messages']
        # client_msg = ast.literal_eval(serial_client_msg)
        client_msg = json.loads(serial_client_msg)

        base_records[round_no][pid] = client_msg

        if len(base_records[round_no]) == num_of_clients and round_no not in sent_status[0]:

            sent_status[0][round_no] = 1  # 0 is base roundq
            slot_permutation = solve_equation(base_records[round_no], params)
            # data = json.dumps(slot_permutation)

            data_to_send = {
                'round_no': round_no,
                'msg_type': "BASE_PROTOCOL_REPLY",
                'slot_order': str(slot_permutation)
            }
            data = json.dumps(data_to_send)
            for sock in client_sockets:
                message_queues[sock].put(data)
                # send_data(sock, data)

            base_protocol_time = time.time() - base_start_time

            # print("base_protocol_time:", base_protocol_time)

            delayfilename = "./relay_base_delay_" + str(num_of_clients) + ".csv"
            with open(delayfilename, "a") as f:
                writer = csv.writer(f)
                writer.writerow([num_of_clients, round_no, base_protocol_time])

        return

    if data_received["msg_type"] == "CLIENT_BULK_MSG":

        round_no = data_received["round_no"]
        DPRINT("Received bulk message for round")
        serial_client_msg = data_received['slot_messages']
        # client_msg = ast.literal_eval(serial_client_msg)
        client_msg = json.loads(serial_client_msg)

        # print("Bulk round - length of received slot values from client:", len(client_msg))

        bulk_records[round_no][pid] = client_msg

        if len(bulk_records[round_no]) == num_of_clients and round_no not in sent_status[1]:
            # print("Not sent yet")

            # Once all the messages are received for the bulk round, compute the messages for slots
            sent_status[1][round_no] = 1  # index 1 is bulk round
            DPRINT("running bulk message computation with round no:", round_no)

            data_to_send = {
                'round_no': round_no,
                'msg_type': "BULK_PROTOCOL_REPLY"}
            data = json.dumps(data_to_send)

            # compute_message(bulk_records[round_no], params, round_no)
            compute_process = Process(target=compute_message,
                                      args=(bulk_records[round_no], params, round_no))
            compute_process.start()
            compute_process.join()

            for sock in client_sockets:
                message_queues[sock].put(data)
                # send_data(sock, data)

        DPRINT("returning")

        return


def solve_equation(record, params):
    DPRINT("record:", record)
    num_of_clients = params['node_params']['N_CLIENTS']
    p = params['base_params']['P']
    q = params['base_params']['Q']

    # TODO: Check the next two lines again
    # num_of_slots = len(record)
    num_of_slots = num_of_clients
    # num_of_cl = len(record)

    # print("record", record)
    # print("p", p)
    # print("q", q)
    # print("slots:", num_of_slots)
    # print("num_of_clients", num_of_clients)

    # compute messages of each block
    relay_messages = []
    for i in range(num_of_slots):
        relay_msg_of_slot = int(0)
        for j in range(num_of_clients):

            if i == 0:
                DPRINT("record -- ", record[j][i])

            # relay_msg_of_slot = (relay_msg_of_slot + record[j][i]) % q
            relay_msg_of_slot = (relay_msg_of_slot + record[j][i])
        relay_messages.append(relay_msg_of_slot % q)
    # print("share_vector_length:", share_vector_length)

    # print("relay_messages:", relay_messages)

    bits = 32

    # load pre-processed prf values
    filename = "../DPRF/PREPROCESSED_PRF/n" + str(num_of_clients) + "/RELAY/bits_" + str(bits) + ".txt"
    with open(filename, 'r') as f:
        # local_prf_evaluations = ast.literal_eval(f.read())
        local_prf_evaluations = json.loads(f.read())

    # print("local prf eval:", local_prf_evaluations[:5])

    # subtract the prf evaluation from message received
    final_equations = []
    for i in range(num_of_slots):
        val = int(round(int(relay_messages[i] - local_prf_evaluations[i]) / 1000) % q)
        val_in_grp = int(val % p)
        final_equations.append(val_in_grp)
    # print("final_equations:", final_equations)

    # Compute the equation solution in a different process

    qu = Queue()
    return_dict = {'output': []}
    qu.put(return_dict)
    equation_process = Process(target=solve_with_return, args=(final_equations, qu))
    equation_process.start()
    equation_process.join()

    return_dict = qu.get()
    # print("return dict:", return_dict)
    return return_dict['output']


def compute_message(bulk_slot_messages, params, round_no):
    DPRINT("RELAY FUNCTION")

    bulk_compute_start_time = time.time()

    vec_length = params['bulk_params']['VECTOR_LENGTH']
    num_of_nodes = params['node_params']['N_CLIENTS']
    bulk_q = params['bulk_params']['Q']
    bulk_p = params['bulk_params']['P']
    relay_messages = []

    bits = 256  # TODO: Take this from params

    # print("vec_length in compute message:", vec_length)

    # -----------------------------------------
    relay_messages = []

    set_bulk = []
    set_number_of_slots = []
    set_total_slots = []
    set_number_of_nodes = []

    relay_messages = []

    number_of_threads = 20

    total_slots = 37 * num_of_nodes

    number_of_slots_per_thread = total_slots // number_of_threads
    remaining_slots = total_slots % number_of_threads

    # print("total_slots:", total_slots)
    # print("number of threads:", number_of_threads)
    # print("number of slots per thread:", number_of_slots_per_thread)

    process_relay_message_start = time.time()
    start_setup_threads = time.time()

    for i in range(number_of_threads + 1):
        set_bulk.append(bulk_slot_messages)
    #
    threads = [None] * (number_of_threads + 1)
    manager = multiprocessing.Manager()
    results = manager.dict()

    ("setup threads time:", time.time() - start_setup_threads)

    start_threads_time = time.time()

    for i in range(len(threads)):
        # threads[i] = Process(target=process_relay_message, args=(set_bulk[i], results, i,
        # number_of_slots_per_thread, total_slots,num_of_nodes, bulk_q ))
        threads[i] = Process(target=process_relay_message,
                             args=(set_bulk[i], results, i,
                                   number_of_slots_per_thread, total_slots, num_of_nodes, bulk_q))
        threads[i].start()
    # do some other stuff

    for i in range(len(threads)):
        threads[i].join()
        if results[str(i)] is not None:
            relay_messages.extend(results[str(i)])
    # print("results:", results)
    DPRINT("lenght of relay messages:", len(relay_messages))
    DPRINT("thread time:", time.time() - start_threads_time)

    DPRINT("process_relay_message_time:", time.time() - process_relay_message_start)
    # This is for 1Kb of data -- each slot 226 bits so for 1kb it is 5 slots
    # vec_length = 5 * num_of_nodes

    '''
    for i in range(vec_length):
        relay_msg_of_slot = int(0)
        for j in range(num_of_nodes):
            # relay_msg_of_slot = (relay_msg_of_slot + client_slot_messages[j][i]) % bulk_q
            relay_msg_of_slot = (relay_msg_of_slot + client_slot_messages[j][i])
        relay_messages.append(relay_msg_of_slot % bulk_q)
    '''

    n_bits = 226


    print("starting prf computation")

    prf_start = time.time()

    ring_v = params['bulk_params']['RING_V']
    share_vector_length = params['bulk_params']['VECTOR_LENGTH']
    relay_share = [1] * share_vector_length
    relay_prf_start = time.time()
    # hash
    '''
    RELAY_HASH = compute_hash(0, share_vector_length, ring_v)
    RING_HASH_VEC = np.array(ntt(RELAY_HASH, ring_v))
    RING_SHARE_ROWS = np.array(ntt(relay_share, ring_v))
    '''

    prf_filename = "../DPRF/PRF_VECTORS_bits_226.txt"
    with open(prf_filename, 'r') as f:
        prf_vectors = json.loads(f.read())

    qvratio = bulk_qvratio
    RING_HASH_VEC = np.array(prf_vectors['ring_hash_vec_'])
    RING_SHARE_ROWS = np.array(prf_vectors['ring_share_rows_'])


    local_prf_evaluations = prf_ring(RING_HASH_VEC, RING_SHARE_ROWS, ring_v, qvratio)
    print("computed prf")
    print("prf time:", time.time() - prf_start)

    # print("updated - share_vector_length:", vec_length)
    filename = "../DPRF/PREPROCESSED_PRF/n" + str(num_of_nodes) + "/RELAY/bits_" + str(n_bits) + ".txt"
    # local_prf_evaluations = []
    with open(filename, 'r') as f:
        # local_prf_evaluations = ast.literal_eval(f.read())
        local_prf_evaluations = json.loads(f.read())

    # print("len of relay_messages:", len(relay_messages))
    # print("len of local_prf_evaluations:", len(local_prf_evaluations))

    vec_length = total_slots

    # subtract the prf evaluation from message received

    # TODO : just for check, remove!
    if len(relay_messages) < vec_length:
        relay_messages.extend(local_prf_evaluations[:vec_length - len(relay_messages)])

    final_values = []
    for i in range(vec_length):
        val = (int(relay_messages[i] - local_prf_evaluations[i])) % bulk_q
        val_in_grp = int(round(int(val) / 1000) % bulk_p)
        final_values.append(val_in_grp)
    # print("final_values:", final_values)

    # Ping google
    hostname = "google.com"  # example
    response = os.system("ping -c 1 " + hostname)

    # and then check the response...
    if response == 0:
        print(hostname, "is up!")
    else:
        print(hostname, "is down!")

    bulk_protocol_time = time.time() - bulk_compute_start_time
    delayfilename = "./relay_bulk_delay_" + str(num_of_nodes) + ".csv"
    with open(delayfilename, "a") as f:
        writer = csv.writer(f)
        writer.writerow([num_of_nodes, round_no, total_slots, bulk_protocol_time])
    return


def process_relay_message(bulk_slot_messages, results, index, number_of_slots_per_thread, total_slots, num_of_nodes,
                          bulk_q):
    relay_messages = []
    start_index = index * number_of_slots_per_thread
    end_index = (index + 1) * number_of_slots_per_thread
    if end_index > total_slots:
        end_index = total_slots

    # print("start_index:", start_index)
    # print("end_index:", end_index)
    # print("num_of_nodes:", num_of_nodes)

    start_process_relay_message_inside = time.time()

    for i in range(start_index, end_index):
        relay_msg_of_slot = int(0)
        for j in range(num_of_nodes):
            relay_msg_of_slot = int(relay_msg_of_slot + bulk_slot_messages[j][i])
        relay_messages.append(int(relay_msg_of_slot % bulk_q))
    results[str(index)] = relay_messages
    # print("inside process relay:", time.time() - start_process_relay_message_inside)

    return
