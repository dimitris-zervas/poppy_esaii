// USART initialization def's
#define FOSC 16000000UL   //clock speed
#define BAUD 115200     //desired baud rate
//#define MYUBRR FOSC/16/BAUD-1
#define MYUBRR (FOSC/4/BAUD-1)/2

boolean txOn = false;
boolean rxOn = false;
boolean com = true;
//unsigned char counterRx = 0;
//unsigned char bufferRx[10] = {0,0,0,0,0,0,0,0,0,0};
volatile unsigned char counterRx = 0; 
volatile unsigned char bufferRx[10] = {0,0,0,0,0,0,0,0,0};
// numnber to be sent
float pos = 0;
unsigned char *pointer_pos = (unsigned char *)&pos;
float time = 0;
unsigned char *pointer_time = (unsigned char *)&time;
//Numbers to be received
float ref = 0;
float *pointer_ref = (float *)&bufferRx[1];
float gain = 0;
float *pointer_gain = (float *)&bufferRx[6];
float P = 0;
float I = 0;
float D = 0;
unsigned char i;

volatile boolean loop_flag = 0;
boolean sendOnce = true;

unsigned char state = 0;

unsigned char eof[4] = {'c','X','r','C'};

unsigned char *pointer_data = (unsigned char *)&UDR0;


/* Counter0 compare match interrupt - for control loop*/
ISR(TIMER0_COMPA_vect) {
  if (loop_flag == 0){
    loop_flag = 1;
    com = true;
  }
}

ISR(USART_RX_vect) {
  bufferRx[counterRx] = UDR0;
  counterRx++;
  digitalWrite(9,!digitalRead(9));
}

ISR(USART_TX_vect) {
  digitalWrite(8,!digitalRead(8));
}




void setup() {
  // USART init
  USART_Init(MYUBRR);
  pinMode(10,OUTPUT);
  digitalWrite(10,LOW);
  pinMode(9,OUTPUT);
  digitalWrite(9,LOW);
  pinMode(8,OUTPUT);
  digitalWrite(8,LOW);
  state = 1;
  txOn = false;
  delay(1000);
  TCCR0A = 0;
  TCCR0B = 0;    //DON'T KNOW WHY - Init. Value of reg = B00000100 (!!)
  
  TCCR0A |= B01000010;
  TCCR0B |= B00000101;
  // DONT FORGET
  TIMSK0 |= B00000010;
  loop_flag = 1;
  
  OCR0A = 233;  //with CS00:2 = 101 -> period = 0.01
  //Enable RX Complete Interrupt
  //UCSR0B |= (1<<RXCIE0);
  //Enable TX Complete Interrupt
  UCSR0B |= (1<<TXCIE0);
  // Enable Global Interrupt
  sei();
  
  //delay(1000);
  loop_flag = 1;
  //time = -0.01;
  time=0;
}

void loop() {
  
  if (loop_flag == 1) {
    while (com == true){
      //digitalWrite(10,!digitalRead(10));   
      if (sendOnce == true) {
        // Send 's' to start the new data income
        USART_Tx('s');
        sendOnce = false;
        // Enable RX Complete interrupt
        UCSR0B |= (1<<RXCIE0);
      }
      if (counterRx == 10) {
        //digitalWrite(13,!digitalRead(13));
        counterRx = 0;
        // Disable RX Complete interrupt
        UCSR0B &= ~(1<<RXCIE0);
        rxOn = true;
        digitalWrite(10,!digitalRead(10));
      }
    
      if (txOn==true) {     
            /* Controller calculation */
            pos = ref + P;
            for (i=0; i<4; i++) {
              USART_Tx(pointer_pos[i]);
            }
            //for (i=0; i<4; i++) {
              //USART_Tx(pointer_time[i]);
            //}
            for (i=0; i<4; i++) {
              USART_Tx(eof[i]);
            }
            txOn = false;
            // Update time
            //time = time + 0.015;
            sendOnce = true;
            com = false;  //finished the com, now wait for the rest of Ts
      }
    
      if (rxOn == true) {
        switch (bufferRx[0]) {
          case 0xf0:  //read reference + gain
             //digitalWrite(13,!digitalRead(13));
             rxOn = false;
             ref = (*pointer_ref);
             // Gains update (one at a time)
             if (bufferRx[5] == 0xf3) {
               //digitalWrite(13,!digitalRead(13));
               P = (*pointer_gain);
             }else if (bufferRx[5] == 0xf4) {
               I = (*pointer_gain);
             }else if (bufferRx[5] == 0xf5) {
               D = (*pointer_gain);
             }
             txOn = true;
             break;
           case 0xf1:  //read only reference
             rxOn = false;
             txOn = true;
             ref = (*pointer_ref);
             break;
           case 0xf2:  //stop
             rxOn = false;
             txOn = false;
             break;
        }
      }
    }  //while
    
    loop_flag = 0;  //WAIT until next time interupt
    //digitalWrite(8,LOW);
  } // control loop
}  // main loop


void USART_Init (unsigned int ubrr)
{
  UCSR0A = 0;
  UCSR0A |= (1<<U2X0);
  /* Set baud rate */
  UBRR0H = (unsigned char)(ubrr>>8);
  UBRR0L = (unsigned char)(ubrr);
  UCSR0B = B00000000;
  // Enable receiver and transmitter 
  UCSR0B |= (1 << RXEN0) | (1 << TXEN0);
  UCSR0C = B00000000;
  // Set frame: 8data, 1 stp
  UCSR0C |= (1 << UCSZ01) | (1 << UCSZ00);
   
}

void USART_Tx (char data)
{
  /* Wait for empty transmit buffer */
  while ( !(UCSR0A & (1<<UDRE0)) ) {
  }
  /* Put data into buffer, sends the data */
  UDR0 = data;
}

