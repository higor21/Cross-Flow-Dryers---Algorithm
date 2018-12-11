 #coding: utf-8
from threading import Thread
from socket import *
import wave, struct, time
import numpy as np
from scipy.io import wavfile


sampleRate = 44100.0 # hertz
duration = 1.0       # segundos de duração da música
frequency = 440.0    # hertz
fim = False

# Thread responsável pela comunicação entre o cliente (PC) e servidor (Galileo)
class socketClass (Thread):
    def __init__(self, fila_dados, fila_comandos):
        Thread.__init__(self)
        self.serverName = '192.168.0.21' 						# ip do servidor
        self.serverPort = 12000 								# porta a se conectar
        self.clientSocket = socket(AF_INET, SOCK_DGRAM)			# Criação do socket UDP 
        self.clientSocket.setblocking(0)						# Define que socket não irá bloquear ao receber dados
        
    def run(self):
        # Inicia Thread de envio de dados
        Thread(target=self.send).start()
        # Inicia Thread de recebimento de dados
        Thread(target=self.recv).start()

        
    # Responsável pelo envio de dados para o servidor (Galileo)    
    def send(self):
        novo_som = []
        fs, data = wavfile.read('som.wav')
        for i in data:
            novo_som.append((i[0] + 32768) >> 8)
            novo_som[-1] -= 128
            
            # Envia os dados no formato comando-tipo_funcao para servidor (Galileo)
            self.clientSocket.sendto(bytes(novo_som[-1]),(self.serverName, self.serverPort))
        time.sleep(5000)
        fim = True
    # Responsável pelo recbimento de dados do servidor (Galileo)    
    def recv(self):
        while not fim: pass

        wavef = wave.open('sound_filtred.wav','w')
        wavef.setnchannels(1) # mono
        wavef.setsampwidth(2) 
        wavef.setframerate(sampleRate)

        for i in range(int(duration * sampleRate)):
            try:
                dados_recebidos = self.clientSocket.recvfrom(1)
                wavef.writeframesraw(struct.pack('<h', dados_recebidos))
                raise timeout
            except timeout:
                print("deu errado!")

        wavef.writeframes('')
        wavef.close()
    
# Inicia threads para comunicação com a Galileo e para a introdução de comandos
socketClass(fila_dados, fila_comandos).start()
exit(1)