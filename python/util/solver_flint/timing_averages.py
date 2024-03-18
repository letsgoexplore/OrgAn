import sys, csv 
def get_averages(csv):
    column_sums = None
    with open(csv) as file:
        lines = file.readlines()
        rows_of_numbers = [map(float, line.split(',')) for line in lines]
        sums = map(sum, zip(*rows_of_numbers))
        averages = [sum_item / len(lines) for sum_item in sums]
        print("averages:", averages)
        return averages


if __name__=="__main__":
    
    for bits in [64]:
        for n in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:

            filename = "./tmp/"+str(bits)+"equ_solve_timing_n_"+str(n)+".csv"
            #filename = "./tmp/"+ str(bits)+ "threads_per_sec"+str(n)+".csv"
            averages = get_averages(filename)
            output_filename = "./timings/"+str(bits)+"timing_averages.csv"
            with open(output_filename, "a") as f:
                string_to_write = "(" + str(n) + "," + str(averages[0]) + ")"
                f.write(string_to_write)
