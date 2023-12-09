#for hand detect
import cv2
import mediapipe as mp
import math
#for socket
import numpy as np
import socket

#for arduino control
import pyfirmata 
#for button control
from pyfirmata import Arduino
import time

# Hand Detect | setup
mpHands = mp.solutions.hands
mpDraw = mp.solutions.drawing_utils

# Hand Detect | Camera setup
cap = cv2.VideoCapture(1)
cap.set(3, 1280)  # Set width
cap.set(4, 720)  # Set height

cv2.namedWindow('image', cv2.WINDOW_AUTOSIZE)
cv2.resizeWindow('image', 1280, 720)  # Set window size

# Vibration | Arduino 
comport = "COM12"
board = pyfirmata.Arduino(comport) 
lenPin = board.get_pin('d:3:p')
# button | Arduino
BUTTON = 2
board.get_pin('d:2:i')

iterater = pyfirmata.util.Iterator(board)
iterater.start()


## Socket | Thumb Position - Unity socket setup
UDP_IP_THUMB_POSITION = "localhost"
UDP_PORT_THUMB_POSITION = 5001
sock_thumb_position = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Constants
FLIP_HORIZONTAL = 1
MID_THRESHOLD_X = 900
MID_THRESHOLD_Y = 300
PINCH_THRESHOLD = 60

# Hand Detect | main loop
with mpHands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:
    
    
    # Initialize the variable for pipette
    selectS = -1
    trigger = 0
    trigger_1_occurred = False
    trigger_2_occurred = False

    
    # Hand Detect | Loop until the video ends
    while cap.isOpened():
        
        button = board.digital[BUTTON].read()
        if (button == True):
            selectS = -1
            trigger = 0
            trigger_1_occurred = False
            trigger_2_occurred = False
            lenPin.write(0)
                
            selectS = 9
            print(button)

        # Hand Detect | read info
        success, image = cap.read()
        if not success:
            continue

        # Hand Detect | image setup (Horizontal flip)
        image = cv2.flip(image, FLIP_HORIZONTAL)

        # Hand Detect | MediaPipe | Convert the BGR image to RGB and process it with MediaPipe Hands.
        results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

        # Hand Detect | Save the thumb position 
        # Socket | send it via UDP
        if results.multi_hand_landmarks:
            
            for hand_landmarks in results.multi_hand_landmarks:
                # Hand Detect | check for pinch
                thumb_tip = hand_landmarks.landmark[4]
                index_tip = hand_landmarks.landmark[8]
                # pinky | trigger
                pinky_tip = hand_landmarks.landmark[17]

                test1 = hand_landmarks.landmark[6]
                test2 = hand_landmarks.landmark[7]

                thumb_x, thumb_y = int(thumb_tip.x * image.shape[1]), int(thumb_tip.y * image.shape[0])
                index_x, index_y = int(index_tip.x * image.shape[1]), int(index_tip.y * image.shape[0])
                pinky_x, pinky_y = int(pinky_tip.x * image.shape[1]), int(pinky_tip.y * image.shape[0])

                test1_x, test1_y = int(test1.x * image.shape[1]), int(test1.y * image.shape[0])
                test2_x, test2_y = int(test2.x * image.shape[1]), int(test2.y * image.shape[0])

                mid_x = (thumb_x + index_x) // 2
                mid_y = (thumb_y + index_y) // 2

                dist = math.sqrt((thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2)

                is_pinch = dist < PINCH_THRESHOLD


                # Pinch
                if is_pinch:                   

                    # Set pip when is_pinch is true
                    if mid_x <= MID_THRESHOLD_X and mid_x >= 670:
                        if mid_y > MID_THRESHOLD_Y:
                            if selectS == -1:
                                selectS = 0
                                
                                
                    elif mid_x > MID_THRESHOLD_X:
                        if mid_y > MID_THRESHOLD_Y:
                            if selectS == -1:
                                selectS = 1  

                # NOT Pinch
                elif not is_pinch:
                    selectS = -1
                    trigger = 0
                    lenPin.write(0)
                
                # trigger
                if (test1.y - test2.y)/(test1.x - test2.x) >= 0 and thumb_y > pinky_y:
                    if selectS == 0 and not trigger_1_occurred:
                        trigger = 1
                        trigger_1_occurred = True
                    elif selectS ==1 and not trigger_2_occurred:
                        trigger = 2      
                        trigger_2_occurred = True

                if is_pinch and not selectS == -1 and trigger == 0 :
                    if selectS == 0 and not trigger_1_occurred:
                        vib = 1 - dist / 60
                        lenPin.write(vib/2)            
                        print(vib*100/2)
                    if selectS == 1 and not trigger_2_occurred:
                        vib = 1 - dist / 60
                        lenPin.write(vib/2)            
                        print(vib*100/2)

                else:                   
                    lenPin.write(0)  

          

                ## Socket | send position
                thumb_position_str = "{}, {}, 0 , {}, {}".format(mid_x, - mid_y, selectS, trigger)
                sock_thumb_position.sendto(thumb_position_str.encode(), (UDP_IP_THUMB_POSITION, UDP_PORT_THUMB_POSITION))  # Send the thumb position via UDP
                                  
                mpDraw.draw_landmarks(
                    image, hand_landmarks, mpHands.HAND_CONNECTIONS)
                
                # default text
                cv2.putText(
                    image, text='MID_X : %d MID_Y : %d Select: %d  Distance : %d trigger : %d' % (mid_x, mid_y, selectS, dist,trigger), org=(10, 30),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=0.5,
                    color=255, thickness=2)
                
        else:
            lenPin.write(0)

        cv2.imshow('image', image)

        if cv2.waitKey(1) & 0xFF == 27:
            #lenPin.write(0)
            cap.release()
            cv2.destroyAllWindows()
            sock_thumb_position.close()
            break
