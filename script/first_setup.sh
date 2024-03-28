mkdir -p ./log

while IFS= read -r line; do
  IPS+=($line)
done < $1

UIPS=($(echo "${IPS[@]}" | tr ' ' '\n' | awk '!seen[$0]++' | tr '\n' ' '))

echo ${IPS[*]}

> ./log/uip.txt
for ((i = 0; i <= $(expr ${#UIPS[@]} - 1); i++)); do
  echo ${UIPS[$i]} >> ./log/uip.txt
done

> ./log/pvt.txt
bash ./script/get_pvt_ip.sh ./log/uip.txt > ./log/pvt.txt

while IFS= read -r line; do
  PIPS+=($line)
done < ./log/pvt.txt

# Correct the config
cd ./script/config/
for d in *; do
  for c in $d/*; do
    jq --arg addr "${PIPS[0]}:8001" '.server_addr = $addr' "$c" > tmp.json && mv tmp.json "$c"
  done
done
cd ../..

# Install the program
script="sudo mv ~/sshd_config ../../etc/ssh/sshd_config; sudo systemctl restart ssh"
for ((i = 0; i <= $(expr ${#UIPS[@]} - 1); i++)); do
  # Upload new SSH config. Enable if needed.
  scp -i ~/organ.pem script/sshd_config ubuntu@${UIPS[$i]}:~/sshd_config
  ssh -i ~/organ.pem ubuntu@${UIPS[$i]} $script
  ssh -t -i ~/organ.pem ubuntu@${UIPS[$i]} 'bash -ls' < script/aws.sh &
done
