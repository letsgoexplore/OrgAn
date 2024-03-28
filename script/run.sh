while IFS= read -r line; do
  IPS+=($line)
done < $1

UIPS=($(echo "${IPS[@]}" | tr ' ' '\n' | awk '!seen[$0]++' | tr '\n' ' '))

for ip in "${UIPS[@]}"
do
    ssh -i ~/organ.pem ubuntu@$ip "killall organ" &
done

wait

cd ./script/config/
for d in "300" "500" ; do
  echo $d
  for c in "$d/rprf1024.json" "$d/rnoprf1024.json" "$d/onoprf1024.json"; do
    echo "Running with config: $c"
    bash ../run_server.sh ${IPS[0]} $d $c &
    for ((i = 1; i <= $d; i++)); do
      bash ../run_client.sh ${IPS[$i]} $d $c $(expr $i - 1) &
    done
    wait
  done
done
cd ../../

wait