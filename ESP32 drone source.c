#include <WiFi.h>
#include <WebServer.h>

const char* ssid = "ESP32-Drone";
const char* password = "drone123";

WebServer server(80);

// Motor control pins
const int motor1 = 14;
const int motor2 = 27;
const int motor3 = 26;
const int motor4 = 25;

void setup() {
  Serial.begin(115200);
  WiFi.softAP(ssid, password);
  Serial.println("WiFi AP started");

  pinMode(motor1, OUTPUT);
  pinMode(motor2, OUTPUT);
  pinMode(motor3, OUTPUT);
  pinMode(motor4, OUTPUT);

  server.on("/control", handleControl);
  server.begin();
  Serial.println("HTTP server started");
}

void handleControl() {
  int throttle = server.arg("throttle").toInt();
  int yaw = server.arg("yaw").toInt();
  int pitch = server.arg("pitch").toInt();
  int roll = server.arg("roll").toInt();

  // Example: Map throttle to PWM
  analogWrite(motor1, throttle + pitch + roll - yaw);
  analogWrite(motor2, throttle + pitch - roll + yaw);
  analogWrite(motor3, throttle - pitch + roll + yaw);
  analogWrite(motor4, throttle - pitch - roll - yaw);

  server.send(200, "text/plain", "Command received");
}

void loop() {
  server.handleClient();
}