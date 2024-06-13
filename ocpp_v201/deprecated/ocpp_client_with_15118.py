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

import asyncio
import logging
from datetime import datetime

from iso15118.secc import SECCHandler
from iso15118.secc.controller.interface import ServiceStatus
from iso15118.secc.controller.simulator import SimEVSEController
from iso15118.secc.secc_settings import Config
from iso15118.shared.exificient_exi_codec import ExificientEXICodec

import uuid

#logger = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)

class ChargePoint(cp):

    def __init__(self, charge_point_id, websocket):
        super(cp, self).__init__(charge_point_id, websocket)
        """
        Entrypoint function that starts the ISO 15118 code running on
        the SECC (Supply Equipment Communication Controller)
        """
        #To execute on __init__ function of OCPP client
        self.iso_config = Config()
        self.iso_config.load_envs()
        self.iso_config.print_settings()
        self.sim_evse_controller = SimEVSEController()
        self.secc_handler = SECCHandler(
                                exi_codec=ExificientEXICodec(),
                                evse_controller=self.sim_evse_controller,
                                config=self.iso_config,
                            )
        self._secc_curr_state = self.get_secc_state()
        self._secc_prev_state = self._secc_curr_state
        self._station_booted = False
        self._heartbeat_interval = 10
        self._new_secc_state = False

        self.evse_id = 1 #charge_point_id
        self.id_token = uuid.uuid4()
        self.id_token_type ="Local"
        self.connector_status = "Available"

        
    
    def update_boot_status(self, new_value:bool):
        print(f"Updating _station_booted from {self._station_booted} to {new_value}")
        self._station_booted = new_value
        print(f"_station_booted is now {self._station_booted}")
        
    def update_new_secc_state(self, new_value:bool):
        print(f"Updating _new_secc_state from {self._station_booted} to {new_value}")
        self._new_secc_state = new_value
        print(f"_new_secc_state is now {self._station_booted}")

    async def secc_routine(self):
        #Task to execute inside the OCPP client
        await self.sim_evse_controller.set_status(ServiceStatus.STARTING)
        await self.secc_handler.start(self.iso_config.iface)
    
    def get_secc_state(self):
        """
        SECC states of ISO 15118-2:
            SupportedAppProtocol
            SessionSetup
            ServiceDiscovery
            PaymentServiceSelection
            Authorization
            ChargeParameterDiscovery
            PowerDelivery
            ChargingStatus
            PowerDelivery* (?)
            SessionStop
        """
        # Ensure the dictionary is not empty
        secc_communication_session = ()
        if self.secc_handler.comm_sessions:
            # Get the first key from the dictionary
            first_key = next(iter(self.secc_handler.comm_sessions))
            #ev_ip = self.secc_handler._current_peer_ip[2:25]
            # Retrieve the tuple corresponding to the first key
            first_tuple = self.secc_handler.comm_sessions[first_key]
            # Extract the SECCCommunicationSession element from the tuple
            secc_communication_session = first_tuple[0]
            # Check if new state is identified
            self._secc_curr_state = secc_communication_session.current_state
            if self._secc_prev_state != self._secc_curr_state:
                self.update_new_secc_state(True)
                self._secc_prev_state = self._secc_curr_state
            return secc_communication_session.current_state, self._new_secc_state
        else:
            print("The comm_sessions dictionary is empty.")
            return None, False
        
        
    
    async def send_boot_notification(self):
        """
        Use:
            First OCPP message that should be sent
        Function:
            This intiates the communication with the server and 
            triggers the cyclic OCPP heartbeat messages
        Example:
        """
        request = call.BootNotificationPayload(
            charging_station={"model": "Wallbox XYZ", "vendor_name": "anewone"},
            reason="PowerUp",
        )
        response = await self.call(request)
        print(response.custom_data)
        self._heartbeat_interval = response.interval

        if response.status == "Accepted":
            print("Connected to central system.")
            self.update_boot_status(True)
            ocpp_msgs_task = asyncio.create_task(self.send_ocpp_message())
            heartbeat_task = asyncio.create_task(self.send_heartbeat(self._heartbeat_interval))
            await asyncio.gather(heartbeat_task, ocpp_msgs_task)
        elif response.status == "Rejected":
            await self._connection.close()

    async def send_heartbeat(self, interval):
        """
        Use: 
            This method should be an asyncio task triggered 
            inside BootNotification method
        Function:
            It checks the liveness of the client for the server and 
            sync time between them
        Example: 
            
        
        """
        ocpp_request = call.HeartbeatPayload()
        while True:
            await self.call(ocpp_request)
            await asyncio.sleep(interval)
    
    async def send_ocpp_message(self):
        """
        Abstract design pattern method

        Use: 
            This method should be an asyncio task
        Function:
            It calls all ocpp messages implemented every time
            but the message only will be really sent if the internal 
            conditions of each method of the message is true
        Example: 
            In a new EV connection only the status_notification 
            and transaction_event messages will be sent
        """
        while True:
            logging.info("ENTERED SEND_OCPP_MESSAGES function")
            if self._station_booted:
                logging.error("ENTERED STATION BOOTED")
                await self.send_status_notification()
                await self.send_transaction_event()
                await self.send_authorize()
                await self.send_notify_ev_charging_needs()
                await self.send_set_charging_profile()
            await asyncio.sleep(0.25)

    
    async def send_transaction_event(self):
        transaction_id = "LOC001"
        #Look into cases to send update of transaction events to add more elif methods on other secc_states
        secc_curr_state, self._new_secc_state = self.get_secc_state()
        if secc_curr_state and self._new_secc_state:
            if secc_curr_state == "SupportedAppProtocol":
                ocpp_request = call.TransactionEventPayload(
                    event_type="Started",
                    timestamp=datetime.now().strftime('%Y-%m-%d T %H:%M:%S'),
                    trigger_reason="EvDetected",
                    seq_no=0,
                    transaction_info={'transactionId': transaction_id, 'chargingState':"EvConnected"},
                )
            elif secc_curr_state == "SessionStop":
                ocpp_request = call.TransactionEventPayload(
                    event_type="Ended",
                    timestamp=datetime.now().strftime('%Y-%m-%d T %H:%M:%S'),
                    trigger_reason="EnergyLimitReached",
                    seq_no=0,
                    transaction_info={'transactionId': transaction_id, 'chargingState':"SuspendedEv"},
                )
            else:
                ocpp_request = call.TransactionEventPayload(
                    event_type="Updated",
                    timestamp=datetime.now().strftime('%Y-%m-%d T %H:%M:%S'),
                    trigger_reason="Trigger",
                    seq_no=0,
                    transaction_info={'transactionId': transaction_id, 'chargingState':"Charging"},
                )
            response = await self.call(ocpp_request)

            self.update_new_secc_state(False)


    async def send_status_notification(self):
        secc_curr_state, self._new_secc_state = self.get_secc_state()
        if secc_curr_state and self._new_secc_state:
            if secc_curr_state == "SupportedAppProtocol":
                self.connector_status = "Occupied"
                ocpp_request = call.StatusNotificationPayload(timestamp=datetime.now().strftime('%Y-%m-%d T %H:%M:%S '),
                                                connector_status=self.connector_status, 
                                                evse_id = self.evse_id, 
                                                connector_id = 1)
            elif secc_curr_state == "SessionStop":
                self.connector_status = "Available"
                ocpp_request = call.StatusNotificationPayload(timestamp=datetime.now().strftime('%Y-%m-%d T %H:%M:%S '),
                                                connector_status=self.connector_status, 
                                                evse_id = self.evse_id, 
                                                connector_id = 1)
            else:
                self.connector_status = "Occupied"
                ocpp_request = call.StatusNotificationPayload(timestamp=datetime.now().strftime('%Y-%m-%d T %H:%M:%S '),
                                                connector_status=self.connector_status, 
                                                evse_id = self.evse_id, 
                                                connector_id = 1)
            response = await self.call(ocpp_request)

    async def send_authorize(self):
        secc_curr_state, self._new_secc_state = self.get_secc_state()
        if secc_curr_state and self._new_secc_state:
            if secc_curr_state == "Authorize":
                ocpp_request = call.AuthorizePayload(id_token={ "id": self.id_token, "type": self.id_token_type})
                self.call(ocpp_request)


    async def send_notify_ev_charging_needs(self):
        pass

    async def send_set_charging_profile(self):
        pass

