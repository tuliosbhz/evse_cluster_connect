# Planeamento de testes

Endereços de integrantes do cluster:

| Endereço | Hostname | Porta selecionada | SD card use | kernel version |
|----------|----------|-------------------|-------------|----------------|
| 192.168.219.8 | inescevse002 | :55000 | 21% | Linux 6.1.21-v7+ armv7l |
| 192.168.219.6 | inescevse003 | :56000 | 21% | Linux 6.1.21-v7+ armv7l |
| 192.168.219.4 | inescevse004 | :57000 | 38% | Linux 5.15.76-v7+ armv7l |
| 192.168.219.141 | inescevse006 | :58000 | 21% | Linux 6.1.21-v7+ armv7l |
| 192.168.219.140 | inescevse001 | :59000 | 46% | Linux 5.15.76-v7+ armv7l |
| 192.168.219.7 | inescevse007 | :60000 | 37% | Linux 6.1.21-v7+ armv7l |


## TODO

Pedir ao chat gpt um programa em python para calcular o uso da CPU e da memória dos principais serviços relacionados ao carregador: 
pidstat -u 600 >/var/log/pidstats.log & disown $!

## Experimento 01

### Configuração da rede: 
- Número de nós: 2
- Tamanho dos pedidos: [10, 2100]
- Pedidos por segundo: [1, 300] #Valor baseado em artigo que realiza testes de desempenho na rede

### Descrição do experimento
- Executar o ficheiro "benchmark_kpy.py node_exp_full nds_addr_exp_one.txt" 
- Resultados serão registados na pasta results/{endereço_do_no}.txt
- Executar o comando:
~~~~
scp pi@192.168.219.6:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.6_56000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.4:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.4_57000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results
~~~~
- [Opcional] No repositório local no PC executar o ficheiro create_csv_from_results.py

## Experimento 02

### Configuração da rede: 
- Número de nós: 3
- Tamanho dos pedidos: [10, 2100]
- Pedidos por segundo: [1, 300] #Valor baseado em artigo que realiza testes de desempenho na rede

### Descrição do experimento
- Executar o ficheiro "benchmark_kpy.py node_exp_full nds_addr_exp_two.txt" 
- Resultados serão registados na pasta results/{endereço_do_no}.txt
- Executar o comando:
~~~~
scp pi@192.168.219.8:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.8_55000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.141:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.141_58000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.140:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.140_59000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

~~~~
- [Opcional] No repositório local no PC executar o ficheiro create_csv_from_results.py

## Experimento 03

### Configuração da rede: 
- Número de nós: 4
- Tamanho dos pedidos: [10, 2100]
- Pedidos por segundo: [1, 300] #Valor baseado em artigo que realiza testes de desempenho na rede

### Descrição do experimento
- Executar o ficheiro "benchmark_kpy.py node_exp_full nds_addr_exp_three.txt" 
- Resultados serão registados na pasta results/{endereço_do_no}.txt
- Executar o comando:
~~~~
scp pi@192.168.219.6:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.6_56000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.4:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.4_57000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.8:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.8_55000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.141:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.141_58000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results
~~~~
- [Opcional] No repositório local no PC executar o ficheiro create_csv_from_results.py

## Experimento 04

### Configuração da rede: 
- Número de nós: 5
- Tamanho dos pedidos: [10, 2100]
- Pedidos por segundo: [1, 300] #Valor baseado em artigo que realiza testes de desempenho na rede

### Descrição do experimento
- Executar o ficheiro "benchmark_kpy.py node_exp_full nds_addr_exp_four.txt" 
- Resultados serão registados na pasta results/{endereço_do_no}.txt
- Executar o comando:
~~~~
scp pi@192.168.219.6:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.6_56000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.4:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.4_57000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.8:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.8_55000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.141:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.141_58000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.140:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.140_59000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

~~~~
- [Opcional] No repositório local no PC executar o ficheiro create_csv_from_results.py

## Experimento 05

### Configuração da rede: 
- Número de nós: 5
- Tamanho dos pedidos: [10, 2100]
- Pedidos por segundo: [1, 300] #Valor baseado em artigo que realiza testes de desempenho na rede

### Descrição do experimento
- Executar o ficheiro "benchmark_kpy.py node_exp_full nds_addr_exp_four.txt" 
- Resultados serão registados na pasta results/{endereço_do_no}.txt
- Executar o comando:
~~~~
scp pi@192.168.219.6:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.6_56000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.4:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.4_57000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.8:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.8_55000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.141:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.141_58000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.140:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.140_59000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.7:/home/pi/evse_cluster_connect/benchmarks/results/192.168.219.7_60000.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results
~~~~
- [Opcional] No repositório local no PC executar o ficheiro create_csv_from_results.py


