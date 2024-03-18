
from conf.includefiles import *
from multiprocessing import Process
import multiprocessing

debug = 0

#N_NODES = 0

client_msg_rcvd = 0

BASE_SEND_TIME = 0
BASE_RECEIVE_REPLY_TIME = 0

BULK_SEND_TIME = 0
BULK_RECEIVE_REPLY_TIME = 0

RESULTS = [None] * 400

u = 1

def DPRINT(*args, **kwargs):
    if debug:
        print(*args, **kwargs)


def serverSock(MY_IP, MY_PORT, nid, params):
    print("server socket")
    #print("N_NODES", N_NODES)
    all_client_threads = []
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('', MY_PORT))

    N_NODES =  params['node_params']['N_NODES']
    SUPER_CLIENTS  =  params['node_params']['N_SUPER_CLIENTS']
    CLIENTS  =  params['node_params']['N_CLIENTS']
    #s.listen(N_NODES)
    s.listen(CLIENTS)

    t = threading.currentThread()


    client_slot_messages = {}
    bulk_slot_messages = {}
    #client_msg_rcvd = 0

    MAX_CLIENT = 400 
    for i in range(MAX_CLIENT):
        client_slot_messages[str(i)] = None
        bulk_slot_messages[str(i)] = None

    while getattr(t, "data_receive", True):
        try:
            peer_con, peer_addr = s.accept()

            handle_peer_thread = threading.Thread(target=handle_peer, args=(peer_con, nid, params, client_slot_messages, bulk_slot_messages))
            handle_peer_thread.start()

            all_client_threads.append(handle_peer_thread)

        except KeyboardInterrupt:
            print("[!] Keyboard Interrupted!")
            s.shutdown(socket.SHUT_RDWR)
            s.close()
            for thread in all_client_threads:
                thread.join()
                break
        except Exception as e:
            print(e)

    DPRINT("***Exiting the loop")

    for thread in all_client_threads:
        thread.join()
    return


def handle_peer(peer_con, nid, params, client_slot_messages, bulk_slot_messages):
    data_received = recv_data(peer_con)

    if not data_received:
        return

    # Send ACK
    #peer_con.sendall(b"ACK")
    peer_con.close()

    data_received = json.loads(data_received)
    pid = data_received["my_id"]

    if data_received["msg_type"] == "HELLO":
        DPRINT("Hello received from:", pid)
        print("Hello received from:", pid)

    if data_received["msg_type"] == "DATA":
        DPRINT("Received Shares")
        receive_shares(nid, pid, data_received, params)

    if data_received["msg_type"] == "CLIENT_BASE_MSG":
        DPRINT("Received Shares")
        receive_msg_base(pid, data_received, client_slot_messages, params)

    if data_received["msg_type"] == "CLIENT_BULK_MSG":
        DPRINT("Received Shares")
        receive_msg_bulk(pid, data_received, bulk_slot_messages, params)

    if data_received["msg_type"] == "BULK_PROTOCOL_REPLY":
        
        BULK_RECEIVE_RESPONSE_TIME = time.time()
        print("BULK_SEND_TIME:", BULK_SEND_TIME)
        print("BULK_RECEIVE_RESPONSE_TIME:", BULK_RECEIVE_RESPONSE_TIME)

        delay_timing = []
        total_bulk_delay = BULK_RECEIVE_RESPONSE_TIME - BULK_SEND_TIME
        total_clients = params['node_params']['N_SLOTS']
        delayfilename = "./tmp/organ_bulk_delay"+str(total_clients)+"_nid_"+ str(nid)+".csv"
        delay_timing.append(total_bulk_delay)

        with open(delayfilename, "a") as f:
            writer = csv.writer(f)
            writer.writerow(delay_timing)

        #Close the server  socket by setting data receive to False  
        #node_server_thread.data_receive = False
        #temp = socket.socket(socket.AF_INET,
        #                     socket.SOCK_STREAM).connect((MY_IP, MY_PORT))
        #node_server_thread.join()

    if data_received["msg_type"] == "BASE_PROTOCOL_REPLY":
        
        #print("SEND_TIME:", SEND_TIME)
        #print("Received base protocol reply")
        #print("Base reply at:", time.time()) 
        #RECEIVE_TIME = time.time()


        BASE_RECEIVE_RESPONSE_TIME = time.time()
        print("BASE_SEND_TIME:", BASE_SEND_TIME)
        print("BASE_RECEIVE_RESPONSE_TIME:", BASE_RECEIVE_RESPONSE_TIME)

        delay_timing = []

        total_base_delay = BASE_RECEIVE_RESPONSE_TIME - BASE_SEND_TIME
        total_clients = params['node_params']['N_SLOTS']
        delayfilename = "./tmp/organ_base_delay"+str(total_clients)+"_nid_"+ str(nid)+".csv"
        delay_timing.append(total_base_delay)
        with open(delayfilename, "a") as f:
            writer = csv.writer(f)
            writer.writerow(delay_timing)

        #delay_timing = [total_delay]

        #print("Total delay:", RECEIVE_TIME - SEND_TIME )
        #delayfilename = "./tmp/organ_delay"+str(TOTAL_CLIENTS)+".csv"
        #with open(delayfilename, "a") as f:
        #    writer = csv.writer(f)
        #    writer.writerow(delay_timing)
        #sys.exit(0)
        #os.system("exit 0")
        #client_message_bulk(nid, bulk_share_vector_length)
        #run_bulk_clients(TOTAL_CLIENTS)
        #run_bulk_clients(params)
    return


