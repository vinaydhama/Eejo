//https://circuitdigest.com/microcontroller-projects/rs485-modbus-serial-communication-using-arduino-uno-as-slave

//RS-485 Modbus Slave (Arduino UNO)
//Circuit Digest
#include<ModbusRtu.h>       //Library for using Modbus in Arduino

Modbus bus;                          //Define Object bus for class modbus 
uint16_t modbus_array[] = {0,0,0,0,0,0,0,0,0,0,0,0};    //Array initilized with three 0 values

// Define analog/digital input pins for button/sensor inputs (ESP32-WROVER compatible)
// 
// ESP32-WROVER Pin Mapping (Exact Physical Locations):
// GPIO25 = Pin 24 on ESP32-WROVER board (for PIN_OUT_31 - CONTROL OUTPUT) *** MEASURE THIS PIN ***
// GPIO32 = Pin 9 on ESP32-WROVER board  (for PIN_IN_32 - INPUT with pull-up)
// GPIO33 = Pin 10 on ESP32-WROVER board (for PIN_IN_33 - INPUT with pull-up)
// GPIO34 = Pin 6 on ESP32-WROVER board  (for PIN_IN_34 - INPUT ONLY, no pull-up)
// GPIO35 = Pin 8 on ESP32-WROVER board  (for PIN_IN_35 - INPUT ONLY, no pull-up)
// GND = Pin 1, 2, or 38 on ESP32-WROVER board
//
// HOW TO FIND THE PINS:
// Look at the ESP32-WROVER silkscreen labels on the board:
// - Left side: GND, IO34, IO35, IO32, IO33, IO25, ... 
// - Right side: 3V3, EN, IO36, IO39, ...
// GPIO25 should be labeled "IO25" on your board - measure between this pin and any GND pin

const int PIN_IN_32 = 32;  // GPIO32 (Pin 9 on WROVER)
const int PIN_IN_33 = 33;  // GPIO33 (Pin 10 on WROVER)
const int PIN_IN_34 = 34;  // GPIO34 (Pin 6 on WROVER - input only, no pull-up)
const int PIN_IN_35 = 35;  // GPIO35 (Pin 8 on WROVER - input only, no pull-up)
const int PIN_OUT_31 = 25; // GPIO25 (Pin 24 on WROVER) *** THIS IS YOUR D31 EQUIVALENT - MEASURE THIS PIN ***

 //Define Connections to 74HC165

// PL pin 1
//int load = 7;
int load = 18;
int SoundPIN=13;
// int LowFreq[]= {2400,2600,2800,3000 ,3200 ,3400 ,3600 ,3800 ,4000 ,4200 ,4400 ,4600};
int LowFreq[]= {0,100,740,800,1000, 2300, 2600,3000 ,3100 , 3600,3700, 4100,4200};

// CE pin 15
//int clockEnablePin = 4;
int clockEnablePin = 15;

// Q7 pin 7
//int dataIn = 5;
int dataIn = 2;
// int i = 0;
int SoundPlayState=0;
unsigned long SoundStartTime=0;
unsigned long CurrentMillis=0;

// HT12D power control via BC547 NPN transistor (connect transistor collector to HT12D VDD, emitter to GND, base via ~1k resistor to MCU pin)
// Note: BC547 actively sinks VDD when the MCU pin is driven HIGH. Therefore logic is inverted compared to a P-channel high-side switch.
const int HT12D_POWER_PIN = 26; // connect BC547 base (via ~1k resistor) to D26


// Helper to read inputs and pack into bits
uint16_t readInputsPacked() {
  // Read raw levels
  int v34 = digitalRead(PIN_IN_34); // GPIO34 (input only, no pull-up)
  int v35 = digitalRead(PIN_IN_35); // GPIO35 (input only, no pull-up)
  int v32 = digitalRead(PIN_IN_32); // GPIO32 (with pull-up)
  int v33 = digitalRead(PIN_IN_33); // GPIO33 (with pull-up)
  // Note: PIN_OUT_31 (GPIO25) is now OUTPUT only, not read as input
  // If you need to read it, use: int v25 = digitalRead(PIN_OUT_31);

  // Pack into bits: bit0=33, bit1=32, bit2=35, bit3=34
  uint16_t reg = 0;
  reg |= (v33 & 0x01) << 0;
  reg |= (v32 & 0x01) << 1;
  reg |= (v35 & 0x01) << 2;
  reg |= (v34 & 0x01) << 3;

  return reg;
}


