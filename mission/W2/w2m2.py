import multiprocessing as mp

def continent_name(name='Asia'):
    print(f"The name of continent is : {name}")


if __name__ == "__main__":
    continents = ['America', 'Europe', 'Africa']

    processes = []
    p = mp.Process(target=continent_name)
    processes.append(p)
    p.start()
    for continent in continents:
        p = mp.Process(target=continent_name, args=(continent,))
        processes.append(p)
        p.start()

    for p in processes:
        p.join()