def sendId2peers(nid):
    data_to_send = {'msg_type': "HELLO",
                    'my_id': nid
                    }
    data_to_send = json.dumps(data_to_send)

    for pid in range(N_NODES):
        if nid != pid:
            DPRINT("Sending Hello to:", pid)
            send2Node(nid, pid, data_to_send)

def client_message_base(nid, params):

    total_clients = params['node_params']['N_TOTAL_CLIENTS']
    no_of_slots = total_clients
    base_p = params['base_params']['P']
    base_q = params['base_params']['Q']
    bits   = params['base_params']['BITS']
    fragments = params['slot_params']['FRAGMENTS']

    message_ele = int(nid+1)

    #bits = 32
    filename = "../DPRF/PREPROCESSED_PRF/n"+str(total_clients)+"/bits_"+str(bits)+"_nid_"+str(nid)+".txt"
    with open(filename, 'r') as f:
        #prf_evaluations = ast.literal_eval(f.read())
        prf_evaluations = json.loads(f.read())

    slot_messages = []
    slot_msg = int(1)
    for i in range(no_of_slots):
        slot_msg = slot_msg * message_ele 
        slot_msg = slot_msg % base_p 
        msg_to_append =  int((int(prf_evaluations[i]) + int(1000*slot_msg)) % base_q)  
        slot_messages.append(msg_to_append)
    data_to_send = { 
                    'msg_type': "CLIENT_BASE_MSG",
                    'my_id': nid,
                    'slot_messages': json.dumps(slot_messages), 
                    'slots_needed': fragments 
                    #'current_slot': SLOT_NUMBER
                    }   
    data_to_send = json.dumps(data_to_send)

    print("time when sending the client packet:", time.time())
    global BASE_SEND_TIME
    BASE_SEND_TIME = time.time()
    
    DPRINT(data_to_send)
    relay_id = int(0)
    
    if nid == 0:
        nid += 1

    try:
        DPRINT("Sending shares to relay id:", relay_id)
        send2Node(nid, relay_id, data_to_send)
    
    except Exception as e:
        print("Exception while sending shares:", e)


