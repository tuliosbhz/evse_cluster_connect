from ocpp_v201.ocpp_server import websockets, logging, asyncio, on_connect

async def main():
    #  deepcode ignore BindToAllNetworkInterfaces: <Example Purposes>
    server = await websockets.serve(
        on_connect, "0.0.0.0", 9002, subprotocols=["ocpp2.0.1"],ping_interval=None
    )

    logging.info("Server Started listening to new connections...")
    await server.wait_closed()


if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v
    asyncio.run(main())
