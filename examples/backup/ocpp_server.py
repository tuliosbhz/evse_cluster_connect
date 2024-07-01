import asyncio
import logging
from datetime import datetime
import random
import signal

from ocpp.routing import on, after
from ocpp.v201 import ChargePoint as cp
from ocpp.v201 import call_result
from ocpp.v201 import call

from opt_scheduler import calculate_optimized_charging_schedule

logging.basicConfig(level=logging.INFO)

class CSMS(cp):
    def __init__(self, charge_point_id, websocket):
        super(CSMS, self).__init__(charge_point_id, websocket)
        #self.ids = []
        #self.ids.append(id)
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

    @on("BootNotification")
    def on_boot_notification(self, charging_station, reason, **kwargs):
        #TODO: Add rejection case
        #heartbet_handler.on_hearbeat_at_csms()
        status="Accepted"
        return call_result.BootNotification(
            current_time=datetime.now().isoformat(), interval=self.interval, status=status, custom_data=self.leader_address
        )

    @on("Heartbeat")
    def on_heartbeat(self):
        print("Got a Heartbeat!")
        return call_result.Heartbeat(
            current_time=datetime.now().strftime("%Y-%m-%dT%H:%M:%S") + "Z"
        )
    
    @on("TransactionEvent")
    def on_transaction_event(self,event_type,timestamp,trigger_reason,seq_no,transaction_info,**kwargs):
        if trigger_reason == "EVDetected":
            self.departure_time = timestamp
        return call_result.TransactionEvent()
    
    @on("StatusNotification")
    def on_status_notification(self, timestamp, connector_status, evse_id, connector_id, **kwargs):
        return call_result.StatusNotification()
    
    @on("Authorize")
    def on_authorize(self,id_token,*args, **kwargs):
        return call_result.Authorize(id_token_info={'status':"Accepted"})

    @on("NotifyEVChargingNeeds")
    def on_notify_ev_charging_needs(self,charging_needs,evse_id,max_schedule_tuples):
        self.charging_needs = charging_needs
        self.evse_id = evse_id
        self.max_schedule_tuples = max_schedule_tuples
        self.ac_charging_parameters = charging_needs['ac_charging_parameters']
        self.departure_time = charging_needs['departure_time']
        logging.info(f"AC_PARAMS:   {self.ac_charging_parameters}")
        return call_result.NotifyEVChargingNeeds(status="Accepted")
    
    @after("NotifyEVChargingNeeds")
    async def after_notify_ev_charging_needs(self,charging_needs,evse_id,max_schedule_tuples):
        if self.ac_charging_parameters:
            #Calculate an optimal schedule
           
            self.departure_time = datetime.now().timestamp() if not self.departure_time else datetime.fromtimestamp(float(self.departure_time))
            self.charging_profile, self.departure_time = calculate_optimized_charging_schedule(self.ac_charging_parameters,
                                                  self.max_schedule_tuples,
                                                  self.departure_time,
                                                  self.cost_energy_hour)
        else: 
            #Calculate a flat schedule
            self.charging_profile = {'id':int(1),
                                    'stackLevel':int(0),
                                    'chargingProfilePurpose':'ChargingStationMaxProfile',
                                    'chargingProfileKind':'Absolute',
                                    'chargingSchedule':[{'id':int(0),
                                                            'chargingRateUnit':"A",
                                                            'chargingSchedulePeriod':[{'startPeriod':int(datetime.now().timestamp()),'limit':int(7380)}]
                                                        }]
                                    }
        request=call.SetChargingProfile(
                                        evse_id=self.evse_id,
                                        charging_profile=self.charging_profile
                                        )
        logging.info(f"Charging profile:{self.charging_profile}")
        response = await self.call(request)

        return response
    