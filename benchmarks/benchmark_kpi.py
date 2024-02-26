from __future__ import print_function
import sys
import pickle
from functools import wraps
from subprocess import Popen, PIPE
import os
import json
from find_my_addr import ip_address_assign, read_ip_port_file, separate_ip_port
import time
DEVNULL = open(os.devnull, 'wb')

START_PORT = 4321
MIN_RPS = 10
MAX_RPS = 10000

"""
Ensaio de desempenho do algoritmo de consenso utilizando uma rede local
"""
def localBenchmark(requestsPerSecond, requestSize, numNodes, numNodesReadonly=0, delay=False):
    # Pedidos por segundo por cada nó, valor útil para comparar com execução em um único nó
    cmd = [sys.executable, 'testobj_kpi.py' if delay else 'testobj.py', str(requestsPerSecond), str(requestSize)]
    processes = []
    allAddrs = []

    # Cria endereços para nós na quantidade contida em numNodes
    for i in range(numNodes):
        allAddrs.append('localhost:%d' % (START_PORT + i))

    # Corre cada nó (servidor RAFT) individualmente em um processo diferente internamente
    for i in range(numNodes):
        addrs = list(allAddrs)
        selfAddr = addrs.pop(i)
        p = Popen(cmd + [selfAddr] + addrs, stdin=PIPE)
        processes.append(p)

    # Cria os nós que são readonly
    for i in range(numNodesReadonly):
        p = Popen(cmd + ['readonly'] + allAddrs, stdin=PIPE)
        processes.append(p)

    errRates = []

    for p in processes:
        p.communicate()
        errRates.append(float(p.returncode) / 100.0)
    #Media de delay entre nós da rede, média de toda a rede
    avgRate = sum(errRates) / len(errRates)
    if delay:
        return avgRate
    #Somente retorna os casos com sucesso acima de 90%
    return avgRate >= 0.9
    
def configure_addrs_from_file(addrs_filename:str):
    #Lê-se endereços do ficheiro local
    if addrs_filename:
        allAddrs = read_ip_port_file(addrs_filename)
    else:
        allAddrs = read_ip_port_file("nodes_addrs.txt")
    return allAddrs

def perNodeBenchmark(requestsPerSecond, requestSize, allAddrs, numNodes, numNodesReadonly=0, delay=False):
    cmd = [sys.executable, 'testobj_kpi.py' if delay else 'testobj.py', str(requestsPerSecond), str(requestSize), str(numNodes)]
    errRates = []
    #if selfAddr in allAddrs:
    p = Popen(cmd + allAddrs, stdin=PIPE)
    p.communicate()
    errRates.append(float(p.returncode) / 100.0)
    avgRate = sum(errRates) / len(errRates)
    if delay:
        return avgRate
    #Somente retorna os casos com sucesso acima de 90%
    return avgRate >= 0.9
    #else:
    #    return -1

def printUsage():
    print('Usage: %s mode(local/rps/custom)' % sys.argv[0])
    sys.exit(-1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        printUsage()

    mode = sys.argv[1]
    addrs_filename = sys.argv[2]
    results_data = []
    if mode == 'local':
        for num_nodes in range(2,7):
            print(f"NUM NODES: {num_nodes} \n\n")
            for i in range(2110,9,-200):
                for j in range(1,310,50):
                    print(f"Experimento: {addrs_filename} | Req Size: {i} | RPS: {j}\n")
                    res = localBenchmark(j, i, num_nodes, delay=True)
    elif mode == "single_node_exp":
        allAddrs = configure_addrs_from_file("nds_addr_local.txt")
        print(perNodeBenchmark(100,2100,allAddrs, 3, delay=True))
    elif mode == "all_nodes_exp":
        allAddrs = configure_addrs_from_file("nds_addr_exp_six_nodes.txt")
        for num_nodes in range(2,7):
            for i in range(2110,9,-200):
                for j in range(1,310,50):
                    print(f"Experimento: {num_nodes} nós | Req Size: {i} | RPS: {j} \n")
                    result = perNodeBenchmark(j,i, allAddrs, num_nodes, delay=True)
                    if result >= 0:
                        results_data.append([i, j, result])
                        print(results_data)
                    
        filename = "results/" + "node_exp_full"+".txt"
        with open(filename,"w") as convert_file:
            convert_file.write(json.dumps(results_data))
    elif mode == 'custom':
        results_data.append([25000, 10, 3, localBenchmark(25000, 10, 3)])
    else:
        printUsage()

    
