#!/usr/bin/env python
import asyncio
import configparser
import logging
import sys
import raftos
import websockets
from websockets import serve
from ocpp_server_bench import *

class ChargePointManagementNode:
    def __init__(self, selfNodeAddr:str, otherNodeAddrs:list, port):
        self.port = port
        self.server = None
        raftos.configure({
        'log_path': './',
        'serializer': raftos.serializers.JSONSerializer
        })
        self.raft_node = selfNodeAddr #format should be "ip:port"
        self.raft_cluster = otherNodeAddrs #format should be "ip:port"
        self.raft_cluster.append(selfNodeAddr)

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
        #self.csms_instances.append(charge_point)
        #self.cp_ids.append(charge_point_id)
        #self.websockets_conn.append(websocket)

        await charge_point.start()
    
    async def open_connections(self):
        self.server = await websockets.serve(
            self.on_connect, "0.0.0.0", self.port, subprotocols=["ocpp2.0.1"],ping_interval=None
        )
        logging.info("Server Started listening to new connections...")
        await self.server.wait_closed()

    async def csms_routine(self):
        while True:
            leader = raftos.get_leader()
            if not leader or (self.raft_node in leader):
                logging.info(f"I'M THE BOSS: {leader}")
                if not self.server:
                    csms_task = asyncio.create_task(self.open_connections())
                    await asyncio.sleep(0.5)
            else:
                logging.info(f"WHO IS THE BOSS? {leader}")
                if self.server:
                    self.server.close()
                    await self.server.wait_closed()
                    self.server = None
                    logging.info("CSMS closed as not leader")
            await asyncio.sleep(1.5)  # Check leadership status every 1 second

    async def raft_routine(node_id):
        while True:
            print(raftos.get_leader())

            await asyncio.sleep(2)

            current_id = random.randint(1, 1000)
            data_map = {
                str(current_id): {
                    'created_at': datetime.now().strftime('%d/%m/%y %H:%M')
                }
            }
            print(data_map)

async def main(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)

    if 'MY_ADDR' not in config or 'PARTNERS_ADDR' not in config:
        print('Error: [MY_ADDR] or [PARTNERS_ADDR] section not found in the config file')
        sys.exit(-1)

    my_address = config['MY_ADDR'].get('self')
    if not my_address:
        print('Error: No self address found in the [MY_ADDR] section of the config file')
        sys.exit(-1)

    partners = [config['PARTNERS_ADDR'][key] for key in config['PARTNERS_ADDR']]
    port = int(config['SERVER_CONFIG']['port'])
    print(partners)
    server_node = ChargePointManagementNode(my_address, partners, port)
    print(server_node.raft_cluster)
    server_start_task = asyncio.create_task(server_node.csms_routine())
    raft_reg_task = asyncio.create_task(raftos.register(server_node.raft_node, 
                                                        cluster=server_node.raft_cluster))
    raft_rou_task = asyncio.create_task(server_node.raft_routine())

    await asyncio.gather(raft_reg_task, raft_rou_task, server_start_task)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: %s config_path' % sys.argv[0])
        sys.exit(-1)

    config_path = sys.argv[1]
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(config_path))
