from pydantic import BaseModel
from datetime import datetime

class ChargerParameters(BaseModel):
    address: str
    plug_status: str
    authenticated: bool
    nominal_power: int
    selected_max_power: int = None
    planned_departure: datetime = None
    user_id: int
    session_id: str
    evse_id: str
    max_cluster_power: int
    # planned_charging_schedule: Schedule = None
    # executed_charging_schedule: Schedule = None

    class Config:
        from_attributes=True

class ConfigParameters(BaseModel):
    address:str
    nominal_power: int
    evse_id: str
    # planned_charging_schedule: Schedule = None
    # executed_charging_schedule: Schedule = None

    class Config:
        from_attributes=True

"""
Formato de dados que inclui todas as variáveis individuais que serão compartilhadas em comum com o cluster
"""
# class ClusterSincData(BaseModel):
#     selected_max_power: int = None
#     planned_departure: datetime = None
#     user_id: int
#     session_id: str
#     evse_id: str
#     max_cluster_power: int #Write here the considered
#     # planned_charging_schedule: Schedule = None
#     # executed_charging_schedule: Schedule = None

#     class Config:
#         from_attributes=True
"""
Formato de dados que resume as variáveis individuais relevantes de um único carregador
"""
class EvseDataSim(BaseModel):
    plug_status: str
    authenticated: bool
    user_id: int
    session_id: str
    evse_id: str
    cluster_id:str
    min_power_capacity:int
    power_capacity: int #Value in whatts of total capacity
    measured_power:int = None
    selected_max_power: int = None
    # planned_charging_schedule: Schedule = None
    # executed_charging_schedule: Schedule = None

    class Config:
        from_attributes=True

class ClusterStats(BaseModel):
    cluster_id:str
    num_nodes:int
    total_limit_power:int #Value received by the agreggator
    total_power_capacity: int
    min_power_capacity: int
    num_active_nodes:int

    class Config:
        from_attributes=True


