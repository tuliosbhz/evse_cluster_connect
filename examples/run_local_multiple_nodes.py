import sys
import os
import asyncio
import logging
from multiprocessing import Process

from cp_node_v301 import ChargePointManagementNode, ExperimentManager

# Adicionar o diretório raiz do projeto ao caminho do sistema
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

# Inicialização do logging
logging.basicConfig(level=logging.INFO)

def create_node_config(node_index, base_port):
    """
    Cria uma configuração de nó com um endereço IP local e uma porta exclusiva.
    """
    ip_address = '127.0.0.1'
    node_port = base_port + node_index
    return f"{ip_address}:{node_port}"

def create_cluster_configs(num_nodes, base_port):
    """
    Cria configurações de cluster com nós usando endereços IP locais e portas exclusivas.
    """
    return [create_node_config(i, base_port) for i in range(num_nodes)]

def run_node(node_address, cluster_addresses, server_port):
    """
    Executa um nó do cluster.
    """
    async def node_main():
        server_node = ChargePointManagementNode(node_address, cluster_addresses, server_port)
        await server_node.raft_start()
        server_start_task = asyncio.create_task(server_node.csms_routine())
        await asyncio.gather(server_start_task)
    
    asyncio.run(node_main())

def main():
    num_nodes = 5
    base_node_port = 2001
    server_port = 2913

    cluster_addresses = create_cluster_configs(num_nodes, base_node_port)

    processes = []

    for i in range(num_nodes):
        node_address = cluster_addresses[i]
        p = Process(target=run_node, args=(node_address, cluster_addresses, server_port))
        p.start()
        processes.append(p)

    for p in processes:
        p.join()

if __name__ == "__main__":
    main()
