import boto3
import botocore 
import paramiko 
import io
import os

OrgAn2 = "3.14.119.173"
C1  = "3.21.8.65"
C2  = "3.22.36.233"
C3  = "3.23.201.157"
C4  = "3.128.141.86"
C5  = "3.13.99.100"
C6  = "3.132.90.153"
C7  = "3.138.149.21"
C8  = "3.138.53.109"
C9  = "3.139.250.107"
C10 = "3.140.3.170"

KEY = "OmTrial1.pem"

NODE_IP = [C1, C2, C3, C4, C5, C6, C7, C8, C9, C10]
no_super_nodes = len(NODE_IP)

RELAY_IP = OrgAn2


