cd ./log/200
for d in o*.json; do 
  cd ../../
  echo $d
  # CHANGE: You can modify your number here
  for e in 50 100 150 200 300 500; do
    python3 ./script/extract.py ./log/$e/$d/client_0.log
  done
  cd ./log/200
  echo
done
for d in r*.json; do 
  cd ../../
  echo $d
  # CHANGE: You can modify your number here
  for e in 50 100 150 200 300 500; do
    python3 ./script/extract.py ./log/$e/$d/client_0.log
  done
  cd ./log/200
  echo
done
cd ../../