// Cycle the HT12D decoder power by driving the BC547 to sink VDD briefly.
// With BC547: HIGH => transistor on => VDD pulled low (decoder OFF). LOW => transistor off => decoder powered.
void cycleDecoderPower(unsigned int pulseMs = 50) {
  // Drive HIGH to pull VDD low (disable decoder)
  digitalWrite(HT12D_POWER_PIN, HIGH);
  delay(pulseMs);
  // Drive LOW to release VDD (enable decoder)
  digitalWrite(HT12D_POWER_PIN, LOW);
  // small settle time
  delay(10);
}


void PlaySound(int Freq, int sounddelay = 10)
{
  CurrentMillis = millis();
  
  // Initialize sound state on first call
  if (SoundPlayState == 0)
  {
    SoundStartTime = millis();
    SoundPlayState = 1;
    Serial.print("PlaySound STARTED - Freq: ");
    Serial.print(Freq);
    Serial.print(" Duration: ");
    Serial.println(sounddelay);
  }

  // Check if still within the sound duration
  unsigned long elapsedTime = CurrentMillis - SoundStartTime;
  
  if (elapsedTime < sounddelay)
  {
    // Sound is still active - turn ON
    if (Freq == 1)
    {
      digitalWrite(SoundPIN, 1);
      digitalWrite(PIN_OUT_31, 1);
      Serial.print("Pins HIGH - Elapsed: ");
      Serial.println(elapsedTime);
    }
    else
    {
      tone(SoundPIN, Freq, sounddelay);
      Serial.print("Tone playing - Freq: ");
      Serial.print(Freq);
      Serial.print(" Elapsed: ");
      Serial.println(elapsedTime);
    }
  }
  else
  {
    // Sound duration expired - turn OFF
    if (Freq == 1)
    {
      digitalWrite(SoundPIN, 0);
      digitalWrite(PIN_OUT_31, 0);
      Serial.println("Pins turned OFF - Duration expired");
    }
    else
    {
      noTone(SoundPIN);
    }
    modbus_array[0] = 0;
    SoundPlayState = 0;
  }
}


// CP pin 2
//int clockIn = 6;
int clockIn = 5;

