#!/usr/bin/env python
from __future__ import print_function

import sys
import time
from functools import partial
sys.path.append("../")
from pysyncobj import SyncObj, SyncObjConf, replicated
from random import randint
import numpy as np
import datetime
import random
import time 
import logging
from schedule import Schedule

from cluster_db import TestTable, SessionLocal
import sqlalchemy

from datetime import datetime
from charger_parameters import ChargerParameters

"""
TODO:
Já realiza leituras corretas e atualizadas a base de dados, mas:
- Precisa replicar os dados de cada nó para todo o cluster
    - Metodo que adiciona os parâmetros dos outros nós usando RAFT
    - Metodo que mantem os dados dos parâmetros dos outros nós atualizados
Subdividir a base de dados em:
- Dados de configuração
- Dados de atualização do contexto de sessão 
- Dados do RAFT
- Dados do planeamento de carregamento

Adicionar dinamica de sincronismo de dados iniciais do cluster entre si 
Cada nó terá os arquivos de configuração um do outro 

"""

class Charger(SyncObj):

    def __init__(self, selfNodeAddr, otherNodeAddrs):
        """_summary_
        Minimum value product do algoritTypeError: __init__() takes exactly 1 positional argument (3 given)mo distribuido para veículos elétricos
        Essa versão o lider gera um valor semi-estocástico para o max_cluster value, deve ser alterado para receber
        TODO: O planeamento de carregamento só deve ser calculado quando o veículo estiver conectado e autenticado
        TODO: O planeamento de carregamento deve ser feito toda vez que um novo veículo é conectado ou desconectado para além do inicio do term
        TODO: Acesso a base de dados e busca de informações
        TODO: Comunicação com cliente, servidor externo para obter o max_power_cluster
        TODO: Planeamento de carregamento orientado ao usuário utilizando KNN
        TODO: Depois que se descobrir as sessões de carregamento históricas mais próximas dentro do K determinado, buscar o session_id dessas sessões e estimar a potência utilizada em cada periodo
        TODO: Tabela de estatisticas das sessões de carregamento anteriores na base de dados para cálculo do planeamento de carga 
        TODO: Determinar o periodo em que deve ser feito o planeamento de carga para cada veículo e usuário conectado
        self.__my_parameters = {
                        "address": "192.168.219.140:3000",
                        'active': False, #Verifica se o programa do carregador está a correr
                        'ready':False,
                        'session_id': "0000000000000000",
                        "user_id": 0,
                        'plug_state':"charging",#, "not_plugged", "plugged_not_charging"
                        "nominal_power":self.__nom_power,
                        "selected_max_power": self.__max_power,
                        "max_cluster_power":self.__nom_power * self.__cluster_size,
                        "planned_departure":datetime.datetime(),
                        "planned_charging_schedule": self.__schedule,
                        "executed_charging_schedule": self.__executed_schedule,
                        }
        self.current_session_stats = {"session_id":"0000000000000000",
                            "ts":datetime.datetime(),
                            "tf":datetime.datetime(),
                            "tl":datetime.datetime(),
                            "e":1500,
                            "user_id":,}
        Args:
            selfNodeAddr (_type_): _description_
            otherNodeAddrs (_type_): _description_
        """
        #super(Charger, self).__init__(chargerParams)
        cfg = SyncObjConf(dynamicMembershipChange = True,
                          commandsWaitLeader = True)
        super(Charger, self).__init__(selfNodeAddr, otherNodeAddrs, cfg)
        self.my_parameters = self.initial_charger_parameters_from_db(selfNodeAddr)
        self.__id = self.my_parameters.evse_id
        self.__cur_power = 0 #Reads from the energy Meter
        self.__max_power = 7360 #Limit of power selected by the schedule
        self.__nom_power = 7360 #Nominal power limit on the EVSE
        self.__min_power = 1380 #Potência mínima permitida no EVSE
        self.__cluster_size = len(otherNodeAddrs) + 1
        #self.__cluster_power_dist = np.array([])
        self.__count_plugged_chargers = 0
        self.__count_auth_chargers = 0
        self.__schedule = Schedule(evse_id=self.__id,
                                   id=1,
                                   charging_rate_unit="W",
                                   duration=0,
                                   charging_schedule_period=[{'startPeriod': datetime.now() ,'limit': self.__nom_power}])
        self.__executed_schedule = Schedule(evse_id=self.__id,
                                            id=1,
                                            charging_rate_unit="W",
                                            duration=0,
                                            charging_schedule_period=[{'startPeriod': datetime.now() ,'limit': self.__nom_power}])

        self.__cluster_parameters = { self.__id: self.my_parameters,}
        #self.__current_time = time.time()

    #Inicializa ou configura dados iniciais do carregador a partir da base de dados
    def initial_charger_parameters_from_db(self, address):
        # Verifica se o plug está conectado
        db = SessionLocal()
        evse_row = db.query(TestTable).filter(TestTable.address == address).first()

        if evse_row:
            charger_data = {
                "address": evse_row.address,
                "plug_status": evse_row.plug_status,
                "authenticated": evse_row.authenticated,
                "nominal_power": evse_row.nominal_power,
                "selected_max_power": evse_row.selected_max_power,
                "planned_departure": evse_row.planned_departure,
                "user_id": evse_row.user_id,
                "session_id": evse_row.session_id,
                "evse_id": evse_row.evse_id,
                "max_cluster_power": evse_row.max_cluster_power
            }

            charger = ChargerParameters(**charger_data)
            db.commit()
            db.close()
            return charger
        #TODO: Cannot return None
        else:
            print("EVSE not found in the database.")
            return None
    
    
    #Metodo para obter os dados do cluster fora da classe
    def get_cluster_parameters(self):
        return self.__cluster_parameters
    #Metodo para obter o id do carregador fora da classe
    def get_my_evse_id(self):
        return self.__id
    
    #Da forma como está aqui a função add.. teria sempre que ser chamada antes da rep... se não tentaria reproduzir um valor que não existe
    
    @replicated
    def add_my_params_to_cluster_parameters(self, evse_id:str, params:ChargerParameters):
        self.__cluster_parameters[evse_id] = params
        return self.__cluster_parameters
    
    def get_selected_max_power(self):
        self.my_parameters = self.__cluster_parameters[self.__id].selected_max_power
        return self.my_parameters

    def update_charger_parameters_from_db(self):
        #Deve atualizar somente dados que  que não serão atualizados na dinâmica do código
        try:
            # Verifica se o plug está conectado
            db = SessionLocal()
            evse_row = db.query(TestTable).where(TestTable.evse_id == self.__id).first()

            if evse_row:
                charger_data = {
                    "address": evse_row.address,
                    "plug_status": evse_row.plug_status,
                    "authenticated": evse_row.authenticated,
                    "nominal_power": evse_row.nominal_power,
                    #"selected_max_power": evse_row.selected_max_power,
                    "planned_departure": evse_row.planned_departure,
                    "user_id": evse_row.user_id,
                    "session_id": evse_row.session_id,
                    "evse_id": evse_row.evse_id,
                    "max_cluster_power": evse_row.max_cluster_power
                }

            self.my_parameters = ChargerParameters(**charger_data)
            db.commit()
            return self.my_parameters

        except sqlalchemy.exc.TimeoutError:
            # Handle the TimeoutError, create a new session, and try again
            print("TimeoutError: Reconnecting to the database...")
            db = SessionLocal()
            evse_row = db.query(TestTable).where(TestTable.evse_id == self.__id).first()

            if evse_row:
                charger_data = {
                    "address": evse_row.address,
                    "plug_status": evse_row.plug_status,
                    "authenticated": evse_row.authenticated,
                    "nominal_power": evse_row.nominal_power,
                    #"selected_max_power": evse_row.selected_max_power,
                    "planned_departure": evse_row.planned_departure,
                    "user_id": evse_row.user_id,
                    "session_id": evse_row.session_id,
                    "evse_id": evse_row.evse_id,
                    "max_cluster_power": evse_row.max_cluster_power
                }

            self.my_parameters = ChargerParameters(**charger_data)
            db.commit()
            return self.my_parameters

        finally:
            # Make sure to close the session after using it
            if db:
                db.close()
    
    #Função utilizada para o lider para no momento de calcular a divisão de potência considerar os 
    #Carregadores conectados 
    def count_plugged_chargers(self):
        i = 0
        for charger in self.__cluster_parameters:
            if self.__cluster_parameters[charger].plug_status == "plugged_not_charging" or "charging":
                i += 1
        self.__count_plugged_chargers = i
        return self.__count_plugged_chargers
    #Função que calcula a divisão de potência entre os carregadores         
    def calculate_schedule(self, max_power_cluster):
        self.__count_plugged_chargers = self.count_plugged_chargers()
        remaining_power = max_power_cluster
        counter_not_authenticated = 0
        if self.__count_plugged_chargers > 0:
            #Para os carregadores não autenticados
            for evse_id in self.__cluster_parameters:
                #Se o carregador não tiver um usuário autenticado e com veículo conectado
                if (self.__cluster_parameters[evse_id].user_id <= 0 and 
                    (self.__cluster_parameters[evse_id].plug_status == "plugged_not_charging" or "charging")):
                    #Fornecer a potência mínima e subtrair do valor máximo
                    self.__cluster_parameters[evse_id].selected_max_power = self.__min_power
                    remaining_power -= self.__min_power
                    counter_not_authenticated += 1
            ############# Equal division of power between connected and authenticated chargers #######################
            if self.__count_plugged_chargers - counter_not_authenticated > 0:
                calc_power = remaining_power/(self.__count_plugged_chargers - counter_not_authenticated)
                for evse_id in self.__cluster_parameters:
                    #Se o carregador tiver um usuário autenticado e veículo conectado
                    if (self.__cluster_parameters[evse_id].user_id > 0 and 
                        (self.__cluster_parameters[evse_id].plug_status == "plugged_not_charging" or "charging")):
                        #Fornecer a potência calculada restante
                        #Verifica se o valor de potência calculado respeita o valor nominal do carregador
                        if calc_power > self.__nom_power:
                            self.__cluster_parameters[evse_id].selected_max_power = self.__max_power
                        else:
                            self.__cluster_parameters[evse_id].selected_max_power = calc_power
        else: 
            self.__cluster_parameters[evse_id].selected_max_power = self.__min_power
        db = SessionLocal()
        chargers = db.query(TestTable).order_by(TestTable.register_id.desc()).all()
        for charger in chargers:
            if charger in self.__cluster_parameters:
                chargers[charger].selected_max_power = self.__cluster_parameters[charger.evse_id].selected_max_power
        db.commit()
        db.close()
        return self.__cluster_parameters
    
    ##############################################################################################################################
    ############################################## SIMULATION METHODS ############################################################
    ##############################################################################################################################
    
    def getNumberNodes(self):
        return int(self.getStatus()["partner_nodes_count"] + 1)

    #Obtem o endereço dos outros nós pela base de dados: "Temporário", 
    #Deve ser obtido automaticamente no futuro utilizando o algoritmo RAFT
    def get_other_nodes_addresses(self, evse_id):
        db = SessionLocal()
        
        otherNodeAddrs = []
        cluster_table = db.query(TestTable).filter(TestTable.evse_id != evse_id).all()
        for row in cluster_table:
            otherNodeAddrs.append(row.address)
        
        db.commit()
        db.close()
        return otherNodeAddrs

