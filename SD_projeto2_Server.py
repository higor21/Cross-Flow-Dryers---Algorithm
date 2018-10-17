#coding: utf-8

import mraa
from threading import Thread
import time
from datetime import datetime
from Queue import Queue, Empty
from socket import *
from math import cos, exp

print(mraa.getVersion())

# Inicia fila de comunicação entre as threads
fila_aquisicao = Queue()
fila_geracao = Queue()
fila_envio = Queue()
fila_tempo = Queue()
fila_calculo = Queue()

# Variável que indica término do programa (fechamento)
fim = False
# Variável que indica se programa está rodando ou parado
start = False
# Variável que indica o tipo da função que irá regir PWM1 (Led2 e motor)
tipo_funcao = 0   #DEFAULT

# Thread responsável por capturar os dados do ADC (sensores)
def AquisicaoDados(fila_tempo, fila_aquisicao):
	
	# Define os pinos 0 (14), ligado ao sensor de temperatura, e o pino 1 (15), ligado ao sensor de luminosidade, como entradas ADC
	adc_temp = mraa.Aio(0)
	adc_lum = mraa.Aio(1)

	while(True):
	  	#Recebe dados da Thread timer (tempo atual, tempo de envio dos dados)
		tempo_atual = fila_tempo.get()  
 
		#Se -1 for enviado pela fila indicando o fim do programa, a thread é desativada
		if(tempo_atual[0] == -1):
			#Envia comando de extinção para proxima thread (ProcessamentoDados)
			fila_aquisicao.put_nowait((-1, 0, 0, tempo_atual[1]))
			break      
		
		# Envia (tempo atual, valor do sensor de temperatura, valor do sendor de luminosidade, tempo de envio de dados) para a thread ProcessamentoDados
		fila_aquisicao.put_nowait((tempo_atual[0], adc_temp.read(), adc_lum.read(), tempo_atual[1]))

# função dada em sala de aula, na qual o valor gerado depend do intervalo da função 
def z(time):
	if(time <= 10) : # [0,10]
		z = 0.035*time 
	elif(time <= 15) : # ]10,15]
		z = 0.35;
	elif(time <= 20) : # ]15,20]
		z = 0.06*time - 0.55
	elif(time <= 25) : # ]20,25]
		z = 0.65
	else: # ]25,30]
		z = -0.13*time + 3.9
	return z
	  	
			
# Thread responsável por calcular e controlar os valores das saídas do sistema  
def ProcessamentoDados(fila_aquisicao, fila_calculo, fila_envio):
	while(True):
		# Dado obtido da Thread AquisicaoDados (tempo atual, valor do sensor de temperatura, valor do sendor de luminosidade, tempo de envio de dados)
		dado_tempo = fila_aquisicao.get()

		#Se -1 for enviado pela fila indicando saída do programa, a Thread é finalizada
		if(dado_tempo[0] == -1):
			# Envia comando de extinção para as threads GeracaoSinais e Comunicacao:send 
			fila_calculo.put_nowait((-1 , 0, 0, 0, dado_tempo[3]))
			fila_envio.put_nowait((-1, 0))
			break
		
		# foram feitas medições em condições extremas estabelecidas de modo a chegar nesse resultado
		temperatura_max = 300.0
		luminosidade_max = 1000.0

		# valor máximo de qualquer função dada
		top_funcao = temperatura_max + luminosidade_max

		# normalizando o valor de 'z' de modo que seja um valor influente no resultado do PWM
		funcao_z = z(dado_tempo[0])*(temperatura_max + luminosidade_max)
        
		# colocando a influência dos parêmetros na função
		funcao_z = (funcao_z + (dado_tempo[1]+dado_tempo[2]))/(2*top_funcao)
        
		# Dependendo do tipo da funcao definida pelo cliente, programa gera diferentes perfis na saída PWM, onde 
        # * valor1 <=> PWM para ventilador 
        # * valor2 <=> PWM para LED
		if(tipo_funcao == 0 ): # tipo_funcao >> é de escolha do usuário 
			valor1 = funcao_z
			valor2 = abs(cos(((dado_tempo[1]+dado_tempo[2])/top_funcao)*dado_tempo[0]))
		elif(tipo_funcao == 1):
			valor1 = 1 - funcao_z
			valor2 = exp(-((dado_tempo[1]+dado_tempo[2])/top_funcao)*dado_tempo[0])
			
		
		print("Enviando: " + str(dado_tempo[0]) + ", " + str(valor1) + ", " + str(valor2))
		# Se o tempo atual == 30, o programa deve desligar
		if(dado_tempo[0] == 30):
		  	# Portanto é enviado o comando -4 para a Thread Comunicacao:enviaDados, indicando para o cliente o desligamento do sistema
			fila_envio.put_nowait((-4, 0))
			# Enviado o valor de tempo atual igual a 30 para a thread GeracaoSinais
			fila_calculo.put_nowait((dado_tempo[0], 0, 0, 0, dado_tempo[3]))
		# Caso contrário, são enviados as informações necessárias para, respectivamente, as threads GeracaoSinais e Comunicacao:enviaDados
		else:            
			# Enviado (tempo atual, valor PWM1 (Led2 e motor), PWM2 (Led3), Led1, tempo dos envios de dados)
			fila_calculo.put_nowait((dado_tempo[0], valor1, valor2, 1, dado_tempo[3]))
			# Enviado (tempo atual, valor PWM1 (Led2 e motor))
			fila_envio.put_nowait((dado_tempo[0], valor1))
		
		
