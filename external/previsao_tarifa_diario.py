import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def read_excel(file):
    data = pd.read_excel(file, header=None).values
    return data

def calculate_variables(data):
    carvao = data[:, 2]
    fuel = data[:, 3]
    gas = data[:, 4]
    albufeiras = data[:, 5]
    fios = data[:, 6]
    PRE_hidro = data[:, 7]
    PRE_termico = data[:, 8]
    PRE_eolica = data[:, 9]
    PRE_foto = data[:, 10]
    PRE_ondas = data[:, 11]
    bombagem = data[:, 12]
    consumo = data[:, 13]
    
    producao = carvao + fuel + gas + albufeiras + fios + PRE_hidro + PRE_termico + PRE_eolica + PRE_foto + PRE_ondas
    renovavel = albufeiras + fios + PRE_hidro + PRE_termico + PRE_eolica + PRE_foto + PRE_ondas
    excesso = renovavel - consumo
    
    return producao, renovavel, excesso

def preprocess_prices(prices):
    prices = prices / 1000
    return prices

# Load data
data_9_aug = read_excel('9ago.xlsx')
data_10_aug = read_excel('10ago.xlsx')
data_2_feb = read_excel('2fev.xlsx')
data_3_feb = read_excel('3fev.xlsx')

# Calculate variables for each day
producao9, renovavel9, excesso9 = calculate_variables(data_9_aug)
producao10, renovavel10, excesso10 = calculate_variables(data_10_aug)
producao2, renovavel2, excesso2 = calculate_variables(data_2_feb)
producao3, renovavel3, excesso3 = calculate_variables(data_3_feb)

# Prices
preco9 = np.array([45.1, 42.5, 37, 35.26, 32.53, 32.5, 39.73, 43.78, 44.8, 43.47, 39.41, 40.85, 42.13, 43.47, 43.47, 38.71, 38, 38, 37, 35.8, 38.41, 44, 44, 36.07]) / 1000
preco10 = np.array([31.34, 30.52, 26.9, 26, 25.97, 26.22, 28.39, 31.05, 33.95, 38.98, 38.63, 38.29, 36.7, 38.44, 38.44, 36.09, 36.9, 38.29, 39.12, 40.84, 44.84, 47.2, 47, 39.7]) / 1000
preco2 = np.array([41.11, 38.74, 36.94, 33.9, 33.85, 33.77, 39.91, 55.58, 57.19, 59.1, 58.69, 57.66, 57.66, 54.44, 50.9, 47.1, 45.98, 48.8, 56.11, 60.79, 61.23, 60.71, 49.61, 42.12]) / 1000
preco3 = np.array([39.87, 34.92, 34.26, 32.55, 32.49, 34.58, 40, 52.6, 53.62, 55.79, 56.67, 55.97, 54.37, 53.67, 51.96, 48.47, 47.47, 52.01, 55.79, 58.29, 53.69, 52.62, 44.25, 39.85]) / 1000

# Combine data for plotting
excesso9_10 = np.concatenate((excesso9, excesso10))
producao9_10 = np.concatenate((producao9, producao10))
consumo9_10 = np.concatenate((data_9_aug[:, 16], data_10_aug[:, 16]))
bombagem9_10 = np.concatenate((data_9_aug[:, 15], data_10_aug[:, 15]))
renovavel9_10 = np.concatenate((renovavel9, renovavel10))
export9_10 = np.concatenate((data_9_aug[:, 9], data_10_aug[:, 9]))
import9_10 = np.concatenate((data_9_aug[:, 8], data_10_aug[:, 8]))

# Plotting
x = np.arange(0, 48, 0.25)
fig, axs = plt.subplots(3, 1, figsize=(10, 12))

# Diagrama Nacional
axs[0].plot(x, consumo9_10 + bombagem9_10, 'b', linewidth=2, label='Consumo+Bombagem')
axs[0].plot(x, consumo9_10, 'k', linewidth=4, label='Consumo')
axs[0].plot(x, renovavel9_10, 'g', linewidth=2, label='Renovável')
axs[0].fill_between(x, consumo9_10 + bombagem9_10, color=[255/255, 211/255, 155/255], label='Importação')
axs[0].fill_between(x, producao9_10, color=[191/255, 239/255, 255/255], label='Produção')
axs[0].set_title('Diagrama de Consumo Total - 9 e 10 de agosto de 2016', fontsize=14, fontweight='bold')
axs[0].set_ylabel('MW', fontweight='bold')
axs[0].legend(loc='upper left')
axs[0].grid(True)
axs[0].set_xticks(np.arange(0, 49, 2))
axs[0].set_xticklabels(['0', '2', '4', '6', '8', '10', '12', '14', '16', '18', '20', '22', '24', '2', '4', '6', '8', '10', '12', '14', '16', '18', '20', '22', '24'])
axs[0].set_xlim([0, 48])

# Balanço Renovável
axs[1].plot(x, excesso9_10, color='green', label='Balanço energia renovável')
axs[1].fill_between(x, excesso9_10, color=[202/255, 255/255, 112/255])
axs[1].set_title('Balanço Energia Renovável - 9 e 10 de agosto de 2016', fontsize=14, fontweight='bold')
axs[1].set_ylabel('MW', fontweight='bold')
axs[1].legend(loc='upper left')
axs[1].grid(True)
axs[1].set_xticks(np.arange(0, 49, 2))
axs[1].set_xticklabels(['0', '2', '4', '6', '8', '10', '12', '14', '16', '18', '20', '22', '24', '2', '4', '6', '8', '10', '12', '14', '16', '18', '20', '22', '24'])
axs[1].set_xlim([0, 48])

# Saldo Importador e Bombagem
axs[2].fill_between(x, bombagem9_10, color=[56/255, 176/255, 222/255], alpha=0.7, label='Bombagem')
axs[2].fill_between(x, -export9_10, color=[255/255, 127/255, 36/255], label='Exportação')
axs[2].fill_between(x, import9_10, color=[255/255, 211/255, 155/255], label='Importação')
axs[2].set_title('Saldo Importador e Bombagem', fontsize=14, fontweight='bold')
axs[2].set_ylabel('MW', fontweight='bold')
axs[2].legend(loc='upper left')
axs[2].grid(True)
axs[2].set_xticks(np.arange(0, 24))
axs[2].set_xlim([0, 23.5])

plt.xlabel('Horas', fontweight='bold')
plt.tight_layout()
plt.show()
