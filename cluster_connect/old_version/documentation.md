    #Função que calcula a divisão de potência entre os carregadores         
    def sch_equal_power_division(self, max_power_cluster, with_authentication:bool=False):
        
        if with_authentication:
            active_chargers = self.auth_chargers()
        else:
            active_chargers = self.plugged_chargers()
        try:
            self.update_sched_cluster_data(max_power_cluster)
            sched_clu_data = self.__sched_cluster_parameters
            #Verifica se carregador cumpre os requisitos para receber potência
            if self.id in active_chargers:
                #self.__schedule = self.schedule_calculation()
                calc_power = max_power_cluster / active_chargers
                #Verifica se está incluida nas variáveis de contexto do cluster
                if self.id in sched_clu_data:
                    #O maximo de potência calculada não pode ser mais do que o máximo nominal
                    if calc_power > self.__power_capacity:
                        sched_clu_data[self.id].selected_max_power = self.__limit_power
                    else:
                        sched_clu_data[self.id].selected_max_power = calc_power
                #Atualiza os dados de sessão individuais no grupo de carregadores
                else:
                    session_params = self.get_evse_data_from_db(self.id)
                    self.update_sim_params_to_cluster(self.id,session_params)
            else: 
                sched_clu_data[self.id].selected_max_power = 0
            
            #Atualiza no cluster e base de dados o novo schedule
            self.update_sched_params_on_cluster(self.id, sched_clu_data[self.id])
            self.update_sched_params_on_db()
        except Exception as error:
            logging.error(f"CALCULATE_SCHEDULE: {str(error)}")
        finally:
            return self.__sched_cluster_parameters

Na funcão sch_equal_power_division dentro da classe Charger é executado os seguintes passos:

- Verificação dos prerequisitos para receber potência, se o sistema de carregamento possuir autenticação o prerequisito é que os carregador em questão esteja autenticado, se não, é que o carregador esteja conectado
- Atualização dos dados que são sincronizados de schedule antes do novo calculo 
- Calculo  do agendamento de carregamento
- Verificação adequação aos limites da capacidade de potência de carregamento individual