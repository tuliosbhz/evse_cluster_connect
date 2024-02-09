# Planeamento de testes

Endereços de integrantes do cluster:

| Endereço | Hostname | Porta selecionada |
|----------|----------|-------------------|
| 192.168.219.8 | inescevse002 | :55000 |
| 192.168.219.6 | inescevse003 | :56000 |
| 192.168.219.4 | inescevse004 | :57000 |
| 192.168.219.141 | inescevse006 | :58000 |
| 192.168.219.140 | inescevse001 | :59000 |

## Experimento 01

### Configuração da rede: 
- Número de nós: 2
- Tamanho dos pedidos: [10, 2100]
- Pedidos por segundo: [1, 300] #Valor baseado em artigo que realiza testes de desempenho na rede

### Descrição do experimento
- Executar o ficheiro "benchmark_kpy.py node_exp_full" 
- Resultados serão registados na pasta results/{endereço_do_no}.txt
- Executar o comando:
~~~~
scp pi@192.168.219.6:/evse_cluster_connect/benchmarks/results/192.168.219.6_56000_nodes_2.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.4:/evse_cluster_connect/benchmarks/results/192.168.219.4_57000_nodes_2.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results
~~~~
- [Opcional] No repositório local no PC executar o ficheiro create_csv_from_results.py

## Experimento 02

### Configuração da rede: 
- Número de nós: 3
- Tamanho dos pedidos: [10, 2100]
- Pedidos por segundo: [1, 300] #Valor baseado em artigo que realiza testes de desempenho na rede

### Descrição do experimento
- Executar o ficheiro "benchmark_kpy.py node_exp_full" 
- Resultados serão registados na pasta results/{endereço_do_no}.txt
- Executar o comando:
~~~~
scp pi@192.168.219.6:/evse_cluster_connect/benchmarks/results/192.168.219.6_56000_nodes_3.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.4:/evse_cluster_connect/benchmarks/results/192.168.219.4_57000_nodes_3.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.8:/evse_cluster_connect/benchmarks/results/192.168.219.8_55000_nodes_3.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results
~~~~
- [Opcional] No repositório local no PC executar o ficheiro create_csv_from_results.py

## Experimento 03

### Configuração da rede: 
- Número de nós: 4
- Tamanho dos pedidos: [10, 2100]
- Pedidos por segundo: [1, 300] #Valor baseado em artigo que realiza testes de desempenho na rede

### Descrição do experimento
- Executar o ficheiro "benchmark_kpy.py node_exp_full" 
- Resultados serão registados na pasta results/{endereço_do_no}.txt
- Executar o comando:
~~~~
scp pi@192.168.219.6:/evse_cluster_connect/benchmarks/results/192.168.219.6_56000_nodes_4.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.4:/evse_cluster_connect/benchmarks/results/192.168.219.4_57000_nodes_4.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.8:/evse_cluster_connect/benchmarks/results/192.168.219.8_55000_nodes_4.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.141:/evse_cluster_connect/benchmarks/results/192.168.219.141_58000_nodes_4.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results
~~~~
- [Opcional] No repositório local no PC executar o ficheiro create_csv_from_results.py

## Experimento 04

### Configuração da rede: 
- Número de nós: 5
- Tamanho dos pedidos: [10, 2100]
- Pedidos por segundo: [1, 300] #Valor baseado em artigo que realiza testes de desempenho na rede

### Descrição do experimento
- Executar o ficheiro "benchmark_kpy.py node_exp_full" 
- Resultados serão registados na pasta results/{endereço_do_no}.txt
- Executar o comando:
~~~~
scp pi@192.168.219.6:/evse_cluster_connect/benchmarks/results/192.168.219.6_56000_nodes_5.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.4:/evse_cluster_connect/benchmarks/results/192.168.219.4_57000_nodes_5.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.8:/evse_cluster_connect/benchmarks/results/192.168.219.8_55000_nodes_5.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.141:/evse_cluster_connect/benchmarks/results/192.168.219.141_58000_nodes_5.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results

scp pi@192.168.219.140:/evse_cluster_connect/benchmarks/results/192.168.219.140_59000_nodes_5.txt C:\Users\tulio.soares\Documents\GitHub\evse_cluster_connect\benchmarks\results
~~~~
- [Opcional] No repositório local no PC executar o ficheiro create_csv_from_results.py

