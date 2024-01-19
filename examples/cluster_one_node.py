#!/usr/bin/env python
from __future__ import print_function

import sys
import time
from functools import partial
sys.path.append("../")
from pysyncobj import SyncObj, replicated
from random import randint
import numpy as np
import datetime
from schedule import Schedule

class Charger(SyncObj):

    def __init__(self, selfNodeAddr, otherNodeAddrs):
        """_summary_
        Minimum value product do algoritmo distribuido para veículos elétricos
        Essa versão o lider gera um valor semi-estocástico para o max_cluster value
        Args:
            selfNodeAddr (_type_): _description_
            otherNodeAddrs (_type_): _description_
        """
        super(Charger, self).__init__(selfNodeAddr, otherNodeAddrs)
        self.__power = 0
        self.__max_power = 7400
        self.__cluster_size = 1
        self.__max_cluster_power = 0
        #self.__count_ready = 0
        self.__cluster_power_dist = np.array([])
        self.__cluster_id_dist = np.array([])
        
        # TODO: self.schedule = Schedule("")
        self.cluster_schedule = {}
        
        # self.session_stats = {"session_id":"0000000000000000",
        #                       "ts":datetime.datetime(),
        #                       "tf":datetime.datetime(),
        #                       "tl":datetime.datetime(),
        #                       "e":1500,
        #                       "user_id":,}

    def get_max_cluster_power(self):
        self.__cluster_size = self.getNumberNodes()
        print(f"CLUSTER SIZE: {self.__cluster_size}")
        if self.__cluster_size is not None or 0:
            self.__max_cluster_power = randint(1380*self.__cluster_size, self.__max_power*self.__cluster_size)
        return self.__max_cluster_power
    
    @replicated
    def set_max_cluster_power(self, value):
        self.__max_cluster_power = value
        return self.__max_cluster_power

    @replicated
    def set_schedule(self, schedule):
        self.__cluster_power_dist = schedule
    
    @replicated
    def set_id_distribution(self, ids):
        self.__cluster_id_dist = ids

    def calculate_schedule(self, max_power_cluster):
        self.__cluster_size = self.getNumberNodes()
        #if self.__cluster_size is not None or 0:
        if self.__cluster_size != 0:
            min_power_per_node = int(max_power_cluster/(self.__cluster_size*2))
            max_power_per_node = int(max_power_cluster/self.__cluster_size)
            self.__cluster_power_dist = np.random.randint(min_power_per_node,max_power_per_node , self.__cluster_size)
            self.__cluster_id_dist = np.array([str(self.selfNode.address)] +[str(node) for node in self.otherNodes])
            calc_power = self.__cluster_power_dist[0]        
        else: 
            calc_power = 0
        
        if calc_power > self.__max_power:
            self.__power = self.__max_power
        else:
            self.__power = calc_power

        return self.__cluster_power_dist
    
    def getPower(self):
        return self.__power
    
    def setPower(self, power:int):
        self.__power = power

    def getNumberNodes(self):
        return int(self.getStatus()["partner_nodes_count"] + 1)

    def getMaxClusterPower(self):
        return self.__max_cluster_power
    
    def getClusterPowerDistribution(self):
        return self.__cluster_power_dist
    
    def getClusterIdDistribution(self):
        return self.__cluster_id_dist

def onAdd(res, err, cnt):
    print('onAdd %d:' % cnt, res, err)

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print('Usage: %s self_port partner1_port partner2_port ...' % sys.argv[0])
        sys.exit(-1)

    port = int(sys.argv[1])
    partners = ['localhost:%d' % int(p) for p in sys.argv[2:]]
    o = Charger('localhost:%d' % port)
    n = 0
    old_value = -1
    max_power_cluster = 0
    old_term = 0
    ready = True
    while True:
        #Condição que só permite começar quando tiver algum lider
        if o._getLeader() is None:
            continue
        #Verifica quando um novo term in raft é criado
        if old_term != int(o.getStatus()["raft_term"]):
            old_term = int(o.getStatus()["raft_term"])
            new_term = True
        #Se for LIDER executa as funções especificas do lider (Somente executa no inicio de cada TERM)
        if str(o.getStatus()["leader"]) == str(o.selfNode.address) and new_term:
            #Recebe a potência máxima para o cluster
            max_power_cluster  = o.get_max_cluster_power()
            #Repassa o valor para o cluster 
            o.set_max_cluster_power(max_power_cluster)
            #Calcula o planeamento de carga para o cluster
            """_summary_
                TODO: Acrescentar os limites de potência nominais de cada nodo em forma de array
                O calculo do schedule não pode ser somente no inicio de cada term, mas deve ocorrer sempre que exista uma mudança
                no código
            """
            schedule = o.calculate_schedule(max_power_cluster)
            #Repassa o schedule para o cluster
            o.set_schedule(schedule, callback=partial(onAdd, cnt=n))
            o.set_id_distribution(o.getClusterIdDistribution())
            new_term = False
        #Se for FOLLOWER executa as funções dentro da condição
        if str(o.getStatus()["leader"]) != str(o.selfNode.address):
            id_pos = np.where(str(o.selfNode.address) == o.getClusterIdDistribution())
            if o.getClusterPowerDistribution().all():
                power = o.getClusterPowerDistribution()[id_pos[0]]
                if len(power) > 0:
                    power = int(power[0])
                else:
                    print("Array is empty or does not contain any elements.")
                o.setPower(power)
        
        
        print(f"MAX_CLUSTER_POWER: {o.getMaxClusterPower()}")
        print(f"POWER ON NODE: {o.getPower()}")
        print(f"POWER DISTRIBUTION: {o.getClusterPowerDistribution()}")
        if o.getPower() != old_value:
            old_value = o.getPower()
            print(f"Power: {old_value}")

        # Estatisticas
        leader = o.getStatus()["leader"]
        partners_count = o.getStatus()["partner_nodes_count"]
        raft_term = o.getStatus()["raft_term"]
        print(f"LEADER: {leader}")
        print(f"PARTNERS COUNT: {partners_count}")
        print(f"RAFT TERM: {raft_term}")
        n += 1
        time.sleep(2)