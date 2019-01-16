import cv2
import urllib2
import numpy as np
import sys
import math
import socket_driver
import time

HOST = "192.168.1.1:8080"
# The grey image is used for most of the calculations and isn't displayed
WINDOW_GRAY_IMAGE = 'gray image'
# This is displayed on screen with overlays showing the line tracking
WINDOW_DISPLAY_IMAGE = 'display image'

# define the lower and upper boundaries of the colors in the HSV color space
lower = {'red': (166, 84, 141), 'green': (50, 100, 100), 'blue': (110,50,50), 'yellow': (23, 59, 119),
         'orange': (5,50,50), 'black' :(0, 0, 0) }  # assign new item lower['blue'] = (93, 10, 0)
upper = {'red': (186, 255, 255), 'green': (70, 255, 255), 'blue': (130,255,255), 'yellow': (54, 255, 255),
         'orange': (20, 255, 255), 'black' : (180, 255, 30)}

# define standard colors for circle around the object
colors = {'red': (0, 0, 255), 'green': (0, 255, 0), 'blue': (255, 0, 0), 'yellow': (0, 255, 217),
          'orange': (15,255,255), 'black' : (0,0,0)}

# Trackbar controls so you can refine how the search works
CONTROL_SCAN_RADIUS = 'Scan Radius'
CONTROL_NUMBER_OF_CIRCLES = 'Number of Scans'
CONTROL_LINE_WIDTH = 'Line Width'
SPEED_LIMIT = 10
SPEED_MAX = 80
KP1 = 1
KD1 = 1


# Resolution of the camera image. larger images allow for more detail, but take more to process.
# valid resolutions include:
#   160 x 120
#   320 x 240
#   640 x 480
#   800 x 600
# etc...
RESOLUTION_X = 640
RESOLUTION_Y = 480

# This is half the width of the line at the bottom of the screen that we start looking for
# the line we want to follow.
#SCAN_RADIUS = RESOLUTION_X / 4
SCAN_RADIUS = RESOLUTION_X / 2
# Start the scan height 10 pixels from the bottom.
SCAN_HEIGHT = RESOLUTION_Y - 150
# This is our centre. We assume that we want to try and track the line in relation to this point
SCAN_POS_X = RESOLUTION_X / 2

# This is the radius that we scan from the last known point for each of the circles
SCAN_RADIUS_REG = 1000
# The number of itterations we scan to allow us to look ahead and give us more time
# to make better choices
NUMBER_OF_CIRCLES = 1


def scanLine(image, display_image, point, radius):
    x = point[0];
    y = point[1];

    scan_start = x - radius
    scan_end = x + radius
    row = image[y]
    data = np.empty(radius * 2)
    data[:] = row[scan_start:scan_end]

    # Draw a line where we are reading the data
    cv2.line(display_image, (scan_start, y), (scan_end, y), (255, 0, 0), 2)
    cv2.circle(display_image, (scan_start, y), 5, (255, 0, 0), -1, 8, 0)
    cv2.circle(display_image, (scan_end, y), 5, (255, 0, 0), -1, 8, 0)
    # print("scanline x:{} y:{} - start x:{} end x:{} - {}".format(x, y, scan_start, scan_end, SCAN_DATA))
    return data;


def coordinateFromPoint(origin, angle, radius):
    xo = origin[0]
    yo = origin[1]

    # Work out the co-ordinate for the pixel on the circumference of the circle
    x = xo - radius * math.cos(math.radians(angle))
    y = yo + radius * math.sin(math.radians(angle))

    # We only want whole numbers
    x = int(round(x))
    y = int(round(y))
    return (x, y);


