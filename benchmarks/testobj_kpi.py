from __future__ import print_function
import sys
import time
import random
from collections import defaultdict
sys.path.append("../")
from pysyncobj import SyncObj, replicated, SyncObjConf, FAIL_REASON
import numpy as np
import json
from psutil import cpu_percent, virtual_memory


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
_tot_time = 0
_cpu_usage = []
_mem_usage = []
#Função de callback que cria uma lista com os valores dos delays em cada transação
"""
Considera no caso de sucesso (FAIL_REASON.SUCCESS) 
"""
def clbck(res, err):
    global _g_error, _g_success, _g_delays, _tot_time
    if err == FAIL_REASON.SUCCESS:
        _g_success += 1
        callTime, recvTime = res
        #Porque não utiliza recvTime: Verificar diferença
        delay = time.time() - callTime
        _g_delays.append(delay)
        _tot_time += delay
    else:
        _g_error += 1
        _g_errors[err] += 1

def getRandStr(l):
    f = '%0' + str(l) + 'x'
    return f % random.randrange(16 ** l)


if __name__ == '__main__':
    if len(sys.argv) < 5:
        print('Usage: %s RPS requestSize selfHost:port partner1Host:port partner2Host:port ...' % sys.argv[0])
        sys.exit(-1)
    ############### Input of parameters ######################
    numCommands = round(float(sys.argv[1]))
    cmdSize = int(sys.argv[2])
    selfAddr = sys.argv[3]
    if selfAddr == 'readonly':
        selfAddr = None
    partners = sys.argv[4:]
    num_nodes = len(partners) + 1
    ############### Configuration #############################
    maxCommandsQueueSize = int(0.9 * SyncObjConf().commandsQueueSize / len(partners))
    #Instancia objeto de teste
    obj = TestObj(selfAddr, partners)
    ############## Wait for leader ###########################
    while obj._getLeader() is None:
        time.sleep(0.5)

    time.sleep(4.0)

    startTime = time.time()
    #Compara tempo atual com tempo de inicio do teste (Somente faz o teste por 25 segundos)
    #Como os comandos são realizados de forma periódica no intervalo de 1 segundo 
    tot_time_experiment = 5.0
    while time.time() - startTime < tot_time_experiment:
        #Regista tempo antes de iniciar uma transação
        st = time.time()
        #Executa uma serie de comandos o mais rápido possível e depois espera 1 segundo para executar Requets per second
        for i in range(0, numCommands):
            #Envia uma transação nova
            obj.testMethod(getRandStr(cmdSize), time.time(), callback=clbck)
            _g_sent += 1
        #Tempo de cada transação acumulado
        _cpu_usage.append(cpu_percent())
        _mem_usage.append(virtual_memory().percent)
        #Calcula tempo de transação
        delta = time.time() - st
        #Verifica que transação durou menos de 1 segundo
        assert delta <= 1.0
        #Sempre espera 1 segundo, pois considera o atraso de retorno da transação
        time.sleep(1.0 - delta)
    #Tempo para esperar a propagação de comandos enviados na rede de consenso
    #Se tiver 10 nós na rede aguarda 10 segundos para se obter as respostas
    time.sleep(float(num_nodes))
    #Results 
    
    num_trans_rede = obj.getNumCommandsApplied()
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

    #['Request Size', 'Num Nodes', 'RPS', "Success Rate", "Total Requests", "Total Time", "Network Threshold", "Node Adress"]
    _results = {"Request Size": cmdSize,
                "Num Nodes": num_nodes,
                "RPS": numCommands,
                "Success Rate": successRate,
                "Total Requests": num_trans_rede,
                "Total Time": _tot_time,
                "Throughput": _tot_time / num_trans_rede,
                "Time of experiment": tot_time_experiment,
                "Average Delay": avgDelay,
                "Num Commands Errors": _g_error,
                "CPU usage": sum(_cpu_usage) / len(_cpu_usage),
                "Mem usage": sum(_mem_usage) / len(_mem_usage),
                "Node Address": str(obj.selfNode.address)}
    filename = "results/"+str(obj.selfNode.ip) + "_" + str(obj.selfNode.port) + "_nodes_" + str(num_nodes) +".txt"
    with open(filename,"w") as convert_file:
        convert_file.write(json.dumps(_results))
    

    sys.exit(round(avgDelay * 100))