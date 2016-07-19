#define heartBeatPin 2
#define alarmPin 13
#define ALARM 5*10      // 5 seconds

int lastState = 0;
unsigned int timer = 0;
int alarmTriggered = 0;

void setup() {
  pinMode(heartBeatPin, INPUT);
  pinMode(alarmPin, OUTPUT);
  digitalWrite(alarmPin, LOW);
  Serial.begin(9600);
  Serial.println("Watch Dog for PLC Home");
}

void loop() {
  int state = digitalRead(heartBeatPin);  
  if(state != lastState) {
    lastState = state;
    timer = 0;
    Serial.println("Got heart beat");
    if(alarmTriggered) {
      alarmTriggered = 0;
      digitalWrite(alarmPin, LOW);
      Serial.println("Alarm reset");
    }
  } else {
    timer++;
    if(timer > ALARM) {
      Serial.println("Alarm!!!");
      alarmTriggered = 1;
      digitalWrite(alarmPin, HIGH);
      delay(3000-100);
    }
  }
  delay(100);
}
