import select
import socket
import sys
import queue

client_socks = {}

# Create a TCP/IP socket
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)

# Bind the socket to the port
server_address = ('localhost', 10000)
print('starting up on %s port %s' % server_address)
server.bind(server_address)

# Listen for incoming connections
server.listen(5)

inputs = [server]

outputs = []

message_queues = {}

while inputs:
    print('\nwaiting for the next event')
    readable, writable, exceptional = select.select(inputs, outputs, inputs)

    for s in readable:
        if s is server:

            print("got something")

            connection, client_address = s.accept()
            connection.setblocking(0)
            inputs.append(connection)

            # Give the connection a queue for data we want to send
            message_queues[connection] = queue.Queue()
        else:
            print("its data")
            data = s.recv(1024)
            if data:
                print('received "%s" from %s' % (data, s.getpeername()))
                message_queues[s].put(data)
                # Add output channel for response
                if s not in outputs:
                    outputs.append(s)
            else:
                # Interpret empty result as closed connection
                print('closing', client_address, 'after reading no data')
                # Stop listening for input on the connection
                if s in outputs:
                    outputs.remove(s)
                inputs.remove(s)
                s.close()

                # Remove message queue
                del message_queues[s]

    for s in writable:
        try:
            next_msg = message_queues[s].get_nowait()
        except queue.Empty:
            # No messages waiting so stop checking for writability.
            print('output queue for', s.getpeername(), 'is empty')
            outputs.remove(s)
        else:
            print('sending "%s" to %s' % (next_msg, s.getpeername()))
            s.send(next_msg)

    for s in exceptional:
        print('handling exceptional condition for', s.getpeername())
        # Stop listening for input on the connection
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()

        # Remove message queue
        del message_queues[s]
