#!/usr/bin/env python
import asyncio
import configparser
import logging
import sys
from pysyncobj import SyncObj, replicated, SyncObjConf
import websockets
from websockets import serve
from ocpp_server import *

class ChargePointManagementNode(SyncObj):
    def __init__(self, selfNodeAddr, otherNodeAddrs, port):
        conf = SyncObjConf(dynamicMembershipChange=True)
        super().__init__(selfNodeAddr, otherNodeAddrs, conf)
        self.port = port
        self.server = None

    @replicated
    def force_election(self):
        common_value = 10
        return common_value
    
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
    
    async def open_connections(self):
        self.server = await websockets.serve(
            self.on_connect, "0.0.0.0", self.port, subprotocols=["ocpp2.0.1"],ping_interval=None
        )
        logging.info("Server Started listening to new connections...")
        await self.server.wait_closed()

    async def csms_routine(self):
        while True:
            if self._isLeader() or (self._getLeader() is None):
                logging.info(f"I'M THE BOSS: {self._getLeader()}")
                if not self.server:
                    csms_task = asyncio.create_task(self.open_connections())
                    await asyncio.sleep(0.5)
            else:
                logging.info(f"WHO IS THE BOSS? {self._getLeader()}")
                if self.server:
                    self.server.close()
                    await self.server.wait_closed()
                    self.server = None
                    logging.info("CSMS closed as not leader")
            self.force_election()
            await asyncio.sleep(1.5)  # Check leadership status every 1 second

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

    node = ChargePointManagementNode(my_address, partners, port)
    await node.csms_routine()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: %s config_path' % sys.argv[0])
        sys.exit(-1)

    config_path = sys.argv[1]
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main(config_path))
