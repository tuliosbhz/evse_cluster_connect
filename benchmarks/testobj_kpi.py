from __future__ import print_function
import sys
import time
import random
from collections import defaultdict
sys.path.append("../")
from pysyncobj import SyncObj, replicated, SyncObjConf, FAIL_REASON
import json
from psutil import cpu_percent, virtual_memory
import os

class TestObj(SyncObj):
    def __init__(self, selfNodeAddr, otherNodeAddrs):        
        cfg = SyncObjConf(
            appendEntriesUseBatch=False,
        )
        super(TestObj, self).__init__(selfNodeAddr, otherNodeAddrs, cfg)
        self.__appliedCommands = 0
        self.__mensagem = ""
        self.__results = {}

    @replicated
    def testMethod(self, val, callTime):
        self.__mensagem = val
        self.__appliedCommands += 1
        return (callTime, time.time())

    def getNumCommandsApplied(self):
        return self.__appliedCommands
    
    def getMensagem(self):
        return self.__mensagem
    
    def set_results(self, results):
        self.__results = results

_g_sent = 0
_g_success = 0
_g_error = 0
_g_errors = defaultdict(int)
_g_delays = []
_results = {}
_tot_time = 0 #Accumulated delay of successful calls
_cpu_usage = []
_mem_usage = []
_terms = []
_up_times = []
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
    tot_time_experiment = 50.0
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

        #Raft parameters
        raft_status = obj.getStatus()
        _terms.append(raft_status["raft_term"])
        _up_times.append(raft_status["uptime"])
        #Calcula tempo de transação
        delta = time.time() - st
        #Verifica que transação durou menos de 1 segundo
        assert delta <= 1.0
        #Sempre espera 1 segundo, pois considera o atraso de retorno da transação
        time.sleep(1.0 - delta)
    #Tempo para esperar a propagação de comandos enviados na rede de consenso
    #Se tiver 10 nós na rede aguarda 10 segundos para se obter as respostas
    time.sleep(float(num_nodes))
    
    num_trans_rede = obj.getNumCommandsApplied()
    successRate = float(_g_success) / float(_g_sent)
    #print(f"G_SENT: {_g_sent} vs GET_NUM_COMMANDS_APPLIED {obj.getNumCommandsApplied()} ")
    #print('SUCCESS RATE:', successRate)
    if _g_delays:
        #_g_delays_sort = sorted(_g_delays)
        #delays = np.array(_g_delays_sort)
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
                "Total Requests in glob": _g_sent,
                "Total Requests in obj": num_trans_rede,
                "Total Time": _tot_time,
                "Throughput": _g_success / _tot_time,
                "Time of experiment": tot_time_experiment,
                "Average Delay": avgDelay,
                "Num Commands Errors": _g_error,
                "CPU usage": round(sum(_cpu_usage) / len(_cpu_usage),2),
                "Mem usage": round(sum(_mem_usage) / len(_mem_usage),2),
                "Raft up time": round(sum(_up_times) / len(_up_times),2),
                "Raft terms": _terms[-1] - _terms[0], #Count of total terms
                "Node Address": str(obj.selfNode.address),
                "ERROR_CNT_QUEUE_FULL    ": _g_errors[FAIL_REASON.QUEUE_FULL],     #: Commands queue full
                "ERROR_CNT_MISSING_LEADER": _g_errors[FAIL_REASON.MISSING_LEADER],      #: Leader is currently missing (leader election in progress, or no connection)
                "ERROR_CNT_DISCARDED     ": _g_errors[FAIL_REASON.DISCARDED],      #: Command discarded (cause of new leader elected and another command was applied instead)
                "ERROR_CNT_NOT_LEADER    ": _g_errors[FAIL_REASON.NOT_LEADER],       #: Leader has changed, old leader did not have time to commit command.
                "ERROR_CNT_LEADER_CHANGED": _g_errors[FAIL_REASON.LEADER_CHANGED],      #: Simmilar to NOT_LEADER - leader has changed without command commit.
                "ERROR_CNT_REQUEST_DENIED": _g_errors[FAIL_REASON.REQUEST_DENIED]       #: Command denied}
                }
    filename = "results/" + str(obj.selfNode.ip) + "_" + str(obj.selfNode.port) + ".txt"

    # Check if the file already exists
    if os.path.exists(filename):
        mode = "a"  # If the file exists, open it in append mode
    else:
        mode = "w"  # If the file doesn't exist, open it in write mode

    with open(filename, mode) as convert_file:
        # If the file already exists and is being opened in append mode,
        # add a newline character before appending the new data
        if mode == "a":
            convert_file.write("\n")
        convert_file.write(json.dumps(_results))

    sys.exit(round(avgDelay * 100))
