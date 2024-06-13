#!/usr/bin/env python
from __future__ import print_function

import sys
import time
from functools import partial
sys.path.append("../")
from pysyncobj import SyncObj, replicated, SyncObjConf

from ocpp.charge_point import ChargePoint as CP_BASIC
#from ocpp_v201.ocpp_server import CSMS
#from ocpp_v201.ocpp_server import *

from ocpp_server import *
import configparser

try:
    import websockets
except ModuleNotFoundError:
    print("This example relies on the 'websockets' package.")
    print("Please install it by running: ")
    print()
    print(" $ pip install websockets")
    import sys
    sys.exit(1)

class ChargePointManagementNode(SyncObj):
    '''
    Essa classe herda caracteristicas da classe charge point da biblioteca OCPP que permite implementar 
    troca de mensagens e gestão das sessões de carregamento de forma local, deve cumprir as seguintes funções:
    1. Receber mensagens OCPP v201 das unidades de carregamento
    2. Ativar e desativar as funções de gestão baseado no algoritmo Raft adicionando redundância ao sistema
    3. Quando mudar do estado CANDIDATE para LEADER, se tornar o lider, deve manter continuar o processo de gestão das sessões de carregamento de onde estava 
    4. Quando se tornar o lider deve informar o novo endereço a rede informar o novo endereço em que está a operar
    4. Deve ser capaz de remover e adicionar nós automaticamente a medida que esses se conectem na rede local (DynamicMembershipChange)
    5. Terá o endereço e porta para comunicação TCP do Raft e endereço e porta para comunicação OCPP por websockets
    '''
    cfg = SyncObjConf(
            autoTick=True,
            appendEntriesUseBatch=False,
            commandsWaitLeader=True, #Commands will be queued to be futher processed by the leader
            dynamicMembershipChange=False, #To allow changes on the nodes,
            #raftMinTimeout=1,
            #raftMaxTimeout=2,
            #appendEntriesPeriod=0.5, #Permite que 100 AppendTries sejam realizados por segundo (5 milisegundos para cada envio)
            #connectionTimeout=3.5,
            #connectionRetryTime=5.0,
            #leaderFallbackTimeout=30.0,
            journalFile=None,
            #tcp_keepalive = (16, 3, 10)
            )
    def __init__(self, selfNodeAddr, otherNodeAddrs):
        super(ChargePointManagementNode, self).__init__(selfNodeAddr, otherNodeAddrs)
        self.__id = "001"
        self.selfNodeAddr = selfNodeAddr
        self.otherNodeAddrs = otherNodeAddrs
        self.port = self.selfNode.port
        self.interval = None
        #TODO: Replicar os ids e conexões entre os servidores e 
        #      quando mudar de um para o outro já terão os dados de conexão
        self.csms_instances = []
        self.cp_ids = [] #IDs de pontos de carregamento que se conectam
        self.websockets_conn = [] #Conexões websockets criadas entre CSMS e CPs
        self.server = None
        
    #################################### RAFT segment ################################
    def add_node_to_cluster(self, node):
        '''
        No momento que um cliente envia uma mensagem de boot notification valida
        e sendo o atual lider do grupo no momento que a mensagem é enviada
        * Se não for o lider mas receber a mensagem repassar para o lider 
            e informar o cliente do endereço do lider atual
        '''
        #:param node: node object or 'nodeHost:nodePort'
        self.addNodeToCluster(node)

    def remove_node(self,node):
        '''
        No caso de perda de conexão por um determinado tempo (OfflineThreshold)
        e sendo o atual lider do grupo no momento que o tempo expira
        '''
        #:param node: node object or 'nodeHost:nodePort'
        self.removeNodeFromCluster(node)

    def get_leader(self):
        return self._getLeader()
    
    #################################### OCPP segment ###########################################
    
    async def on_connect(self, websocket, path):
        """For every new charge point that connects, create a ChargePoint
        instance and start listening for messages.
        """
        try:
            requested_protocols = websocket.request_headers["Sec-WebSocket-Protocol"]
        except KeyError:
            logging.error("Client hasn't requested any Subprotocol. Closing Connection")
            return await websocket.close()
        if websocket.subprotocol:
            logging.info("Protocols Matched: %s | %s", websocket.subprotocol, path)
        else:
            # In the websockets lib if no subprotocols are supported by the
            # client and the server, it proceeds without a subprotocol,
            # so we have to manually close the connection.
            logging.warning(
                "Protocols Mismatched | Expected Subprotocols: %s,"
                " but client supports %s | Closing connection",
                websocket.available_subprotocols,
                requested_protocols,
            )
            return await websocket.close()
        
        #Charge point instantiantion
        charge_point_id = path.strip("/")
        charge_point = CSMS(charge_point_id, websocket)

        #Armazenar informações internas
        self.csms_instances.append(charge_point)
        self.cp_ids.append(charge_point_id)
        self.websockets_conn.append(websocket)

        await charge_point.start()

    async def csms_routine(self):
        #  deepcode ignore BindToAllNetworkInterfaces: <Example Purposes>
        while True:
            port = self.port + random.randint(50,100)
            if not self.server and (self._isLeader() or self._getLeader() is None):
                self.server = await websockets.serve(
                    self.on_connect, "0.0.0.0", port, subprotocols=["ocpp2.0.1"],ping_interval=None
                )
                logging.info("Server Started listening to new connections...")
                await self.server.wait_closed()
            await asyncio.sleep(1.5)
    
    async def close_csms_connections(self):
        curr_leader = self.get_leader()
        old_leader = curr_leader
        new_leader = False
        while True:
            curr_leader = self.get_leader()
            new_leader = True if curr_leader != old_leader else False
            if curr_leader == None:
                print("ONLY SERVER GET LEADER NONE") if new_leader else None
            else:
                if self._isLeader():
                    #Activate or Start CSMS functionality
                    #This device is the leader
                    print("SERVER IS THE LEADER ") if new_leader else None
                else:
                    #Stop CSMS functionality
                    #This device is NOT the leader
                    print("SERVER IS NOT THE LEADER ") if new_leader else None
                    if self.server:
                        self.server.close()
                        await self.server.wait_closed()
                        self.server = None
            old_leader = curr_leader
            await asyncio.sleep(1)
            
    ######################## End of ChargePointManagementNode class #############################

