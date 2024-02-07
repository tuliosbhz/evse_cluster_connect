from __future__ import print_function
import sys
import time
import random
from collections import defaultdict
sys.path.append("../")
from pysyncobj import SyncObj, replicated, SyncObjConf, FAIL_REASON
import numpy as np
import pandas as pd
import os

class TestObj(SyncObj):

    def __init__(self, selfNodeAddr, otherNodeAddrs):
        cfg = SyncObjConf(
            appendEntriesUseBatch=False,
        )
        super(TestObj, self).__init__(selfNodeAddr, otherNodeAddrs, cfg)
        self.__appliedCommands = 0
        self.__results = {}

    @replicated
    def testMethod(self, val, callTime):
        self.__appliedCommands += 1
        return (callTime, time.time())

    def getNumCommandsApplied(self):
        return self.__appliedCommands
    
    def set_results(self, results):
        self.__results = results

_g_sent = 0
_g_success = 0
_g_error = 0
_g_errors = defaultdict(int)
_g_delays = []
_results = {}
#Função de callback que cria uma lista com os valores dos delays em cada transação
"""
Considera no caso de sucesso (FAIL_REASON.SUCCESS) 
"""
def clbck(res, err):
    global _g_error, _g_success, _g_delays
    if err == FAIL_REASON.SUCCESS:
        _g_success += 1
        callTime, recvTime = res
        #Porque não utiliza recvTime: Verificar diferença
        delay = time.time() - callTime
        _g_delays.append(delay)
    else:
        _g_error += 1
        _g_errors[err] += 1

def getRandStr(l):
    f = '%0' + str(l) + 'x'
    return f % random.randrange(16 ** l)

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

def create_and_save_dataframe(data, filename):
    try:
        # Check if the file is empty
        is_empty = os.stat(filename).st_size == 0

        # Try to read the existing CSV file
        if not is_empty:
            df = pd.read_csv(filename)

            # Check if the columns match
            if set(df.columns) != set(['Request Size', 'Num Nodes', 'RPS', "Success Rate", "Total Requests", "Total Time", "Network Threshold", "Node Adress"]):
                raise ValueError("Columns in existing file do not match expected columns.")
            
            # Append new data to the existing DataFrame
            df = pd.concat([df, pd.DataFrame(data, columns=df.columns)], ignore_index=True)

        else:
            # If the file is empty, create a new DataFrame
            df = pd.DataFrame(data, columns=['Request Size', 'Num Nodes', 'RPS', "Success Rate", "Total Requests", "Total Time", "Network Threshold", "Node Adress"])

        # Save the updated DataFrame to the same CSV file
        df.to_csv(filename, index=False)
        print(f"Updated DataFrame saved to {filename}")

    except FileNotFoundError:
        # If the file doesn't exist, create a new DataFrame and save it to the file
        df = pd.DataFrame(data, columns=['Request Size', 'Num Nodes', 'RPS', "Success Rate", "Total Requests", "Total Time", "Network Threshold", "Node Adress"])
        df.to_csv(filename, index=False)
        print(f"New DataFrame saved to {filename}")


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('Usage: %s RPS requestSize selfHost:port partner1Host:port partner2Host:port ...' % sys.argv[0])
        sys.exit(-1)

    numCommands = round(float(sys.argv[1]))
    cmdSize = int(sys.argv[2])

    selfAddr = sys.argv[3]
    if selfAddr == 'readonly':
        selfAddr = None
    partners = sys.argv[4:]

    maxCommandsQueueSize = int(0.9 * SyncObjConf().commandsQueueSize / len(partners))
    #Instancia objeto de teste
    obj = TestObj(selfAddr, partners)

    while obj._getLeader() is None:
        time.sleep(0.5)

    time.sleep(4.0)

    startTime = time.time()
    accTime = 0
    #Compara tempo atual com tempo de inicio do teste (Somente faz o teste por 25 segundos)
    while time.time() - startTime < 25.0:
        #Regista tempo antes de iniciar uma transação
        st = time.time()
        #Executa uma serie de comandos o mais rápido possível e depois espera 1 segundo para executar Requets per second
        for i in range(0, numCommands):
            #Envia uma transação nova
            obj.testMethod(getRandStr(cmdSize), time.time(), callback=clbck)
            _g_sent += 1
        #Calcula tempo de transação
        delta = time.time() - st
        #Tempo de cada transação acumulado
        accTime += delta
        #Verifica que transação durou menos de 1 segundo
        assert delta <= 1.0
        #Sempre espera 1 segundo, pois considera o atraso de retorno da transação
        time.sleep(1.0 - delta)
    #Tempo para estabilizar a rede de consenso
    time.sleep(4.0)
    #Results 
    num_nodes = len(partners) + 1
    num_trans_rede = obj.getNumCommandsApplied()
    total_time_seconds = accTime
    successRate = float(_g_success) / float(_g_sent)
    #print(f"G_SENT: {_g_sent} vs GET_NUM_COMMANDS_APPLIED {obj.getNumCommandsApplied()} ")
    #print('SUCCESS RATE:', successRate)
    if _g_delays:
        _g_delays_sort = sorted(_g_delays)
        delays = np.array(_g_delays_sort)
        #avgDelay = float(delays.mean())
        #Problema quando não 
        avgDelay = _g_delays[round(len(_g_delays) / 2)-1]
    else:
        avgDelay=0
    #print('AVG DELAY:', avgDelay)

    if successRate < 0.9:
        print('LOST RATE:', 1.0 - float(_g_success + _g_error) / float(_g_sent))
        print('ERRORS STATS: %d' % len(_g_errors))
        for err in _g_errors:
            print(err, float(_g_errors[err]) / float(_g_error))

    _results = {"Request Size": cmdSize,
                "Num Nodes": num_nodes,
                "RPS": numCommands,
                "Success Rate": successRate,
                "Total Requests": num_trans_rede,
                "Total Time": total_time_seconds,
                "Network Threshold": 0,
                "Node Address": str(obj.selfNode.address)}
    print(_results)
    time.sleep(random.randint(1,5))
    #['Request Size', 'Num Nodes', 'RPS', "Success Rate", "Total Requests", "Total Time", "Network Threshold", "Node Adress"]
    #benchmark_results = [cmdSize, num_nodes, numCommands, successRate, num_trans_rede, total_time_seconds, 0, str(obj.selfNode.address)]
    create_and_save_dataframe(data=[list(_results.values),], filename="resultado_experimento.csv")

    sys.exit(round(avgDelay * 100))
