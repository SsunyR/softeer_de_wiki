import multiprocessing as mp
import time
import random

def work_log(task):
    
    name, period = task

    print(f"Process {name} waiting {period} seconds")
    time.sleep(period)
    print(f"Process {name} Finished.")

if __name__ == '__main__':
    
    work = [('A', 5), ('B', 2), ('C', 1), ('D', 3)]
    
    with mp.Pool(processes=2) as pool:
        pool.map(work_log, work)