async def raft_routine(server_node:ChargePointManagementNode, selfNodeAddr, otherNodeAddrs):
    '''
    Essa rotina não executa a gestão do raft, mas operações relacionadas a replicação de dados na rede
    '''
    o = server_node
    while True:
        leader = o.getStatus()["leader"]
        partners_count = o.getStatus()["partner_nodes_count"]
        raft_term = o.getStatus()["raft_term"]
        #print(f"LEADER: {leader}")
        #print(f"PARTNERS COUNT: {partners_count}")
        #print(f"RAFT TER: {raft_term}")
        await asyncio.sleep(2)
        if o._getLeader() is None:
            continue

async def main(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    
    if 'MY_ADDR' not in config or 'PARTNERS_ADDR' not in config:
        print('Error: [MY_ADDR] or [PARTNERS_ADDR] section not found in cluster_init_conf.ini')
        sys.exit(-1)
    
    my_address = config['MY_ADDR'].get('self')
    if not my_address:
        print('Error: No self address found in the [MY_ADDR] section of cluster_init_conf.ini')
        sys.exit(-1)
    
    partners = [config['PARTNERS_ADDR'][key] for key in config['PARTNERS_ADDR']]
    
    server_node = ChargePointManagementNode(my_address, partners)

    server_start_task = asyncio.create_task(server_node.csms_routine())
    raft_task = asyncio.create_task(raft_routine(server_node,server_node.selfNodeAddr, server_node.otherNodeAddrs))
    close_csms_conn = asyncio.create_task(server_node.close_csms_connections())

    await asyncio.gather(raft_task, server_start_task, close_csms_conn)

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print('Usage: %s config_path' % sys.argv[0])
        sys.exit(-1)

    config_path = sys.argv[1]
    asyncio.run(main(config_path))