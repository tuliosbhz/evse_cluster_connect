#TODO: Think on the best way to implement that idea, which design pattern to use
from ocpp.v201 import call_result
from ocpp.v201 import call

import time
import asyncio
#import ocpp_v201.charge_point as charge_point
import ocpp_v201.deprecated.charge_point_find_csms_ip as charge_point_find_csms_ip
#CSMS side messages
def on_hearbeat_at_csms(hearbeat_request_payload:call.HeartbeatPayload):
    #TODO: Add the parameters and the return based on the defined use case
    return call_result.HeartbeatPayload

async def send_heartbeat(self:charge_point_find_csms_ip.ChargePoint,
                         request:call.HeartbeatPayload, 
                         interval: int):
    sent_time = time.time()
    await self.call(request)
    self.round_trip_times.append(time.time() - sent_time)
    await asyncio.sleep(interval)
    await self.write_key_performance_indicators()