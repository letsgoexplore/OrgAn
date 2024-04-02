mkdir -p ./log

while IFS= read -r line; do
  IPS+=($line)
done < $1

for ((i = 0; i <= $(expr ${#IPS[@]} - 1); i++)); do
  echo "$i:${IPS[i]}"
done

UIPS=($(echo "${IPS[@]}" | tr ' ' '\n' | awk '!seen[$0]++' | tr '\n' ' '))
sleep 3

MAX_RETRIES=3
scp_with_retry() {
  local retries=0
  local src_file=$1
  local dest=$2
  local src_size=$(stat -c %s "$src_file")
  local dest_size

  while [[ $retries -lt $MAX_RETRIES ]]; do
    if scp -i ~/organ.pem "$src_file" "$dest"; then
      # Check the size of the destination file
      dest_size=$(ssh -i ~/organ.pem "${dest%%:*}" "stat -c %s ${dest##*:}"/$(basename "$src_file"))
      if [[ "$src_size" -eq "$dest_size" ]]; then
        echo "File $src_file transferred successfully."
        break
      else
        echo "File size mismatch for $src_file. Retrying..."
      fi
    else
      echo "SCP failed for $src_file. Retrying..."
    fi
    ((retries++))
    echo "Retry $retries of $MAX_RETRIES..."
    sleep 1
  done

  if [[ $retries -eq $MAX_RETRIES ]]; then
    echo "Failed to scp $src_file after $MAX_RETRIES attempts."
  fi
}
sleep 3

cd ./script/config/
for ((i = 0; i <= $(expr ${#UIPS[@]} - 1); i++)); do
    scp -r -i ~/organ.pem ../config ubuntu@${UIPS[$i]}:~/organ/script/ &
done
cd ../..
wait
sleep 3

script="mkdir ./organ/log/300; mkdir ./organ/log/500"
for ((i = 0; i <= $(expr ${#UIPS[@]} - 1); i++)); do
  ssh -i ~/organ.pem ubuntu@${UIPS[$i]} $script
done

sleep 10
cd ./script/config/
# CHANGE: You can modify your number here
for d in "300" "500"; do
  scp_with_retry ../../log/$d/bits_64_relay.txt ubuntu@${IPS[0]}:~/organ/log/$d/ &
  scp_with_retry ../../log/$d/bits_226_relay.txt ubuntu@${IPS[0]}:~/organ/log/$d/ &
  for ((i = 1; i <= $d; i++)); do
    scp_with_retry ../../log/$d/bits_64_nid_$(expr $i - 1).txt ubuntu@${IPS[$i]}:~/organ/log/$d/ &
    scp_with_retry ../../log/$d/bits_226_nid_$(expr $i - 1).txt ubuntu@${IPS[$i]}:~/organ/log/$d/ &
  done
done
cd ../../

wait