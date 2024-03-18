import socket, struct, json, sys, time
from OpenSSL import SSL, crypto

sys.path += ['./', '../']

from conf.connectionconfig import *
from time import sleep

debug = 0


def DPRINT(*args, **kwargs):
    if debug:
        print(*args, **kwargs)


def recvInt(sock):
    integer = sock.recv(1024)
    integer = integer.decode('utf-8')
    integer = int(integer)
    return integer


def sendInt(sock, integer):
    sock.send(str(integer).encode('utf-8'))


def verifyConnection(conn, cert, errnum, depth, ok):
    print("Got Certificate from ", str(conn))
    return ok


def send_data(sock, data):
    # Prefix each message with a 4-byte length (network byte order)
    # data = struct.pack('>I', len(data)) + data
    data = struct.pack('>I', len(data)) + bytes(data, 'utf-8')
    # data = struct.pack('>I', len(data)) + bytes(data)
    sock.sendall(data)

def recv_data(sock):
    # Read message length and unpack it into an integer
    raw_datalen = recvall(sock, 4)
    if not raw_datalen:
        return None
    datalen = struct.unpack('>I', raw_datalen)[0]
    # Read the message data
    return recvall(sock, datalen)


def recvall(sock, n):
    # Helper function to recv n bytes or return None if EOF is hit
    data = bytearray()
    while len(data) < n:
        packet = sock.recv(n - len(data))
        if not packet:
            return None
        data.extend(packet)
    return data


def disconnect(sock):
    sock.shutdown()
    sock.close()


def send_with_retry(sock, data):
    retries_left = 10
    while retries_left > 0:
        try:
            send_data(sock, data)
        except:
            retries_left -= 1
        else:
            return


def send2relay(nid, RELAY_ID, data_to_send):
    # here sockets is a global dict
    if RELAY_ID in sockets:
        send_data(sockets[RELAY_ID], data_to_send)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            if AWS:
                s.connect((NODE_IP[node_index], BASE_PORT + node_index))
            else:
                s.connect(("127.0.0.1", BASE_PORT + node_index))
        except Exception as e:
            print("Retry connect to  node_id:", node_index, "with exception: ", e)
        DPRINT("Connected - Sending data to PORT", BASE_PORT + node_index, " of Node", node_index)

        # store it in sockets
        sockets[RELAY_ID] = s
        send_data(s, data_to_send)


def send2client(nid, pid, data_to_send):
    # here sockets is a global dict
    node_index = pid
    if pid in client_sockets:
        send_data(client_sockets[pid], data_to_send)
    else:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        client_sockets[pid] = s
        try:
            if AWS:
                s.connect((NODE_IP[node_index], BASE_PORT + node_index))
            else:
                s.connect(("127.0.0.1", BASE_PORT + node_index))
        except Exception as e:
            print("Retry connect to  node_id:", node_index, "with exception: ", e)
        DPRINT("Connected - Sending data to PORT", BASE_PORT + node_index, " of Node", node_index)
        send_data(s, data_to_send)