void setup()
{
  // Initialize serial for debugging output voltage on GPIO25 (ESP32-WROVER)
  Serial.begin(115200);
  delay(1000);
  Serial.println("\n\n=== ESP32-WROVER TimerPoolsideSlave Starting ===");
  Serial.println("Board: ESP32-WROVER");
  Serial.println("");
  Serial.println("PIN LOCATIONS ON YOUR ESP32-WROVER BOARD:");
  Serial.println("  GPIO25 (Pin 24) = CONTROL OUTPUT - *** MEASURE THIS PIN FOR HIGH/LOW ***");
  Serial.println("  GPIO32 (Pin 9)  = Input with Pull-up");
  Serial.println("  GPIO33 (Pin 10) = Input with Pull-up");
  Serial.println("  GPIO34 (Pin 6)  = Input only (no pull-up)");
  Serial.println("  GPIO35 (Pin 8)  = Input only (no pull-up)");
  Serial.println("  GND (Pins 1,2,38) = Ground for measurements");
  Serial.println("");
  Serial.println("HOW TO MEASURE:");
  Serial.println("1. Use a multimeter set to DC Voltage");
  Serial.println("2. Connect Black probe to any GND pin");
  Serial.println("3. Connect Red probe to GPIO25 (Pin 24)");
  Serial.println("4. You should see: 0V (LOW) then 3.3V (HIGH)");
  Serial.println("");
  
  pinMode(PIN_IN_34, INPUT);               // GPIO34 input only (no pull-up)
  pinMode(PIN_IN_35, INPUT);               // GPIO35 input only (no pull-up)
  pinMode(PIN_OUT_31, OUTPUT);             // GPIO25 output pin for control signal
  digitalWrite(PIN_OUT_31, LOW);           // Ensure LOW at startup

  // For 32/33 you can choose internal pulls if your wiring needs it:
  pinMode(PIN_IN_32, INPUT_PULLUP);        // GPIO32 with internal pull-up
  pinMode(PIN_IN_33, INPUT_PULLUP);        // GPIO33 with internal pull-up

  pinMode(load, OUTPUT);
  pinMode(SoundPIN, OUTPUT);               // Set pin 13 as output for the buzzer
  digitalWrite(SoundPIN, LOW);             // Ensure LOW at startup
  pinMode(clockEnablePin, OUTPUT);
  pinMode(clockIn, OUTPUT);
  pinMode(dataIn, INPUT);

  // HT12D power control pin (drive BC547). Default LOW = decoder powered.
  pinMode(HT12D_POWER_PIN, OUTPUT);
  digitalWrite(HT12D_POWER_PIN, LOW);      // ensure decoder enabled by default

  bus = Modbus(1,1,22);            //Modbus slave ID as 1 and 1 connected via RS-485 and 4 connected to DE & RE pin of RS-485 Module 
  bus.begin(115200);                //Modbus slave baudrate at 9600
  
  Serial.println("Setup complete - TESTING GPIO25 NOW");
  Serial.println("Watch your multimeter on GPIO25...");
  delay(500);
  
  // Test GPIO25 and SoundPIN
  digitalWrite(PIN_OUT_31, HIGH);
  digitalWrite(SoundPIN, HIGH);
  Serial.println(">>> [TEST 1] GPIO25 set to HIGH - Multimeter should show 3.3V");
  delay(2000);
  
  digitalWrite(PIN_OUT_31, LOW);
  digitalWrite(SoundPIN, LOW);
  Serial.println(">>> [TEST 2] GPIO25 set to LOW - Multimeter should show 0V");
  delay(1000);
  
  Serial.println("");
  Serial.println("Ready - waiting for Modbus commands...");
  Serial.println("Send: modbus_array[0]=1 and modbus_array[1]=10000 to keep GPIO25 HIGH for 10 seconds");
  PlaySound(32, 1000);
}
void loop()
{
  digitalWrite(load, LOW);
  delayMicroseconds(5);
  digitalWrite(load, HIGH);
  delayMicroseconds(5);

   // Get data from 74HC165
  digitalWrite(clockIn, HIGH);
  digitalWrite(clockEnablePin, LOW);
  byte incoming1 = shiftIn(dataIn, clockIn, LSBFIRST);
  byte incoming2 = shiftIn(dataIn, clockIn, LSBFIRST);
  byte incoming3 = shiftIn(dataIn, clockIn, LSBFIRST);
  byte incoming4 = shiftIn(dataIn, clockIn, LSBFIRST);

  digitalWrite(clockEnablePin, HIGH);

  modbus_array[3]=incoming1;
  modbus_array[4]=incoming2;
  modbus_array[5]=incoming3;
  modbus_array[6]=incoming4;
  modbus_array[7] = readInputsPacked();

  // Example: if you detect a stuck latch condition, cycle decoder power to clear internal latches.
  // Replace the condition below with your actual detection logic. For now it is commented.
  // if ( /* stuck-latch detected */ false ) {
  //   cycleDecoderPower(100); // pull VDD low for 100ms then restore
  // }

  if ( modbus_array[0]>0)
  {
    PlaySound( modbus_array[0],modbus_array[1]);
  }
  else
  {
  SoundPlayState=0;
  }
     bus.poll(modbus_array,sizeof(modbus_array)/sizeof(modbus_array[0]));       //
  //  i=i+1;
  delay(10); 

}