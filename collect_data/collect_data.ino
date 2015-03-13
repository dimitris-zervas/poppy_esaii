/* Magnetic encoder variables */
uint8_t u8byteCount;
uint8_t u8data;
uint32_t u32result = 0;
uint32_t u32send;

/* Flags */
boolean loop_flag, receive_flag, send_flag, dir_flag;

/* VARIABLES */
uint8_t dir;
uint8_t incomingByte;

//TIMER
unsigned long time;


/* Counter0 compare match interrupt - for control loop
------------------------------------------------------*/
ISR(TIMER0_COMPA_vect) {
  loop_flag = 1;
  receive_flag = 1;
  send_flag = 0;
  
}
/*----------------------------------------------------*/


void setup() {
  
  Serial.begin(115200);
  /* ---------------------- Pin modes  ----------------------- */
  pinMode(10,OUTPUT);  // SPI pulse
  pinMode(4, OUTPUT);  // Direction pin
  pinMode(7, OUTPUT);  // Direction pin
  pinMode(8, OUTPUT);  // Debug pin
  pinMode(11,OUTPUT);  // OC2A
  pinMode(3, OUTPUT);  // PWM
  /* --------------------------------------------------------- */
  
  /* ------------ Timer 0 - Configuration (CTC)  ------------- */
  TCCR0A = 0;
  TCCR0B = 0;    //DON'T KNOW WHY - Init. Value of reg = B00000100 (!!)
  TCCR0A |= B01000010;
  TCCR0B |= B00000101;
  TIMSK0 |= B00000010;
  /* ---------------------------------------------------------- */
  
  /* ---------- Timer 2 - Configuration (FAST_PWM) ------------ */
  TCCR2A = 0;
  TCCR2B = 0;    //DON'T WHY - Init. Value of reg = B00000100 (!!)
  TCCR2A |= B00100011;
  TCCR2B |= B00000111;
  /* -----------------------------------------------------------*/
  
  /* ------------------  SPI configuration  ------------------- */
  DDRB = 0;  //To_check!!
  // configure SCK(PB5) and Slave Select(PB2) as output, MISO(PB4) as input
  DDRB = (1 << PB5) | (1 << PB2) | (0 << PB4);
  // configure SPI as master, SPR0=1 -> fosc/16 CHANGE: SPR0 = 0 -> fosc/4
  SPCR = (1 << SPE) | (1 << MSTR) | (0 << CPOL) | (1 << SPR0) | (CPHA << 1);
  //SPSR = (1 << SPI2X);
  /* -----------------------------------------------------------*/
  
  /* ------------------  Initialize Flags  -------------------- */
  loop_flag = 1;
  receive_flag = 1;
  send_flag = 0;
  dir_flag = 0;
  dir = 0;
  /* ---------------------------------------------------------- */

  OCR0A = 250;
  sei();
  
  
}



void loop () {
  
  if (loop_flag == 1) {  // Control loop
      // RECEIVE DATA
      if ((receive_flag == 1) && (send_flag == 0)) {  // Runs only first time of control_loop
        Serial.println("s");  // Tell Matlab to send data
        receive_flag = 0;  // Goes 1 again from loop_interrupt
      }
      if ((Serial.available() > 0) && (receive_flag == 0)) {
        dir = Serial.read();  // Read the direction (byte)
        incomingByte = Serial.read();  // Read the pwm value (byte)
        change_direction(dir);  // Change direction (if needed)
        OCR2B = incomingByte;  // Apply PWM
        /*if ((dir == 0) && (incomingByte == 204)) {
          digitalWrite(8,HIGH);
        } else if ((dir == 1)&& (incomingByte == 204)) {
          digitalWrite(8,LOW);
        }*/
        send_flag = 1;
        
      }
    
      // SENDING DATA
      if ((receive_flag == 0) && (send_flag == 1)) {
        Serial.println("t");
        u32send = readSSI();
        Serial.println(u32send);
        send_flag = 0;
      }
      loop_flag = 0;  // Do all that staff, once per loop (...)
  }  // control loop
}  // void loop
  
  
  
  
void change_direction (uint8_t dir) {
  // dir_flag is the previous direction. If previous direction is
  // different than the new direciton, then change, otherwise you ask
  // for the direction you already have so do nothing.
  // 1 = clockwise - 0 = anti-cw
  if ((dir_flag == 0) && (dir == 1)) {
    digitalWrite(7,LOW);  digitalWrite(4,LOW);  //Stop
    digitalWrite(4,HIGH);
    dir_flag = 1;
  }else if ((dir_flag == 1) && (dir == 0)) {
     digitalWrite(7,LOW);  digitalWrite(4,LOW);  //Stop
     digitalWrite(7,HIGH);
     dir_flag = 0;
  }
}


uint32_t readSSI () {
    uint32_t data;
    //Pulse to initiate new transfer
    digitalWrite(10,HIGH);
    digitalWrite(10,LOW);
    //Receive the 3 bytes (AS5145 sends 18bit word)
    for (u8byteCount=0; u8byteCount<3; u8byteCount++){
       u32result <<= 8;  // left shift the result so far - first time shifts 0's-no change
       SPDR = 0xFF;  // send 0xFF as dummy (triggers the transfer)
       while ( (SPSR & (1 << SPIF)) == 0);  // wait until transfer complete
       u8data = SPDR;  // read data from SPI register
       u32result |= u8data;  //store the byte
    }
    // Print only the data no check of flags!
    u32result >>= 12;
    data = u32result;
    u32result = 0;
    return data;
}