def receive_msg_base(pid, data_received, client_slot_messages, params):
    #global client_messages

    num_of_clients = params['node_params']['N_CLIENTS']

    serial_client_msg = data_received['slot_messages']
    client_id         = data_received['my_id']
    client_msg = json.loads(serial_client_msg)
    
    #add to client slot message list 
    #global client_slot_messages, client_msgs_rcvd
    client_slot_messages[str(client_id)] = client_msg

    global client_msg_rcvd 
    client_msg_rcvd += 1 

    #num_of_clients = CLIENTS 
    if client_msg_rcvd == num_of_clients:
        client_msg_rcvd = 0 

        relay_function_base(client_slot_messages, params)
    #return client_msgs_rcvd, client_slot_messages


def relay_function_base(client_slot_messages, params):

    clients = params['node_params']['N_CLIENTS']
    base_p = params['base_params']['P']
    base_q = params['base_params']['Q']
    bits   = params['base_params']['BITS']
    fragments = params['slot_params']['FRAGMENTS']

    num_of_slots = clients
    num_of_nodes = clients

    relay_begin_time = time.time()

    relay_messages = []

    #getcontext().prec = 10


    equ_formation_begin_time = time.time()

    relay_messages = []
    for i in range(num_of_nodes):
        relay_msg_of_slot = int(0)
        for j in range(num_of_nodes):
            relay_msg_of_slot = int(relay_msg_of_slot + client_slot_messages[str(j)][i]) 
        relay_messages.append(int(relay_msg_of_slot % base_q))
    
    filename = "../DPRF/PREPROCESSED_PRF/n"+str(clients)+"/RELAY/bits_"+str(bits)+".txt"
    with open(filename, 'r') as f:
        local_prf_evaluations = json.loads(f.read())

    #subtract the prf evaluation from message received 
    final_equations = []
    for i in range(num_of_slots):
        val = int(round(int(relay_messages[i] - local_prf_evaluations[i])/1000) % base_q)
        val_in_grp = int(val % base_p)
        final_equations.append(val_in_grp)

    DPRINT("final_equations:", final_equations)

    #DPRINT("solving dc sums")
    output = solve(final_equations)
    DPRINT(output)
    DPRINT(output)

    #clear the client messages 
    #global client_slot_messages
    #client_slot_messages = []

    nid = 0 #just set to 1 instead of 0 
    data_to_send = { 
                    'msg_type': "BASE_PROTOCOL_REPLY",
                    'my_id': nid,
                    'slot_order':str(output)
                    }   
    data_to_send = json.dumps(data_to_send)

    #for pid in [1]:
    #for pid in range(1, N_NODES+1):
    N_NODES =  params['node_params']['N_NODES']
    SUPER_CLIENTS  =  params['node_params']['N_SUPER_CLIENTS']
    for pid in range(SUPER_CLIENTS, 0, -1):
    #TODO: check the index 
        try:
            DPRINT("Sending ping reply to node id:", pid)
            send2Node(nid, pid , data_to_send)
        
        except Exception as e:
            print("Exception while sending shares:", e)



    
def client_message_bulk(nid, params):

    total_clients = params['node_params']['N_TOTAL_CLIENTS']
    no_of_slots = total_clients
    bulk_p = params['bulk_params']['P']
    bulk_q = params['bulk_params']['Q']
    bits   = params['bulk_params']['BITS']
    fragments = params['slot_params']['FRAGMENTS']
    vec_length = params['bulk_params']['VECTOR_LENGTH']

    message_ele = int(nid+1)
    
    bits =  226

    filename = "../DPRF/PREPROCESSED_PRF/n"+str(total_clients)+"/bits_"+str(bits)+"_nid_"+str(nid)+".txt"
    #filename = "../DPRF/PREPROCESSED_PRF/n"+str(TOTAL_CLIENTS)+"/bits_"+str(bits)+"_nid_"+str(nid)+".txt"
    with open(filename, 'r') as f:
        #prf_evaluations = ast.literal_eval(f.read())
        prf_evaluations = json.loads(f.read())

    vec_length = 37*total_clients 

    if total_clients > 200:
        vec_length = 37*total_clients 
        prf_evaluations = prf_evaluations + prf_evaluations 
        pr_evaluations = prf_evaluations[:vec_length]

    slot_messages = []
    slot_msg = int(1)

    slots_per_client = int(vec_length/total_clients)
    my_slot_index_start = int(nid) * slots_per_client
    my_slot_index_end = (int(nid)+1) * slots_per_client

    for i in range(my_slot_index_start, my_slot_index_end):
        prf_evaluations[i] = int((prf_evaluations[i] + 1000* message_ele) % bulk_q )
    data_to_send = {'msg_type': "CLIENT_BULK_MSG",
                    'my_id': nid,
                    #'slot_messages': str(prf_evaluations), 
                    'slot_messages': json.dumps(prf_evaluations) 
                    }   
    data_to_send = json.dumps(data_to_send)

    print("time when sending the client packet:", time.time())

    global BULK_SEND_TIME
    BULK_SEND_TIME = time.time()
       
    DPRINT(data_to_send)
    relay_id = int(0)
       
    if nid == 0:
        nid += 1

    try:
        DPRINT("Sending shares to relay id:", relay_id)
        send2Node(nid, relay_id, data_to_send)
       
    except Exception as e:
        print("Exception while sending shares:", e)




