
for i in {1..50}
do 
    for n in 10 20 30 40 50 60 70 80 90 100
    do 
        python3 my_sol_frag.py -n $n -b 64  -f 171 
        python3 my_sol_frag.py -n $n -b 96  -f 74 
        python3 my_sol_frag.py -n $n -b 128 -f 47 
        python3 my_sol_frag.py -n $n -b 256 -f 19 
    done 
done 
