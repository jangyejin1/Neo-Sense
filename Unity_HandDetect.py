import cv2 
# , time, os, sys, json
import numpy as np
import mediapipe as mp
import socket
import math
from threading import Thread


# Thumb(ALL) | Thumb Position UDP socket setup
UDP_IP_THUMB_POSITION = "localhost"
UDP_PORT_THUMB_POSITION = 5001
sock_thumb_position = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)


# Unity socket setup
UNITY_IP = "localhost"  # Change this to the IP address of your Unity application
UNITY_PORT = 5002  # Change this to the port number used by your Unity application
sock_unity = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)



def remove_background(fps):

    mp_hands = mp.solutions.hands
    mpDraw = mp.solutions.drawing_utils
    hands = mp_hands.Hands(static_image_mode=False, max_num_hands=1,min_detection_confidence=0.5,min_tracking_confidence=0.5)

    # Initialize the variable for pipette
    pip = -1
    # Declare and initialize the Coordinate variable
    start_coords = None

    #MediaPipe | Open the video file
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
            print("오류: 비디오 파일을 열 수 없습니다.")
    else:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        ret, image = cap.read()
        if not ret:
            print("오류: 비디오 파일에서 프레임을 읽을 수 없습니다.")
        else:
            (h, w, c) = image.shape
            bg_image = np.ones((h, w, c)) * 255 
            bg_image = bg_image.astype(np.uint8) 

    # vectors_data = []  # Will contain the vectors

    ###### frame rate ##### 
    desired_frame_rate = fps

    # Determine the skip value for achieving the desired frame rate
    video_frame_rate = int(cap.get(cv2.CAP_PROP_FPS))  # Get the original frame rate of the video
    skip_frames = int(video_frame_rate / desired_frame_rate)  # Calculate how many frames to skip between the processed frames

    frame_number = 0
    #######################

    # Loop until the video ends
    while cap.isOpened():

        success, image = cap.read()
        if not success:
            break

        # Horizontal flip the image
        image = cv2.flip(image, 1)

        ###### frame rate  #####
        # Increment the frame number
        frame_number += 1
        # Skip frames to match the desired frame rate
        if frame_number % skip_frames != 0:
            continue
        ##########################

        # MediaPipe | Convert the BGR image to RGB and process it with MediaPipe Hands.
        results = hands.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

         # Hand | Save the thumb position in a dictionary and send it via UDP
        if results.multi_hand_landmarks:
            
            for hand_landmarks in results.multi_hand_landmarks:
                # Check for pinch (thumb and index finger touching)
                thumb_tip = hand_landmarks.landmark[4]
                index_tip = hand_landmarks.landmark[8]

                thumb_x = int(thumb_tip.x * image.shape[1])
                thumb_y = int(thumb_tip.y * image.shape[0])
                index_x = int(index_tip.x * image.shape[1])
                index_y = int(index_tip.y * image.shape[0])

                # Calculate the midpoint coordinates
                mid_x = (thumb_x + index_x) // 2
                mid_y = (thumb_y + index_y) // 2

                dist = math.sqrt((thumb_x - index_x) ** 2 + (thumb_y - index_y) ** 2)

                # Check if thumb and index fingers are close
                PINCH_THRESHOLD = 60  # Adjust this threshold based on your preferences
                is_pinch = dist < PINCH_THRESHOLD

                #for check
                # cv2.putText(
                #     image, text='Distance : %d' % dist, org=(10, 30),
                #     fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                #     color=255, thickness=2)

                # mpDraw.draw_landmarks(
                #     image, hand_landmarks, mp_hands.HAND_CONNECTIONS)


                if is_pinch:

                    unity_signal = "PINCH_DETECTED"
                    sock_unity.sendto(unity_signal.encode(), (UNITY_IP, UNITY_PORT))

                    if start_coords is None:
                        start_coords = (mid_x, mid_y)

                    # Calculate relative coordinates
                    relative_x = mid_x - start_coords[0]
                    relative_y = mid_y - start_coords[1]

                    # Set pip when is_pinch is true
                    if mid_x <= 310:
                        pip = 0
                    elif mid_x > 310:
                        pip = 1

                # Set pip to -1 when is_pinch is not true
                elif not is_pinch:
                    pip = -1
                    start_coords = None

                cv2.putText(
                    image, text='MID_X : %d  PIP: %d Distance : %d' % (mid_x, pip,dist), org=(10, 30),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                    color=255, thickness=2)
           

                if is_pinch:
                    cv2.putText(image, text='SUCCESS!', org=(10, 60),
                                fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                                color=0, thickness=2)

                mpDraw.draw_landmarks(image, hand_landmarks, mp_hands.HAND_CONNECTIONS)

                # cv2.putText(image, text='SUCCESS!', org=(10, 60),
                #             fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                #             color=0, thickness=2)
                
                # Send a signal to Unity when pinch is detected

                thumb_position_str = "{}, {}, 0".format(relative_x, - relative_y)
                sock_thumb_position.sendto(thumb_position_str.encode(), (UDP_IP_THUMB_POSITION, UDP_PORT_THUMB_POSITION))  # Send the thumb position via UDP


            # hand_landmarks = results.multi_hand_landmarks[0]  # Assuming only one hand is detected
            # thumb = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
            # thumb_x = int(thumb.x * image.shape[1])
            # thumb_y = int(-1 * thumb.y * image.shape[0])
            #thumb_position_str = "{}, {}, 0".format(thumb_x, thumb_y)
            
        # Display the current frame
        cv2.imshow("Camera Feed", image)

        #handler
        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):  # Exit when the 'q' key is pressed
            break
  
    # Release everything after the loop finishes
    cap.release()
    cv2.destroyAllWindows()
    sock_thumb_position.close()
    sock_unity.close()

if __name__ == "__main__":

    remove_background(12)
    

    #"http://10.210.40.231:8080/video"

