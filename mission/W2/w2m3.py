import multiprocessing as mp

def push(color, q):
    q.put(color)

if __name__ == "__main__":
    colors = ['red', 'green', 'blue', 'black']
    q = mp.Queue()
    processes = []

    print("pushing items to queue:")
    for i, color in enumerate(colors):
        print(f"item no: {i+1} {color}")
        p = mp.Process(target=push, args=(color, q,))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

    print("popping items from queue:")
    num = 0
    while not q.empty():
        color = q.get()
        print(f"item no: {num} {color}")
        num += 1