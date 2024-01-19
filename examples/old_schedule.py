class Schedule():
    """_summary_
    A estrutura de dados da classe a ser retornada e construida:
    {'id':self.id,
    'chargingRateUnit': self.chargingRateUnit ,
    'duration': self.duration ,
    'chargingSchedulePeriod': [{'startPeriod': self.currentStartPeriod,
                                'limit': self.currentLimit}]}

    startPeriod type is datetime.datetime
    """
    def __init__(self, evse_id:str, id:int, charging_rate_unit:str, duration:float, charging_schedule_period:list):
        self._evse_id = evse_id
        self._id = id
        self._chargingRateUnit = charging_rate_unit #"W"
        self._duration = duration
        self._chargingSchedulePeriod = charging_schedule_period
        self._currentSchedulePeriodIndex = 0
        self._currentSchedule = charging_schedule_period[self._currentSchedulePeriodIndex]
        self._currentStartPeriod = charging_schedule_period[self._currentSchedulePeriodIndex]["startPeriod"]
        self._currentLimit = charging_schedule_period[self._currentSchedulePeriodIndex]["limit"]
        self._currentDuration = self.calculate_current_duration()
        self._currentTime = datetime.datetime.now()
        self._remainingTime = 0.0 #Tempo que resta para cumprir o periodo atual do planeamento
        
    @property
    def evse_id(self):
        return self._evse_id
    
    @evse_id.setter
    def evse_id(self, value):
        self._evse_id = value
        self.update_tot_schedule()
    
    @property
    def id(self):
        return self._id
    
    @id.setter
    def id(self, value):
        self._id = value
        self.update_tot_schedule()
    
    @property
    def chargingRateUnit(self):
        return self._chargingRateUnit
    
    @chargingRateUnit.setter
    def chargingRateUnit(self, value):
        self._chargingRateUnit = value
        self.update_tot_schedule()
    
    @property
    def duration(self):
        return self._duration
    
    @duration.setter
    def duration(self, value):
        self._duration = value
        self.update_tot_schedule()
    
    @property
    def chargingSchedulePeriod(self):
        return self._chargingSchedulePeriod
    
    @chargingSchedulePeriod.setter
    def chargingSchedulePeriod(self, value):
        self._chargingSchedulePeriod = value
        self.update_tot_schedule()
    
    @property
    def currentSchedulePeriodIndex(self):
        return self._currentSchedulePeriodIndex
    
    @currentSchedulePeriodIndex.setter
    def currentSchedulePeriodIndex(self, value):
        self._currentSchedulePeriodIndex = value
        self.update_tot_schedule()
    
    @property
    def currentSchedule(self):
        return self._currentSchedule
    
    @currentSchedule.setter
    def currentSchedule(self, value):
        self._currentSchedule = value
        self.update_tot_schedule()
    
    @property
    def currentStartPeriod(self):
        return self._currentStartPeriod
    
    @currentStartPeriod.setter
    def currentStartPeriod(self, value):
        self._currentStartPeriod = value
        self.update_tot_schedule()
    
    @property
    def currentLimit(self):
        return self._currentLimit
    
    @currentLimit.setter
    def currentLimit(self, value):
        self._currentLimit = value
        self.update_tot_schedule()
    
    @property
    def currentDuration(self):
        return self._currentDuration
    
    @currentDuration.setter
    def currentDuration(self, value):
        self._currentDuration = value
        self.update_tot_schedule()
    
    @property
    def currentTime(self):
        return self._currentTime
    
    @currentTime.setter
    def currentTime(self, value):
        self._currentTime = value
        self.update_tot_schedule()
    
    @property
    def remainingTime(self):
        return self._remainingTime
    
    @remainingTime.setter
    def remainingTime(self, value):
        self._remainingTime = value
        self.update_tot_schedule()
    
    @property
    def tot_schedule(self):
        return {
            'id': self.id,
            'chargingRateUnit': self.chargingRateUnit,
            'duration': self.duration,
            'chargingSchedulePeriod': self.chargingSchedulePeriod
        }
    #Para manter o tempo atualizado
    def update_current_time(self):
        self.currentTime = datetime.datetime.now()
    
    def update_tot_schedule(self):
        #self.currentTime = datetime.datetime.now()
        self._remainingTime = self.calc_remaining_time()
        self._currentSchedule = self._chargingSchedulePeriod[self._currentSchedulePeriodIndex]
        self._currentStartPeriod = self._currentSchedule["startPeriod"]
        self._currentLimit = self._currentSchedule["limit"]
        self._currentDuration = self.calculate_current_duration()
    #Para atualizar o tot_schedule com as variáveis interanas
    # def update_current_sched_period(self):
    #     self.remaining_time = self.calc_remaining_time()
    #     self.calculate_current_duration()
    #     self.currentSchedule = self.chargingSchedulePeriod[self.currentSchedulePeriodIndex]
    #     self.currentStartPeriod = self.currentSchedule["startPeriod"]
    #     self.currentLimit = self.currentSchedule["limit"]
    #     self.currentDuration = self.calculate_current_duration()

    def calculate_current_duration(self):
        #Se existir um segundo campo do Charging Schecule Period
        print(f"Current index: {self.currentSchedulePeriodIndex} | Tamanho do schedule {len(self.chargingSchedulePeriod)}")
        if self.currentSchedulePeriodIndex + 1 < len(self.chargingSchedulePeriod):
            #Calcula o intervalo temporal
            delta = (self.chargingSchedulePeriod[self.currentSchedulePeriodIndex + 1]["startPeriod"]-
                   self.chargingSchedulePeriod[self.currentSchedulePeriodIndex]["startPeriod"])
            return delta.total_seconds()
        else:
            #Utiliza a duração fornecida na criação da classe
            return self.duration        
    
    def set_new_schedule(self,
                        evse_id:str, 
                        id:int, 
                        charging_rate_unit:str, 
                        duration:float,
                        charging_schedule_period:list):
        self.evse_id = evse_id
        self.id = id
        self.chargingRateUnit = charging_rate_unit #"W"
        self.duration = duration
        self.chargingSchedulePeriod = charging_schedule_period
        self.currentSchedulePeriodIndex = 0
        self.currentSchedule = charging_schedule_period[self.currentSchedulePeriodIndex]
        self.currentStartPeriod:datetime.datetime = charging_schedule_period[self.currentSchedulePeriodIndex]["startPeriod"]
        self.currentLimit = charging_schedule_period[self.currentSchedulePeriodIndex]["limit"]
        #Se existir um segundo campo do Charging Schecule Period
        if charging_schedule_period[self.currentSchedulePeriodIndex + 1]["startPeriod"]:
            #Calcula o intervalo temporal
            self.currentDuration = (charging_schedule_period[self.currentSchedulePeriodIndex + 1]["startPeriod"] - 
                                    charging_schedule_period[self.currentSchedulePeriodIndex]["startPeriod"])
        else:
            #Utiliza a duração fornecida na criação da classe
            self.currentDuration = duration
        self.currentTime = datetime.datetime.now()
        self.remainingTime: float = 0.0
        self.tot_schedule = {
            'id':self.id,
            'chargingRateUnit': self.chargingRateUnit,
            'duration': self.duration,
            'chargingSchedulePeriod': self.chargingSchedulePeriod
            }
        return self.tot_schedule
    
    ##############################################################################################################################
    ############################################## Execute Schedule Methods ######################################################
    ##############################################################################################################################
    
    def calc_remaining_time(self):
        time_difference = self.currentTime - self.currentStartPeriod
        remaining_time = self.currentDuration - time_difference.total_seconds()
        # Se tempo restante for menor que 5 segundos
        print(f"REMAINING TIME: {remaining_time}")
        #Recomeçar remaining time de um novo periodo
        if remaining_time < 1:
            # Atualiza o periodo atual para o próximo
            self.currentSchedulePeriodIndex = self.currentSchedulePeriodIndex + 1
            # Se ainda há períodos restantes
            if self.currentSchedulePeriodIndex < len(self.chargingSchedulePeriod):
                time_difference = self.currentTime - self.currentStartPeriod
                remaining_time = self.currentDuration - time_difference.total_seconds()
            else:
                remaining_time = self.duration
        return remaining_time

    def get_current_power(self):
        self.calc_remaining_time()
        return self.currentLimit