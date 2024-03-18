#!/bin/bash

NODES=$1

echo Total Nodes:$NODES

for i in `seq 1 $NODES`;
do
    j=$(($i-1))
        osascript -e 'tell app "Terminal" 
            do script "cd ~/OrgAn/nodes/; python3 node.py  -i '$j' -n '$NODES'"  
        end tell'
done 
    