def receive_msg_bulk(pid, data_received, bulk_slot_messages, params):
    #global client_messages

    serial_client_msg = data_received['slot_messages']
    #client_msg = ast.literal_eval(serial_client_msg)
    client_id         = data_received['my_id']
    client_msg = json.loads(serial_client_msg)
    
    #add to client slot message list 
    bulk_slot_messages[str(client_id)] = client_msg

    global client_msg_rcvd 
    client_msg_rcvd += 1 

    num_of_clients = params['node_params']['N_CLIENTS']
    if client_msg_rcvd == num_of_clients:
        client_msg_rcvd = 0 
        relay_function_bulk(bulk_slot_messages, params)

def process_relay_message(bulk_slot_messages, results, index, number_of_slots_per_thread, total_slots, num_of_nodes, bulk_q):

    relay_messages = []
    start_index = index * number_of_slots_per_thread
    end_index = (index+1) * number_of_slots_per_thread

    if end_index > total_slots:
        end_index = total_slots


    for i in range(start_index, end_index):
        relay_msg_of_slot = int(0)
        for j in range(num_of_nodes):
            relay_msg_of_slot = int (relay_msg_of_slot + bulk_slot_messages[str(j)][i])
        relay_messages.append(int (relay_msg_of_slot % bulk_q))
    results[str(index)]= relay_messages
    #print("inside the proces: relay_messages[0]", relay_messages[0])
    #results[index] = relay_messages
    #print("inside funciton: len(relay_messages):",len(relay_messages) )


