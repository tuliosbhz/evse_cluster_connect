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
            'heartbeat_interval': 0.01,
            'step_down_missed_heartbeats': 5,
            'election_interval_spread': 3
        })
        self.raft_node = selfNodeAddr
        self.raft_cluster = nodeAddrs
        logging.info(f"CLUSTER FOR EXPERIMENT: {self.raft_cluster}")

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
        while True:
            leader = raftos.get_leader()
            if leader == self.raft_node:
                if not self.server:
                    csms_task = asyncio.create_task(self.open_connections())
                    await asyncio.sleep(0.5)
            else:
                if self.server:
                    self.server.close()
                    await self.server.wait_closed()
                    self.server = None
            await asyncio.sleep(1.5)

    async def raft_routine(self):
        was_leader = False
        while True:
            leader = raftos.get_leader()
            logging.info(f"Current Leader: {leader}")
            if leader is None:
                if not was_leader:
                    metrics_logger.start_election()
                    was_leader = True
            else:
                if was_leader:
                    metrics_logger.end_election()
                    was_leader = False
            await asyncio.sleep(2)

    async def close(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()

async def simulate_failure(node):
    metrics_logger.record_failure()
    start_recovery_time = time.time()
    raftos.stop()
    await asyncio.sleep(5)  # Simula tempo de falha
    await raftos.register(node.raft_node, cluster=node.raft_cluster)
    end_recovery_time = time.time()
    metrics_logger.record_repair()
    metrics_logger.downtime += end_recovery_time - start_recovery_time - 5  # Ajusta o tempo de recuperação

class ExperimentManager:
    def __init__(self, config_path, duration=120):
        self.config_path = config_path
        self.duration = duration
        self.raft_params = {
            'heartbeat_interval': [0.01, 0.1, 0.5, 1, 2],
            'step_down_missed_heartbeats': [2, 4, 6, 8, 10],
            'election_interval_spread': [2, 4, 6, 8, 10],
            'num_nodes': [2, 3, 4, 5]
        }

    async def run_experiments(self):
        for heartbeat in self.raft_params['heartbeat_interval']:
            for step_down in self.raft_params['step_down_missed_heartbeats']:
                for election_spread in self.raft_params['election_interval_spread']:
                    await self.run_experiment(heartbeat, step_down, election_spread)

    async def run_experiment(self, heartbeat, step_down, election_spread):
        raftos.configure({
            'log_path': './',
            'serializer': raftos.serializers.JSONSerializer,
            'heartbeat_interval': heartbeat,
            'step_down_missed_heartbeats': step_down,
            'election_interval_spread': election_spread
        })

        config = configparser.ConfigParser()
        config.read(self.config_path)

        my_address = config['MY_ADDR'].get('self')
        cluster = [config['NODES_ADDR'][key] for key in config['NODES_ADDR']]
  
        server_node = ChargePointManagementNode(my_address, cluster, int(config['SERVER_CONFIG']['port']))

        try:
            server_start_task = asyncio.create_task(server_node.csms_routine())
            raft_reg_task = asyncio.create_task(raftos.register(server_node.raft_node, cluster=server_node.raft_cluster)) if my_address in cluster else None
            raft_rou_task = asyncio.create_task(server_node.raft_routine())
            failure_task = asyncio.create_task(self.simulate_failures(server_node))

            logging.info(f"Starting experiment with heartbeat={heartbeat}, step_down={step_down}, election_spread={election_spread}")

            await asyncio.sleep(self.duration)
        finally:
            metrics_logger.log_raft_metrics(heartbeat, step_down, election_spread)

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

    async def simulate_failures(self, server_node):
        while True:
            await asyncio.sleep(300)  # Simula falhas a cada 5 minutos
            await simulate_failure(server_node)

async def main(config_path):
    experiment_manager = ExperimentManager(config_path)
    await experiment_manager.run_experiments()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: %s config_path' % sys.argv[0])
        sys.exit(-1)

    config_path = sys.argv[1]
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(config_path))
