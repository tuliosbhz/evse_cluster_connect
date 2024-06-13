import asyncio
import logging

try:
    import websockets
except ModuleNotFoundError:
    print("This example relies on the 'websockets' package.")
    print("Please install it by running: ")
    print()
    print(" $ pip install websockets")
    import sys

    sys.exit(1)

from ocpp.v201 import ChargePoint as cp
from ocpp.v201 import call

logging.basicConfig(level=logging.INFO)

class ChargePoint(cp):

    async def send_heartbeat(self, interval):
        request = call.HeartbeatPayload()
        while True:
            await self.call(request)
            await asyncio.sleep(interval)

    async def send_boot_notification(self):
        request = call.BootNotificationPayload(
            charging_station={"model": "Wallbox XYZ", "vendor_name": "anewone"},
            reason="PowerUp",
        )
        response = await self.call(request)
        print(response.custom_data)
        if response.status == "Accepted":
            print("Connected to central system.")
            await self.send_heartbeat(response.interval)
        elif response.status == "Rejected":
            await self._connection.close()



async def main():
    csms_base_port = 2050
    port = csms_base_port + 1
    leader_address = None
    while True:
        try:
            async with websockets.connect(
                f"ws://localhost:{port}/CP0{port}", subprotocols=["ocpp2.0.1"]
            ) as ws:
                charge_point = ChargePoint("CP_1", ws)
                await asyncio.gather(
                    charge_point.start(), charge_point.send_boot_notification()
                )
        except Exception as e:
            logging.info(str(e))
            if port > 2100:
                port = csms_base_port
            else:
                port += 1
            await asyncio.sleep(0.2)
if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v
    asyncio.run(main())