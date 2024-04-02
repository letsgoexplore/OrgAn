while IFS= read -r line; do
  IPS+=($line)
done < $1

cd ./script/config/
# CHANGE: You can modify your number here
for d in "768" ; do
  echo $d
  for c in "$d/rprf1024.json" "$d/rnoprf1024.json"; do
    echo "Running with config: $c"
    scp -i ~/organ.pem ubuntu@${IPS[0]}:./output.log ../../log/$c/relay.log &
    for ((i = 1; i <= $d; i++)); do
        scp -i ~/organ.pem ubuntu@${IPS[$i]}:./output_$(expr $i - 1).log ../../log/$c/client_$(expr $i - 1).log &
    done
    wait
  done
done
cd ../../

wait