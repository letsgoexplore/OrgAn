#!/bin/bash

NODES=$1

echo Total Nodes:$NODES

osascript -e 'tell app "Terminal" 
    do script "cd ~/OrgAn/nodes/; python3 nf_prifi.py -i 0 -n 2 -sup 2 -c 10"  
end tell'

osascript -e 'tell app "Terminal" 
    do script "cd ~/OrgAn/nodes/; python3 nf_prifi.py -i 1 -n 2 -s 10 -sc 5"  
end tell'

osascript -e 'tell app "Terminal" 
    do script "cd ~/OrgAn/nodes/; python3 nf_prifi.py -i 2 -n 2 -s 10 -sc 5"  
end tell'

#    do script "cd /Users/easwarvivek/Documents/OrgAn/nodes/; python3 multiclient.py -i 0 -n '$NODES'"  
