% Este script, através dos ficheiros Excel disponibilizados pelo site de
% informação da REN (http://www.centrodeinformacao.ren.pt/) calcula o excesso
% de energia renovável que existe em determinados dias
% As informações do preço da energia foram adquiridas em:
%http://www.mercado.ren.pt/PT/Electr/InfoMercado/InfOp/MercOmel/Paginas/Precos.aspx
%% Dados referentes a 9 de agosto de 2016
data = xlsread('9ago.xlsx'); %Colocar nome do ficheiro. Por vezes ocorre
um erro que tem de se abrir o Excel normalmente e gravar novamente
carvao = data(:,3);
fuel = data(:,4);
gas = data(:,5);
albufeiras = data(:,6);
fios = data(:,7);
import9 = data(:,8);
export9 = data(:,9);
PRE_hidro = data(:,10);
PRE_termico = data(:,11);
PRE_eolica = data(:,12);
PRE_foto = data(:,13);
PRE_ondas = data(:,14);
bombagem9 = data(:,15);
consumo9 = data(:,16);
producao9 = carvao + fuel + gas + albufeiras + fios + PRE_hidro +
PRE_termico + PRE_eolica + PRE_foto + PRE_ondas;
renovavel9 = albufeiras + fios +PRE_hidro + PRE_termico + PRE_eolica +
PRE_foto + PRE_ondas;
excesso9 = renovavel9 - consumo9;
preco9 = [45.1000000000000 42.5000000000000 37 35.2600000000000
32.5300000000000 32.5000000000000 39.7300000000000 43.7800000000000
44.8000000000000 43.4700000000000 39.4100000000000 40.8500000000000
42.1300000000000 43.4700000000000 43.4700000000000 38.7100000000000 38 38 37
35.8000000000000 38.4100000000000 44 44 36.0700000000000];
preco9 = preco9 / 1000;
%% Dados referentes a 10 de agosto de 2016
data = xlsread('10ago.xlsx'); %Colocar nome do ficheiro. Por vezes ocorre
um erro que tem de se abrir o Excel normalmente e gravar novamente pois o
ficheiro, segundo o Excel, provém de fontes não seguras.
carvao = data(:,3);
fuel = data(:,4);
gas = data(:,5);
albufeiras = data(:,6);
fios = data(:,7);
import10 = data(:,8);
export10 = data(:,9);
PRE_hidro = data(:,10);
PRE_termico = data(:,11);
PRE_eolica = data(:,12);
PRE_foto = data(:,13);
PRE_ondas = data(:,14);
bombagem10 = data(:,15);
consumo10 = data(:,16);

producao10 = carvao + fuel + gas + albufeiras + fios + PRE_hidro +
PRE_termico + PRE_eolica + PRE_foto + PRE_ondas;
renovavel10 = albufeiras + fios +PRE_hidro + PRE_termico + PRE_eolica +
PRE_foto + PRE_ondas;
excesso10 = renovavel10 - consumo10;
preco10 = [31.3400000000000 30.5200000000000 26.9000000000000 26
25.9700000000000 26.2200000000000 28.3900000000000 31.0500000000000
33.9500000000000 38.9800000000000 38.6300000000000 38.2900000000000
36.7000000000000 38.4400000000000 38.4400000000000 36.0900000000000
36.9000000000000 38.2900000000000 39.1200000000000 40.8400000000000
44.8400000000000 47.2000000000000 47 39.7000000000000];
preco10 = preco10 / 1000;
%% Dados referentes a 2 de fevereiro de 2017
data = xlsread('2fev.xlsx'); %Colocar nome do ficheiro. Por vezes ocorre
um erro que tem de se abrir o excel normalmente e gravar novamente pois o
ficheiro, segundo o Excel, provém de fontes não seguras.
carvao = data(:,3);
fuel = data(:,4);
gas = data(:,5);
albufeiras = data(:,6);
fios = data(:,7);
import2 = data(:,8);
export2 = data(:,9);
PRE_hidro = data(:,10);
PRE_termico = data(:,11);
PRE_eolica = data(:,12);
PRE_foto = data(:,13);
PRE_ondas = data(:,14);
bombagem2 = data(:,15);
consumo2 = data(:,16);
producao2 = carvao + fuel + gas + albufeiras + fios + PRE_hidro +
PRE_termico + PRE_eolica + PRE_foto + PRE_ondas;
renovavel2 = albufeiras + fios +PRE_hidro + PRE_termico + PRE_eolica +
PRE_foto + PRE_ondas;
excesso2 = renovavel2 - consumo2;
preco2 = [41.1100000000000 38.7400000000000 36.9400000000000
33.9000000000000 33.8500000000000 33.7700000000000 39.9100000000000
55.5800000000000 57.1900000000000 59.1000000000000 58.6900000000000
57.6600000000000 57.6600000000000 54.4400000000000 50.9000000000000
47.1000000000000 45.9800000000000 48.8000000000000 56.1100000000000
60.7900000000000 61.2300000000000 60.7100000000000 49.6100000000000
42.1200000000000];
preco2 = preco2 / 1000;
%% Dados referentes a 3 de fevereiro de 2017
data = xlsread('3fev.xlsx'); %Colocar nome do ficheiro. Por vezes ocorre
um erro que tem de se abrir o excel normalmente e gravar novamente pois o
ficheiro, segundo o Excel, provém de fontes não seguras.
carvao = data(:,3);
fuel = data(:,4);
gas = data(:,5);
albufeiras = data(:,6);
fios = data(:,7);
import3 = data(:,8);
export3 = data(:,9);
PRE_hidro = data(:,10);
PRE_termico = data(:,11);
PRE_eolica = data(:,12);
PRE_foto = data(:,13);
PRE_ondas = data(:,14);
bombagem3 = data(:,15);
consumo3 = data(:,16);
producao3 = carvao + fuel + gas + albufeiras + fios + PRE_hidro +
PRE_termico + PRE_eolica + PRE_foto + PRE_ondas;
renovavel3 = albufeiras + fios +PRE_hidro + PRE_termico + PRE_eolica +
PRE_foto + PRE_ondas;
excesso3 = renovavel3 - consumo3;
preco3 = [39.8700000000000 34.9200000000000 34.2600000000000
32.5500000000000 32.4900000000000 34.5800000000000 40 52.6000000000000
53.6200000000000 55.7900000000000 56.6700000000000 55.9700000000000
54.3700000000000 53.6700000000000 51.9600000000000 48.4700000000000
47.4700000000000 52.0100000000000 55.7900000000000 58.2900000000000
53.6900000000000 52.6200000000000 44.2500000000000 39.8500000000000];
preco3 = preco3 / 1000;
%% Associações de dias de modo a ter uma janela não de um mas de dois dias
% 9 com 10 de agosto
excesso9_10(1:96) = excesso9;
excesso9_10(97:192) = excesso10;
producao9_10(1:96) = producao9;
producao9_10(97:192) = producao10;
consumo9_10(1:96) = consumo9;
consumo9_10(97:192) = consumo10;
bombagem9_10(1:96) = bombagem9;
bombagem9_10(97:192) = bombagem10;
renovavel9_10(1:96) = renovavel9;
renovavel9_10(97:192) = renovavel10;
export9_10(1:96) = export9;
export9_10(97:192) = export10;
import9_10(1:96) = import9;
import9_10(97:192) = import10;
%2 com 3 de fevereiro
excesso2_3(1:96) = excesso2;
excesso2_3(97:192) = excesso3;
producao2_3(1:96) = producao2;
producao2_3(97:192) = producao3;
consumo2_3(1:96) = consumo2;
consumo2_3(97:192) = consumo3;
bombagem2_3(1:96) = bombagem2;
bombagem2_3(97:192) = bombagem3;
renovavel2_3(1:96) = renovavel2;
renovavel2_3(97:192) = renovavel3;
export2_3(1:96) = export3;
export2_3(97:192) = export3;
import2_3(1:96) = import3;
import2_3(97:192) = import3;
%Os preços estão variam a cada hora. É preciso ter valores de 15 em 15
mim tal como os diagramas de energia
i=1;
for j=1:24 %Preços de dia 2 com 96 valores.
preco2_96(i) = preco2(j);
i=i+1;
preco2_96(i) = preco2(j);
i=i+1;
preco2_96(i) = preco2(j);
i=i+1;
preco2_96(i) = preco2(j);
i=i+1;
end
i=1;
for j=1:24 %Preços de dia 3 com 96 valores.
preco3_96(i) = preco3(j);
i=i+1;
preco3_96(i) = preco3(j);
i=i+1;
preco3_96(i) = preco3(j);
i=i+1;
preco3_96(i) = preco3(j);
i=i+1;
end
preco2_3(1:96) = preco2_96;
preco2_3(97:192) = preco3_96;
i=1;
for j=1:24 %Preços de dia 9 com 96 valores.
preco9_96(i) = preco9(j);
i=i+1;
preco9_96(i) = preco9(j);
i=i+1;
preco9_96(i) = preco9(j);
i=i+1;
preco9_96(i) = preco9(j);
i=i+1;
end
i=1;
for j=1:24 %Preços de dia 3 com 96 valores.
preco10_96(i) = preco10(j);
i=i+1;
preco10_96(i) = preco10(j);
i=i+1;
preco10_96(i) = preco10(j);
i=i+1;
preco10_96(i) = preco10(j);
i=i+1;
end
preco9_10(1:96) = preco9_96;
preco9_10(97:192) = preco10_96;
%Preços tarifa bi-horária
n = 0.1942;
v = 0.1014;
bi = [v v v v v v v v n n n n n n n n n n n n n n v v];
i = 1;
for j=1:24
bi_96(i) = bi(j);
i=i+1;
bi_96(i) = bi(j);
i=i+1;
bi_96(i) = bi(j);
i=i+1;
bi_96(i) = bi(j);
i=i+1;
end
bi_2_96(1:96) = bi_96; %Adaptar tarifa bi-horária para 2 dias
bi_2_96(97:192) = bi_96;
bi_2_96 = bi_2_96 * 1.23; %(IVA)
%% Graficos 9 e 10 de agosto de 2016
x = 0:0.25:47.75;
figure
subplot(3,1,1) % Diagrama Nacional
hold on
grid on
yyaxis left
ylabel('MW','fontweight','bold')
a1 = area(x,consumo9_10+bombagem9_10);
a1.FaceColor = [255/255;211/255;155/255];
a2 = area(x,producao9_10);
a2.FaceColor = [191/255;239/255;255/255];
plot(x,consumo9_10 + bombagem9_10,'b','LineWidth',2);
plot(x,consumo9_10,'k','LineWidth',4);
plot(x,renovavel9_10,'g','LineWidth',2)
yyaxis right
plot(x,preco9_10)
ylabel('E/MWh','fontweight','bold')
title('Diagrama de Consumo Total - 9 e 10 de agosto de
2016','fontweight','bold','fontsize',14)
legend('Importação','Produção','Consumo+Bombagem','Consumo','Renováve
l','Custo Energia','Location','southeast')
xlabel('Horas','fontweight','bold');
horizontal = line([0 48],[0 0]); %Linha horizontal y = 0
horizontal.Color = 'black';
set(gca,'XTick',0:2:48); %Aumentar o número de espaçamentos no eixo x
xticklabels({0 2 4 6 8 10 12 14 16 18 20 22 24 2 4 6 8 10 12 14 16 18
20 22 24})
xlim([0 48])
subplot(3,1,2) % Balanço Renovável
hold on
grid on
aux1 = excesso9_10;
a3 = area(x,aux1);
a3.FaceColor = [202/255;255/255;112/255];
title('Balanço Energia Renovável - 9 e 10 de agosto de 2016 (face ao
consumo)','fontweight','bold','fontsize',14)
legend('Balanço energia renovável')
ylabel('MW','fontweight','bold')
xlabel('Horas','fontweight','bold');
horizontal = line([0 48],[0 0]); %Linha horizontal y = 0
horizontal.Color = 'black';
set(gca,'XTick',0:2:48); %Aumentar o número de espaçamentos no eixo x
xticklabels({0 2 4 6 8 10 12 14 16 18 20 22 24 2 4 6 8 10 12 14 16 18
20 22 24})
xlim([0 48])
subplot(3,1,3); %Saldo Importador e Bombagem
hold on
grid on
a4 = area(x,bombagem9_10);
a4.FaceColor = [56/255;176/255;222/255];
alpha(.7)
a5 = area(x,-export9_10);
a5.FaceColor = [255/255 127/255 36/255];
a6 = area(x,import9_10);
a6.FaceColor = [255/255;211/255;155/255];
title('Saldo Importador e
Bombagem','fontweight','bold','fontsize',14)
legend('Bombagem','Exportação','Importação');
ylabel('MW','fontweight','bold')
xlabel('Horas','fontweight','bold');
xlim([0 23.5])
set(gca,'XTick',0:1:24); %Aumentar o número de espaçamentos no eixo x
%% Gráficos 2 e 3 de fevereiro de 2017
figure
subplot(3,1,1) % Diagrama Nacional
hold on
grid on
yyaxis left
ylabel('MW','fontweight','bold')
a7 = area(x,consumo2_3+bombagem2_3);
a7.FaceColor = [255/255;211/255;155/255];
a8 = area(x,producao2_3);
a8.FaceColor = [191/255;239/255;255/255];
plot(x,consumo2_3 + bombagem2_3,'b','LineWidth',2);
plot(x,consumo2_3,'k','LineWidth',4);
plot(x,renovavel2_3,'g','LineWidth',2)
yyaxis right
plot(x,preco2_3)
ylabel('E/MWh','fontweight','bold')
title('Diagrama de Consumo Total - 2 e 3 de fevereiro de
2017','fontweight','bold','fontsize',14)
legend('Importação','Produção','Consumo+Bombagem','Consumo','Renovave
l','Custo Energia','Location','southeast')
xlabel('Horas','fontweight','bold');
horizontal = line([0 48],[0 0]); %Linha horizontal y = 0
horizontal.Color = 'black';
set(gca,'XTick',0:2:48); %Aumentar o número de espaçamentos no eixo x
xticklabels({0 2 4 6 8 10 12 14 16 18 20 22 24 2 4 6 8 10 12 14 16 18
20 22 24})
xlim([0 48])
subplot(3,1,2) % Balanço Renovável
grid on
plot(x,excesso2_3)
aux2 = excesso2_3;
a9 = area(x,aux2);
a9.FaceColor = [202/255;255/255;112/255];
title('Balanço Energia Renovável - 2 e 3 de fevereiro de 2017 (face
ao consumo)','fontweight','bold','fontsize',14)
legend('Balanço energia renovável')
xlabel('Horas','fontweight','bold');
ylabel('MW','fontweight','bold')
horizontal = line([0 48],[0 0]); %Linha horizontal y = 0
horizontal.Color = 'black';
set(gca,'XTick',0:2:48); %Aumentar o número de espaçamentos no eixo x
xticklabels({0 2 4 6 8 10 12 14 16 18 20 22 24 2 4 6 8 10 12 14 16 18
20 22 24})
xlim([0 48])
subplot(3,1,3); %Saldo Importador e Bombagem
hold on
grid on
a10 = area(x,bombagem2_3);
a10.FaceColor = [56/255;176/255;222/255];
alpha(.7)
a11 = area(x,-export2_3);
a11.FaceColor = [255/255 127/255 36/255];
a12 = area(x,import2_3);
a12.FaceColor = [255/255;211/255;155/255];
title('Saldo Importador e
Bombagem','fontweight','bold','fontsize',14)
legend('Bombagem','Exportação','Importação');
ylabel('MW','fontweight','bold')
xlabel('Horas','fontweight','bold');
xlim([0 23.5])
set(gca,'XTick',0:1:24); %Aumentar o número de espaçamentos no eixo x
%% Preço real pago pelos consumidores
% Estamos a utilizar os dados do MIBEL para termos tarifas variáveis hora a
hora.
% A única incoerência é o seu valor absoluto. Quando houver tarifas em tempo
% real é normal que estas acompanhem a variação do MIBEL, mas o valor
absoluto
% da tarifa que chega ao cliente final é obviamente mais alto (para pagar
% transporte, distribuição, margens de lucro, etc.).
% Assim, para termos valores mais realistas o ideal é utilizar a variação
% da tarifa no MIBEL nesse dia, mas multiplicada por um fator que a relacione
% com o preço final.
% Considerando a tarifa
%http://www.edpsu.pt/pt/particulares/tarifasehorarios/BTN/Pages/TarifasBTNate20.7kVA.aspx
% [ 0,1942*1.23(IVA)*14(horas) + 0,1014*1.23(IVA)*10(horas) ] / 24 (horas)
% Podemos também calcular o preço médio do MIBEL para esse dia durante as
% 24 horas (M) e ter assim o fator que relaciona os preços médios F=C/M
% Basta assim multiplicar os valores do MIBEL por F para no final termos um
% custo da energia médio que corresponde ao custo atual para o cliente final,
% mas com uma variação igual à do MIBEL.
C = (0.1942*1.23*14 + 0.1014*1.23*10) / 24;
M9_10 = mean(preco9_10);
F9_10 = C/M9_10;
M2_3 = mean(preco2_3);
F2_3 = C/M2_3;
preco9_10 = preco9_10 * F9_10;
preco2_3 = preco2_3 * F2_3;
%-------------------------------------------------------------------------
% Alterar daqui para baixo caso se pretenda usar preços bi-horário
excesso9_10 = [x' excesso9_10'/r preco9_10' bi_2_96'];
excesso2_3 = [x' excesso2_3'/r preco2_3' bi_2_96'];
% Inverter comentários
% excesso9_10 = [x' excesso9_10'/r bi_2_96' bi_2_96'];
% excesso2_3 = [x' excesso2_3'/r bi_2_96' bi_2_96'];