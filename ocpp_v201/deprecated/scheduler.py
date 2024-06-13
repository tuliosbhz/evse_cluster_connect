import datetime
import math

def calculate_charging_schedule(acChargingParameters, max_schedule_tuples, departure_time):
    eAmount = acChargingParameters['energyAmount']
    evMinCurrent = acChargingParameters['evMinCurrent']
    evMaxCurrent = acChargingParameters['evMaxCurrent']
    evMaxVoltage = acChargingParameters['evMaxVoltage']

    # Calculate the total time available for charging
    departure_timestamp = int(departure_time.timestamp())
    current_timestamp = int(datetime.datetime.now().timestamp())
    available_time = departure_timestamp - current_timestamp  # in seconds
    
    if available_time <= 0:
        raise ValueError("Departure time should be in the future.")

    # Calculate the energy required to charge the EV
    energy_needed = eAmount  # in Wh

    # Calculate the power constraints
    max_power = evMaxCurrent * evMaxVoltage  # in W
    min_power = evMinCurrent * evMaxVoltage  # in W

    # Determine the number of schedule periods
    schedule_periods = max_schedule_tuples

    # Determine the charging periods
    charging_schedule_periods = []
    remaining_energy = energy_needed
    period_duration = available_time // schedule_periods  # equal duration for each period

    for i in range(schedule_periods):
        if i == schedule_periods - 1:
            # Last period takes the remaining time
            period_duration = available_time - (period_duration * (schedule_periods - 1))
        
        # Calculate the current limit needed for the remaining energy
        limit = remaining_energy / (period_duration / 3600)  # W
        limit = min(limit, max_power)
        limit = max(limit, min_power)
        
        # Convert limit to current (A)
        limit_current = limit / evMaxVoltage
        
        # Create the charging schedule period
        charging_schedule_periods.append({
            'startPeriod': current_timestamp + (i * period_duration),
            'limit': limit_current
        })
        
        # Update the remaining energy
        remaining_energy -= (limit * (period_duration / 3600))

    # Construct the charging profile
    charging_profile = {
        'id': int(1),
        'stackLevel': int(0),
        'chargingProfilePurpose': 'ChargingStationMaxProfile',
        'chargingProfileKind': 'Absolute',
        'chargingSchedule': [{
            'id': int(0),
            'chargingRateUnit': "A",
            'chargingSchedulePeriod': charging_schedule_periods
        }]
    }

    return charging_profile

# Example usage
acChargingParameters = {
    'energy_amount': 50000,  # in Wh
    'ev_min_current': 10,  # in A
    'ev_max_current': 32,  # in A
    'ev_max_voltage': 230  # in V
}
max_schedule_tuples = 5
departure_time = datetime.datetime.now() + datetime.timedelta(hours=2)

charging_profile = calculate_charging_schedule(acChargingParameters, max_schedule_tuples, departure_time)
print(charging_profile)
