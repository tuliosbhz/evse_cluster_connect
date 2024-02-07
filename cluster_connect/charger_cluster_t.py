#!/usr/bin/env python
from __future__ import print_function

import sys
import time
from functools import partial
sys.path.append("../")
from pysyncobj import SyncObj, SyncObjConf, replicated, replicated_sync
from pysyncobj.batteries import ReplDict
from random import randint
import numpy as np
import datetime
import random
import time 
import logging
from schedule import Schedule

from cluster_db import SessionLocal, Configuration, EvseDataSimTable, ClusterStatsTable
import sqlalchemy

from datetime import datetime
from charger_parameters import ConfigParameters, EvseDataSim, ClusterStats

import asyncio

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

    def __init__(self, evse_id):
        """_summary_
        TODO: O planeamento de carregamento só deve ser calculado quando o veículo estiver conectado e autenticado
        TODO: O planeamento de carregamento deve ser feito toda vez que um novo veículo é conectado ou desconectado para além do inicio do term
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
                        "nominal_power":self.__power_capacity,
                        "selected_max_power": self.__limit_power,
                        "max_cluster_power":self.__power_capacity * self.__cluster_size,
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

        ####################### Busca inicialmente parametros para objeto Sync ############################
        self.cluster_id = "cluster001"
        init_params = self.get_address_from_id(evse_id)
        selfNodeAddr = init_params.address
        self.config_params = self.get_config_from_db(selfNodeAddr)
        self.id = str(self.config_params.evse_id)
        
        otherNodeAddrs = [p for p in self.get_other_nodes_addresses(evse_id)]
        print(f"Other nodes addresses: {otherNodeAddrs}")
        cfg = SyncObjConf(dynamicMembershipChange = True,
                          commandsWaitLeader = False)
        ############################ Inicializa classe do objeto Sync #####################################
        super(Charger, self).__init__(selfNodeAddr, otherNodeAddrs, cfg)

        ####################### Configuração dos parâmetros do carregador ############################
        #TODO: Avaliar o deletar dessas variáveis individuais e trabalhar com variáveis do dicionário
        self.__limit_power = 7360 #Limit of power selected by the schedule
        self.__power_capacity = 7360 #Nominal power limit on the EVSE
        self.__min_power = 1380 #Potência mínima permitida no EVSE
        self.__schedule = Schedule(evse_id=self.id,
                                   id=1,
                                   charging_rate_unit="W",
                                   duration=0,
                                   charging_schedule_period=[{'startPeriod': datetime.now() ,'limit': self.__power_capacity}])
        self.__executed_schedule = Schedule(evse_id=self.id,
                                            id=1,
                                            charging_rate_unit="W",
                                            duration=0,
                                            charging_schedule_period=[{'startPeriod': datetime.now() ,'limit': self.__power_capacity}])
        #Dado que será replicado entre os nós
        self.__cluster_ids = {}
        self.evse_data_sim:EvseDataSim = self.get_evse_data_from_db(self.id)
        self.__evse_sinc_data = { self.id: self.evse_data_sim,}
        self.cluster_stats:ClusterStats = self.get_cluster_stats_from_db()
        self.__sinc_cluster_stats = { self.id: self.cluster_stats,}
        #self.__cluster_stats = ClusterStats(cluster_id="cluster001")~

        
    #Inicializa ou configura dados iniciais do carregador a partir da base de dados
    def get_config_from_db(self, address):
        # Verifica se o plug está conectado
        db = SessionLocal()
        config_row = db.query(Configuration).filter(Configuration.address == address).first()

        if config_row:
            config_data = {
                "address": config_row.address,
                "nominal_power": config_row.nominal_power,
                "evse_id": config_row.evse_id,
            }

            charger = ConfigParameters(**config_data)
            db.commit()
            db.close()
            return charger
        #TODO: Cannot return None
        else:
            logging.error(f"GET_CONFIG_FROM_DB: EVSE not found in the database for {address}")
            logging.error(f"Type of address: {type(address)}")
            return None
    ######################### Funções individuais de cada carregador ################################
    #Inicializa ou configura dados iniciais do carregador a partir da base de dados    
    def get_cluster_stats_from_db(self):
        # Verifica se o plug está conectado
        db = SessionLocal()
        sched_row = db.query(ClusterStatsTable).filter(ClusterStatsTable.cluster_id == self.cluster_id).first()
        #print(sched_row.planned_departure)
        if sched_row:
            sched_data = {
                "cluster_id": sched_row.cluster_id,
                "num_nodes": sched_row.num_nodes,
                "total_limit_power": sched_row.total_limit_power if sched_row.total_limit_power is not None else 0,
                "total_power_capacity": sched_row.total_power_capacity if sched_row.total_power_capacity is not None else 0,
                "min_power_capacity": sched_row.min_power_capacity if sched_row.min_power_capacity is not None else 0,
                "num_active_nodes": sched_row.num_active_nodes if sched_row.num_active_nodes is not None else 0,
            }

            schedule = ClusterStats(**sched_data)
            db.commit()
            db.close()
            return schedule
        #TODO: Cannot return None
        else:
            logging.error(f"GET_SCHEDULE_FROM_DB: EVSE not found in the database for evse_id: {evse_id}")
            return ClusterStats()
    
    def query_evse_data(self, evse_id):
        db = SessionLocal()
        evse_row = db.query(EvseDataSimTable).where(EvseDataSimTable.evse_id == evse_id).first()

        if evse_row:
            charger_data = {
                "plug_status": evse_row.plug_status,
                "authenticated": evse_row.authenticated,
                "user_id": evse_row.user_id,
                "session_id": evse_row.session_id,
                "evse_id": evse_row.evse_id,
                "cluster_id": evse_row.cluster_id,
                "min_power_capacity": evse_row.min_power_capacity,
                "power_capacity": evse_row.power_capacity,  # Value in watts of total capacity
                "measured_power": evse_row.measured_power if evse_row.measured_power is not None else 0,
                "selected_max_power": evse_row.selected_max_power if evse_row.selected_max_power is not None else 0,
            }

            evse_data_sim = EvseDataSim(**charger_data)
            db.commit()
            db.close()
            return evse_data_sim

        
    def get_evse_data_from_db(self, evse_id):
        #Deve atualizar somente dados que  que não serão atualizados na dinâmica do código
        evse_data_sim = None
        try:
            # Verifica se o plug está conectado
            return self.query_evse_data(evse_id)

        except sqlalchemy.exc.TimeoutError:
            # Handle the TimeoutError, create a new session, and try again
            print("TimeoutError: Reconnecting to the database...")
            return self.query_evse_data(evse_id)
        finally:
            print(evse_data_sim)

    def get_my_evse_id(self):
        return self.id
    
    @replicated
    def add_id_to_cluster(self, address, id):
        self.__cluster_ids[address] = id
    
    @replicated
    def update_id_to_cluster(self, address, id):
        self.__cluster_ids.update({address:id})

    
    def get_cluster_ids(self):
        return self.__cluster_ids
        
    """
    Cada carregador adiciona o seu estado na variável que será comum a todos os carregadores do grupo:
    As variáveis são:
    - Identificador do carregador
    - Estado de conexão do veículo
    - Estado de autenticação do usuário juntamente com o identificador do usuário
    - Identificador da sessão de carregamentos
    - Maximo de potẽncia para o grupo recebido por aquele carregador (Relevante quando for o lider)
    Returns:
        Retorna o novo cluster após a adição dos dados individuais
    """
    @replicated
    def add_sim_params_to_cluster(self, evse_id, params:EvseDataSim):
        self.__evse_sinc_data[evse_id] = params
    
    @replicated
    def update_sim_params_to_cluster(self, evse_id, params:EvseDataSim):
        self.__evse_sinc_data.update({evse_id:params})
    
    def get_sim_cluster_params(self):
        return self.__evse_sinc_data
    """
    Adiciona os dados de scheduling inicialmente de cada nó para que o lider saiba quais nós estão conectados
    """
    @replicated
    def add_my_sched_params_to_cluster(self, evse_id ,params:ClusterStats):
        self.__sinc_cluster_stats[evse_id] = params
    """
    Adiciona os dados de scheduling criado pelo lider a todos os nós
    """
    @replicated
    def sinc_cluster_stats(self, evse_id:str, params:ClusterStats):
        self.__sinc_cluster_stats.update({evse_id:params})
    
    def set_cluster_stats_on_db(self, cluster_stats):
        db = SessionLocal()
        cluster_stats = db.query(ClusterStatsTable).filter_by(cluster_id = self.cluster_id).first()
        cluster_stats.num_nodes = len(self.otherNodes) + 1
        cluster_stats.num_active_nodes = len(self.connected_nodes())
        cluster_stats.min_power_capacity = self.cluster_minimum_capacity()
        cluster_stats.total_power_capacity = self.cluster_maximum_capacity()
        db.commit()
        db.close()


    def get_sched_cluster_params(self):
        return self.__sinc_cluster_stats
    
    def get_selected_max_power(self):
        return self.__evse_sinc_data[self.id].selected_max_power
        #Metodo para obter os dados do cluster fora da classe
    
    def get_power_capacities(self):
        clu_data = self.__evse_sinc_data
        power_capacities = [clu_data[charger].power_capacity for charger in clu_data]
        return power_capacities
    
    def cluster_maximum_capacity(self): 
        return int(sum(self.get_power_capacities()))

    #TODO: get from the database the minimum power of each charger and use that, 
    #Because for trifasic chargers the minimum capacity is higher
    def cluster_minimum_capacity(self):
        active_nodes = self.connected_nodes()
        return len(active_nodes) * self.__min_power
    #Função utilizada para o lider para no momento de calcular a divisão de potência considerar os 
    #Carregadores conectados 
    def plugged_chargers(self):
        plugged = []
        evse_id = ""
        clu_data = self.__evse_sinc_data
        active_nodes = self.connected_nodes()
        print(f"ACTIVE NODES PLUGGED: {active_nodes}")
        if clu_data:
            for node_addr in active_nodes:
                if node_addr in self.__cluster_ids:
                    evse_id = self.__cluster_ids[node_addr]
                if (evse_id in clu_data and 
                    (clu_data[evse_id].plug_status == "plugged_not_charging" or "charging")):
                        plugged.append(evse_id)
        return plugged
    
    def auth_chargers(self):
        auths = []
        evse_id = ""
        active_nodes = self.connected_nodes()
        if self.__evse_sinc_data:            #Itera por todos os outros nós do grupo
            for node_addr in active_nodes:
                node_addr = str(node_addr)
                if node_addr in self.__cluster_ids:
                    evse_id = self.__cluster_ids[node_addr]
                #Verifica se está autenticado
                if evse_id in self.__evse_sinc_data:
                    if self.__evse_sinc_data[evse_id].user_id > 0:
                        auths.append(evse_id)
        return auths
    
    def connected_nodes(self):
        active_nodes = []
        #if self.isNodeConnected(self.selfNode):
        active_nodes.append(self.selfNode.address)
        for node in self.otherNodes:
            if self.isNodeConnected(node):
                active_nodes.append(node.address)
        active_nodes.sort()
        return active_nodes
    
    # def remove_not_connected_node(self):
    #     connected_nodes = self.count_connected_nodes()
    #     if connected_nodes != len(self.__cluster_ids):
            #Significa que existe algum nó a ma
    
    # def update_sched_cluster_data(self, max_power_cluster):
    #     #Update the schedule variables with the most updated values
    #     self.__sinc_cluster_stats[self.id].total_limit_power = max_power_cluster #Informação que vem do lider
    #     self.__sinc_cluster_stats[self.id].session_id = self.__evse_sinc_data[self.id].session_id
    #     self.__sinc_cluster_stats[self.id].evse_id = self.__evse_sinc_data[self.id].evse_id
    #     self.__sinc_cluster_stats[self.id].user_id = self.__evse_sinc_data[self.id].user_id
    #     return self.__sinc_cluster_stats
    
    def update_sched_params_on_db(self):
        #Atualiza base de dados com schedule calculado próprio
        db = SessionLocal()
        sched_row = db.query(EvseDataSimTable).filter(EvseDataSimTable.evse_id == self.id).order_by(EvseDataSimTable.register_id.desc()).first()
        if sched_row:
            sched_row.selected_max_power = self.__evse_sinc_data[self.id].selected_max_power
            sched_row.user_id = self.__evse_sinc_data[self.id].user_id
            db.commit()
            db.close()
    
    #Função que calcula a divisão de potência entre os carregadores         
    def sch_equal_power_division(self, max_power_cluster, with_authentication:bool=False):
        evse_data_sinc = self.__evse_sinc_data
        if with_authentication:
            active_chargers = self.auth_chargers()
        else:
            active_chargers = self.plugged_chargers()
        try:
            # self.update_sched_cluster_data(max_power_cluster)
            #Verifica se carregador cumpre os requisitos para receber potência
            if self.id in active_chargers:
                #self.__schedule = self.schedule_calculation()
                calc_power = max_power_cluster / len(active_chargers)
                #Verifica se está incluida nas variáveis de contexto do cluster
                if self.id in evse_data_sinc:
                    #O maximo de potência calculada não pode ser mais do que o máximo nominal
                    if calc_power > evse_data_sinc[self.id].power_capacity:
                        evse_data_sinc[self.id].selected_max_power = evse_data_sinc[self.id].power_capacity
                    else:
                        evse_data_sinc[self.id].selected_max_power = calc_power
                #Atualiza os dados de sessão individuais no grupo de carregadores
                else:
                    session_params = self.get_evse_data_from_db(self.id)
                    self.update_sim_params_to_cluster(self.id,session_params)
            else: 
                evse_data_sinc[self.id].selected_max_power = 0
            
            #Atualiza no cluster e base de dados o novo schedule
            self.sinc_cluster_stats(self.id, evse_data_sinc[self.id])
            self.update_sched_params_on_db()
        except Exception as error:
            logging.error(f"CALCULATE_SCHEDULE: {str(error)}")
        finally:
            return evse_data_sinc
        
    #Função que calcula a divisão de potência entre os carregadores         
    def sch_capacity_based(self, max_power_cluster, with_authentication:bool=False):
        evse_data_sinc = self.__evse_sinc_data
        if with_authentication:
            active_chargers = self.auth_chargers()
        else:
            active_chargers = self.plugged_chargers()
        
        try:
            self.update_sched_cluster_data(max_power_cluster)
            tot_cap = self.cluster_maximum_capacity()
            #Se estiver algum carregador autenticado e se o carregador atual está autenticado
            if self.id in active_chargers:
                #self.__schedule = self.schedule_calculation()
                if tot_cap:
                    power_portion = self.__power_capacity / tot_cap
                    calc_power = max_power_cluster * power_portion
                else:
                    logging.error("No total capacity of power corrected calculated")
                #Para os carregadores não autenticados
                #Verifica se está incluida nas variáveis de contexto do cluster
                if self.id in evse_data_sinc:
                    #O maximo de potência calculada não pode ser mais do que o máximo nominal
                    if calc_power > self.__power_capacity:
                        evse_data_sinc[self.id].selected_max_power = self.__limit_power
                    else:
                        evse_data_sinc[self.id].selected_max_power = calc_power
                #Atualiza os dados de sessão individuais no grupo de carregadores
                else:
                    session_params = self.get_evse_data_from_db(self.id)
                    self.update_sim_params_to_cluster(self.id,session_params)
            else: 
                evse_data_sinc[self.id].selected_max_power = 0
            
            #Atualiza no cluster e base de dados o novo schedule
            self.sinc_cluster_stats(self.id, evse_data_sinc[self.id])
            self.update_sched_params_on_db()
        except Exception as error:
            logging.error(f"CALCULATE_SCHEDULE: {str(error)}")
        finally:
            return evse_data_sinc
    
    ##############################################################################################################################
    ############################################## SIMULATION METHODS ############################################################
    ##############################################################################################################################
    
    def getNumberNodes(self):
        return int(self.getStatus()["partner_nodes_count"] + 1)

    #Obtem o endereço dos outros nós pela base de dados: "Temporário", 
    #Deve ser obtido automaticamente no futuro utilizando o algoritmo RAFT
    def get_other_nodes_addresses(self, evse_id):
        db = SessionLocal()
        db.commit()
        otherNodeAddrs = []
        cluster_table = db.query(Configuration).filter(Configuration.evse_id != evse_id).all()
        for row in cluster_table:
            otherNodeAddrs.append(row.address)
        db.close()
        return otherNodeAddrs

    #Inicializa ou configura dados iniciais do carregador a partir da base de dados
    def get_address_from_id(self, evse_id):
        # Verifica se o plug está conectado
        db = SessionLocal()
        config_row = db.query(Configuration).filter(Configuration.evse_id == evse_id).first()

        if config_row:
            config_data = {
                "address": config_row.address,
                "nominal_power": config_row.nominal_power,
                "evse_id": config_row.evse_id,
            }

            charger = ConfigParameters(**config_data)
            db.commit()
            db.close()
            return charger
        #TODO: Cannot return None
        else:
            print("EVSE not found in the database.")
            db.close()
            return None
        
def onRemove(res, err):
    logging.info(f"On remove: {res}, {err}")

def onAdd(res, err):
    logging.info(f"On add: {res}, {err}")

def main(evse_id):
    o = Charger(evse_id=evse_id)
    n = 0
    my_address = str(o.selfNode.address)
    my_evse_id = o.id
    o.add_id_to_cluster(my_address, my_evse_id)
    o.addNodeToCluster(o.selfNode, callback=partial(onAdd))
    # try:
    while True:
        #Condição que só permite começar quando tiver algum lider
        if o._getLeader() is None:
            time.sleep(1)
            continue
        #Update local variable
        cluster_evse_data_sim = o.get_sim_cluster_params()
        cluster_sinc_data = o.get_sched_cluster_params()
        #Atualiza os dados nominais do cluster de potência
        o.set_cluster_stats_on_db(cluster_stats=cluster_sinc_data)
        #Obtem o dado de potência recebido nominal
        db_stats = o.get_cluster_stats_from_db()
        o.update_id_to_cluster(address=o.selfNode.address, id=o.id)
        print(f"MY ID on begging of cycle: {o.get_my_evse_id()}")
        #Mantem atualizado no cluster as variáveis que determinam contexto no carregador
        dict_ids = o.get_cluster_ids()
        if my_address in dict_ids:
            my_evse_id = dict_ids[my_address]
            o.update_sim_params_to_cluster(my_evse_id, o.get_evse_data_from_db(my_evse_id))
        # if my_address not in o.get_sched_cluster_params():
        #     o.add_my_sched_params_to_cluster(my_evse_id, o.get_cluster_stats_from_db(my_evse_id))
    
        #Atualizo aqui todos os dados que vem somente da DB de simulação do estado atual de cada carregador
        print(f"{o.id} SCHEDULE PARAMETERS")
        print(o.get_sched_cluster_params())
        print(f"{o.id} SIMULATION PARAMETERS")
        print(o.get_sim_cluster_params())
        #print(f"GET LEADER STAT: {o._getLeader()}")
        
        ############################################# LEADER ##################################################
        #Se for LIDER executa as funções especificas do lider (Somente executa no inicio de cada TERM)
        # if str(o.getStatus()["leader"]) == my_address: #or (new_term or on_charger_ready):
        #     #Recebe a potência máxima para o cluster
        #     max_pfower_cluster = o.get_sim_cluster_params()[my_evse_id].max_cluster_power
        #Get leader id
        leader_address = str(o.getStatus()["leader"])
        print(f"LEADER_ADDRESS: {leader_address}")
        
        if leader_address and leader_address in o.get_cluster_ids():
            leader_evse_id = o.get_cluster_ids()[leader_address]
            print(f"LEADER: {leader_evse_id}")
            # raft_status = o.getStatus()
            # print(f"RAFT STATUS: {raft_status}")
            #Repassa o valor para o cluster 
            if leader_evse_id in o.get_sim_cluster_params():
                sched_parameters = o.sch_equal_power_division(db_stats.total_limit_power)
                print(sched_parameters)
            #Repassa o schedule para o cluster
            #Atualização dos dados do cluster baseado no calculo de replicação do sistema
            if my_evse_id in o.get_sched_cluster_params():
                o.sinc_cluster_stats(
                    evse_id=my_evse_id, 
                    params=o.get_sched_cluster_params()[my_evse_id])

        if o.hasQuorum == False:
            #Repassa o valor para o cluster 
            o.evse_data_sim = o.get_evse_data_from_db(my_evse_id)
            sched_parameters = o.sch_equal_power_division(db_stats.total_limit_power)
            #Repassa o schedule para o cluster
            #Atualização dos dados do cluster baseado no calculo de replicação do sistema
            if my_evse_id in o.get_sched_cluster_params():
                o.sinc_cluster_stats(
                    evse_id=my_evse_id, 
                    params=sched_parameters)
            #Carregador está sozinho
        #########################################################################################################
        ############################################# FOLLOWER ##################################################
        #Se for FOLLOWER executa as funções dentro da condição
        #if str(o.getStatus()["leader"]) != str(o.selfNode.address):
        if my_evse_id in cluster_sinc_data:
            o.cluster_stats = cluster_sinc_data[my_evse_id]
            print(f"MAX_CLUSTER_POWER: {o.cluster_stats.total_limit_power}")
            print(f"POWER ON NODE: {o.evse_data_sim.selected_max_power}")
        # Estatisticas RAFT
        # leader = o.getStatus()["leader"]
        # partners_count = o.getStatus()["partner_nodes_count"]
        # raft_term = o.getStatus()["raft_term"]


        # print(f"POWER DISTRIBUTION: {o.get_sched_cluster_params()}")
        # print(f"LEADER: {leader}")
        # print(f"PARTNERS COUNT: {partners_count}")
        # print(f"RAFT TERM: {raft_term}")

        #Atualiza na base de dados os valores do schedule individuais de acordo com a variável comum ao cluster
        #o.set_cluster_stats_on_db()

        n += 1
        time.sleep(3)
    # except Exception as error:
    #     logging.error(f"Error in main loop of {my_evse_id}: {str(error)}")

    
if __name__ == '__main__':
    if len(sys.argv) < 1:
        print('Usage: %s evse_hostname_id ...' % sys.argv[0])
        sys.exit(-1)
    evse_id = str(sys.argv[1])
    main(evse_id)