import multiprocessing as mp
import queue
import time


def handle_task(q1, q2):
    while True:
        try:
            task = q1.get_nowait()
        except queue.Empty:
            break
        
        print(f"Task no {task}")
        time.sleep(0.5)
        q2.put((task, mp.current_process().name))


if __name__ == "__main__":

    tasks_to_accomplish = mp.Queue()
    tasks_that_are_done = mp.Queue()
    processes = []

    for i in range(10):
        tasks_to_accomplish.put(i)
        
    for i in range(4):
        p = mp.Process(target=handle_task, args=(tasks_to_accomplish, tasks_that_are_done,))
        p.start()
        processes.append(p)
    
    for p in processes:
        p.join()

    while not tasks_that_are_done.empty():
        task, process = tasks_that_are_done.get()
        print(f"Task no {task} is done by {process}")