SD card memory used at experiment time: 

pi@inescevse001:~ $ df
Filesystem     1K-blocks     Used Available Use% Mounted on
/dev/root       29757940 12913624  15600600  46% /
devtmpfs          340548        0    340548   0% /dev
tmpfs             472132        0    472132   0% /dev/shm
tmpfs             188856     1020    187836   1% /run
tmpfs               5120        4      5116   1% /run/lock
/dev/mmcblk0p1    258095    50793    207302  20% /boot
tmpfs              94424        0     94424   0% /run/user/1000 

pi@inescevse004:~ $ df
Filesystem     1K-blocks     Used Available Use% Mounted on
/dev/root       29724864 10536028  17925496  38% /
devtmpfs          439044        0    439044   0% /dev
tmpfs             472324        0    472324   0% /dev/shm
tmpfs             188932      944    187988   1% /run
tmpfs               5120        0      5120   0% /run/lock
/dev/mmcblk0p1    258095    50755    207340  20% /boot
tmpfs              94464       20     94444   1% /run/user/1000  

pi@inescevse007:~/evse_cluster_connect $ df
Filesystem     1K-blocks     Used Available Use% Mounted on
/dev/root       29501800 10261572  18009412  37% /
devtmpfs          340460        0    340460   0% /dev
tmpfs             472044        0    472044   0% /dev/shm
tmpfs             188820     1028    187792   1% /run
tmpfs               5120        4      5116   1% /run/lock
/dev/mmcblk0p1    261108    51630    209478  20% /boot
tmpfs              94408        0     94408   0% /run/user/1000 

pi@inescevse002:~/evse_cluster_connect/benchmarks $ df
Filesystem     1K-blocks    Used Available Use% Mounted on
/dev/root       29769160 5863240  22664252  21% /
devtmpfs          340460       0    340460   0% /dev
tmpfs             472044       0    472044   0% /dev/shm
tmpfs             188820     996    187824   1% /run
tmpfs               5120       4      5116   1% /run/lock
/dev/mmcblk0p1    261108   51630    209478  20% /boot
tmpfs              94408       0     94408   0% /run/user/1000

pi@inescevse003:~/evse_cluster_connect/benchmarks $ df
Filesystem     1K-blocks    Used Available Use% Mounted on
/dev/root       29501800 5882480  22388504  21% /
devtmpfs          438956       0    438956   0% /dev
tmpfs             472236       0    472236   0% /dev/shm
tmpfs             188896     900    187996   1% /run
tmpfs               5120       0      5120   0% /run/lock
/dev/mmcblk0p1    261108   51632    209476  20% /boot
tmpfs              94444       0     94444   0% /run/user/1000

pi@inescevse006:~ $ df
Filesystem     1K-blocks    Used Available Use% Mounted on
/dev/root       29501800 5680080  22590904  21% /
devtmpfs          340460       0    340460   0% /dev
tmpfs             472044       0    472044   0% /dev/shm
tmpfs             188820    1028    187792   1% /run
tmpfs               5120       4      5116   1% /run/lock
/dev/mmcblk0p1    261108   51636    209472  20% /boot
tmpfs              94408       0     94408   0% /run/user/1000 

pi@inescevse004:~/evse_cluster_connect/benchmarks $ cat /etc/os-release
PRETTY_NAME="Raspbian GNU/Linux 11 (bullseye)"       
NAME="Raspbian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums" 
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"

pi@inescevse001:~/evse_cluster_connect/benchmarks $ cat /etc/os-release
PRETTY_NAME="Raspbian GNU/Linux 11 (bullseye)"
NAME="Raspbian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"

pi@inescevse007:~/evse_cluster_connect $ cat /etc/os-release 
PRETTY_NAME="Raspbian GNU/Linux 11 (bullseye)"
NAME="Raspbian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"

pi@inescevse002:~/evse_cluster_connect/benchmarks $ cat /etc/os-release
PRETTY_NAME="Raspbian GNU/Linux 11 (bullseye)"
NAME="Raspbian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"

pi@inescevse003:~/evse_cluster_connect/benchmarks $ cat /etc/os-release
PRETTY_NAME="Raspbian GNU/Linux 11 (bullseye)"
NAME="Raspbian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"

pi@inescevse006:~ $ cat /etc/os-release 
PRETTY_NAME="Raspbian GNU/Linux 11 (bullseye)"
NAME="Raspbian GNU/Linux"
VERSION_ID="11"
VERSION="11 (bullseye)"
VERSION_CODENAME=bullseye
ID=raspbian
ID_LIKE=debian
HOME_URL="http://www.raspbian.org/"
SUPPORT_URL="http://www.raspbian.org/RaspbianForums"
BUG_REPORT_URL="http://www.raspbian.org/RaspbianBugs"

