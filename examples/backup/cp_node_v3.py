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
        self.active_ocpp_servers = raftos.ReplicatedDict(name="active_ocpp_servers")
        leader = raftos.get_leader()
        if self.raft_node in self.raft_cluster and self.raft_node == leader:
            await self.active_ocpp_servers.update({str(self.raft_node): 0})
        else:
            logging.warning(f"Node not on cluster: {self.raft_node}  or not the leader {leader}")


    async def raft_stop(self):
        """
        Responsável por:
        - Atualizar os dados replicados finalizando contribuição
        - finalizar o nó no cluster
        - Informa a outros nós quando o nó raft não está mais ativo
        """
        #await self.active_nodes.update({str(self.raft_node): 0})
        #await self.active_ocpp_servers.update({str(self.raft_node): 0})

    async def raft_routine(self):
        """
        Responsável por:
        - Mantem os dados replicados atualizados
        """
        old_leader = ""
        while True:
            try:
                leader = raftos.get_leader()
                if leader != old_leader and leader is not None:
                    old_leader = leader
                    logging.info(f"Current Leader: {leader}")
                    if leader == self.raft_node:
                        await self.active_ocpp_servers.update({str(self.raft_node): 1})                    
                await asyncio.sleep(0.8)
            except Exception as e:
                await self.raft_stop()

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
        while True:
            active_servers_dict = dict(self.active_ocpp_servers)
            logging.info(active_servers_dict)
            if active_servers_dict[self.raft_node] == 1:
                    csms_task = asyncio.create_task(self.activate_ocpp_server())
                    await asyncio.sleep(0.5)
            else:
                if self.server:
                    self.server.close()
                    await self.server.wait_closed()
                    self.server = None
                await asyncio.sleep(1)

    async def close(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

async def simulate_failure(node):
    logging.warning("SIMULATE FAILURE ON RAFT")
    metrics_logger.record_failure()
    start_recovery_time = time.time()
    raftos.stop()
    await asyncio.sleep(1)  # Simula tempo de falha
    await raftos.register(node.raft_node, cluster=node.raft_cluster)
    end_recovery_time = time.time()
    metrics_logger.record_repair()
    metrics_logger.downtime += end_recovery_time - start_recovery_time - 5  # Ajusta o tempo de recuperação

class ExperimentManager:
    def __init__(self, config_path, duration=1200):
        self.config_path = config_path
        self.duration = duration
        self.heartbeat = 0.1
        self.step_down_leader = 5
        self.election_interval = 3
        self.log_timing = 120
        self.failures_multiplier = 3 #Multiplica pelo intervalo entre falhas 3 * log_timing
        self.failures_counter = 0

    async def run_experiments(self):
        while True:
            await self.run_experiment(self.heartbeat, self.step_down_leader, self.election_interval)
            #metrics_logger.log_raft_metrics(self.heartbeat, self.step_down_leader, self.election_interval)
            await asyncio.sleep(5)

    async def run_experiment(self, heartbeat, step_down, election_spread):
        config = configparser.ConfigParser()
        config.read(self.config_path)

        my_address = config['MY_ADDR'].get('self')
        cluster = [config['NODES_ADDR'][key] for key in config['NODES_ADDR']]

        server_node = ChargePointManagementNode(my_address, cluster, int(config['SERVER_CONFIG']['port']))

        try:
            await server_node.raft_start()
            server_start_task = asyncio.create_task(server_node.csms_routine())
            raft_rou_task = asyncio.create_task(server_node.raft_routine())
            failure_task = asyncio.create_task(self.simulate_failures(server_node,
                                                                      heartbeat,
                                                                      step_down,
                                                                      election_spread))

            logging.info(f"Starting experiment with heartbeat={heartbeat}, step_down={step_down}, election_spread={election_spread}")
            asyncio.gather(raft_rou_task, server_start_task, failure_task)
            await asyncio.sleep(self.duration)
        except Exception as e:
            logging.error(e)
            """ 
            # Cancel tasks after the experiment duration
            for task in [raft_reg_task, raft_rou_task, server_start_task, failure_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logging.warning(e)
            # Ensure all connections are closed
            await server_node.close()
            """

    async def simulate_failures(self, server_node, raft_heart, raft_step_down, raft_election_spread):
        while True:
            #Gaussiana com media em 120 segundos com desvio padrão de X segundos
            await asyncio.sleep(120)  # Simula falhas a cada 2 minutos se for o lider e dobra o tempo a cada falha
            metrics_logger.log_raft_metrics(raft_heart,raft_step_down, raft_election_spread)
            if self.failures_counter == self.failures_multiplier:
                self.failures_counter = 0 #Reset failure counter
                current_leader = raftos.get_leader()
                if server_node.raft_node == current_leader:
                    await simulate_failure(server_node)
                    self.failures_multiplier = 2 * self.failures_multiplier #Double the time to the next failure
            else:
                self.failures_counter += 1
            

async def main(config_path):
    experiment_manager = ExperimentManager(config_path, 1200)
    await experiment_manager.run_experiment(heartbeat=0.1,
                                            step_down=5,
                                            election_spread=3)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: %s config_path' % sys.argv[0])
        sys.exit(-1)

    config_path = sys.argv[1]
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(config_path))
