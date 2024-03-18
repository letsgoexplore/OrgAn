import sys
import argparse

sys.path += ['./', '../', '../../']

import util.nf_prifi_round as nf
from   util.nf_prifi_round import *
from conf.groupparam import *

from multiprocessing import Process

SLOTS = 0
CLIENTS = 0
SUB_CLIENTS = 0

def node_thread(nid, params):

    DPRINT("Starting Node: ", nid)
    print("Starting Node: ", nid)
    MY_PORT = BASE_PORT + nid
    #DPRF_PORT = MY_PORT + 1000
    # start server part of node to receive Hello

    DPRINT("PHASE0: Attempting handshake with all the nodes")

    node_server_thread = threading.Thread(target=serverSock, args=(MY_IP, MY_PORT, nid, params))
    node_server_thread.start()

    #sleep(2)
    ## start client part to send hello to all other peers
    #node_client_thread = threading.Thread(target=sendId2peers, args=(nid,))
    #node_client_thread.start()
    #node_client_thread.join()
    #DPRINT("PHASE0: Finished the first handshake with all the nodes")
    #sleep(2)

    if nid != 0:

        sleep(0.5)

        my_id = nid - 1 
        node_threads = []
        
        sub_clients = params['node_params']['N_SUB_CLIENTS']  

        start_client_index = my_id * sub_clients 
        end_client_index =   start_client_index + sub_clients

        params['node_params']['START_CLIENT_INDEX'] = start_client_index
        params['node_params']['END_CLIENT_INDEX'] = end_client_index

        for cnid in range(start_client_index, end_client_index):
            #new_node_thread = threading.Thread(target=node_thread, args=(MY_IP, MY_PORT, cnid))
            #new_node_thread = threading.Thread(target=client_message_bulk, args=(cnid,params ))
            sleep(0.1)
            new_node_thread = Process(target=client_message_bulk, args=(cnid,params ))
            new_node_thread.start()
            node_threads.append(new_node_thread)

        for i in range(len(node_threads)):
            node_threads[i].join()    
        #Close the server socket 
        #node_server_thread.data_receive = False
        #temp = socket.socket(socket.AF_INET,
        #                     socket.SOCK_STREAM).connect((MY_IP, MY_PORT))
        #node_server_thread.join()
        #timeout_end = time.process_time()

if __name__ == "__main__":
    description = """ 
    This program provides a single node 
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-i", "--id", default=0, type=int, help="node id "
    )

    parser.add_argument(
        "-n", "--nodes", default=4, type=int, help="number of nodes in System including relay"
    )

    parser.add_argument(
        "-s", "--slots", default=3, type=int, help="number of slots in system"
    )
    parser.add_argument(
        "-c", "--clients", default=3, type=int, help="number of clients in system"
    )

    parser.add_argument(
        "-sc", "--sclients", default=3, type=int, help="number of subclients in system"
    )

    parser.add_argument(
        "-sup", "--superclients", default=3, type=int, help="number of superclients in system"
    )

    args = parser.parse_args()

    #nf.N_NODES = args.nodes
    #nf.CLIENTS = args.clients 
    #nf.TOTAL_CLIENTS = args.slots
    #if args.id == 0:
    #    nf.TOTAL_CLIENTS = args.clients
    ##nf.CLIENTS = args.slots


    #SLOTS = args.slots 
    #SUB_CLIENTS = args.sclients 

    params = {}

    params['base_params'] = BASE_PARAMS
    params['bulk_params'] = BULK_PARAMS
    params['node_params'] = NODE_PARAMS
    params['slot_params'] = SLOT_PARAMS

    params['node_params']['N_NODES']   = args.nodes
    params['node_params']['N_CLIENTS'] = args.clients
    params['node_params']['N_SLOTS']   = args.slots
    params['node_params']['N_SUB_CLIENTS']   = args.sclients
    params['node_params']['N_SUPER_CLIENTS']   = args.superclients
    if args.id == 0:
        params['node_params']['N_TOTAL_CLIENTS'] = args.clients
    else:
        params['node_params']['N_TOTAL_CLIENTS'] = args.slots


    node_thread(int(args.id), params)



    sys.exit(0)
    os.system("exit 0")
