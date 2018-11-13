import serial
import matplotlib.pyplot as plt
import drawnow

#Valores eixo y
values = []
#Valores eixo x
eixox = []

#plt.ion()
cnt=0

#Obtem uma palavra de 8 bits da porta COM3 a uma taxa de 9600 bit/s usando a paridade par para verificar
#a integridade do dado recebido
serialArduino = serial.Serial('COM3', 9600, parity=serial.PARITY_EVEN, bytesize=serial.EIGHTBITS)

#Função usada para plotar o gráfico
def plotValues():
    plt.title('Valores da saida do PWM') #titulo para o gráfico
    plt.grid(True) #colocar grid no grafico
    plt.ylabel('Valor (%)') #label do eixo y
    plt.plot(eixox, values, 'rx-', label='tempo (s)') #plot do eixox pelos values 
    plt.legend(loc='upper right') # legenda

time = 0
print("Esperando")

#Enquanto os segundos forem menores que 30 (usado 29.5 por causa de erro de precisão)
while time <= 30:
    #Aguarda até obter centésimos times
    while (serialArduino.inWaiting()==0):
        pass
    pwm_value = serialArduino.read(1) # ler um byte (valor correspondente ao pwm)

    #check if valid value can be casted
    try:
        #Converte os valores recebidos de byte para inteiro
        pwm_value = int(pwm_value) # conversão 'byte' para 'int' (garantido pois só é 1 byte transmitido pelo UDR0 )
        
        print(str(time) + " : " + str(pwm_value))

        #Insere os segundos e o x(t) domínio do plot
        eixox.append(time)
        values.append(pwm_value)

        #Atualiza o plot
        drawnow.drawnow(plotValues)
    except ValueError:
        print("Inválido! Impossível converter")

    time += 0.25
serialArduino.close()
