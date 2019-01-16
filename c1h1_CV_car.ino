/*
  WIFI模块：D0,D1
  LED小车头灯：D2,D4
  电机控制：D3,D5,D6,D9
  超声波测距：D7,D8
  舵机云台：D10,D11
  蜂鸣器：D12
  状态指示灯：D13  
  寻线模块：A0,A1,A2
  红外发射控制：A3
  I2C接口:A4,A5
  5V电源检测：A6
  电池电压检测：A7
*/

#include <Servo.h>    
#include <Arduino.h>
#define Kp 0.1        // experiment to determine this, start by something small that just makes your bot follow the line at a slow speed
#define Kd 4         
#define MaxSpeed 255 
#define BaseSpeed 255 
#define SPEED_MAX 100
bool is_connected = false;
#define DEBUG true


int8_t motor_speed_left = 0;
int8_t motor_speed_right = 0;


int left_go = 3;
int left_back = 5;
int right_go = 6;
int right_back = 9;
int ledR = 2;
int ledL = 4;
int val;
int lx = 90;

enum Order {
	HELLO = 0,
	SERVO = 101,
	MOTOR = 102,
	ALREADY_CONNECTED = 103,
	ERROR = 104,
	RECEIVED = 105,
	STOP = 106,
	SERVO_LEFT = 107,
	SERVO_RIGHT = 108,
	SERVO_UP = 109,
	SERVO_DOWN = 110,
  
};


//2路舵机
Servo servoX; //云台X轴舵机 左右
Servo servoY; //云台Y轴舵机 上下

//舵机左转
void servo_left()
{
	servoX.attach(10);  //水平舵机接10脚
	servoY.attach(11);  //上下舵机接11脚

	int servotemp=servoX.read();   //获取舵机目前的角度值
	Serial.println("servoX");
	Serial.println(servotemp);
	servotemp-=1;                  //舵机运动1度
	if(servotemp<180&&servotemp>1) //我定义的舵机旋转角度为10度到170度
	servoX.write(servotemp);
	else if (servotemp<=10)  servoX.write(10);
	else servoX.write(170);
	delay(200);

	servoY.detach();
	servoX.detach();
	mydetach();

}

//舵机右转
void servo_right()
{
	servoX.attach(10);  //水平舵机接10脚
	servoY.attach(11);  //上下舵机接11脚

	int servotemp=servoX.read();//获取舵机目前的角度值
	Serial.println("servoX");
	Serial.println(servotemp);
	servotemp+=1;//舵机运动1度
	if(servotemp<180&&servotemp>1)
	servoX.write(servotemp);
	else if (servotemp<=10)  servoX.write(10);
	else servoX.write(170);
	delay(200);

	servoY.detach();
	servoX.detach();
	mydetach();

}


//舵机上转
void servo_up()
{
	servoX.attach(10);  //水平舵机接10脚
	servoY.attach(11);  //上下舵机接11脚

	int servotemp1=servoY.read();//获取舵机目前的角度值
	Serial.println("servoY");
	Serial.println(servotemp1);
	servotemp1+=1;//舵机运动1度
	if(servotemp1<180&&servotemp1>1)
	servoY.write(servotemp1);
	else if (servotemp1<=10)  servoY.write(10);
	else servoY.write(170);
	delay(50);

	servoY.detach();
	servoX.detach();
	mydetach();
}


//舵机下转
void servo_down()
{
	servoX.attach(10);  //水平舵机接10脚
	servoY.attach(11);  //上下舵机接11脚

	int servotemp1=servoY.read();//获取舵机目前的角度值
	Serial.println("servoY");
	Serial.println(servotemp1);
	servotemp1-=1;//舵机运动1度
	if(servotemp1<180&&servotemp1>1)
	servoY.write(servotemp1);
	else if (servotemp1<=10)  servoY.write(10);
	else servoY.write(170);
	delay(50);

	servoY.detach();
	servoX.detach();
	mydetach();
}

void mydetach()
{
    TCCR1B = 0;

    TCCR1B=_BV(CS11);

    TCCR1B=_BV(CS10);

    TCCR1A=_BV(WGM10);

    TIMSK1=0;
}

void setup()
{
	pinMode(left_go, OUTPUT);
	pinMode(left_back, OUTPUT);
	pinMode(right_go, OUTPUT);
	pinMode(right_back, OUTPUT);
	pinMode(ledR, OUTPUT);
	pinMode(ledL, OUTPUT);
	servoX.attach(10);  //水平舵机接10脚
	servoY.attach(11);  //上下舵机接11脚
	servoX.write(85);   //输出舵机初始位置为90度(80-102)
	servoY.write(30);   //输出舵机初始位置为90度 


	for(int i=0;i<40;i++){
		digitalWrite(ledR, HIGH);
		digitalWrite(ledL, HIGH);
		delay(500);
		digitalWrite(ledR, LOW);
		digitalWrite(ledL, LOW);
		delay(500);
	}

	servoY.detach();
	servoX.detach();
	mydetach();
	Serial.begin(38400);//设置波特率为38400bps
	Serial.println("set up set up set up set up");
	TCCR1B = TCCR1B & B11111000 | B00000001;
}

