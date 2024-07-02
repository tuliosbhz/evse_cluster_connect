import sys
import os

# Adicionar o diretório raiz do projeto ao caminho do sistema
script_dir = os.path.dirname(__file__)
project_root = os.path.abspath(os.path.join(script_dir, '..'))
sys.path.insert(0, project_root)

import asyncio
import logging
import websockets
from websockets import serve

from metrics_logger import MetricsLogger
from ocpp_server_bench import *

# Inicialização do metrics_logger
metrics_logger = MetricsLogger()

async def on_ocpp_client_connect(websocket, path):
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


async def activate_ocpp_server():
    server = await websockets.serve(
        on_ocpp_client_connect, "0.0.0.0", 2914, subprotocols=["ocpp2.0.1"], ping_interval=None
    )
    logging.info("Server Started listening to new connections...")
    await server.wait_closed()

async def csms_routine():
    csms_task = None
    while True:
        try:
            if not csms_task:
                csms_task = asyncio.create_task(activate_ocpp_server())
            await asyncio.sleep(0.5)
        except Exception as e:
            logging.error(e)

async def main():
    await csms_routine()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())
