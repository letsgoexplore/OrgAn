import sys
import argparse

sys.path += ['./', '../', '../../']
from util.client_fullround import *
import util.client_fullround as nf
from conf.groupparam import *
import random


def node_thread(nid, params):
    print("Starting Node: ", nid)

    node_start_time = time.time()

    sleep(random.uniform(0.5, 3))
    if AWS:
        server_address = (RELAY_IP, RELAY_PORT)
    else:
        server_address = ('localhost', 10000)
    relay_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect the socket to the port where the server is listening
    # print('connecting to %s port %s' % server_address)
    relay_socket.connect(server_address)
    print("connected")

    data_to_send = {'msg_type': "HELLO", 'my_id': nid}
    data = json.dumps(data_to_send)
    print("data:", data)
    send_data(relay_socket, data)

    # Don't start transmitting till 5 seconds
    while time.time() - node_start_time < 5:
        sleep(0.01)


    # print("Start actual protocol")
    node_server_thread = threading.Thread(target=server_socket, args=(nid, params, relay_socket))
    node_server_thread.start()

    nf.TIMING['START_TIME'] = time.time()
    print("start time:", nf.TIMING['START_TIME'])

    num_of_rounds = params['node_params']['rounds']
    print("num of rounds:", num_of_rounds)
    for i in range(num_of_rounds):
        sleep(0.01)
        client_message_base(nid, params, i, relay_socket)


if __name__ == "__main__":
    description = """ 
    This program provides a single node 
    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "-i", "--id", default=0, type=int, help="node id "
    )

    parser.add_argument(
        "-c", "--clients", default=2, type=int, help="number of clients in system"
    )

    args = parser.parse_args()

    params = {}

    params['base_params'] = BASE_PARAMS
    params['bulk_params'] = BULK_PARAMS
    params['node_params'] = NODE_PARAMS
    params['slot_params'] = SLOT_PARAMS

    params['base_msgs_rcvd'] = 0
    params['bulk_msgs_rcvd'] = 0

    params['node_params']['rounds'] = ROUNDS
    params['node_params']['RELAY_IP'] = RELAY_IP
    params['node_params']['RELAY_PORT'] = RELAY_PORT

    params['node_params']['N_CLIENTS'] = args.clients

    node_thread(int(args.id), params)

    sys.exit(0)
