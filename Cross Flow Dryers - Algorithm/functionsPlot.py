import matplotlib.pyplot as plt
import random
import drawnow
from math import exp, cos
import numpy as np


tempo = np.arange(0.0, 30.0, 0.1)
eixoy1 = []
eixoy2 = []
result = []

plt.ion()
#Função usada para plotar o gráfico
def plotValues():
    plt.title('Valores da saida do PWM') #titulo para o gráfico
    plt.grid(True) #colocar grid no grafico
    plt.ylabel('Valor (%)') #label do eixo y
    plt.plot(tempo, result, 'rx-', label='tempo (s)') #plot do tempo pelos values 
    plt.legend(loc='upper right') # legenda

Tp = 300
Lp = 1000
top_funcao = Tp + Lp

i = 0
while i < len(tempo):
	lm = random.randint(540,561)
	tp = random.randint(95,116)
	eixoy1.append(abs(cos(((tp+lm)/top_funcao)*tempo[i])))
	eixoy2.append(exp(-0.3*((tp+lm)/top_funcao)*tempo[i]))
	i += 1

result = eixoy1
drawnow.drawnow(plotValues)

while input():
	pass

result = eixoy2
drawnow.drawnow(plotValues)

input('exit?')