def initial_charger_parameters_from_db(evse_id):
    # Verifica se o plug está conectado
    db = SessionLocal()
    evse_row = db.query(TestTable).filter(TestTable.evse_id == evse_id).first()

    if evse_row:
        charger_data = {
            "address": evse_row.address,
            "plug_status": evse_row.plug_status,
            "authenticated": evse_row.authenticated,
            "nominal_power": evse_row.nominal_power,
            "selected_max_power": evse_row.selected_max_power,
            "planned_departure": evse_row.planned_departure,
            "user_id": evse_row.user_id,
            "session_id": evse_row.session_id,
            "evse_id": evse_row.evse_id,
            "max_cluster_power": evse_row.max_cluster_power
        }

        charger = ChargerParameters(**charger_data)
        db.close()
        return charger
    else:
        print("EVSE not found in the database.")
        db.close()
        return None

def get_other_nodes_addresses(evse_id):
    db = SessionLocal()
    db.commit()
    otherNodeAddrs = []
    cluster_table = db.query(TestTable).filter(TestTable.evse_id != evse_id).all()
    for row in cluster_table:
        otherNodeAddrs.append(row.address)
    db.close()
    return otherNodeAddrs

def onAdd(res, err, cnt):
    print('onAdd %d:' % cnt, res, err)