# Thread responsável pela comunicação entre o cliente (PC) e a Galileo
class Comunicacao (Thread):
	def __init__(self, fila_envio):
		Thread.__init__(self)
		self.serverName = '' 								       # ip do servidor (em branco)
		self.serverPort = 12000 							       # porta a se conectar
		self.serverSocket = socket(AF_INET, SOCK_DGRAM) 	       # criacao do socket UDP
		self.serverSocket.bind((self.serverName, self.serverPort)) # bind do ip do servidor com a porta 
		self.fila_envio = fila_envio  
		self.enderecoCliente = None
		
	def run(self):
		# Inicia thread de envio de dados
		Thread(target=self.enviaDados).start()
		# Inicia thread de recebimento de dados
		Thread(target=self.recebeDados).start()
	
	
	#Envio de dados para o cliente    
	def enviaDados(self):
		# Aguarda ter um endereco de cliente disponivel, que ocorre quando este se conecta ao servidor
		while(self.enderecoCliente == None):
			time.sleep(0.25)

		while (True):
			# Obtem (tempo atual, valor PWM1 (Led2 e motor)) da fila de envio 
			dados = self.fila_envio.get()
			
			#Se o comando de extinção for enviado, a thread é finalizada para a saída do programa
			if(dados[0] == -1):
				break

			try:                
			  	# Envia para o cliente o tempo e o valor da função no formato tempo:valor                
				self.serverSocket.sendto((str(dados[0])+":"+str(dados[1])).encode("utf-8"), self.enderecoCliente) 
			except error:  
				# Se o cliente estiver desconectado durante envio de dados, a exceção é lançada, parando thread  
				print("Cliente saiu. Saindo")
				break
				
	
	#Recebimento de dados do cliente
	def recebeDados(self):        
		global start
		global tipo_funcao
		global fim
		while(True):
			# Recebe dados do cliente através do socket no formato:
			# comando-tipo_funcao
			message, self.enderecoCliente = self.serverSocket.recvfrom(2048)
			message = message.decode("utf-8").split("-")
			print(message)
			
			# Comando de inicio
			if(int(message[0])==0):
				# Atribui o tipo de funcao e inicia timer
				start = True
				tipo_funcao = int(message[1])
			# Comando de desligamento do sistema
			elif(int(message[0])==1):
				# Para timer e define o tipo_funcao para o valor padrao
				start = False
				tipo_funcao = 0
			# Comando para sair do sistema
			elif(int(message[0])==2):
				# Para timer, atribui o valor true a varável fim, fecha socket e sai do loop de recebimento de dados para finalização da thread e do programa
				start = False
				fim = True
				self.serverSocket.close()
				break
			# Comando para que o endereço do cliente seja atribuido ao socket na thread de envio
			elif(int(message[0])==3):
				pass
	 

