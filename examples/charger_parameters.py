from pydantic import BaseModel, validator
from datetime import datetime
import os

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
        orm_mode=True

class ConfigParameters(BaseModel):
    address:str
    nominal_power: int
    evse_id: str
    # planned_charging_schedule: Schedule = None
    # executed_charging_schedule: Schedule = None

    class Config:
        orm_mode=True

class ScheduleParameters(BaseModel):
    selected_max_power: int = None
    planned_departure: datetime = None
    user_id: int
    session_id: str
    evse_id: str
    max_cluster_power: int #Write here the considered
    # planned_charging_schedule: Schedule = None
    # executed_charging_schedule: Schedule = None

    class Config:
        orm_mode=True

class SimulationParameters(BaseModel):
    plug_status: str
    authenticated: bool
    user_id: int
    session_id: str
    evse_id: str
    max_cluster_power: int #Read from here the inputed
    # planned_charging_schedule: Schedule = None
    # executed_charging_schedule: Schedule = None

    class Config:
        orm_mode=True