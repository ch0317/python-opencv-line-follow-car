
import socket
import time

class socket_driver:

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        conn = self.sock.connect(("192.168.11.1",2001))
        if conn:
            print ("socket connect.")

    def forward(self):
        print("Forward")
        self.sock.send(chr(1).encode())

    def backward(self):
        print("Reverse")
        self.sock.send(chr(2).encode())

    def left(self):
        print("Right")
        self.sock.send(chr(3).encode())

    def right(self):
        print("Left")
        self.sock.send(chr(4).encode())

    def stop(self):
        print("stop")
        self.sock.send(chr(0).encode())


    def socket_close(self):
        self.sock.close()


def main():
    driver = socket_driver()
    while True:
        ctrl = raw_input("input cmd:")
        if ctrl == "t":
            driver.motor_control(40,40)
            time.sleep(1)
            driver.motor_control(60,60)
            time.sleep(1)
            driver.stop()
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