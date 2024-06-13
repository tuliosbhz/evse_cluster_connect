import psutil
import speedtest
import time
import json
import os

def get_seconds_to_next_minute():
    current_time = time.localtime()
    seconds_remaining = 60 - current_time.tm_sec
    return seconds_remaining


def monitorar_desempenho():
    # Inicializar o Speedtest
    try:
        teste_velocidade = speedtest.Speedtest()
    except Exception as e:
        print(str(e))
        while True: #Persiste em tentar adquirir um servidor para o teste de internet
            teste_velocidade = speedtest.Speedtest()
            time.sleep(10)
    while True:
        # Calculate time until the next minute mark
        seconds_to_wait = get_seconds_to_next_minute()
        # Wait until the next minute mark
        time.sleep(seconds_to_wait)
        
        # Get current timestamp
        data_hora = time.strftime('%Y-%m-%d %H:%M:%S')
        # Obter o uso da CPU e da memória
        uso_cpu = psutil.cpu_percent()
        uso_memoria = psutil.virtual_memory().percent

        # Realizar o teste de velocidade
        teste_velocidade.get_best_server()
        velocidade_upload = teste_velocidade.upload() / 1024 / 1024
        velocidade_download = teste_velocidade.download() / 1024 / 1024

        # Escrever os dados no arquivo
        results = {'Data hora':data_hora, 
                    'CPU': uso_cpu, 
                    'Memória': uso_memoria, 
                    'Upload': velocidade_upload,                                                  
                    'Download': velocidade_download
                    }
        filename = 'desempenho_base.txt'
            # Check if the file already exists
        if os.path.exists(filename):
            mode = "a"  # If the file exists, open it in append mode
        else:
            mode = "w"  # If the file doesn't exist, open it in write mode
        
        with open(filename, mode) as arquivo:
            json.dump(results, arquivo)
            arquivo.write('\n')
            #arquivo.write(json.dump(results, "a"))
        print(results)

if __name__ == "__main__":
    monitorar_desempenho()
