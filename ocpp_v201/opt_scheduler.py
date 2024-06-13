import datetime
import numpy as np
from scipy.optimize import linprog
import math

def calculate_optimized_charging_schedule(acChargingParameters, max_schedule_tuples, departure_time:datetime.datetime, cost_per_hour):
    eAmount = acChargingParameters['energy_amount']
    evMinCurrent = acChargingParameters['ev_min_current']
    evMaxCurrent = acChargingParameters['ev_max_current']
    evMaxVoltage = acChargingParameters['ev_max_voltage']

    # Calculate the total time available for charging
    departure_timestamp = int(departure_time.timestamp())
    current_timestamp = int(datetime.datetime.now().timestamp())
    available_time_seconds = departure_timestamp - current_timestamp  # in seconds

    if available_time_seconds <= 0:
        error = ValueError("Departure time should be in the future.")
        print(error)
        #Next 24 hours in seconds
        available_time_seconds = 24 * 3600

    # Convert available time to hours (float) including minutes
    available_hours = available_time_seconds / 3600

    # Ensure minimum power does not exceed energy requirement
    min_power = evMinCurrent * evMaxVoltage  # in W
    min_energy = min_power * available_hours
    if min_energy > eAmount:
        # Adjust available hours to meet minimum power constraint
        required_hours = math.ceil(eAmount / min_power)
        available_hours = max(available_hours, required_hours)
        eAmount = min_energy

    # Ensure cost_per_hour array matches the available hours
    if len(cost_per_hour) < available_hours:
        raise ValueError("cost_per_hour array does not cover the available hours until departure.")

    # Calculate the energy required to charge the EV
    energy_needed = eAmount  # in Wh

    # Calculate the power constraints
    max_power = evMaxCurrent * evMaxVoltage  # in W
    min_power = evMinCurrent * evMaxVoltage  # in W

    print(f"Energy needed: {energy_needed} Wh")
    print(f"Available hours: {available_hours}")
    print(f"Max power: {max_power} W")
    print(f"Min power: {min_power} W")

    available_hours_int = min(int(math.ceil(available_hours)), max_schedule_tuples)
    max_energy_deliverable = available_hours_int * max_power

    if energy_needed > max_energy_deliverable:
        energy_needed = max_energy_deliverable  # Adjust to the maximum deliverable energy

    result = None
    # Linear programming to minimize cost
    while available_hours_int <= max_schedule_tuples:
        c = np.array(cost_per_hour[:available_hours_int])  # cost coefficients
        A = np.eye(available_hours_int)  # Coefficients for inequality constraints (each hour's power)
        b = np.full(available_hours_int, max_power)  # Upper limit for power in each hour
        A_eq = np.ones((1, available_hours_int))  # Coefficients for equality constraints (total energy)
        b_eq = np.array([energy_needed])  # Total energy needed

        # Bounds for each variable (min_power to max_power)
        bounds = [(min_power, max_power)] * available_hours_int

        # Solve the linear program
        result = linprog(c, A_ub=A, b_ub=b, A_eq=A_eq, b_eq=b_eq, bounds=bounds, method='highs')

        if result.success:
            break

        available_hours_int += 1

    if not result or not result.success:
        raise RuntimeError("Optimization failed: Unable to find a feasible solution within the max_schedule_tuples constraint.")

    # Extract optimized power values
    optimized_power = result.x

    # Determine the charging schedule
    charging_schedule_periods = []
    for i, power in enumerate(optimized_power):
        # Convert power to current (A)
        limit_current = power / evMaxVoltage

        # Create the charging schedule period
        period_start = current_timestamp + (i * 3600)
        charging_schedule_periods.append({
            'startPeriod': period_start,
            'limit': int(limit_current)
        })

    # Calculate the duration of the last charging period
    last_period_energy = optimized_power[-1]  # in Wh
    last_period_duration_seconds = int((last_period_energy / max_power) * 3600)  # convert to seconds

    # Construct the charging profile
    charging_profile = {
        'id': int(1),
        'stackLevel': int(0),
        'chargingProfilePurpose': 'ChargingStationMaxProfile',
        'chargingProfileKind': 'Absolute',
        'chargingSchedule': [{
            'id': int(0),
            'chargingRateUnit': "A",
            'duration': last_period_duration_seconds,
            'chargingSchedulePeriod': charging_schedule_periods
        }]
    }

    return charging_profile, departure_time

# Example usage
acChargingParameters = {
    'energy_amount': 10000,  # in Wh
    'ev_min_current': 6,  # in A
    'ev_max_current': 32,  # in A
    'ev_max_voltage': 230  # in V
}
max_schedule_tuples = 5
departure_time = datetime.datetime.now() + datetime.timedelta(hours=10)  # Example initial schedule

# Cost per kWh for each hour of the day
cost_per_hour = [
    0.10, 0.10, 0.10, 0.10, 0.10, 0.10,  # 00:00 - 05:59 Off-peak
    0.15, 0.15, 0.15, 0.15, 0.15, 0.15,  # 06:00 - 11:59 Mid-peak
    0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20, 0.20,  # 12:00 - 19:59 Peak
    0.15, 0.15,  # 20:00 - 21:59 Mid-peak
    0.10, 0.10   # 22:00 - 23:59 Off-peak
]

charging_profile, adjusted_departure_time = calculate_optimized_charging_schedule(acChargingParameters, max_schedule_tuples, departure_time, cost_per_hour)
print(charging_profile)
print(f"Adjusted departure time: {adjusted_departure_time}")
