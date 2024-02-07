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

from cluster_db import SessionLocal, Configuration, ClusterSincDataTable, EvseDataSimTable
import sqlalchemy

from datetime import datetime
from charger_parameters import ConfigParameters, ClusterSincData, EvseDataSim

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

!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
ERRO na identificação do carregador quando falha e volta depois, pensa que é o lider
!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
"""

class Charger(SyncObj):

    def __init__(self, evse_id):
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

        ####################### Busca inicialmente parametros para objeto Sync ############################
        init_params = self.get_address_from_id(evse_id)
        selfNodeAddr = init_params.address
        otherNodeAddrs = [p for p in self.get_other_nodes_addresses(evse_id)]
        print(f"Other nodes addresses: {otherNodeAddrs}")
        cfg = SyncObjConf(dynamicMembershipChange = True,
                          commandsWaitLeader = False)
        ############################ Inicializa classe do objeto Sync #####################################
        super(Charger, self).__init__(selfNodeAddr, otherNodeAddrs, cfg)
        ####################### Configuração dos parâmetros do carregador ############################
        self.config_params = self.get_config_from_db(selfNodeAddr)
        self.id = self.config_params.evse_id
        self.__cur_power = 0 #Reads from the energy Meter
        self.__max_power = 7360 #Limit of power selected by the schedule
        self.__nom_power = 7360 #Nominal power limit on the EVSE
        self.__min_power = 1380 #Potência mínima permitida no EVSE
        self.__max_cluster_power = 0
        self.__cluster_size = len(otherNodeAddrs) + 1
        self.__count_plugged_chargers = 0
        self.__count_auth_chargers = 0
        self.__schedule = Schedule(evse_id=self.id,
                                   id=1,
                                   charging_rate_unit="W",
                                   duration=0,
                                   charging_schedule_period=[{'startPeriod': datetime.now() ,'limit': self.__nom_power}])
        self.__executed_schedule = Schedule(evse_id=self.id,
                                            id=1,
                                            charging_rate_unit="W",
                                            duration=0,
                                            charging_schedule_period=[{'startPeriod': datetime.now() ,'limit': self.__nom_power}])
        #Dado que será replicado entre os nós
        self.__cluster_ids = {}
        self.evse_data_sim = self.get_my_sim_parameters_from_db(self.id)
        self.__cluster_sim_params = { self.id: self.evse_data_sim,}
        self.schedule_parameters = self.get_schedule_params_from_db(self.id)
        self.__sched_cluster_parameters = { self.id: self.schedule_parameters,}

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
    def get_schedule_params_from_db(self, evse_id):
        # Verifica se o plug está conectado
        db = SessionLocal()
        sched_row = db.query(ClusterSincDataTable).filter(ClusterSincDataTable.evse_id == evse_id).first()
        #print(sched_row.planned_departure)
        if sched_row:
            sched_data = {
                "selected_max_power": sched_row.selected_max_power,
                #"planned_departure": sched_row.planned_departure,
                "user_id": sched_row.user_id,
                "session_id": sched_row.session_id,
                "evse_id": sched_row.evse_id,
                "max_cluster_power": sched_row.max_cluster_power
            }

            schedule = ClusterSincData(**sched_data)
            db.commit()
            db.close()
            return schedule
        #TODO: Cannot return None
        else:
            logging.error(f"GET_SCHEDULE_FROM_DB: EVSE not found in the database for evse_id: {evse_id}")
            return None
        
    def get_my_sim_parameters_from_db(self, evse_id):
        #Deve atualizar somente dados que  que não serão atualizados na dinâmica do código
        evse_data_sim = None
        try:
            # Verifica se o plug está conectado
            db = SessionLocal()
            evse_row = db.query(EvseDataSimTable).where(EvseDataSimTable.evse_id == evse_id).first()

            if evse_row:
                charger_data = {
                    "plug_status": evse_row.plug_status,
                    "authenticated": evse_row.authenticated,
                    "user_id": evse_row.user_id,
                    "session_id": evse_row.session_id,
                    "evse_id": evse_row.evse_id,
                    "max_cluster_power": evse_row.max_cluster_power
                }

            evse_data_sim = EvseDataSim(**charger_data)
            db.commit()
            return evse_data_sim

        except sqlalchemy.exc.TimeoutError:
            # Handle the TimeoutError, create a new session, and try again
            print("TimeoutError: Reconnecting to the database...")
            db = SessionLocal()
            evse_row = db.query(EvseDataSimTable).where(EvseDataSim.evse_id == evse_id).first()

            if evse_row:
                charger_data = {
                    "plug_status": evse_row.plug_status,
                    "authenticated": evse_row.authenticated,
                    "user_id": evse_row.user_id,
                    "session_id": evse_row.session_id,
                    "evse_id": evse_row.evse_id,
                    "max_cluster_power": evse_row.max_cluster_power
                }

            evse_data_sim = EvseDataSim(**charger_data)
            db.commit()
            return evse_data_sim

        finally:
            print(evse_data_sim)
            # Make sure to close the session after using it
            if db:
                db.close()
    
    def set_schedule_params_on_db(self):
        # Verifica se o plug está conectado
        db = SessionLocal()
        sched_row = db.query(ClusterSincDataTable).filter(ClusterSincDataTable.evse_id == self.id).first()

        if sched_row:
            sched_row.selected_max_power = self.__sched_cluster_parameters[self.id].selected_max_power
            #sched_row.planned_departure = self.__sched_cluster_parameters[self.id].planned_departure
            sched_row.user_id = self.__sched_cluster_parameters[self.id].user_id
            sched_row.session_id = self.__sched_cluster_parameters[self.id].session_id
            sched_row.evse_id = self.id
            sched_row.max_cluster_power = self.__sched_cluster_parameters[self.id].max_cluster_power
            db.commit()
            db.close()
        else:
            print("EVSE not found in the database.")
            return None
    #Metodo para obter o id do carregador fora da classe
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
        self.__cluster_sim_params[evse_id] = params
    
    @replicated
    def update_sim_params_to_cluster(self, evse_id, params:EvseDataSim):
        self.__cluster_sim_params.update({evse_id:params})
    
    def get_sim_cluster_params(self):
        return self.__cluster_sim_params
    """
    Adiciona os dados de scheduling inicialmente de cada nó para que o lider saiba quais nós estão conectados
    """
    @replicated
    def add_my_sched_params_to_cluster(self, evse_id ,params:ClusterSincData):
        self.__sched_cluster_parameters[evse_id] = params
    """
    Adiciona os dados de scheduling criado pelo lider a todos os nós
    """
    @replicated
    def update_sched_params_on_cluster(self, evse_id:str, params:ClusterSincData):
        self.__sched_cluster_parameters.update({evse_id:params})

    def get_sched_cluster_params(self):
        return self.__sched_cluster_parameters
    
    def get_selected_max_power(self):
        self.__sched_cluster_parameters = self.__sched_cluster_parameters[self.id].selected_max_power
        return self.__sched_cluster_parameters
        #Metodo para obter os dados do cluster fora da classe
    

    #Função utilizada para o lider para no momento de calcular a divisão de potência considerar os 
    #Carregadores conectados 
    def count_plugged_chargers(self):
        i = 0
        if self.__cluster_sim_params:
            for charger in self.__cluster_sim_params:
                if self.__cluster_sim_params[charger].plug_status == "plugged_not_charging" or "charging":
                    i += 1
            self.__count_plugged_chargers = i
        return self.__count_plugged_chargers
    
    def count_auth_chargers(self):
        i = 0
        evse_id = ""
        if self.__cluster_sim_params:            #Itera por todos os outros nós do grupo
            for node in self.otherNodes:
                #Se o nodo estiver conectado ao grupo
                if self.isNodeConnected(node):
                    if str(node.address) in self.__cluster_ids:
                        evse_id = self.__cluster_ids[str(node.address)]
                    #Verifica se está autenticado
                    if evse_id in self.__cluster_sim_params:
                        if self.__cluster_sim_params[evse_id].user_id > 0:
                            i += 1
            #Adiciona verificação de autenticação do próprio carregador
            if self.__cluster_sim_params[self.id].user_id > 0:
                self.__count_auth_chargers = i + 1
            else:
                self.__count_auth_chargers = i 
        return self.__count_auth_chargers
    
    def count_connected_nodes(self):
        connected_nodes = 0
        if self.isNodeConnected(self.selfNode):
            connected_nodes += 1
            for node in self.otherNodes:
                if self.isNodeConnected(node):
                    connected_nodes += 1
        return connected_nodes

    # def remove_not_connected_node(self):
    #     connected_nodes = self.count_connected_nodes()
    #     if connected_nodes != len(self.__cluster_ids):
            #Significa que existe algum nó a ma

    
    #Função que calcula a divisão de potência entre os carregadores         
    def calculate_schedule(self, max_power_cluster):
        self.__count_plugged_chargers = self.count_plugged_chargers()
        self.__count_auth_chargers = self.count_auth_chargers()
        try:
            #Update the schedule variables with the most updated values
            self.__sched_cluster_parameters[self.id].max_cluster_power = max_power_cluster #Informação que vem do lider
            self.__sched_cluster_parameters[self.id].session_id = self.__cluster_sim_params[self.id].session_id
            self.__sched_cluster_parameters[self.id].evse_id = self.__cluster_sim_params[self.id].evse_id
            self.__sched_cluster_parameters[self.id].user_id = self.__cluster_sim_params[self.id].user_id
            #Lista os carregadores existentes
            evse_id_list = self.__cluster_sim_params.keys()
            #Se estiver algum carregador autenticado e se o carregador atual está autenticado
            if self.__count_auth_chargers > 0 and self.__cluster_sim_params[self.id].user_id > 0:
                calc_power = max_power_cluster / self.__count_auth_chargers
                #Para os carregadores não autenticados
                #Verifica se está incluida nas variáveis de contexto do cluster
                if self.id in evse_id_list:
                    #O maximo de potência calculada não pode ser mais do que o máximo nominal
                    if calc_power > self.__nom_power:
                        self.__sched_cluster_parameters[self.id].selected_max_power = self.__max_power
                    else:
                        self.__sched_cluster_parameters[self.id].selected_max_power = calc_power
                #Atualiza os dados de sessão individuais no grupo de carregadores
                else:
                    session_params = self.get_my_sim_parameters_from_db(self.id)
                    self.update_sim_params_to_cluster(self.id,session_params)
            else: 
                self.__sched_cluster_parameters[self.id].selected_max_power = 0
            self.update_sched_params_on_cluster(self.id, self.__sched_cluster_parameters[self.id])
            #Atualiza base de dados com schedule calculado individud
            db = SessionLocal()
            sched_row = db.query(ClusterSincDataTable).filter(ClusterSincDataTable.evse_id == self.id).order_by(ClusterSincDataTable.register_id.desc()).first()
            if sched_row:
                sched_row.max_cluster_power = self.__sched_cluster_parameters[self.id].max_cluster_power
                sched_row.selected_max_power = self.__sched_cluster_parameters[self.id].selected_max_power
                sched_row.user_id = self.__sched_cluster_parameters[self.id].user_id
                db.commit()
                db.close()
            else:
                self.set_schedule_params_on_db()
        except Exception as error:
            logging.error(f"CALCULATE_SCHEDULE: {str(e)}")
        finally:
            return self.__sched_cluster_parameters
    
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
    
if __name__ == '__main__':
    if len(sys.argv) < 1:
        print('Usage: %s evse_hostname_id ...' % sys.argv[0])
        sys.exit(-1)
    evse_id = str(sys.argv[1])
    #port = int(sys.argv[2])
    o = Charger(evse_id=evse_id)
    n = 0
    max_power_cluster = 0
    my_address = str(o.selfNode.address)
    my_evse_id = o.id
    o.add_id_to_cluster(my_address, my_evse_id)
    o.addNodeToCluster(o.selfNode, callback=partial(onAdd))
    # try:
    while True:
        #Condição que só permite começar quando tiver algum lider
        if o._getLeader() is None:
            continue
        #Update local variable
        cluster_evse_data_sim = o.get_sim_cluster_params()
        cluster_sinc_data = o.get_sched_cluster_params()

        o.update_id_to_cluster(address=o.selfNode.address, id=o.id)
        print(f"MY ID on begging of cycle: {o.get_my_evse_id()}")
        #Mantem atualizado no cluster as variáveis que determinam contexto no carregador
        dict_ids = o.get_cluster_ids()
        if my_address in dict_ids:
            my_evse_id = dict_ids[my_address]
            o.update_sim_params_to_cluster(my_evse_id, o.get_my_sim_parameters_from_db(my_evse_id))
        if my_address not in o.get_sched_cluster_params():
            o.add_my_sched_params_to_cluster(my_evse_id, o.get_schedule_params_from_db(my_evse_id))
    
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
                sched_parameters = o.calculate_schedule(o.get_sim_cluster_params()[leader_evse_id].max_cluster_power)
                print(sched_parameters)
            #Repassa o schedule para o cluster
            #Atualização dos dados do cluster baseado no calculo de replicação do sistema
            if my_evse_id in o.get_sched_cluster_params():
                o.update_sched_params_on_cluster(
                    evse_id=my_evse_id, 
                    params=o.get_sched_cluster_params()[my_evse_id])

        if o.hasQuorum == False:
            #Repassa o valor para o cluster 
            o.evse_data_sim = o.get_my_sim_parameters_from_db(my_evse_id)
            sched_parameters = o.calculate_schedule(o.evse_data_sim.max_cluster_power)
            #Repassa o schedule para o cluster
            #Atualização dos dados do cluster baseado no calculo de replicação do sistema
            if my_evse_id in o.get_sched_cluster_params():
                o.update_sched_params_on_cluster(
                    evse_id=my_evse_id, 
                    params=sched_parameters)
            #Carregador está sozinho
        #########################################################################################################
        ############################################# FOLLOWER ##################################################
        #Se for FOLLOWER executa as funções dentro da condição
        #if str(o.getStatus()["leader"]) != str(o.selfNode.address):
        if my_evse_id in cluster_sinc_data:
            o.schedule_parameters = cluster_sinc_data[my_evse_id]
            print(f"MAX_CLUSTER_POWER: {o.schedule_parameters.max_cluster_power}")
            print(f"POWER ON NODE: {o.schedule_parameters.selected_max_power}")
        # Estatisticas RAFT
        # leader = o.getStatus()["leader"]
        # partners_count = o.getStatus()["partner_nodes_count"]
        # raft_term = o.getStatus()["raft_term"]


        # print(f"POWER DISTRIBUTION: {o.get_sched_cluster_params()}")
        # print(f"LEADER: {leader}")
        # print(f"PARTNERS COUNT: {partners_count}")
        # print(f"RAFT TERM: {raft_term}")

        #Atualiza na base de dados os valores do schedule individuais de acordo com a variável comum ao cluster
        #o.set_schedule_params_on_db()

        n += 1
        time.sleep(3)
    # except Exception as error:
    #     logging.error(f"Error in main loop of {my_evse_id}: {str(error)}")
    """ 
    except KeyboardInterrupt as error:
        o.removeNodeFromCluster(o.selfNode, callback=partial(onRemove))
        o.update_sim_params_to_cluster(evse_id=my_evse_id, 
                                       params=EvseDataSim(plug_status="not_plugged",
                                                                    authenticated=False,
                                                                    user_id=0,
                                                                    session_id="00000000000000",
                                                                    evse_id=my_evse_id,
                                                                    max_cluster_power=0))
        print("Keyboard Interruption")
    """
