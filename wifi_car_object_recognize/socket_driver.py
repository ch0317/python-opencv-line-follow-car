
import socket
import time
import numpy as np
MOTOR = 102
STOP = 106
SERVO_LEFT = 107
SERVO_RIGHT = 108
SERVO_UP = 109
SERVO_DOWN = 110

class socket_driver:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        conn = self.sock.connect(("192.168.11.1",2001))
        if conn:
            print "socket connect."

    def motor_control(self, left_speed, right_speed):
        my_bytes = ''
        my_bytes += chr(MOTOR)
        my_bytes += '#'
        my_bytes += str(np.uint8(left_speed))
        my_bytes += '$'
        my_bytes += '#'
        my_bytes += str(np.uint8(right_speed))
        my_bytes += '$'
        print repr(my_bytes)

        self.sock.send(my_bytes)
        #time.sleep(0.02)
        print "recv:%s" % repr(self.sock.recv(1024))

    def stop(self):
        b = chr(STOP)
        self.sock.send(b)

    def eye_control(self, cmd):
        if cmd == SERVO_LEFT:
            b = chr(SERVO_LEFT)
            self.sock.send(b)
            print "recv:%s" % self.sock.recv(1024)
        elif cmd == SERVO_RIGHT:
            b = chr(SERVO_RIGHT)
            self.sock.send(b)
            print "recv:%s" % self.sock.recv(1024)
        elif cmd == SERVO_UP:
            b = chr(SERVO_UP)
            self.sock.send(b)
            print "recv:%s" % self.sock.recv(1024)
        elif cmd == SERVO_DOWN:
            b = chr(SERVO_DOWN)
            self.sock.send(b)
            print "recv:%s" % self.sock.recv(1024)

    def socket_close(self):
        self.sock.close()
        print "socket driver close."


def main():
    driver = socket_driver()
    while True:
        ctrl = raw_input("input cmd:")
        if ctrl == "t":
            speed = -1
            while speed > -127:
                speed -= 1
                driver.motor_control(0,speed)
                time.sleep(0.1)
                #driver.motor_control(40, 40)
                #time.sleep(2)
                #driver.stop()

        elif ctrl == 's':
            driver.stop()
        elif ctrl == "u":
            driver.eye_control(SERVO_UP)
        elif ctrl == "d":
            driver.eye_control(SERVO_DOWN)
        elif ctrl == "l":
            driver.eye_control(SERVO_LEFT)
        elif ctrl == "r":
            driver.eye_control(SERVO_RIGHT)
        elif ctrl == "q":
            driver.socket_close()
            return

if __name__ == '__main__':
    main()