def relay_function_bulk(bulk_slot_messages, params):

    print("RELAY FUNCTION")
    clients = params['node_params']['N_CLIENTS']
    bulk_p = params['bulk_params']['P']
    bulk_q = params['bulk_params']['Q']
    bits   = params['bulk_params']['BITS']
    share_vector_length   = params['bulk_params']['VECTOR_LENGTH']
    fragments = params['slot_params']['FRAGMENTS']


    relay_messages = []

    DPRINT("client slot messages len:", len(bulk_slot_messages))
    #print("client_slot_messages:", client_slot_messages)

    #getcontext().prec = 10

    num_of_slots = params['node_params']['N_CLIENTS']
    num_of_nodes = num_of_slots

    equ_formation_begin_time = time.time()
    bulk_process_start = time.time()


    #__________________________________________________________________________________`
    relay_messages = []

    set_bulk = []
    set_number_of_slots = []
    set_total_slots = []
    set_number_of_nodes = []

    ##for i in range(share_vector_length):
    #for i in range(37*num_of_nodes):
    #    relay_msg_of_slot = int(0)
    #    for j in range(num_of_nodes):
    #        relay_msg_of_slot = int (relay_msg_of_slot + bulk_slot_messages[str(j)][i]) 
    #    relay_messages.append(int (relay_msg_of_slot % bulk_q))

    #__________________________________________________________________________________`


    relay_messages = []
   
    number_of_threads = 20
    #print("Using multiple threads")

    #For ping each node needs two slots 

    #total_slots = share_vector_length
    total_slots = 37 * num_of_nodes
    number_of_slots_per_thread = total_slots//number_of_threads
    remaining_slots = total_slots % number_of_threads 

    for i in range(number_of_threads+1):
        set_bulk.append(bulk_slot_messages)
    #
    threads = [None] * (number_of_threads+1)
    manager = multiprocessing.Manager()
    results = manager.dict()
    
    for i in range(len(threads)):
        #threads[i] = Process(target=process_relay_message, args=(set_bulk[i], results, i, number_of_slots_per_thread, total_slots,num_of_nodes, bulk_q ))
        threads[i] = Process(target=process_relay_message, args=(set_bulk[i], results, i, number_of_slots_per_thread, total_slots,num_of_nodes, bulk_q ))
        threads[i].start()
    # do some other stuff
    
    for i in range(len(threads)):
        threads[i].join()

        if results[str(i)] is not None:
            relay_messages.extend(results[str(i)])
    #print("results:", results)
    print(len(relay_messages))



    filename = "../DPRF/PREPROCESSED_PRF/n"+str(clients)+"/RELAY/bits_"+str(bits)+".txt"
    with open(filename, 'r') as f:
        local_prf_evaluations = json.loads(f.read())

    #Ideally take the next set of PRF values 
    if clients > 200:
        local_prf_evaluations = local_prf_evaluations + local_prf_evaluations 
        local_prf_evaluations = local_prf_evaluations[:total_slots]

    #subtract the prf evaluation from message received 
    final_equations = []
    #for i in range(share_vector_length):
    for i in range(37*num_of_nodes):
    #for i in range(num_of_slots):
        val = (int(relay_messages[i] - local_prf_evaluations[i])) % bulk_q
        val_in_grp = int(round(int(val)/1000) % bulk_p)

    bulk_process_end = time.time()

    print("bulk processing time:", bulk_process_end - bulk_process_start)


    #__________________________________________________________________________________`



    ping_begin_time = time.time()

    hostname = "google.com" #example
    response = os.system("ping -c 1 " + hostname)
   
    #and then check the response...
    if response == 0:
        print (hostname, "is up!")
    else:
        print (hostname, "is down!")
    ping_end_time = time.time()

    relay_end_time = time.time()


    nid = 0 #just set to 1 instead of 0 

    data_to_send = {
                    'msg_type': "BULK_PROTOCOL_REPLY",
                    'my_id': nid,
                    #'computed_messages':str(serialized_output)
                    }
    data_to_send = json.dumps(data_to_send)

    N_NODES = params['node_params']['N_NODES']
    SUPER_CLIENTS  =  params['node_params']['N_SUPER_CLIENTS']
    for pid in range(SUPER_CLIENTS, 0, -1):
    #for pid in range(1, N_NODES+1):
    #for pid in range(N_NODES, 0, -1):
    #TODO: check the index
        try:
            DPRINT("Sending ping reply to node id:", pid)
            send2Node(nid, pid , data_to_send)

        except Exception as e:
            print("Exception while sending shares:", e)

def run_bulk_clients(params):

    START_CLIENT_INDEX = params['node_params']['START_CLIENT_INDEX']
    END_CLIENT_INDEX   = params['node_params']['END_CLIENT_INDEX']

    bulk_threads = []
    for cnid in range(START_CLIENT_INDEX, END_CLIENT_INDEX):
        #new_node_thread = Process(target=client_message_bulk, args=(cnid, bulk_share_vector_length, total_clients))
        new_node_thread = Thread(target=client_message_bulk, args=(cnid, params))
        #new_node_thread = Process(target=client_message_bulk, args=(cnid, params))
        new_node_thread.start()
        bulk_threads.append(new_node_thread)

    for i in range(len(bulk_threads)):
        bulk_threads[i].join()


