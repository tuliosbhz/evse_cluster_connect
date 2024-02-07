import unittest
from datetime import datetime, timedelta
from cluster_connect.schedule import Schedule  # Replace 'your_module' with the actual module name
import time

class TestScheduleClass(unittest.TestCase):
    def setUp(self):
        #Common setup for tests
        #Example charging schedule period data
        current_time = datetime.now()
        charging_schedule_period = [
            # {"startPeriod": datetime(2022, 1, 1, 12, 0, 0), "limit": 100},
            # {"startPeriod": datetime(2022, 1, 1, 12, 0, 30), "limit": 50},
            {"startPeriod": current_time, "limit": 7400},
            {"startPeriod": current_time + timedelta(seconds=3), "limit": 3000},
            {"startPeriod": current_time + timedelta(seconds=6), "limit": 1380},
            # Add more periods as needed
        ]

        self.schedule_instance = Schedule(
            evse_id="EV1",
            id=1,
            charging_rate_unit="W",
            duration=9,  # 9 seconds on last inteval
            charging_schedule_period=charging_schedule_period
        )
    
    def test_current_variables_behaviour(self):
        before_update = self.schedule_instance.currentSchedulePeriodIndex
        print("################### INICIO DO TESTE #####################")
        print(self.schedule_instance.get_schedule())
        print(F"CURRENT SCHEDULE: {self.schedule_instance.currentSchedule}")
        print(f"REMAINING TIME: {self.schedule_instance.remainingTime}")
        print(f"CURRENT DURATION: {self.schedule_instance.currentDuration}")
        print(f"CURRENT POWER LIMIT: {self.schedule_instance.currentLimit}")
        print(f"CURRENT INDEX PERIOD: {before_update}")
        time.sleep(self.schedule_instance.currentDuration)
        self.schedule_instance.update_current_variables()
        after_update = self.schedule_instance.currentSchedulePeriodIndex
        print("########## PRIMEIRO PERIODO CUMPRIDO DO TESTE ############")
        print(F"CURRENT SCHEDULE: {self.schedule_instance.currentSchedule}")
        print(f"REMAINING TIME: {self.schedule_instance.remainingTime}")
        print(f"CURRENT DURATION: {self.schedule_instance.currentDuration}")
        print(f"CURRENT POWER LIMIT: {self.schedule_instance.currentLimit}")
        print(f"CURRENT INDEX PERIOD: {after_update}")
        self.assertNotEqual(after_update, before_update)
        before_update = self.schedule_instance.currentSchedulePeriodIndex
        time.sleep(self.schedule_instance.currentDuration)
        self.schedule_instance.update_current_variables()
        after_update = self.schedule_instance.currentSchedulePeriodIndex
        print("######### SEGUNDO PERIODO CUMPRIDO DO TESTE #############")
        print(F"CURRENT SCHEDULE: {self.schedule_instance.currentSchedule}")
        print(f"REMAINING TIME: {self.schedule_instance.remainingTime}")
        print(f"CURRENT DURATION: {self.schedule_instance.currentDuration}")
        print(f"CURRENT POWER LIMIT: {self.schedule_instance.currentLimit}")
        print(f"CURRENT INDEX PERIOD: {after_update}")
        self.assertNotEqual(after_update, before_update)
        before_update = self.schedule_instance.currentSchedulePeriodIndex
        time.sleep(self.schedule_instance.currentDuration)
        self.schedule_instance.update_current_variables()
        after_update = self.schedule_instance.currentSchedulePeriodIndex
        print("######## PERIODO FINAL CUMPRIDO DO TESTE ##############")
        print(F"CURRENT SCHEDULE: {self.schedule_instance.currentSchedule}")
        print(f"REMAINING TIME: {self.schedule_instance.remainingTime}")
        print(f"CURRENT DURATION: {self.schedule_instance.currentDuration}")
        print(f"CURRENT POWER LIMIT: {self.schedule_instance.currentLimit}")
        print(f"CURRENT INDEX PERIOD: {after_update}")
        #Periodo final o indices devem ser iguais por estar a cumprir o último periodo do schedule
        self.assertEqual(after_update, before_update)

if __name__ == '__main__':
    unittest.main()