def scanCircle(image, display_image, point, radius, look_angle):
    x = point[0];
    y = point[1];
    scan_start = x - radius
    scan_end = x + radius

    endpoint_left = coordinateFromPoint(point, look_angle - 90, radius)
    endpoint_right = coordinateFromPoint(point, look_angle + 90, radius)

    # print("scanline left:{} right:{} angle:{}".format(endpoint_left, endpoint_right, look_angle))
    # Draw a circle to indicate where we start and end scanning.
    cv2.circle(display_image, (endpoint_left[0], endpoint_left[1]), 5, (255, 100, 100), -1, 8, 0)
    cv2.circle(display_image, (endpoint_right[0], endpoint_right[1]), 5, (100, 255, 100), -1, 8, 0)
    cv2.line(display_image, (endpoint_left[0], endpoint_left[1]), (endpoint_right[0], endpoint_right[1]), (255, 0, 0),
             1)
    cv2.circle(display_image, (x, y), radius, (100, 100, 100), 1, 8, 0)

    # We are only going to scan half the circumference
    data = np.zeros(shape=(180, 3))

    # Getting the co-ordinates and value for every degree in the semi circle
    startAngle = look_angle - 90

    returnVal = True
    for i in range(0, 180, 1):
        current_angle = startAngle + i
        scan_point = coordinateFromPoint(point, current_angle, radius)

        if inImageBounds(image, scan_point[0], scan_point[1]):
            imageValue = image[scan_point[1]][scan_point[0]]
            data[i] = [imageValue, scan_point[0], scan_point[1]]
        else:
            returnVal = False
            break;

    return returnVal, data;


def findInCircle(display_image, scan_data):
    data = np.zeros(shape=(len(scan_data) - 1, 1))
    data[0] = 0
    data[len(data) - 1] = 0
    for index in range(1, len(data)):
        data[index] = scan_data[index - 1][0] - scan_data[index][0]

    # left and right should be the boundry values.
    # first element will be the image value
    # second element will be the index of the data item
    left = [0, 0]
    right = [0, 0]

    for index in range(0, len(data)):
        if data[index] > left[1]:
            left[1] = data[index]
            left[0] = index

        if data[index] < right[1]:
            right[1] = data[index]
            right[0] = index

    leftx = int(scan_data[left[0]][1])
    lefty = int(scan_data[left[0]][2])
    lefti = left[0]
    rightx = int(scan_data[right[0]][1])
    righty = int(scan_data[right[0]][2])
    righti = right[0]

    centre_index = int(round((righti + lefti) / 2))

    position = [int(scan_data[centre_index][1]), int(scan_data[centre_index][2])]

    # mid point, where we believe is the centre of the line
    cv2.circle(display_image, (position[0], position[1]), 5, (255, 255, 255), -1, 8, 0)
    # left boundrary dot on the line
    cv2.circle(display_image, (leftx, lefty), 2, (0, 0, 102), 2, 8, 0)
    # right boundrary dot on the line
    cv2.circle(display_image, (rightx, righty), 2, (0, 0, 102), 2, 8, 0)

    return position;


def inImageBounds(image, x, y):
    return x >= 0 and y >= 0 and y < len(image) and x < len(image[y])


def findLine(display_image, scan_data, x, y, radius):
    data = np.empty(len(scan_data) - 1)
    data[0] = 0
    data[len(data) - 1] = 0
    for index in range(1, len(data)):
        data[index] = scan_data[index - 1] - scan_data[index]

    scan_start = x - radius
    scan_end = x + radius

    left = [0, 0]
    right = [0, 0]

    for index in range(0, len(data)):
        if data[index] > left[1]:
            left[1] = data[index]
            left[0] = index

        if data[index] < right[1]:
            right[1] = data[index]
            right[0] = index

    line_position = (right[0] + left[0]) / 2
    # print("line position {} {}, {} - {}".format(scan_start, left, right, line_position))
    # mid point, where we believe is the centre of the line
    # cv2.circle(display_image, (scan_start + line_position, y), 5, (0, 204, 102), -1, 8, 0)
    # left boundrary dot on the line
    # cv2.circle(display_image, (scan_start + left[0], y), 5, (0, 0, 102), -1, 4, 0)
    # right boundrary dot on the line
    # cv2.circle(display_image, (scan_start + right[0], y), 5, (0, 0, 102), -1, 4, 0)
    return (scan_start + line_position, y);


