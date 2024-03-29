from __future__ import print_function
import sys
import pickle
from functools import wraps
from subprocess import Popen, PIPE
import os
import json
from find_my_addr import ip_address_assign
DEVNULL = open(os.devnull, 'wb')

START_PORT = 4321
MIN_RPS = 10
#MAX_RPS = 40000
MAX_RPS = 10000

def memoize(fileName):
    def doMemoize(func):
        if os.path.exists(fileName):
            with open(fileName, 'rb') as f:
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

# Calcula a taxa de sucesso para diferentes valores de débito (pedidos por segundo)
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

def read_ip_port_file(file_path):
    ip_port_list = []
    with open(file_path, 'r') as file:
        for line in file:
            ip_port = line.strip()  # Remove leading/trailing whitespace and newline characters
            ip_port_list.append(str(ip_port))
    return ip_port_list

def separate_ip_port(ip_port_str):
    # Split the string by ':'
    parts = ip_port_str.split(':')
    
    # Check if there are exactly two parts (IP and Port)
    if len(parts) == 2:
        ip = parts[0]
        port = parts[1]
        return ip, port
    else:
        # If the format is incorrect, return None for both IP and Port
        return None, None

def perNodeBenchmark(requestsPerSecond, requestSize, addrs_filename:str=None, numNodesReadonly=0, delay=False):
    cmd = [sys.executable, 'testobj_kpi.py' if delay else 'testobj.py', str(requestsPerSecond), str(requestSize)]
    allAddrs = []
    errRates = []
    #Lê-se endereços do ficheiro local
    if addrs_filename:
        allAddrs = read_ip_port_file(addrs_filename)
    else:
        allAddrs = read_ip_port_file("nodes_addrs.txt")
    #print(f"All addresses: {allAddrs}")
    selfAddr = ip_address_assign()
    for addr in allAddrs:
        ip,port = separate_ip_port(addr)
        if selfAddr == ip:
            selfAddr = f"{selfAddr}:{port}"
    #print(f"Self Address: {selfAddr}")
    if selfAddr:
        allAddrs.remove(selfAddr)
        addrs = allAddrs
    p = Popen(cmd + [selfAddr] + addrs, stdin=PIPE)
    p.communicate()
    errRates.append(float(p.returncode) / 100.0)
    print(errRates)
    avgRate = errRates[-1]
    if delay:
        return avgRate
    #Somente retorna os casos com sucesso acima de 90%
    return avgRate >= 0.9

def printUsage():
    print('Usage: %s mode(local/rps/custom)' % sys.argv[0])
    sys.exit(-1)

if __name__ == '__main__':
    if len(sys.argv) != 3:
        printUsage()

    mode = sys.argv[1]
    addrs_filename = sys.argv[2]
    results_data = []
    #Teste de número de nós na rede de 2 até 659 que é o valor de carregadores existentes na cidade do porto
    if mode == 'local':
        # TODO: realizar testes consistentes com número dinâmico de Pedidos por segundo, Tamanho dos pedidos e Número de nós
        #for num_nodes in range(2,7):
            num_nodes = 3
            print(f"NUM NODES: {num_nodes} \n\n")
            for i in range(2110,9,-200):
                for j in range(1,310,50):
                    print(f"Experimento: {addrs_filename} | Req Size: {i} | RPS: {j}\n")
                    res = localBenchmark(j, i, num_nodes, delay=True)
    elif mode == "node_exp":
        print(perNodeBenchmark(100,2100))
    elif mode == "node_exp_full":
        for i in range(2110,9,-200):
            for j in range(1,310,50):
                print(f"Experimento: {addrs_filename} | Req Size: {i} | RPS: {j}")
                results_data.append([i, j, perNodeBenchmark(j,i, addrs_filename=addrs_filename, delay=True)])
                print(results_data)
        filename = "results/" + "node_exp_full"+".txt"
        with open(filename,"w") as convert_file:
            convert_file.write(json.dumps(results_data))
    elif mode == 'custom':
        results_data.append([25000, 10, 3, localBenchmark(25000, 10, 3)])
    else:
        printUsage()

    
