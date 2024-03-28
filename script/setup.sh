mkdir -p ./log

while IFS= read -r line; do
  IPS+=($line)
done < $1

UIPS=($(echo "${IPS[@]}" | tr ' ' '\n' | awk '!seen[$0]++' | tr '\n' ' '))

# Upload the config
cd ./script/config/
for ((i = 0; i <= $(expr ${#UIPS[@]} - 1); i++)); do
    scp -r -i ~/organ.pem ../config ubuntu@${UIPS[$i]}:~/organ/script/ &
done
cd ../..

# Generate the shares
cd ./script/config/
for d in *; do
  mkdir -p ../../log/$d
  RUST_LOG=info ../../target/release/organ config ./$d/rprf1024.json ../../log/$d &
done
cd ../../

wait

cd ./script/config/
# Upload the shares
for ((i = 0; i <= $(expr ${#UIPS[@]} - 1); i++)); do
  for d in *; do
    ssh -t -i ~/organ.pem ubuntu@${UIPS[$i]} "mkdir -p ~/organ/log/$d" &
  done
done
cd ../../

wait

cd ./script/config/
for d in *; do
  scp -i ~/organ.pem ../../log/$d/bits_64_relay.txt ubuntu@${IPS[0]}:~/organ/log/$d/ &
  scp -i ~/organ.pem ../../log/$d/bits_226_relay.txt ubuntu@${IPS[0]}:~/organ/log/$d/ &
  for ((i = 1; i <= $d; i++))
  do
    scp -i ~/organ.pem ../../log/$d/bits_64_nid_$(expr $i - 1).txt ubuntu@${IPS[$i]}:~/organ/log/$d/ &
    scp -i ~/organ.pem ../../log/$d/bits_226_nid_$(expr $i - 1).txt ubuntu@${IPS[$i]}:~/organ/log/$d/ &
  done
done
cd ../../

wait

