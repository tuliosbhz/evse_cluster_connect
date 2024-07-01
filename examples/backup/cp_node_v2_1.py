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
        self.active_nodes = None
        logging.info(f"MY_ADDRESS: {self.raft_node}")
        logging.info(f"CLUSTER FOR EXPERIMENT: {self.raft_cluster}")
        self.active_nodes = raftos.ReplicatedDict(name="active_nodes")
        self.active_ocpp_servers = raftos.ReplicatedDict(name="active_ocpp_servers")


    async def raft_start(self):
        """
        Responsável por:
        - registar um novo cluster 
        - Inicializar os dados replicados
        - Informa a outros nós que o nó raft está ativo

        Inicializa todos os nós configurados como ativos e os 
        próprios nós quando se desligam se desativam
        """
        for node in self.raft_cluster:
            if self.raft_node in str(node):
                active_nodes = {
                    str(node): 1
                }
            else:
                active_nodes = {
                    str(node): 1
                }
            active_ocpp = {
                    str(node): 0
                }
        await self.active_nodes.update(active_nodes)
        await self.active_ocpp_servers.update(active_ocpp)

    async def raft_stop(self):
        """
        Responsável por:
        - Atualizar os dados replicados finalizando contribuição
        - finalizar o nó no cluster
        - Informa a outros nós quando o nó raft não está mais ativo
        """
        self.active_nodes[self.raft_node] = 0
        await self.active_nodes.update(self.active_nodes)

    async def raft_routine(self):
        """
        Responsável por:
        - Mantem os dados replicados atualizados
        """
        try:
            await self.raft_start()
            while True:
                print("Atualiza dados replicados")
                #Check the charging session errors to 
                # activate more than one OCPP server

        except Exception as e:
            await self.raft_stop()

    async def on_connect(self, websocket, path):
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

    async def open_connections(self):
        self.server = await websockets.serve(
            self.on_connect, "0.0.0.0", self.port, subprotocols=["ocpp2.0.1"], ping_interval=None
        )
        logging.info("Server Started listening to new connections...")
        await self.server.wait_closed()

    async def csms_routine(self):
        old_leader = ""
        while True:
            leader = raftos.get_leader()
            logging.info(f"CLUSTER COUNT: {self.active_nodes[0].cluster_count}")
            if leader != old_leader:
                logging.info(f"Current Leader: {leader}")
                if leader == self.raft_node:
                    #if not self.server:
                    csms_task = asyncio.create_task(self.open_connections())
                    await asyncio.sleep(0.5)
                else:
                    if self.server:
                        self.server.close()
                        await self.server.wait_closed()
                        self.server = None
            old_leader = leader
            await asyncio.sleep(0.8)

    async def raft_routine(self):
        was_leader = False
        while True:
            leader = raftos.get_leader()
            if leader is None:
                if not was_leader:
                    logging.info(f"Current Leader: {leader}")
                    metrics_logger.start_election()
                    was_leader = True
            else:
                if was_leader:
                    logging.info(f"Current Leader: {leader}")
                    metrics_logger.end_election()
                    was_leader = False
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

async def cluster_dinamic_membership_change(node):
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
            server_node.active_nodes = await raftos.register(server_node.raft_node, cluster=server_node.raft_cluster) if my_address in cluster else logging.error(f"Node not on cluster: {my_address}")
            server_start_task = asyncio.create_task(server_node.csms_routine())
            #raft_rou_task = asyncio.create_task(server_node.raft_routine())
            failure_task = asyncio.create_task(self.simulate_failures(server_node,
                                                                      heartbeat,
                                                                      step_down,
                                                                      election_spread))

            logging.info(f"Starting experiment with heartbeat={heartbeat}, step_down={step_down}, election_spread={election_spread}")
            asyncio.gather(server_start_task, failure_task)
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
