 #coding: utf-8
import matplotlib.pyplot as plt
import drawnow
import queue
from threading import Thread
from socket import *
from time import sleep


# Thread responsável pela comunicação entre o cliente (PC) e servidor (Galileo)
class socketClass (Thread):
    def __init__(self, fila_dados, fila_comandos):
        Thread.__init__(self)
        self.serverName = '192.168.0.21' 						# ip do servidor
        self.serverPort = 12000 								# porta a se conectar
        self.clientSocket = socket(AF_INET, SOCK_DGRAM)			# Criação do socket UDP 
        self.clientSocket.setblocking(0)						# Define que socket não irá bloquear ao receber dados
        self.clientSocket.settimeout(1)							# Define tempo de espera de 1s para recebimento dos dados 
        self.fila_dados = fila_dados
        self.fila_comandos = fila_comandos

        
    def run(self):
        # Inicia Thread de envio de dados
        Thread(target=self.send).start()
        # Inicia Thread de recebimento de dados
        Thread(target=self.recv).start()

        
    # Responsável pelo envio de dados para o servidor (Galileo)    
    def send(self):
        # Fica escutando servidor até receber comando de parada (2)
        while(True):
          	# Recebe (comando, tipo funcao) da thread de recebeComandos
            comando = self.fila_comandos.get()       
            
            # Envia os dados no formato comando-tipo_funcao para servidor (Galileo)
            self.clientSocket.sendto((str(comando[0]) + "-" + str(comando[1])).encode('utf-8'),(self.serverName, self.serverPort))
            # Se o comando for relativo ao fim do programa, a thread é finalizada
            if(comando[0] == 2):
                break    

                
    # Responsável pelo recbimento de dados do servidor (Galileo)    
    def recv(self):
        # Enquanto o programa não tiver terminado, escuta o servidor  
        while (not fim):
            try:
                # Recebe os dados do servidor na forma tempo_atual:valor_PWM1(Led2 e motor)
                dados_recebidos = self.clientSocket.recvfrom(2048)[0].decode("utf-8").split(":")
                
                # Dados recebidos são inseridos na fila para serem consumidos pelo plotter (tempo atual/comando, valor PWM1 (Led2 e motor)) 
                self.fila_dados.put((float(dados_recebidos[0]), float(dados_recebidos[1])))
            
            # Caso não receba dados dentro de 1s, reinicia loop, verificando se o programa foi finalizado (fim = True)
            # impedindo que a Thread fique bloqueada esperando receber dados e não finalize juntamente com o programa
            except timeout:
                pass
 

# Valores eixo y do gráfico
values = []
#Valores eixo x do gráfico
eixox = []
# Flag que indica quando plottar o gráfico
plot = False
# Flag que indica o fim do programa
fim = False


# Função usada para plottar os dados em um gráfico
def plotValues():
    plt.title('Valores da saida do PWM')                #titulo para o gráfico
    plt.grid(True)                                      #colocar grid no grafico
    plt.ylabel('Valor (%)')                             #label do eixo y
    plt.plot(eixox, values, 'rx-', label='tempo (s)')   #plot dos valores sobre eixox
    plt.legend(loc='upper right')                       #legenda

    
# Thread responsável por receber comandos do usuário
def recebeComandos(fila_dados, fila_comandos):
    
    print("Comandos disponiveis: ")
    print("ligar(funcao=0) - Iniciar programa Galileo")
    print("plot()          - Plotar valores enviados pela placa ")
    print("desligar()      - Parar programa Galileo")
    print("sair()          - Sair do programa")
    
    global fim
    global plot

    while(True):    
        comando = input("Digite o comando: ")
        
        # Tratamento do comando ligar(funcao=0)
        if(comando.startswith("ligar(") and comando.endswith(")")):
          	# Obtem tipo da função se indicado pelo usuário. Caso contrário não seja indicado é usado o valor padrão (0)
            # Insere os dados na forma (comando, tipo da função) para ser consumi
            if(comando[6] == ")"):      
                fila_comandos.put_nowait((0, 0))
            else:
                fila_comandos.put_nowait((0, int(comando[6])))
            
            # Insere o comando -2 na fila_dados para o plotter ser reiniciado
            fila_dados.put_nowait((-2, 0))
              
        # Plota os dados que foram/(estão sendo) enviado    
        elif(comando == "plot()"):          
            fila_dados.put_nowait((-3, 0)) 
            plot = True     
         
        elif(comando == "desligar()"):  
          	# Envia comando para o sistema (Galileo) ser desligado
            fila_comandos.put_nowait((1, 0))

        elif(comando == "sair()"):
          	# A plottagem dos dados é parada.
            plot = False           
            
            # Finaliza o thread socketClass:recv
            fila_dados.put_nowait((-1, 0))       
            
            # É enviado o comando para que a thread socketClass:send e o servidor finalizem
            fila_comandos.put_nowait((2, 0))
            
            # Finaliza loop responsável pela plottagem dos valores a thread recebeComandos
            fim = True
            break

        else:
            print("Comando nao reconhecido")


