while IFS= read -r line; do
  IPS+=($line)
done < $1

bash ./script-ubuntu/run_server.sh ${IPS[0]} &
for ((i = 1; i <= $(expr ${#IPS[@]} - 1); i++))
do
    bash ./script-ubuntu/run_client.sh ${IPS[$i]} $(expr $i - 1) &
done

wait

for ip in "${IPS[@]}"
do
    ssh -i ~/organ.pem ubuntu@$ip "killall organ" &
done

wait