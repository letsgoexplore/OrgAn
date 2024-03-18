
for i in {1..50}
do 
    for bits in 64 96 128 256 
    do 
        for n in 10 20 30 40 50 60 70 80 90 100
        do 
            python3 my_sol.py -n $n -b $bits 
        done 
    done 
done 