def lineAngle(point1, point2):
    angle = round(math.atan2((point2[1] - point1[1]), -(point2[0] - point1[0])) * 180 / math.pi)
    return angle


def lineLength(point1, point2):
    dx = point1[0] - point2[0]
    dy = point1[1] - point2[1]
    return int(round(math.sqrt(dx * dx + dy * dy)));


def onScanRadiusChange(newValue):
    global SCAN_RADIUS_REG
    SCAN_RADIUS_REG = newValue
    return;


def onCircleScanChange(newValue):
    global NUMBER_OF_CIRCLES
    NUMBER_OF_CIRCLES = newValue
    return;

def onLineWidthChange(newValue):
    global SCAN_RADIUS
    SCAN_RADIUS = int(round(newValue / 2))
    return;

def main():
    # Create a window
    cv2.namedWindow(WINDOW_DISPLAY_IMAGE)
    # position the window
    cv2.moveWindow(WINDOW_DISPLAY_IMAGE, 0, 35)

    # Add some controls to the window
    cv2.createTrackbar(CONTROL_SCAN_RADIUS, WINDOW_DISPLAY_IMAGE, 5, 50, onScanRadiusChange)
    cv2.setTrackbarPos(CONTROL_SCAN_RADIUS, WINDOW_DISPLAY_IMAGE, SCAN_RADIUS_REG)

    cv2.createTrackbar(CONTROL_NUMBER_OF_CIRCLES, WINDOW_DISPLAY_IMAGE, 0, 7, onCircleScanChange)
    cv2.setTrackbarPos(CONTROL_NUMBER_OF_CIRCLES, WINDOW_DISPLAY_IMAGE, NUMBER_OF_CIRCLES)

    cv2.createTrackbar(CONTROL_LINE_WIDTH, WINDOW_DISPLAY_IMAGE, 0, RESOLUTION_X, onLineWidthChange)
    cv2.setTrackbarPos(CONTROL_LINE_WIDTH, WINDOW_DISPLAY_IMAGE, SCAN_RADIUS * 2)

    returnString = """
    Press Esc to end the program
    Using camera resolution: {}x{}
    Centre point: {}:{}
    Scan radius: {}
    Number of search itterations: {}
    Baseline Width: {}
    """.format(RESOLUTION_X, RESOLUTION_Y, SCAN_POS_X, SCAN_HEIGHT, SCAN_RADIUS_REG, NUMBER_OF_CIRCLES, SCAN_RADIUS * 2)

    print(returnString)

    driver = socket_driver.socket_driver()
    last_error = 0
    last_time = time.time()
    speed_base = 100

    host_str = 'http://' + HOST + '/?action=stream'
    print 'Streaming ' + host_str

    print 'Print Esc to quit'
    stream = urllib2.urlopen(host_str)
    video_bytes = ''
    while True:

        e1 = cv2.getTickCount()

        video_bytes += stream.read(1024)
        a = video_bytes.find('\xff\xd8')
        b = video_bytes.find('\xff\xd9')
        if a != -1 and b != -1:
            jpg = video_bytes[a:b + 2]
            video_bytes = video_bytes[b + 2:]
            image = cv2.imdecode(np.fromstring(jpg, dtype=np.uint8), flags=1)

            grey_image = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
            display_image = cv2.copyMakeBorder(image, 0, 0, 0, 0, cv2.BORDER_REPLICATE)
            hsv = cv2.cvtColor(image,cv2.COLOR_BGR2HSV)
            center_point = (SCAN_POS_X, SCAN_HEIGHT)

            # San a horizontal line based on the centre point
            # We could just use this data to work out how far off centre we are and steer accordingly.
            # Get a data array of all the falues along that line
            # scan_data is an array containing:
            #   - pixel value
            scan_data = scanLine(grey_image, display_image, center_point, SCAN_RADIUS)
            # The center point we believe the line we are following intersects with our scan line.
            point_on_line = findLine(display_image, scan_data, SCAN_POS_X, SCAN_HEIGHT, SCAN_RADIUS)

            # Start scanning the arcs
            # This allows us to look ahead further ahead at the line and work out an angle to steer
            # From the intersection point of the line, scan in an arc to find the line
            # The scan data contains an array
            #   - pixel value
            #   - x co-ordinate
            #   - y co-ordinate
            returnVal, scan_data = scanCircle(grey_image, display_image, point_on_line, SCAN_RADIUS_REG, -90)
            previous_point = point_on_line
            # in the same way ads the findLine, go through the data, find the mid point and return the co-ordinates.
            last_point = findInCircle(display_image, scan_data)
            cv2.line(display_image, (previous_point[0], previous_point[1]), (last_point[0], last_point[1]),
                     (255, 255, 255), 1)

            actual_number_of_circles = 0
            for scan_count in range(0, NUMBER_OF_CIRCLES):
                returnVal, scan_data = scanCircle(grey_image, display_image, last_point, SCAN_RADIUS_REG,
                                                  lineAngle(previous_point, last_point))

                # Only work out the next itteration if our point is within the bounds of the image
                if returnVal == True:
                    actual_number_of_circles += 1
                    previous_point = last_point
                    last_point = findInCircle(display_image, scan_data)
                    cv2.line(display_image, (previous_point[0], previous_point[1]), (last_point[0], last_point[1]),
                             (255, 255, 255), 1)
                else:
                    break;

            # Draw a line from the centre point to the end point where we last found the line we are following
            cv2.line(display_image, (center_point[0], center_point[1]), (last_point[0], last_point[1]), (0, 0, 255), 1)

            # Display the image
            cv2.imshow(WINDOW_DISPLAY_IMAGE, display_image)
            # This is the maximum distance the end point of our search for a line can be from the centre point.
            line_scan_length = SCAN_RADIUS_REG * (actual_number_of_circles + 1)
            # This is the measured line length from the centre point
            line_length_from_center = lineLength(center_point, last_point)
            center_y_distance = center_point[1] - last_point[1]
            center_x_distance = center_point[0] - last_point[0]

            # Stop counting all work is done at this point and calculate how we are doing.
            e2 = cv2.getTickCount()

            returnString = "fps {} - bearing {} - x:{} y:{} look distance:{} distance from origin:{}".format(
                1000 / ((e2 - e1) / cv2.getTickFrequency() * 1000),
                lineAngle(center_point, last_point) * -1 - 90,
                center_x_distance,
                center_y_distance,
                line_scan_length,
                line_length_from_center)
            #print(returnString)
            print "center_x_distance: ",center_x_distance

            t = time.time()
            '''if int(round(t * 1000)) - last_time > 100:
                last_time = int(round(t * 1000));
                if SPEED_LIMIT > speed_base:
                    speed_base += 1
                elif SPEED_LIMIT < speed_base:
                    speed_base -= 2'''

            position = center_x_distance
            error = -center_x_distance

            motorSpeed = int(KP1 * error + KD1 * (error - last_error))

            print "motorSpeed: %d" % motorSpeed
            last_error = error
            m1_speed_ = speed_base + motorSpeed
            m2_speed_ = speed_base - motorSpeed
            print "m1_speed_origin: %d" % m1_speed_
            print "m2_speed_origin: %d" % m2_speed_


            if m1_speed_ < 0:
                m1_speed_ = 0
            if m2_speed_ < 0:
                m2_speed_ = 0


            #map 0~50
            m1 = int(m1_speed_ * 50 / 255)
            m2 = int(m2_speed_ * 50 / 255)
            print "m1: %d" % m1
            print "m2: %d" % m2
            driver.motor_control(m1, m2)
            time.sleep(0.001)

            #print image.shape
            # Create a window
            #cv2.namedWindow(WINDOW_DISPLAY_IMAGE)
            # position the window
            #cv2.moveWindow(WINDOW_DISPLAY_IMAGE, 0, 35)
            #hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
            #cv2.imshow("open cv video:", image)
            #cv2.imshow("hsv window", hsv)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                exit(0)

if __name__ == '__main__':
    main()