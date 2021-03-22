from multiprocessing import Pool
import os, time, random

def println(name):
    print(f"inner name: inner-{name}")

def long_time_task(name):
    print(f"Run task {name} ({os.getpid()})")
    start = time.time()
    time.sleep(random.random() * 3)
    end = time.time()
    print(f"Task {name} runs {end - start} seconds.")
    print("inner start")
    p = Pool()
    for i in range(3):
        p.apply_async(println, args=(i,))
    p.close()
    p.join()
    print("inner end")

if __name__=='__main__':
    print(f"Parent process {os.getpid()}.")
    p = Pool()
    for i in range(5):
        p.apply_async(long_time_task, args=(i,))
    print("Waiting for all subprocesses done...")
    p.close()
    p.join()
    print('All subprocesses done.')