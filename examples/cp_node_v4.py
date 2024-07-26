import sys
import os

# Adicionar o diretório raiz do projeto ao caminho do sistema
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

import time
import csv
import asyncio
import configparser
import logging
import websockets
from websockets import serve

import raftos
from metrics_logger import MetricsLogger
from ocpp_server_bench import *

# Inicialização do metrics_logger
metrics_logger = MetricsLogger()

class ChargePointManagementNode:
    def __init__(self, selfNodeAddr:str, nodeAddrs:list, port):
        self.port = port
        self.server = None
        raftos.configure({
            'log_path': './',
            'serializer': raftos.serializers.JSONSerializer,
            'heartbeat_interval': 0.1,
            'step_down_missed_heartbeats': 5,
            'election_interval_spread': 3
        })
        self.raft_node = selfNodeAddr
        self.raft_cluster = nodeAddrs
        logging.info(f"MY_ADDRESS: {self.raft_node}")
        logging.info(f"CLUSTER FOR EXPERIMENT: {self.raft_cluster}")
        self.active_ocpp_servers = None #raftos.ReplicatedDict(name="active_ocpp_servers")


    async def raft_start(self):
        """
        Responsável por:
        - registar um novo cluster 
        - Inicializar os dados replicados
        - Informa a outros nós que o nó raft está ativo

        Inicializa todos os nós configurados como ativos e os 
        próprios nós quando se desligam se desativam
        """
        await raftos.register(self.raft_node, cluster=self.raft_cluster)


    async def raft_stop(self):
        """
        Responsável por:
        - Atualizar os dados replicados finalizando contribuição
        - finalizar o nó no cluster
        - Informa a outros nós quando o nó raft não está mais ativo
        """
        #await self.active_nodes.update({str(self.raft_node): 0})
        #await self.active_ocpp_servers.update({str(self.raft_node): 0})

    async def on_ocpp_client_connect(self, websocket, path):
        try:
            requested_protocols = websocket.request_headers["Sec-WebSocket-Protocol"]
        except KeyError:
            logging.error("Client hasn't requested any Subprotocol. Closing Connection")
            return await websocket.close()
        if websocket.subprotocol:
            logging.info("Protocols Matched: %s | %s", websocket.subprotocol, path)
        else:
            logging.warning(
                "Protocols Mismatched | Expected Subprotocols: %s,"
                " but client supports %s | Closing connection",
                websocket.available_subprotocols,
                requested_protocols,
            )
            return await websocket.close()

        charge_point_id = path.strip("/")
        charge_point = CSMS(charge_point_id, websocket)

        await charge_point.start()

    async def activate_ocpp_server(self):
        self.server = await websockets.serve(
            self.on_ocpp_client_connect, "0.0.0.0", self.port, subprotocols=["ocpp2.0.1"], ping_interval=None
        )
        logging.info("Server Started listening to new connections...")
        await self.server.wait_closed()

    async def csms_routine(self):
        last_leader = ""
        max_time_experiment = 4 * 3600 #4 hours
        try:
            for i in range(max_time_experiment):
                current_leader = raftos.get_leader()
                if last_leader != current_leader:
                    logging.info(f"NEW LEADER: {current_leader}")
                    last_leader = current_leader
                    if current_leader:
                        if self.raft_node == current_leader:
                            if not self.server:
                                csms_task = asyncio.create_task(self.activate_ocpp_server())
                                await asyncio.sleep(0.5)
                        else:
                            if self.server:
                                self.server.close()
                                await self.server.wait_closed()
                                self.server = None
                if i % 60 == 0: #1 minute between records
                    metrics_logger.log_raft_metrics(0.1 ,5, 3)
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logging.info("csms_routine has been cancelled")
        finally:
            return

    async def close(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

async def run_experiment(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)

    my_address = config['MY_ADDR'].get('self')
    cluster = [config['NODES_ADDR'][key] for key in config['NODES_ADDR']]
    ip, port = my_address.split(':')
    ip = ip.split(".")[-1]
    metrics_logger.raft_file_name = f"benchmark_{ip}_{port}_raft_{datetime.now().strftime('%m-%d-%Y')}.csv"
    server_node = ChargePointManagementNode(my_address, cluster, int(config['SERVER_CONFIG']['port']))
    try:
        await server_node.raft_start()
        await server_node.csms_routine()
        #server_start_task = asyncio.create_task()
        #logging.info(f"Starting experiment with heartbeat={heartbeat}, step_down={step_down}, election_spread={election_spread}")
        #await asyncio.gather(server_start_task)
    except Exception as e:
        await server_node.raft_stop()
        logging.error(f"On run_experiment: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: %s config_path' % sys.argv[0])
        sys.exit(-1)

    config_path = sys.argv[1]
    
    logging.basicConfig(level=logging.INFO)
    asyncio.run(run_experiment(config_path))
