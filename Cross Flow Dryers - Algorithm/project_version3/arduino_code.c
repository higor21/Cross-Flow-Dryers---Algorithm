void setup(){
  //SCK - PB5
  //MISO - PB4
  //MOSI - PB3
  //SS - PB2
  //clkArduino- PB1
  //selData - PB0
  //chave PD7
  
  //Timer para contagem do tempo
  TCCR1A = 0b10000000;
  //Prescale de 256: 16MHz/64 = 250000
  TCCR1B = 0b00011011;
  //SE 250000 - 1 s
  //   62500 - 1/4 s
  ICR1 = (uint16_t) 62500;
  //Mantem em pulso em 10 contagens para que registrador da FPGA
  //contablize clock
  OCR1A = (uint16_t) 10;
	
  //Ativa mestre SPI
	SPCR = 0b01010001;
	//SCK, MOSI e SS como saída e MISO como entrada e OCR1 como saída
	DDRB = 0b00101111;
	
  //Configurando ADC
	ADMUX = 0b01100000;
	ADCSRA = 0b10000111;
  
  //UART - baud 9600 
  UCSR0B = 0b00001000;
  UCSR0C = 0b00100110;  
  UBRR0 = (uint8_t) 103;
}

uint8_t temp = 10;
uint8_t lum = 10;
uint8_t envia_pc = 0;

void loop(){
  //Aguarda chave estar em ON, esperando caso contrário
  while(!(PIND & 0b10000000));
  
	//ADC de 8 bits
	ADMUX &= 0b11110000;
	ADCSRA |= 0b01000000;
	while(!(ADCSRA & 0b00010000));
	temp = ADCH;	
  
  //ADC de 8 bits
	ADMUX &= 0b11110001;
	ADCSRA |= 0b01000000;
	while(!(ADCSRA & 0b00010000));
	temp = ADCH;	
  
  //envia e recebe dados da fpga
  PORTB = 0b00000000;
	SPDR = (uint8_t) temp;	
	while(!SPSR & 0b10000000);
	envia_pc = (uint8_t) SPDR;
  
  //envia e recebe dados da fpga
  PORTB = 0b00000001;
	SPDR = (uint8_t) umid;	
	while(!SPSR & 0b10000000);
	envia_pc = (uint8_t) SPDR;
  
  //Envia para o computador
  while (!( UCSR0A & 0b00100000));
	UDR0 = envia_pc;
}