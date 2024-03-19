mkdir -p ./log

while IFS= read -r line; do
  IPS+=($line)
done < $1

UIPS=($(echo "${IPS[@]}" | tr ' ' '\n' | sort -u | tr '\n' ' '))

echo ${IPS[*]}

echo ${UIPS[*]} > ./log/uip.txt

bash ./script/get_pvt_ip.sh $1 > ./log/pvt.txt

while IFS= read -r line; do
  PIPS+=($line)
done < ./log/pvt.txt

# Correct the config
cd ./script/config/
for d in *; do
  for c in $d/*; do
    sed -i 's/[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,3\}'/${PIPS[0]}/ $c 
  done
done

# Install the program
for ((i = 0; i <= $(expr ${#UIPS[@]} - 1); i++)); do
  # Upload new SSH config. Enable if needed.
  scp -i ~/organ.pem script/sshd_config ubuntu@${UIPS[$i]}:~/sshd_config 
done
