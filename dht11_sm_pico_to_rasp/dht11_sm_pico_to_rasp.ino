#include <Arduino.h>
#include <DHT.h>

// --- DHT11 Sensor Setup ---
#define DHTPIN 22
#define DHTTYPE DHT11
DHT dht(DHTPIN, DHTTYPE);

// --- Soil Moisture Pins ---
int SoilMoisture1 = 26;  // ADC0
int SoilMoisture2 = 27;  // ADC1
int SoilMoisture3 = 28;  // ADC2 


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
    timer = millis() + 1000; // 15 minutes delay
  }



  delay(60000); // small delay to stabilize readings
}
