import numpy as np
import cv2
import urllib2  # for reading image from URL
import socket_driver
import time

host = "192.168.11.1:8080"
hoststr = 'http://' + host + '/?action=stream'
print 'Video Streaming from:' + hoststr

image_center = 320

SPEED_LIMIT = 10
SPEED_MAX = 80
KP1 = 0.55
KD1 = 0.55

# define the lower and upper boundaries of the colors in the HSV color space
lower = {'red': (170, 70, 50), 'red ':(0,200,50),'green': (30, 50, 50), 'blue': (90,110,20), 'yellow': (20, 124, 123)
          }  # assign new item lower['blue'] = (93, 10, 0)
#'black' :(0, 0, 0)
#'orange': (5,50,50)
#upper = {'red': (180, 255, 255),'red ':(10,255,255), 'green': (80, 220, 220), 'blue': (110,255,255), 'yellow': (30, 255, 255)}
upper = {'green': (80, 220, 220)}
#'black' : (180, 255, 30)
#'orange': (20, 255, 255)

# define standard colors for circle around the object
colors = {'red': (0, 0, 255), 'red ':(0,0,255),'green': (0, 255, 0), 'blue': (255, 200, 0), 'yellow': (0, 255, 217)
          }
#'black': (0, 0, 0)
#'orange': (15,255,255)

# pts = deque(maxlen=args["buffer"])


class ShapeRecognition():
    def __init__(self):
        pass

stream = urllib2.urlopen(hoststr)
bytes=''

driver = socket_driver.socket_driver()
speed_base = 100
last_error = 0




# keep looping
while True:
    bytes += stream.read(1024)
    a = bytes.find('\xff\xd8')
    b = bytes.find('\xff\xd9')
    if a != -1 and b != -1:
        jpg = bytes[a:b + 2]
        bytes = bytes[b + 2:]
        frame = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), flags=1)

        # IP webcam image stream
        # URL = 'http://10.254.254.102:8080/shot.jpg'
        # urllib.urlretrieve(URL, 'shot1.jpg')
        # frame = cv2.imread('shot1.jpg')
        # resize the frame, blur it, and convert it to the HSV
        # color space

        blurred = cv2.GaussianBlur(frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        # for each color in dictionary check object in frame
        for key, value in upper.items():
            # construct a mask for the color from dictionary`1, then perform
            # a series of dilations and erosions to remove any small
            # blobs left in the mask
            kernel = np.ones((9, 9), np.uint8)
            mask = cv2.inRange(hsv, lower[key], upper[key])
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

            # find contours in the mask and initialize the current
            # (x, y) center of the ball
            cnts = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL,
                                    cv2.CHAIN_APPROX_SIMPLE)[-2]
            center = None

            ballPixel = 0

            # only proceed if at least one contour was found
            if len(cnts) > 0:
                # find the largest contour in the mask, then use
                # it to compute the minimum enclosing circle and
                # centroid
                c = max(cnts, key=cv2.contourArea)
                ((x, y), radius) = cv2.minEnclosingCircle(c)
                M = cv2.moments(c)
                center = (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))


                print "radius: %d center: x %d , y %d "% (radius,center[0],center[1])

                # only proceed if the radius meets a minimum size. Correct this value for your obect's size
                if radius > 10:
                    # draw the circle and centroid on the frame,
                    # then update the list of tracked points
                    cv2.circle(frame, (int(x), int(y)), int(radius), colors[key], 2)
                    cv2.putText(frame, key + " ", (int(x - radius), int(y - radius)), cv2.FONT_HERSHEY_SIMPLEX, 0.6,colors[key], 2)

                    position = center[0] - image_center
                    error = position

                    motorSpeed = int(KP1 * error + KD1 * (error - last_error))

                    #print "motorSpeed: %d" % motorSpeed
                    last_error = error
                    m1_speed_ = speed_base + motorSpeed
                    m2_speed_ = speed_base - motorSpeed
                    print "m1_speed_origin: %d" % m1_speed_
                    print "m2_speed_origin: %d" % m2_speed_

                    m1 = int(m1_speed_ * 60 / 255)
                    m2 = int(m2_speed_ * 60 / 255)
                    print "m1: %d" % m1
                    print "m2: %d" % m2
                    driver.motor_control(m1, m2)
                else:
                    driver.stop()
            else:
                driver.stop()

        # show the frame to our screen

        cv2.imshow("Frame", frame)
        time.sleep(0.05)

        key = cv2.waitKey(1) & 0xFF
        # if the 'q' key is pressed, stop the loop
        if key == ord("q"):
            break

# cleanup the camera and close any open windows
cv2.destroyAllWindows()