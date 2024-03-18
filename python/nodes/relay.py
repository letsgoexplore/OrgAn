import sys
import argparse

sys.path += ['./', '../', '../../']

from util.relay_fullround import *
from conf.groupparam import *

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

    params['node_params']['rounds'] = ROUNDS
    params['node_params']['RELAY_IP'] = RELAY_IP
    params['node_params']['RELAY_PORT'] = RELAY_PORT

    params['node_params']['N_CLIENTS'] = args.clients

    node_server_thread = threading.Thread(target=server_socket, args=(params,))
    node_server_thread.start()

