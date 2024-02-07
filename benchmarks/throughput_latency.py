from __future__ import print_function
import sys
import pickle
from functools import wraps
from subprocess import Popen, PIPE
import os
import time
from statistics import mean
from collections import defaultdict

DEVNULL = open(os.devnull, 'wb')

START_PORT = 4321
MIN_RPS = 10
MAX_RPS = 40000

def memoize(fileName):
    def doMemoize(func):
        if os.path.exists(fileName):
            with open(fileName) as f:
                cache = pickle.load(f)
        else:
            cache = {}
        @wraps(func)
        def wrap(*args):
            if args not in cache:
                cache[args] = func(*args)
                with open(fileName, 'wb') as f:
                    pickle.dump(cache, f)
            return cache[args]
        return wrap
    return doMemoize

def calculate_throughput(successful_transactions, total_time_seconds):
    return successful_transactions / total_time_seconds

def calculate_latency(request_submission_time, response_received_time, network_threshold=1.0):
    confirmation_time = response_received_time - request_submission_time
    return confirmation_time * network_threshold

def run_benchmark(requests_per_second, request_size, num_nodes, num_nodes_readonly=0, delay=False):
    rps_per_node = requests_per_second / (num_nodes + num_nodes_readonly)
    cmd = [sys.executable, 'testobj_delay.py' if delay else 'testobj.py', str(rps_per_node), str(request_size)]
    processes = []
    all_addrs = []

    for i in range(num_nodes):
        all_addrs.append('localhost:%d' % (START_PORT + i))

    for i in range(num_nodes):
        addrs = list(all_addrs)
        self_addr = addrs.pop(i)
        p = Popen(cmd + [self_addr] + addrs, stdin=PIPE)
        processes.append(p)

    for i in range(num_nodes_readonly):
        p = Popen(cmd + ['readonly'] + all_addrs, stdin=PIPE)
        processes.append(p)

    err_rates = []
    successful_transactions = 0
    latencies = []

    for p in processes:
        p.communicate()
        err_rates.append(float(p.returncode) / 100.0)
        successful_transactions += _g_success
        latencies.extend(_g_delays)

    total_time_seconds = 25.0  # The total time of the benchmark (adjust as needed)

    throughput = calculate_throughput(successful_transactions, total_time_seconds)
    print('Throughput (requests per second):', throughput)

    latencies.sort()
    avg_latency = mean(latencies)
    min_latency = latencies[0]
    max_latency = latencies[-1]
    print('Average Latency (seconds):', avg_latency)
    print('Min Latency (seconds):', min_latency)
    print('Max Latency (seconds):', max_latency)

    avg_rate = sum(err_rates) / len(err_rates)
    print('Average Success Rate:', avg_rate)

    if delay:
        return avg_rate
    return avg_rate >= 0.9

def doDetectMaxRps(requestSize, numNodes):
    a = MIN_RPS
    b = MAX_RPS
    numIt = 0
    while b - a > MIN_RPS:
        c = a + (b - a) / 2
        res = singleBenchmark(c, requestSize, numNodes)
        if res:
            a = c
        else:
            b = c
        print('subiteration %d, current max %d' % (numIt, a))
        numIt += 1
    return a

@memoize('maxRpsCache.bin')
def detectMaxRps(requestSize, numNodes):
    results = []
    for i in range(0, 5):
        res = doDetectMaxRps(requestSize, numNodes)
        print('iteration %d, current max %d' % (i, res))
        results.append(res)
    return sorted(results)[len(results) / 2]

def printUsage():
    print('Usage: %s mode(delay/rps/custom)' % sys.argv[0])
    sys.exit(-1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        printUsage()

    mode = sys.argv[1]
    if mode == 'delay':
        print('Average delay:', run_benchmark(50, 10, 5, delay=True))
    elif mode == 'rps':
        for i in range(10, 2100, 500):
            res = detect_max_rps(i, 3)
            print('request size: %d, rps: %d' % (i, int(res)))
            run_benchmark(res, i, 3)  # Adjust parameters as needed

        for i in range(3, 8):
            res = detect_max_rps(200, i)
            print('nodes number: %d, rps: %d' % (i, int(res)))
            run_benchmark(res, 200, i)  # Adjust parameters as needed

    elif mode == 'custom':
        run_benchmark(25000, 10, 3)  # Adjust parameters as needed

    else:
        print_usage()
