import psutil
import speedtest
import time
import json
import os
def monitorar_desempenho():
    # Inicializar o Speedtest
    teste_velocidade = speedtest.Speedtest()
    while True:
        # Obter o uso da CPU e da memória
        uso_cpu = psutil.cpu_percent()
        uso_memoria = psutil.virtual_memory().percent

        # Realizar o teste de velocidade
        teste_velocidade.get_best_server()
        velocidade_upload = teste_velocidade.upload() / 1024 / 1024
        velocidade_download = teste_velocidade.download() / 1024 / 1024

        # Obter a data e hora atual
        data_hora = time.strftime("%Y-%m-%d %H:%M:%S")

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
            arquivo.write(json.dump(results))

        # Esperar 1 minuto antes de realizar outra medição
        time.sleep(60)

if __name__ == "__main__":
    monitorar_desempenho()