# Inicia filas responsáveis pela comunicação entre threads
fila_dados = queue.Queue() 
fila_comandos = queue.Queue()

# Inicia threads para comunicação com a Galileo e para a introdução de comandos
socketClass(fila_dados, fila_comandos).start()
Thread(target=recebeComandos, args=(fila_dados, fila_comandos)).start()

# Inicia conexão com servidor
fila_comandos.put((3, 0))

# Inicia variável segundoAnterior que indica o tempo anterior que foi plotado. 
# Seu valor inicial é negativo para aceitar o tempo 0
segundoAnterior = -1
plt.ion()
dados_plot = []
    
# Enquanto o programa não for finalizado
while (not fim):
    try:
        # Recebe dados da fila (tempo atual, valor PWM1 (Led2 e motor)) e armazena em dados_plot.
        # Dados da fila são inseridos em uma lista, permitindo a leitura dos últimos dados, de forma que
        # os comando enviados possam ser porcessados antes dos dados recebidos
        dados_plot.append(fila_dados.get(True))
        
        # A seguir, são verificados os últimos valores inseridos na fila na busca de comandos enviados pela thread recebeComandos.
        # Comando relativo à saída da thread e fechamento dos gráficos que estiverem sendo exibidos
        if(dados_plot[-1][0] == -1):
            plt.close("all")
            break

        # Comando relativo ao reinício (esvaziamento) das variáveis do gráfico para a chegada de novos dados
        elif(dados_plot[-1][0] == -2):
            dados_plot = []
            values = []
            eixox = []
            plot = False
            while(not fila_dados.empty()):
                fila_dados.get()
            plt.close("all")

        # Comando relativo ao inicio da plottagem dos valores no gráfico
        elif(dados_plot[-1][0] == -3):
            # Fecha gráficos anteriores e remove -3 da lista para que não seja plottado no gráfico
            plt.close("all")
            dados_plot.pop()     
            segundoAnterior = -1      

            while(plot):  
                tempo = 0.0
                valor = 0.0
                
                # Enquanto a lista tiver itens, copiamos os dados para as variáveis temporárias tempo e valor e o removemos da lista
                if(dados_plot):           
                    tempo = dados_plot[0][0]
                    valor = dados_plot[0][1]
                    dados_plot.pop(0)
                # Se a lista ficar vazia, pegamos dados diretamente da fila_dados até vir o comando de fim de transmissão (-4)
                else:
                    # Aguarda 1 segundo até dado chegar, caso contrário, termina loop 
                    try:                        
                        dado_plot = fila_dados.get(timeout=1)
                    except queue.Empty:                     
                        break
                        
                    tempo = dado_plot[0]
                    valor = dado_plot[1]
                                       
                # A plottagem é finalizada ao receber o comando -4 (fim de transmissão) do servidor ou da thread recebeComandos, esvaziando todas as variáveis
                if(tempo == -4):
                    plot = False 
                    dados_plot = []
                    values = []
                    eixox = []
                    break 
                                    
                # Verifica se o tempo recebido é maior que o anterior, descartando dados que tenham chegado com atraso
                if tempo > segundoAnterior:
                    # Atualiza valor do tempo anterior
                    segundoAnterior = tempo

                    # Insere os segundos e o valor do PWM1 (Led2 e motor) na lista de dados a serem plotados
                    eixox.append(tempo)
                    values.append(valor)

                    # Atualiza o plot
                    drawnow.drawnow(plotValues)
                
        # Condição que lida com o comando -4 (fim dos dados). Esse comando apenas tem efeite durante plot de dados
        elif(dados_plot[-1][0] == -4):
            pass
    except ValueError:
        print("Inválido! Impossível converter")
      

exit(1)