#Conta o tempo, lançando dados a cada 0.25 s            
def timer(fila_tempo):
	# Tempo de sleep em segundos 
	sleep_time = 0.0
	# Tempo passado desde o inicio da execução do programa
	segundos = 0.0 
	global start
	global fim

	# Enquanto o fim do programa não acontecer
	while(not fim):        
		# Obtem tempo inicial do programa em microssegundos
		ts_inicial = datetime.now().microsecond + datetime.now().second*1000000 + datetime.now().minute*60000000  

		# Enquanto o sistema estiver rodando
		while(start):
			# Calcula o tempo em que o sistema deve dormir, definido pelo tempo que o sistema deve estar menos o tempo em que ele realmente está
			# de forma que a thread tenta emitir dados a cada 0.25s
			sleep_time = segundos - (datetime.now().minute * 60000000 + datetime.now().second * 1000000 + datetime.now().microsecond - ts_inicial)/1000000.0 
			
			# Se o tempo de sleep for menor que 0, o sistema está atrasado, portanto o sleep não ocorre
			if(sleep_time >= 0):     
				time.sleep(sleep_time)   
		   
			print("sleep_time: %f" % sleep_time)
			
			# Envia (segundos, tempo do envio dos dados) para thread AquisicaoDados 
			fila_tempo.put_nowait((segundos, datetime.now()))

			# Se o tempo chegar a 30 segundos, o timer para e a contagem é reiniciada
			if(segundos == 30):
				start = False
				segundos = 0.0
				break   

			# Se o sistema for desligado antes dos 30 segundos acabarem, o loop de contagem é quebrado e a contagem reiniciada
			if(not start):                
				# o valor 30 é enviado para o próximo Thread (AquisicaoDados) indicando desligamento do sistema e por fim ao cliente
				fila_tempo.put_nowait((30, datetime.now()))
				segundos = 0.0
				break;
			
			segundos += 0.25
		
	# Comando -1 é enviado para o thread AquisicaoDados indicando que o usuário requisitou a saida do programa e que ela deve ser extinta, juntamente com as outras
	fila_tempo.put_nowait((-1, 0))


# Thread responsável por aplicar na saída os seus respectivos valores
def GeracaoSinais(fila_calculo):
	# Define os pinos 6 (Motor e Led2) e 5 (Led3) como saídas PWM
	pwm1 = mraa.Pwm(6)
	pwm2 = mraa.Pwm(5)
		
	# Definem que as saídas PWM tenham período de 1ms (f=1KHz)
	pwm1.period_ms(1)
	pwm2.period_ms(1)

	# Ativa saídas PWM
	pwm1.enable(True)
	pwm2.enable(True)

	# Coloca sobre o PWM o valor 0 para que as saídas permaneçam desligadas
	pwm1.write(0)
	pwm2.write(0)

	# Define o pino 7 como saída e define seu valor como 0, para que o led1 permanece incialmente desligado
	led_ativ = mraa.Gpio(7)
	led_ativ.dir(mraa.DIR_OUT)
	led_ativ.write(0)

	while(True):
	  	# calculo recebe (valor PWM1, valor PWM2, valor Led1)
		calculo = fila_calculo.get()  
	 
		#Se -1 for enviado pela fila indicando que o programa deve fechar, a thread é parada e todas as saídas são zeradas
		if(calculo[0] == -1):          	
			pwm1.write(0)
			pwm2.write(0)
			led_ativ.write(0) 
			break      
			   
		print("Delay: " + str(datetime.now()-calculo[4]) + "\n") 
		
		# Atribui às saídas seus espectivos valores enviados pelo thread ProcessamentoDados
		led_ativ.write(calculo[3])    
		pwm1.write(calculo[1])
		pwm2.write(calculo[2])
	  
	
try:    
	# Define o pino 4 como entrada com o pullup ativado
	botao = mraa.Gpio(4)
	botao.dir(mraa.DIR_IN)
	botao.mode(mraa.MODE_PULLUP)

	# Início das threads, que se comunicam conforme indicado no diagrama de funcionamento
	Comunicacao(fila_envio).start()
	Thread(target=timer, args=(fila_tempo, )).start()
	Thread(target=AquisicaoDados, args=(fila_tempo, fila_aquisicao)).start()
	Thread(target=ProcessamentoDados, args=(fila_aquisicao, fila_calculo, fila_envio)).start() 
	Thread(target=GeracaoSinais, args=(fila_calculo, )).start() 

	# Enquanto o programa não for finalizado
	while(not fim):
		   
		# Enquanto o sistema não estiver rodando, verifica se o botão foi pressionado
		if(not start):
		  	# Se o botão for pressionado, aguarda 0.05s e verifica se ainda está pressionado, evitando o efeito do bouncing, para iniciar o programa de fato
			if(botao.read() == 0):
				time.sleep(0.05)
				if(botao.read() == 0):
					start = True    
	   

except Exception as e: 
	print(e)

