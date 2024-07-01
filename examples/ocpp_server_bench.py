import asyncio
import logging
import time
from datetime import datetime
import random
import csv
import os
import sys
import json

from ocpp.routing import on, after
from ocpp.v201 import ChargePoint as cp
from ocpp.v201 import call_result
from ocpp.v201 import call

from opt_scheduler import calculate_optimized_charging_schedule

from metrics_logger import MetricsLogger
# Inicialização do metrics_logger
metrics_logger = MetricsLogger()

logging.basicConfig(level=logging.INFO)

class CSMS(cp):
    def __init__(self, charge_point_id, websocket):
        super(CSMS, self).__init__(charge_point_id, websocket)
        self.cp_id = charge_point_id
        self.interval = 10
        self.leader_address = None
        self._server = None
        self.address = "0.0.0.0"
        self.port = 9000
        self.conn = websocket

        self.departure_time = None
        self.charging_needs = None
        self.evse_id = None
        self.max_schedule_tuples = None
        self.ac_charging_parameters = None
        # Reference: https://www.energyprices.eu/electricity/portugal - Prices per of EUR/kWh
        self.cost_energy_hour = [
                                    0.103, 0.102, 0.102, 0.102, 0.101, 0.101,  # 00:00 - 05:59 Off-peak
                                    0.100, 0.073, 0.048, 0.044, 0.035, 0.023,  # 06:00 - 11:59 Mid-peak
                                    0.010, 0.005, 0.001, 0.040, 0.005, 0.004, 0.027, 0.047,  # 12:00 - 19:59 Peak
                                    0.059, 0.102,  # 20:00 - 21:59 Mid-peak
                                    0.103, 0.101   # 22:00 - 23:59 Off-peak
                                ]
        self.charging_profile = None
        self.transaction_ids = []
        self.transaction_id = ""
        self.successfull_transactions = 0
        self.connected_ocpp_clients = []
        self.max_ocpp_connections = 30

    def record_benchmark(self):
        try:
            logging.info(f"Recording benchmark -> Connected ocpp clients: {len(self.connected_ocpp_clients)}, latency: {latency}, size: {msg_size}")
            metrics_logger.record_ocpp_latency(start_time, end_time)
            metrics_logger.record_ocpp_throughput(msg_size)
            metrics_logger.log_ocpp_metrics(message,
                                            self.transaction_id, 
                                            self.evse_id,
                                            self.cp_id,
                                            self.interval)
        except Exception as e:
            logging.error(f"Failed to write benchmark data: {e}")

    @on("BootNotification")
    async def on_boot_notification(self, charging_station, reason, **kwargs):
        if len(self.connected_ocpp_clients) < self.max_ocpp_connections:
            status = "Accepted"
            self.connected_ocpp_clients.append(charging_station)
        else: 
            status ="Rejected"
        self.interval = 3 #random.randint(3, 15)
        result = call_result.BootNotification(
            current_time=datetime.now().isoformat(), interval=self.interval, status=status, custom_data=self.leader_address
        )
        return result

    @on("Heartbeat")
    async def on_heartbeat(self):
        result = call_result.Heartbeat(
            current_time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        )
        return result
    
    @on("TransactionEvent")
    async def on_transaction_event(self, event_type, timestamp, trigger_reason, seq_no, transaction_info, **kwargs):
        if trigger_reason == "EVDetected":
            self.departure_time = timestamp
        self.transaction_id = transaction_info["transaction_id"]
        #self.transaction_id = transaction_info["transaction_id"]
        result = call_result.TransactionEvent()
        return result
    
    @on("StatusNotification")
    async def on_status_notification(self, timestamp, connector_status, evse_id, connector_id, **kwargs):
        self.evse_id = evse_id
        result = call_result.StatusNotification()
        return result
    
    @on("Authorize")
    async def on_authorize(self, id_token, *args, **kwargs):
        result = call_result.Authorize(id_token_info={'status': "Accepted"})
        return result

    @on("NotifyEVChargingNeeds")
    async def on_notify_ev_charging_needs(self, charging_needs, evse_id, max_schedule_tuples):
        self.charging_needs = charging_needs
        self.evse_id = evse_id
        self.max_schedule_tuples = max_schedule_tuples
        self.ac_charging_parameters = charging_needs['ac_charging_parameters']
        self.departure_time = charging_needs['departure_time']
        logging.info(f"AC_PARAMS: {self.ac_charging_parameters}")
        result = call_result.NotifyEVChargingNeeds(status="Accepted")
        return result
    
    @after("NotifyEVChargingNeeds")
    async def after_notify_ev_charging_needs(self, charging_needs, evse_id, max_schedule_tuples):
        if self.ac_charging_parameters:
            self.departure_time = datetime.now().timestamp() if not self.departure_time else datetime.fromtimestamp(float(self.departure_time))
            self.charging_profile, self.departure_time = calculate_optimized_charging_schedule(self.ac_charging_parameters,
                                                                                                self.max_schedule_tuples,
                                                                                                self.departure_time,
                                                                                                self.cost_energy_hour)
        else:
            self.charging_profile = {'id': int(1),
                                    'stackLevel': int(0),
                                    'chargingProfilePurpose': 'ChargingStationMaxProfile',
                                    'chargingProfileKind': 'Absolute',
                                    'chargingSchedule': [{'id': int(0),
                                                          'chargingRateUnit': "A",
                                                          'chargingSchedulePeriod': [{'startPeriod': int(datetime.now().timestamp()), 'limit': int(7380)}]
                                                          }]
                                    }
        request = call.SetChargingProfile(
            evse_id=self.evse_id,
            charging_profile=self.charging_profile
        )
        logging.info(f"Charging profile: {self.charging_profile}")
        response = await self.call(request)
        return response
