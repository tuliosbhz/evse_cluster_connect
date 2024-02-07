from __future__ import print_function
import sys
import pickle
from functools import wraps
from subprocess import Popen, PIPE
import os
import pandas as pd

DEVNULL = open(os.devnull, 'wb')

START_PORT = 4321
MIN_RPS = 10
MAX_RPS = 40000

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
def singleBenchmark(requestsPerSecond, requestSize, numNodes, numNodesReadonly=0, delay=False):
    # Pedidos por segundo por cada nó, valor útil para comparar com execução em um único nó
    rpsPerNode = requestsPerSecond / (numNodes + numNodesReadonly)
    cmd = [sys.executable, 'testobj_debito.py' if delay else 'testobj_debito.py', str(rpsPerNode), str(requestSize)]
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
"""
Obtem o valor do Máximo RPS testando diferentes valores de RPS
Os parametros de configuração da rede:
- Tamanho dos pedidos 
- Número de nós
"""
def doDetectMaxRps(requestSize, numNodes):
    a = MIN_RPS
    b = MAX_RPS
    numIt = 0
    while b - a > MIN_RPS: #Intervalo igual a MIN_RPS considera-se que encontrou o máxímo RPS
        #Centro do intervalo entre a e b
        c = a + (b - a) / 2
        res = singleBenchmark(c, requestSize, numNodes)
        if res:
            #Se recebeu algum retorno aumenta o mínimo antigo centro do intervalo (b-a)
            a = c
        else:
            #Se não recebeu retorno diminui máximo para o centro do intervalo (b-a)
            b = c
        numIt += 1
    return a

@memoize('maxRpsCache.bin')
def detectMaxRps(requestSize, numNodes):
    results = []
    for i in range(0, 5):
        res = doDetectMaxRps(requestSize, numNodes)
        results.append(res)
    return sorted(results)[len(results) // 2]

def init_results(filename):
    # If the file doesn't exist, create a new DataFrame and save it to the file
    data = [[0,0,0,0.0,0,0,0,""],]
    df = pd.DataFrame(data, columns=['Request Size', 'Num Nodes', 'RPS', "Success Rate", "Total Requests", "Total Time", "Network Threshold", "Node Adress"])
    df.to_csv(filename, index=False)
    print(f"New DataFrame saved to {filename}")

#Essa função não está atualizando
def update_csv_inplace(csv_path, num_nodes_filter, update_column, update_value):
    # Read CSV file into a DataFrame
    df = pd.read_csv(csv_path)

    # Filter rows based on 'Num Nodes' column
    filtered_rows = df[df['Num Nodes'] == num_nodes_filter]

    # Update the specified column in the filtered rows
    filtered_rows[update_column] = update_value

    # Update the original DataFrame with the changes
    df.update(filtered_rows)

    # Save the updated DataFrame to the same CSV file
    df.to_csv(csv_path, index=False)
    print(f"Updated DataFrame saved to {csv_path}")

def printUsage():
    print('Usage: %s mode(latencia/debito/custom)' % sys.argv[0])
    sys.exit(-1)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        printUsage()

    mode = sys.argv[1]
    results_data = []
    init_results("resultado_experimento.csv")
    #Teste de número de nós na rede de 2 até 659 que é o valor de carregadores existentes na cidade do porto
    if mode == 'debito':
        # TODO: realizar testes consistentes com número dinâmico de Pedidos por segundo, Tamanho dos pedidos e Número de nós
        # TODO: realizar testes consistentes com número dinâmico de Pedidos por segundo, Tamanho dos pedidos e Número de nós
        request_size = 10
        for num_nodes in range(2,11):
            print(f"NUM NODES: {num_nodes}")
            requests_per_second = num_nodes * 2
            res = singleBenchmark(requests_per_second, request_size, num_nodes, delay=True)
            # ['Request Size', 'Num Nodes', 'RPS', "Success Rate","Total Requests", "Total Time", "Limite Rede"]
            #update_csv_inplace('resultado_experimento.csv', num_nodes, "RPS", requests_per_second)
            # results_data.append([requests_per_second, request_size, num_nodes, requests_per_second,
            #                      res[0], res[1], res[2]],)
    elif mode == 'latencia':
        # Varia o valor do tamanho dos requests e recebe o máximo do pedidos por segundo possíveis
        for i in range(10, 2100, 500):
            res = detectMaxRps(i, 3)
            results_data.append([i, 3, int(res)])
        # Varia o número de nós e verifica
        for i in range(3, 8):
            res = detectMaxRps(200, i)
            results_data.append([200, i, int(res)])
    elif mode == 'custom':
        results_data.append([25000, 10, 3, singleBenchmark(25000, 10, 3)])
    else:
        printUsage()

    
