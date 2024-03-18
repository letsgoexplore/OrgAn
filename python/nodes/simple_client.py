import sys 
import argparse

sys.path += ['./', '../', '../../']

import socket

messages = [ 'This is the message. ',
             'It will be sent ',
             'in parts.',
             ]
server_address = ('localhost', 10000)

# Create a TCP/IP socket
relaysock =  socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Connect the socket to the port where the server is listening
print ('connecting to %s port %s' % server_address)
relaysock.connect(server_address)
print("connected")

for message in messages:
    print ('%s: sending "%s"' % (relaysock.getsockname(), message))
    relaysock.send(message.encode())

    # Read responses on both sockets
    #data = relaysock.recv(1024)
    #print ('%s: received "%s"' % (relaysock.getsockname(), data))
    #if not data:
    #    print ('closing socket', relaysock.getsockname())
    #    s.close()