void update_motors_orders()
{

	motor_speed_left = constrain(motor_speed_left, -SPEED_MAX, SPEED_MAX);
	motor_speed_right = constrain(motor_speed_right, -SPEED_MAX, SPEED_MAX);
	// Send motor speed order
	if (motor_speed_left > 0)
	{
		analogWrite(left_go, convert_to_pwm(float(motor_speed_left)));
		digitalWrite(left_back, LOW);
	}
	else
	{
		//analogWrite(left_back, convert_to_pwm(40));
		analogWrite(left_back, convert_to_pwm(float(abs(motor_speed_left))));
		//digitalWrite(left_back, HIGH);
		digitalWrite(left_go, LOW);
	}

	if (motor_speed_right > 0)
	{
		analogWrite(right_go, convert_to_pwm(float(motor_speed_right)));
		digitalWrite(right_back,LOW);
	}
	else
	{
		//analogWrite(right_back, convert_to_pwm(40));
		analogWrite(right_back, convert_to_pwm(float(abs(motor_speed_right))));
		//digitalWrite(right_back, HIGH);
		digitalWrite(right_go,LOW);
	}

}

void stop()
{
	digitalWrite(left_go, LOW);
	digitalWrite(right_go, LOW);
	digitalWrite(left_back, LOW);
	digitalWrite(left_back, LOW);
}

void get_messages_from_serial()
{
	if(Serial.available() > 0)
	{
		// The first byte received is the instruction
		Order order_received = read_order();

		switch(order_received)
		{
			case STOP:
			{
				motor_speed_left = 0;
				motor_speed_right = 0;
				stop();
				if(DEBUG)
				{
					write_order(STOP);
				}
				break;
			}
			case MOTOR:
			{
				// between -100 and 100
				if(read_i8() == '#')
				{
					String inString = "";
					int inChar = 0;
					while((inChar = read_i8()) != '$')
					{
						if(isdigit(inChar)){
						inString += (char)inChar;
						}
					}
					motor_speed_left = (int8_t)inString.toInt();
				}

				if(read_i8() == '#')
				{
					String inString = "";

					int inChar = 0;
					while((inChar = read_i8()) != '$')
					{
						if(isdigit(inChar))
						{
							inString += (char)inChar;
						}
					}
					motor_speed_right = (int8_t)inString.toInt();    
				}
				if(DEBUG)
				{
					Serial.println(motor_speed_left);
					Serial.println(motor_speed_right);
				}
				break;
			}
			case SERVO_LEFT:
			{
				servo_right();
				break;
			}      

			case SERVO_RIGHT:
			{
				servo_left();
				break;
			}      

			case SERVO_UP:
			{
				servo_up();
				break;
			}      

			case SERVO_DOWN:
			{
				servo_down();
				break;
			}      

			default:
				write_i16(404);
			}
	}
}

void loop()
{ 
	get_messages_from_serial();
	update_motors_orders();
}


int convert_to_pwm(float motor_speed)
{
	return (int) round(abs(motor_speed)*(255./100.));
}

Order read_order()
{
	return (Order) Serial.read();
}

void wait_for_bytes(int num_bytes, unsigned long timeout)
{
	unsigned long startTime = millis();
	while ((Serial.available() < num_bytes) && (millis() - startTime < timeout)){}
}

// NOTE : Serial.readBytes is SLOW
// this one is much faster, but has no timeout
void read_signed_bytes(int8_t* buffer, size_t n)
{
	size_t i = 0;
	int c;
	while (i < n)
	{
		c = Serial.read();
		if (c < 0) break;
		*buffer++ = (int8_t) c; // buffer[i] = (int8_t)c;
		i++;
	}
}

int8_t read_i8()
{
	wait_for_bytes(1, 100); // Wait for 1 byte with a timeout of 100 ms
 	return (int8_t) Serial.read();
}

int16_t read_i16()
{
 	int8_t buffer[2];
	wait_for_bytes(2, 100); // Wait for 2 bytes with a timeout of 100 ms
	read_signed_bytes(buffer, 2);
 	return (((int16_t) buffer[0]) & 0xff) | (((int16_t) buffer[1]) << 8 & 0xff00);
}

int32_t read_i32()
{
 	int8_t buffer[4];
	wait_for_bytes(4, 200); // Wait for 4 bytes with a timeout of 200 ms
	read_signed_bytes(buffer, 4);
 	return (((int32_t) buffer[0]) & 0xff) | (((int32_t) buffer[1]) << 8 & 0xff00) | (((int32_t) buffer[2]) << 16 & 0xff0000) | (((int32_t) buffer[3]) << 24 & 0xff000000);
}

void write_order(enum Order myOrder)
{
	uint8_t* Order = (uint8_t*) &myOrder;
 	Serial.write(Order, sizeof(uint8_t));
}

void write_i8(int8_t num)
{
	Serial.write(num);
}

void write_i16(int16_t num)
{
	int8_t buffer[2] = {(int8_t) (num & 0xff), (int8_t) (num >> 8)};
	Serial.write((uint8_t*)&buffer, 2*sizeof(int8_t));
}

void write_i32(int32_t num)
{
	int8_t buffer[4] = {(int8_t) (num & 0xff), (int8_t) (num >> 8 & 0xff), (int8_t) (num >> 16 & 0xff), (int8_t) (num >> 24 & 0xff)};
	Serial.write((uint8_t*)&buffer, 4*sizeof(int8_t));
}

