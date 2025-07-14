import multiprocessing as mp
import time
import random

def work_log(task):
    
    name, period = task

    print(f"Process {name} waiting {period} seconds")
    time.sleep(period)
    print(f"Process {name} Finished.")

if __name__ == '__main__':
    
    work = []
    task = ['A', 'B', 'C', 'D']
    for i in range(4):
        period = random.randint(1, 5)

        work.append((task[i], period))

    with mp.Pool(processes=2) as pool:
        pool.map(work_log, work)

