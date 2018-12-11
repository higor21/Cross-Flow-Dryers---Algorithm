#coding: utf-8

import mraa
from threading import Thread
from socket import *
from numpy import fft, ifft
import struct #bytes
import numpy as np

# Inicializa a comunicação USART
usart = mraa.Uart(0)
# Informa que a taxa de transmissão será de 115.2 kb/s
usart.setBaudRate(115200)
# Informa que o tamanho das palavras recebidas terão 8 bits, que serão recebidas juntamente com um 
# bit de paridade par para conferir a integridade dos dados recebidos e que haverá um bit indicando o fim do frame transmitido
usart.setMode(8, mraa.UART_PARITY_EVEN, 1)
# Desativa controles de fluxo
usart.setFlowcontrol(False, False)

sound_fft = []
fft_filtrada = []
sound_ifft = []


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
		while(not fim):
			continue

		for k in found_ifft:
			try:  
			  	# Envia para o cliente o tempo e o valor da função no formato tempo:valor                
				self.serverSocket.sendto(k.real, self.enderecoCliente) 
			except error:  
				# Se o cliente estiver desconectado durante envio de dados, a exceção é lançada, parando thread  
				print("Cliente saiu. Saindo")
				break
	
	#Recebimento de dados do cliente
	def recebeDados(self):
		sound = []
		i = 0
		sound[i], self.enderecoCliente = self.serverSocket.recvfrom(8)
		while(sound[i] != 0):
			i+=1
			sound[i], self.enderecoCliente = self.serverSocket.recvfrom(8)
			sound[i] = int(sound[i])
		sound_fft = fft.fft(sound)
		for cn in sound_fft:
			usart.write(struct.pack("B", cn.real))
			usart.write(struct.pack("B", cn.imag))
		
		while not usart.dataAvaliable(): pass	
		i = 0
		while usart.dataAvaliable():
			real[i] = usart.readStr(1)
			complexo[i] = usart.readStr(1)
		fft_filtrada.append(complex(real, complexo))
		sound_ifft = fft.ifft(fft_filtrada)
		fim = true