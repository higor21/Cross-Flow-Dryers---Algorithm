void setup(){
  //SCK - PB5
  //MISO - PB4
  //MOSI - PB3
  //SS - PB2
  //chave - PB1
  //Sensor Luminosidade - A0
  //Sensor temperatura - A1
  
  //Define SCK (PB5), MOSI(PB3), SS(PB2) e chave(PB1) como saída e MISO(PB4) como entrada 
  DDRB = 0b00101100;  
  PORTB = 0b00000100;
  
  //SPI - Configuração
  //Ativa o SPI
  //Define como mestre SPI
  //Seleciona o prescale de 128, de modo que a frequência do SPI fica (16M/128 = 125KHz)
  SPCR = 0b01010011;
  
  //ADC - Configuração
  //Ativa o ADC
  //Define o prescale de 128, de forma que a frequência de entrada do ADC fique em (16M/128 = 125KHz)
  //Usando Vref como referência de voltagem
  //Ativa ADLAR para facilitar a obtenção dos 8 bits mais significativos
  ADMUX = 0b01100000;
  ADCSRA = 0b10000111;
  
  //USART - Configuração
  //Modo assíncrono
  //Baudrate de 9600 bits/s
  //Ativa modo transmissão do USART
  //Bit de paridade par
  //8 bits por transmissão
  //1 bit de parada
  UCSR0A = 0b00000000;
  UCSR0B = 0b00001000;
  UCSR0C = 0b00100110;  
  UBRR0 = (uint8_t) 103;
}

//Respectivamente, variáveis que armazenam a temperatura  e luminosidade obtidas do ADC e o valor PWM recebido da FPGA
uint8_t temp = 0;
uint8_t lum = 0;
uint8_t envia_pc = 0;

void loop(){
  
  //Aguarda chave estar ligada para iniciar o processo de envio e recebimento de dados
  while(!(PINB & 0b00000010));
  
  //Obtem luminosidade por meio do ADC
  ADMUX &= 0b11110000;
  ADCSRA |= 0b01000000;
  while(!(ADCSRA & 0b00010000));
  lum = (uint8_t) ADCH;  
  
  //Obtem temperatura por meio do ADC
  ADMUX |= 0b00000001;
  ADCSRA |= 0b01000000;
  while(!(ADCSRA & 0b00010000));
  temp = (uint8_t) ADCH; 
  
  //Desativa porta SS para ativar transmissão de dados no escravo
  PORTB &= 0b11111011;  
  delayMicroseconds(100);

  //Envia valor de luinosidade para a FPGA usando SPI
  SPDR = (uint8_t) lum;  
  while(!(SPSR & 0b10000000));
  
  //Liga e desliga porta SS para zerar registradores do escravos e recomeçar transmissão de dados
  PORTB != 0b00000100;
  delayMicroseconds(100);
  PORTB &= 0b11111011;
  delayMicroseconds(100);
  
  //Envia valor de temperatura para FPGA usando SPI, que retorna o valor do PWM
  SPDR = (uint8_t) temp; 
  while(!(SPSR & 0b10000000));
  envia_pc = (uint8_t) SPDR;

  //Envia dado para o computador usando USART
  while (!( UCSR0A & 0b00100000));
  UDR0 = envia_pc;
  PORTB != 0b00000100;
  delay(250);
}