async def websocket_connection(port, charge_point:ChargePoint):
    try:
        async with websockets.connect(
            f"ws://localhost:{port}/CP0{port}", subprotocols=["ocpp2.0.1"]
        ) as ws:
            charge_point._connection = ws
            # Start the other tasks once the WebSocket connection is established
            start_task = asyncio.create_task(charge_point.start())
            boot_task = asyncio.create_task(charge_point.send_boot_notification())

            # Wait for the tasks to complete
            await asyncio.gather(start_task, boot_task)
    except Exception as e:
        logging.info(str(e))

async def main():
    csms_base_port = 2050
    port = csms_base_port + 1
    leader_address = None

    # Create a ChargePoint instance without a WebSocket connection initially
    charge_point = ChargePoint("CP0{port}", None)

    # Start the secc_routine task before attempting WebSocket connections
    #secc_task = asyncio.create_task(charge_point.secc_routine())
    #await asyncio.sleep(0.5)

    while True:
        msg_ev = charge_point.get_secc_state()
        logging.info(f"Last message exchange with EV: {msg_ev}")
        await websocket_connection(port, charge_point)
        if port > 2100:
            port = csms_base_port
        else:
            port += 1
        await asyncio.sleep(0.2)
if __name__ == "__main__":
    # asyncio.run() is used when running this example with Python >= 3.7v
    asyncio.run(main())