mkdir -p ./log

while IFS= read -r line; do
  IPS+=($line)
done < $1

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
