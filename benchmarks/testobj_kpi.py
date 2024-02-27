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

def find_upper_power_of_two(n):
    power_of_two = 1
    while power_of_two < n:
        power_of_two *= 2
    return power_of_two
""" 
    self.raftMinTimeout = kwargs.get('raftMinTimeout', 0.4)

    #: Same as raftMinTimeout
    self.raftMaxTimeout = kwargs.get('raftMaxTimeout', 1.4)

    #: Interval of sending append_entries (ping) command.
    #: Should be less than raftMinTimeout.
    self.appendEntriesPeriod = kwargs.get('appendEntriesPeriod', 0.1)

    #: When no data received for connectionTimeout - connection considered dead.
    #: Should be more than raftMaxTimeout.
    self.connectionTimeout = kwargs.get('connectionTimeout', 3.5)

    #: Interval between connection attempts.
    #: Will try to connect to offline nodes each connectionRetryTime.
    self.connectionRetryTime = kwargs.get('connectionRetryTime', 5.0)

    #: When leader has no response from the majority of the cluster
    #: for leaderFallbackTimeout - it will fallback to follower state.
    #: Should be more than appendEntriesPeriod.
    self.leaderFallbackTimeout = kwargs.get('leaderFallbackTimeout', 30.0)
"""
class TestObj(SyncObj):
    def __init__(self, selfNodeAddr, otherNodeAddrs, tcpBufferSize, dumpFile):
        """
        param "commandsWaitLeader" pode ser retirado e depois inserido para assim determinar os parametros quando espera o sistema sincronizar e quando não)
        """  
        ############### Calculate the optimal TCP buffer size for sockets transactions ##################
        cfg = SyncObjConf(
            appendEntriesUseBatch=False,
            commandsWaitLeader=True, #Commands will be queued to be futher processed by the leader
            dynamicMembershipChange=False, #To allow changes on the nodes,
            raftMinTimeout=0.4,
            raftMaxTimeout=1,
            appendEntriesPeriod=0.01, #Permite que 1000 AppendTries sejam realizados por segundo
            connectionTimeout=3.5,
            connectionRetryTime=5.0,
            leaderFallbackTimeout=30.0,
            sendBufferSize= tcpBufferSize,
            recvBufferSize= tcpBufferSize,
            fullDumpFile=dumpFile
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

#Função de callback que cria uma lista com os valores dos delays em cada transação
"""
Considera no caso de sucesso (FAIL_REASON.SUCCESS) 
"""
def clbck(res, err):
    global _g_error, _g_success, _g_delays, _tot_time, _cpu_usage, _mem_usage
    #Tempo de cada transação acumulado
    _cpu_usage.append(cpu_percent())
    _mem_usage.append(virtual_memory().percent)
    if err == FAIL_REASON.SUCCESS:
        _g_success += 1
        callTime, recvTime = res
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
    #Compara tempo atual com tempo de inicio do teste (Somente faz o teste por 50 segundos)
    tot_time_experiment = 50.0
    opt_tcp_buffer_size = find_upper_power_of_two(numCommands * cmdSize)
    #Instancia objeto de teste
    obj = TestObj(selfAddr, partners, opt_tcp_buffer_size,"experiment.txt")
    ############## Wait for leader ###########################
    startTimeInitialization = time.time()

    while obj._getLeader() is None:
        print("Waiting for leader to start experiment \n")
        time.sleep(0.5)

    time.sleep(4.0)
    initializationDelay = startTimeInitialization - time.time()
    startTime = time.time()
    while time.time() - startTime < tot_time_experiment:
        #Regista tempo antes de iniciar uma transação
        st = time.time()
        #Executa uma serie de comandos o mais rápido possível e depois espera 1 segundo para executar Requets per second
        for i in range(0, numCommands):
            #Envia uma transação nova
            obj.testMethod(getRandStr(cmdSize), time.time(), callback=clbck)
            _g_sent += 1
        #Calcula tempo de transação
        delta = time.time() - st
        #Verifica que transação durou menos de 1 segundo
        assert delta <= 1.0
        #Sempre espera 1 segundo, pois considera o atraso de retorno da transação
        time.sleep(1.0 - delta)
    #Tempo para esperar a propagação de comandos enviados na rede de consenso
    #Se tiver 10 nós na rede aguarda 10 segundos para se obter as respostas
    wait_estabilize_network_time = num_nodes*10
    time.sleep(float(wait_estabilize_network_time))

    #Raft parameters - Final values
    raft_status = obj.getStatus()
    num_trans_rede = obj.getNumCommandsApplied()
    successRate = float(_g_success) / float(_g_sent)
    if _g_delays:
        avgDelay = _g_delays[round(len(_g_delays) / 2)-1]
    else:
        avgDelay=0

    if successRate < 0.9:
        print('LOST RATE:', 1.0 - float(_g_success + _g_error) / float(_g_sent))
        print('ERRORS STATS: %d' % len(_g_errors))
        for err in _g_errors:
            print(err, float(_g_errors[err]) / float(_g_error))

    #['Request Size', 'Num Nodes', 'RPS', "Success Rate", "Total Requests", "Total Time", "Network Threshold", "Node Adress"]
    _results = {"Request Size": cmdSize,
                "RPS": numCommands,
                "Num Nodes": num_nodes,
                "Total Time": _tot_time,
                "Throughput": _g_success / _tot_time,
                "Average Succ Delay": avgDelay,
                "Success Rate": successRate,
                "CPU usage": round(sum(_cpu_usage) / len(_cpu_usage),2),
                "Mem usage": round(sum(_mem_usage) / len(_mem_usage),2),
                "Raft up time": raft_status["uptime"] - initializationDelay,
                "Raft terms": raft_status["raft_term"], #Count of total terms,
                "Total Err Requets": _g_error,
                "Total Requests global": _g_sent,
                "Total Requests in object": num_trans_rede,
                "Total Succ Requests": _g_success,
                "ERROR_CNT_QUEUE_FULL    ": _g_errors[FAIL_REASON.QUEUE_FULL],     #: Commands queue full
                "ERROR_CNT_MISSING_LEADER": _g_errors[FAIL_REASON.MISSING_LEADER],      #: Leader is currently missing (leader election in progress, or no connection)
                "ERROR_CNT_DISCARDED     ": _g_errors[FAIL_REASON.DISCARDED],      #: Command discarded (cause of new leader elected and another command was applied instead)
                "ERROR_CNT_NOT_LEADER    ": _g_errors[FAIL_REASON.NOT_LEADER],       #: Leader has changed, old leader did not have time to commit command.
                "ERROR_CNT_LEADER_CHANGED": _g_errors[FAIL_REASON.LEADER_CHANGED],      #: Simmilar to NOT_LEADER - leader has changed without command commit.
                "ERROR_CNT_REQUEST_DENIED": _g_errors[FAIL_REASON.REQUEST_DENIED],      #: Command denied}
                "Time of experiment": tot_time_experiment,
                "Node Address": str(obj.selfNode.address)
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
    #Add this to not interfer with next experiment
    obj.destroy()

    sys.exit(round(avgDelay * 100))
