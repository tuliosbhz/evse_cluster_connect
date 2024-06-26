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
        self.cost_energy_hour = [
                                    0.10, 0.10, 0.10, 0.10, 0.10, 0.10,  # 00:00 - 05:59 Off-peak
                                    0.15, 0.15, 0.15, 0.15, 0.15, 0.15,  # 06:00 - 11:59 Mid-peak
                                    0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20,  # 12:00 - 19:59 Peak
                                    0.15, 0.15,  # 20:00 - 21:59 Mid-peak
                                    0.10, 0.10   # 22:00 - 23:59 Off-peak
                                ]
        self.charging_profile = None
        self.transaction_id = ""

    def record_benchmark(self, message, start_time, msg_size):
        try:
            end_time = time.time()
            latency = end_time - start_time
            logging.info(f"Recording benchmark for message: {message}, latency: {latency}, size: {msg_size}")
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
        start_time = time.time()
        status = "Accepted"
        self.interval = random.randint(3, 15)
        result = call_result.BootNotification(
            current_time=datetime.now().isoformat(), interval=self.interval, status=status, custom_data=self.leader_address
        )
        msg_size = sys.getsizeof(json.dumps({
            "current_time": datetime.now().isoformat(), 
            "interval": self.interval, 
            "status": status, 
            "custom_data": self.leader_address
        }))
        self.record_benchmark("BootNotification", start_time, msg_size)
        return result

    @on("Heartbeat")
    async def on_heartbeat(self):
        start_time = time.time()
        result = call_result.Heartbeat(
            current_time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        )
        msg_size = sys.getsizeof(json.dumps({
            "current_time": datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        }))
        self.record_benchmark("Heartbeat", start_time, msg_size)
        return result
    
    @on("TransactionEvent")
    async def on_transaction_event(self, event_type, timestamp, trigger_reason, seq_no, transaction_info, **kwargs):
        start_time = time.time()
        if trigger_reason == "EVDetected":
            self.departure_time = timestamp
        self.transaction_id = transaction_info["transaction_id"]
        result = call_result.TransactionEvent()
        msg_size = sys.getsizeof(json.dumps({
            "event_type": event_type,
            "timestamp": timestamp,
            "trigger_reason": trigger_reason,
            "seq_no": seq_no,
            "transaction_info": transaction_info
        }))
        self.record_benchmark("TransactionEvent", start_time, msg_size)
        return result
    
    @on("StatusNotification")
    async def on_status_notification(self, timestamp, connector_status, evse_id, connector_id, **kwargs):
        start_time = time.time()
        self.evse_id = evse_id
        result = call_result.StatusNotification()
        msg_size = sys.getsizeof(json.dumps({
            "timestamp": timestamp,
            "connector_status": connector_status,
            "evse_id": evse_id,
            "connector_id": connector_id
        }))
        self.record_benchmark("StatusNotification", start_time, msg_size)
        return result
    
    @on("Authorize")
    async def on_authorize(self, id_token, *args, **kwargs):
        start_time = time.time()
        result = call_result.Authorize(id_token_info={'status': "Accepted"})
        msg_size = sys.getsizeof(json.dumps({
            "id_token_info": {'status': "Accepted"}
        }))
        self.record_benchmark("Authorize", start_time, msg_size)
        return result

    @on("NotifyEVChargingNeeds")
    async def on_notify_ev_charging_needs(self, charging_needs, evse_id, max_schedule_tuples):
        start_time = time.time()
        self.charging_needs = charging_needs
        self.evse_id = evse_id
        self.max_schedule_tuples = max_schedule_tuples
        self.ac_charging_parameters = charging_needs['ac_charging_parameters']
        self.departure_time = charging_needs['departure_time']
        logging.info(f"AC_PARAMS: {self.ac_charging_parameters}")
        result = call_result.NotifyEVChargingNeeds(status="Accepted")
        msg_size = sys.getsizeof(json.dumps({
            "charging_needs": charging_needs,
            "evse_id": evse_id,
            "max_schedule_tuples": max_schedule_tuples,
            "ac_charging_parameters": self.ac_charging_parameters,
            "departure_time": self.departure_time,
            "status": "Accepted"
        }))
        self.record_benchmark("NotifyEVChargingNeeds", start_time, msg_size)
        return result
    
    @after("NotifyEVChargingNeeds")
    async def after_notify_ev_charging_needs(self, charging_needs, evse_id, max_schedule_tuples):
        start_time = time.time()
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
        msg_size = sys.getsizeof(json.dumps({
            "evse_id": self.evse_id,
            "charging_profile": self.charging_profile
        }))
        self.record_benchmark("SetChargingProfile", start_time, msg_size)
        return response
