import subprocess
from AWS_node_ips import *


IPS = NODE_IP
IDS = []

no_super_nodes = 10 
total_clients = 10 

clients_per_node = int(total_clients/no_super_nodes)

print("\n\n")
for i in range(no_super_nodes):

    '''
    filename = "organScripts/runOrgan_supernode_"+str(i)
    file = open(filename, 'w+')

    for j in range(clients_per_node):
    #generate tendermint command for each node 
    #commandstring = "cd KODE/DKG/bbss_dkg/; python3 aws_bbss_non_mal_node.py -i " + str(i) + " -n " + str(n) 
        commandstring = "cd newOrgan/nodes; python3 client.py -i " + str((clients_per_node*i)+j) + " -n " + str(total_clients) + "\n" 

    #generate bash scripts with name tendermint_comamnd_(i) for each node
        try:
            filename = "organScripts/runOrgan_supernode_"+str(i)
            with open(filename, 'a') as outfile:
                outfile.write(commandstring)
        except Exception as e: print("Exception:", e)
    print("commandstring:",commandstring)

    '''
    # copy the bash script to the node 
    try:
        cmd = "scp -i " + KEY + " -r  ../DPRF/PREPROCESSED_PRF  ubuntu@"+NODE_IP[i]+":/home/ubuntu/newOrgan/DPRF/"
        print("Running command:", cmd)
        os.system(cmd)
    except Exception as e: print(e) 
