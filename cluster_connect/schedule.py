import datetime


class Schedule():
    """_summary_
    A estrutura de dados da classe a ser retornada e construída:
    {'id':self.id,
    'chargingRateUnit': self.chargingRateUnit ,
    'duration': self.duration ,
    'chargingSchedulePeriod': [{'startPeriod': self.currentStartPeriod,
                                'limit': self.currentLimit}]}

    startPeriod type is datetime.datetime

    Tem uma diferença agora das simples variáveis do sistema que são representadas por self._variavel (com underline)
    e as propriedades, quando quero atualizar algum valor devo utilizar a propriedade self.variavel (sem underscore)
    exitem variáveis que são somente propriedades como current_time, remaining_time que são atualizadas automaticamente para cumprir o planeamento de carga atual
    """
    def __init__(self, evse_id:str, id:int, charging_rate_unit:str, duration:float, charging_schedule_period:list):
        self.evse_id = evse_id
        self.id = id
        self.chargingRateUnit = charging_rate_unit  # "W"
        self.duration = duration
        self.chargingSchedulePeriod = charging_schedule_period
        self.currentPeriodIndex = 0
        self.currentPeriod:dict = charging_schedule_period[self.currentPeriodIndex]
        self.currentStartPeriod = charging_schedule_period[self.currentPeriodIndex]["startPeriod"]
        self.currentLimit = charging_schedule_period[self.currentPeriodIndex]["limit"]
        self.currentDuration = 0.0  # self.calculate_current_duration()
        self._currentTime = datetime.datetime.now()
        self._remainingTime = 0.0 # Tempo que resta para cumprir o período atual do planeamento
        

    #########################################################################
    ## Metodos para reconfigurar parâmetros do planeamento de carregamento ##
    #########################################################################
    def set_evse_id(self, evse_id:str):
        self.evse_id = evse_id

    def set_id(self, id:int):
        self.id = id

    def set_charging_rate_unit(self, charging_rate_unit:str):
        self.chargingRateUnit = charging_rate_unit

    def set_duration(self, duration:float):
        self.duration = duration

    def set_charging_schedule_period(self, charging_schedule_period:list):
        self.chargingSchedulePeriod = charging_schedule_period

    ###########################################################################
    ## Metodos para obter dados transformados do planeamento de carregamento ##
    ###########################################################################
    def get_limit_list(self):
        limitList = [self.chargingSchedulePeriod[period]["limit"] for period in self.chargingSchedulePeriod]
        return limitList
    
    def get_start_period_list(self):
        startPeriodList = [self.chargingSchedulePeriod[period]["startPeriod"] for period in self.chargingSchedulePeriod]
        return startPeriodList
    
    def get_duration_period_list(self):
        duration_list = [delta.total_seconds() for delta in
              (self.chargingSchedulePeriod[i + 1]["startPeriod"] -
               self.chargingSchedulePeriod[i]["startPeriod"]
               for i in range(len(self.chargingSchedulePeriod) - 1))]
        duration_list.append(self.duration)
        return duration_list
    
    ##########################################################################
    #### Metodos para acompanhar o schedule recebido em tempo real ###########
    ##########################################################################
        
    @property
    def currentTime(self):
        self._currentTime = datetime.datetime.now()
        return self._currentTime
    
    @property
    def remainingTime(self):
        # Recalculate remaining time before returning
        time_difference = self.currentTime - self.currentStartPeriod
        self.currentDuration = self.get_current_duration()
        remaining_time = self.currentDuration - time_difference.total_seconds()
        if remaining_time < 1:
            if self.currentPeriodIndex < len(self.chargingSchedulePeriod):
                time_difference = self.currentTime - self.currentStartPeriod
                remaining_time = self.currentDuration - time_difference.total_seconds()
            else:
                remaining_time = self._duration
        self._remainingTime = max(remaining_time, 0.0)
        return self._remainingTime

    def __get_current_schedule(self):
        #Atualiza internamente para o schedule atual e depois retorna o schedule atual
        self.currentPeriod = self.chargingSchedulePeriod[self.currentPeriodIndex]
        return self.currentPeriod

    def get_current_start_period(self):
        currentPeriod = self.__get_current_schedule()
        self.currentStartPeriod = currentPeriod["startPeriod"]
        return self.currentStartPeriod

    def get_current_limit(self):
        currentPeriod = self.__get_current_schedule()
        self.currentLimit = currentPeriod["limit"]
        return self.currentLimit
    
    def set_current_period_index(self):
        if self.remainingTime < 1 and (self.currentPeriodIndex + 1 < len(self.chargingSchedulePeriod)):
            self.currentPeriodIndex += 1
    
    def get_current_duration(self):
        if self.currentPeriodIndex + 1 < len(self.chargingSchedulePeriod):
            #Calcula o intervalo temporal
            delta = (self.chargingSchedulePeriod[self.currentPeriodIndex + 1]["startPeriod"]-
                    self.chargingSchedulePeriod[self.currentPeriodIndex]["startPeriod"])
            self.currentDuration = delta.total_seconds()
        else:
            #Utiliza a duração fornecida na criação da classe
            self.currentDuration = self.duration    
        return self.currentDuration

    def update_current_variables(self):
        #Atualiza o indice pelo qual o periodo é regido
        self.set_current_period_index()
        self.get_current_start_period()
        self.get_current_limit()

    def get_schedule(self):
        return {
            'id': self.id,
            'chargingRateUnit': self.chargingRateUnit,
            'duration': self.duration,
            'chargingSchedulePeriod': self.chargingSchedulePeriod
        }        
