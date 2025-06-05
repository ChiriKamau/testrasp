#include <Arduino.h>
#include <DHT.h>

// --- DHT11 Sensor Setup ---
#define DHTPIN 22
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// --- Soil Moisture Pins ---
int SoilMoisture1 = 26;  // ADC0
int SoilMoisture2 = 27;  // ADC1
int SoilMoisture3 = 28;  // ADC2 (New)
int valve = 16;          // GPIO for valve control

unsigned long timer = 0;

float temps;
float Humidity;
int soilvalue1;
int soilvalue2;
int soilvalue3;

void setup() {
  Serial.begin(115200);
  delay(1000);

  dht.begin();
  pinMode(valve, OUTPUT);
  digitalWrite(valve, LOW);

  timer = millis() + 1000; // start sending after 1s
}

void loop() {
  Humidity = dht.readHumidity();
  temps = dht.readTemperature();

  soilvalue1 = map(analogRead(SoilMoisture1), 0, 1023, 100, 0);
  soilvalue2 = map(analogRead(SoilMoisture2), 0, 1023, 100, 0);
  soilvalue3 = map(analogRead(SoilMoisture3), 0, 1023, 100, 0);

  if (millis() > timer) {
    String jsonData = "{";
    jsonData += "\"temperature\":" + String(temps) + ",";
    jsonData += "\"humidity\":" + String(Humidity) + ",";
    jsonData += "\"soilMoisture1\":" + String(soilvalue1) + ",";
    jsonData += "\"soilMoisture2\":" + String(soilvalue2) + ",";
    jsonData += "\"soilMoisture3\":" + String(soilvalue3);
    jsonData += "}";

    Serial.println(jsonData); // Send JSON to Raspberry Pi over Serial
    timer = millis() + 900000; // 15 minutes delay
  }

  if (soilvalue1 < 50) {
    digitalWrite(valve, HIGH);
    delay(15000);
    digitalWrite(valve, LOW);
  }

  delay(1000); // small delay to stabilize readings
}
