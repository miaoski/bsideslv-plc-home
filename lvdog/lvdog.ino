#define heartBeatPin 2
#define alarmPin 13
#define ALARM 5*10      // 5 seconds

int lastState = 0;

void setup() {
  pinMode(heartBeatPin, INPUT);
  pinMode(alarmPin, OUTPUT);
  Serial.begin(9600);
  Serial.println("Watch Dog for PLC Home");
}

void loop() {
  int state = digitalRead(heartBeatPin);
  unsigned int timer = 0;
  int alarmTriggered = 0;
  
  if(heartBeatPin != lastState) {
    lastState = heartBeatPin;
    if(alarmTriggered) {
      alarmTriggered = 0;
      timer = 0;
      digitalWrite(alarmPin, LOW);
      Serial.println("Alarm reset");
    }
    Serial.println("Got heart beat");
  } else {
    timer++;
    if(timer > ALARM) {
      Serial.println("Alarm!!!");
      alarmTriggered = 1;
      digitalWrite(alarmPin, HIGH);
    }
  }
  delay(100);
}
