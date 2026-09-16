#include <Wire.h>
#include <U8g2lib.h>

// OLED
U8G2_SH1106_128X64_NONAME_F_HW_I2C display(U8G2_R0);

// Encoder
#define ENC_CLK 4
#define ENC_DT 5
#define ENC_SW 6

int lastCLK;
int lastStateCLK;
int lastStateDT;
long encoderValue = 0;
int lastEncoded = 0;
long lastEncoderValue = 0;

// UI
int modo = 0;

// Setpoints
int setpoint[3] = {60,60,60};

// Temperaturas simuladas
float temp[4] = {55.2,52.7,50.8,23.4};

// Parpadeo
bool blinkState = true;
unsigned long lastBlink = 0;


// ---------------- SETUP ----------------
void setup()
{
  Serial.begin(115200);

  pinMode(ENC_CLK, INPUT_PULLUP);
  pinMode(ENC_DT, INPUT_PULLUP);
  pinMode(ENC_SW, INPUT_PULLUP);

  lastStateCLK = digitalRead(ENC_CLK);
  lastStateDT = digitalRead(ENC_DT);
  lastEncoded = (digitalRead(ENC_CLK) << 1) | digitalRead(ENC_DT);

  display.begin();
}


// ---------------- PANTALLA PRINCIPAL ----------------
void pantallaPrincipal()
{
  display.setFont(u8g2_font_6x12_tr);

  display.drawStr(18,10,"CONTROL TERMICO");

  display.setCursor(0,26);
  display.print("T1 ");
  display.print(temp[0],1);
  display.print("C");

  display.setCursor(70,26);
  display.print("SP ");
  display.print(setpoint[0]);

  display.setCursor(0,40);
  display.print("T2 ");
  display.print(temp[1],1);
  display.print("C");

  display.setCursor(70,40);
  display.print("SP ");
  display.print(setpoint[1]);

  display.setCursor(0,54);
  display.print("T3 ");
  display.print(temp[2],1);
  display.print("C");

  display.setCursor(70,54);
  display.print("SP ");
  display.print(setpoint[2]);

  display.setCursor(0,64);
  display.print("AMB ");
  display.print(temp[3],1);
}


// ---------------- PANTALLA SETPOINT ----------------
void pantallaSetpoint()
{
  display.setFont(u8g2_font_6x12_tr);

  display.drawStr(34,10,"SETPOINT");

  for(int i=0;i<3;i++)
  {
    int y = 28 + i*12;

    if(modo == i+1 && blinkState)
      display.drawStr(0,y,">");

    display.setCursor(10,y);

    display.print("T");
    display.print(i+1);
    display.print(" SP ");
    display.print(setpoint[i]);
    display.print("C");
  }
}


// ---------------- ENCODER ----------------

void leerEncoder()
{
  int MSB = digitalRead(ENC_CLK);
  int LSB = digitalRead(ENC_DT);

  int encoded = (MSB << 1) | LSB;
  int sum = (lastEncoded << 2) | encoded;

  if(sum == 0b1101 || sum == 0b0100 || sum == 0b0010 || sum == 0b1011)
    encoderValue++;

  if(sum == 0b1110 || sum == 0b0111 || sum == 0b0001 || sum == 0b1000)
    encoderValue--;

  lastEncoded = encoded;

  // Solo actuar cada 4 pasos (1 clic real)
  long value = encoderValue / 4;

  if(value != lastEncoderValue)
  {
    int cambio = value - lastEncoderValue;
    lastEncoderValue = value;

    if(modo > 0)
    {
      int tanque = modo - 1;

      setpoint[tanque] += cambio;
      setpoint[tanque] = constrain(setpoint[tanque],30,100);
    }
  }
}



// ---------------- BOTON ----------------
void leerBoton()
{
  static bool lastButton = HIGH;
  bool button = digitalRead(ENC_SW);

  if(lastButton == HIGH && button == LOW)
  {
    modo++;

    if(modo > 3)
      modo = 0;

    delay(250);
  }

  lastButton = button;
}


// ---------------- LOOP ----------------
void loop()
{
  if(millis() - lastBlink > 400)
  {
    blinkState = !blinkState;
    lastBlink = millis();
  }

  leerEncoder();
  leerBoton();

  display.clearBuffer();

  if(modo == 0)
    pantallaPrincipal();
  else
    pantallaSetpoint();

  display.sendBuffer();

  delay(10);
}