if __name__ == '__main__':
    if len(sys.argv) < 1:
        print('Usage: %s evse_hostname_id ...' % sys.argv[0])
        sys.exit(-1)
    evse_id = str(sys.argv[1])
    #port = int(sys.argv[2])
    partners = [p for p in get_other_nodes_addresses(evse_id)]
    charger_parameters = initial_charger_parameters_from_db(evse_id)
   
    print(charger_parameters.address)
    o = Charger(charger_parameters.address, partners)
    o.add_my_params_to_cluster_parameters(
        evse_id=o.get_my_evse_id(), 
        params=o.my_parameters)
    n = 0
    old_value = -1
    max_power_cluster = 0
    old_term = 0
    old_count_ready = 0
    on_charger_ready = False
    ready = True
    while True:
        #Condição que só permite começar quando tiver algum lider
        if o._getLeader() is None:
            continue
        #Realiza a leitura correta da base de dados, mas não atualiza o cluster
        o.update_charger_parameters_from_db()
        # o.add_my_params_to_cluster_parameters(
        #             evse_id=o.get_my_evse_id(), 
        #             params=o.get_cluster_parameters()[o.get_my_evse_id()])
        #Atualizo aqui todos os dados que vem somente da DB de simulação do estado atual de cada carregador
        print(o.get_cluster_parameters())
        
        
        print(f"GET LEADER STAT: {o._getLeader()}")
        if old_count_ready != int(o.count_plugged_chargers()):
            old_count_ready = int(o.count_plugged_chargers())
            on_charger_ready = True
        # #Verifica quando um novo term in raft é criado
        if old_term != int(o.getStatus()["raft_term"]):
            old_term = int(o.getStatus()["raft_term"])
            new_term = True
        
        ############################################# LEADER ##################################################
        #Se for LIDER executa as funções especificas do lider (Somente executa no inicio de cada TERM)
        if str(o.getStatus()["leader"]) == str(o.selfNode.address): #and (new_term or on_charger_ready):
            #Recebe a potência máxima para o cluster
            max_power_cluster  = o.my_parameters.max_cluster_power
            #Repassa o valor para o cluster 
            cluster_parameters = o.calculate_schedule(max_power_cluster)
            #Repassa o schedule para o cluster
            #o.replicate_cluster_parameters(callback=partial(onAdd, cnt=n))
            #Atualização dos dados do cluster baseado no calculo de replicação do sistema
            for charger in cluster_parameters:
                o.add_my_params_to_cluster_parameters(
                    evse_id=charger, 
                    params=o.get_cluster_parameters()[charger])
            if new_term == True:
                new_term = False
            elif on_charger_ready == True:
                on_charger_ready = False

        #########################################################################################################
        ############################################# FOLLOWER ##################################################
        #Se for FOLLOWER executa as funções dentro da condição
        #if str(o.getStatus()["leader"]) != str(o.selfNode.address):
        o.my_parameters.selected_max_power = o.get_cluster_parameters()[o.get_my_evse_id()].selected_max_power
        
        # Estatisticas RAFT
        # leader = o.getStatus()["leader"]
        # partners_count = o.getStatus()["partner_nodes_count"]
        # raft_term = o.getStatus()["raft_term"]
        print(f"MAX_CLUSTER_POWER: {o.my_parameters.max_cluster_power}")
        print(f"POWER ON NODE: {o.my_parameters.selected_max_power}")
        # print(f"POWER DISTRIBUTION: {o.get_cluster_parameters()}")
        # print(f"LEADER: {leader}")
        # print(f"PARTNERS COUNT: {partners_count}")
        # print(f"RAFT TERM: {raft_term}")

        n += 1
        time.sleep(5)