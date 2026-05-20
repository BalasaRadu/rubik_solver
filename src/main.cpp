#include <Arduino.h>
#include <ESP32Servo.h>

const int PIN_TOP_COVER   = 22;
const int PIN_CUBE_HOLDER = 23;

Servo topCoverServo;
Servo cubeHolderServo;

const int TOP_CLOSE = 115;
const int TOP_OPEN  = 70;
const int TOP_FLIP  = 15;

const int BASE_HOME = 90;
const int BASE_HOME_OVER = 80;
const int BASE_HOME_TARGET = 90;


const int BASE_CW_OVER   = 180; 
const int BASE_CW_TARGET = 175;

const int BASE_CCW_OVER   = 0;   
const int BASE_CCW_TARGET = 5;   

const int DELAY_CMD     = 3000;
const int DELAY_MOVE    = 450;
const int DELAY_RELEASE = 150;

void rotateCW();
void rotateCCW();
void rotateHome();

void setup() {
    Serial.begin(115200);

    ESP32PWM::allocateTimer(0);
    ESP32PWM::allocateTimer(1);
    
    topCoverServo.setPeriodHertz(50);
    cubeHolderServo.setPeriodHertz(50);

    topCoverServo.attach(PIN_TOP_COVER, 500, 2500);
    cubeHolderServo.attach(PIN_CUBE_HOLDER, 500, 2500);

    topCoverServo.write(TOP_OPEN);
    cubeHolderServo.write(BASE_HOME);
    
    Serial.println("waiting for commands");
}

void loop() {
    if (Serial.available() > 0) {
        String command = Serial.readStringUntil('\n');
        
        command.trim(); 

        if (command.length() > 0) {
            Serial.print("command received:: ");
            Serial.println(command);

            if (command == "closed") {
                topCoverServo.write(TOP_CLOSE);
            } 
            else if (command == "open") {
                topCoverServo.write(TOP_OPEN);
            } 
            else if (command == "flip") {
                topCoverServo.write(TOP_FLIP);
            } 
            else if (command == "start") {
                rotateHome();
            } 
            else if (command == "cw") {
                rotateCW();
            } 
            else if (command == "ccw") {
                rotateCCW();
            } 
            else {
                Serial.println("error: unknown command!");
            }
        }
    }
}


void rotateCW() {
    cubeHolderServo.write(BASE_CW_OVER);    
    delay(DELAY_MOVE);                      
    cubeHolderServo.write(BASE_CW_TARGET);  
    delay(DELAY_RELEASE);                   
}

void rotateCCW() {
    cubeHolderServo.write(BASE_CCW_OVER);   
    delay(DELAY_MOVE);                      
    cubeHolderServo.write(BASE_CCW_TARGET); 
    delay(DELAY_RELEASE);                   
}

void rotateHome() {
    cubeHolderServo.write(BASE_HOME_OVER);   
    delay(DELAY_MOVE);                      
    cubeHolderServo.write(BASE_HOME_TARGET); 
    delay(DELAY_RELEASE);                   

}