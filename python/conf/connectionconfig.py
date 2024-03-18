import requests

SERVER_PVT_KEY_FILE = "certs/server.pkey"
SERVER_CERT_FILE = "certs/server.cert"
CLIENT_PVT_KEY_FILE = "certs/client.pkey"
CLIENT_CERT_FILE = "certs/client.cert"
CA_FILE = "certs/CA.cert"

AWS = 1
if AWS:
    MY_IP = (requests.get('http://checkip.amazonaws.com')).text.strip()
else:
    MY_IP = "127.0.0.1"

RELAY_IP = "3.14.119.173"
RELAY_PORT = 11000
ROUNDS = 2

from decimal import *

getcontext().prec = 571
