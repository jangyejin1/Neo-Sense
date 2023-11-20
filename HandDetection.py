import cv2
import mediapipe as mp
import math

mpHands = mp.solutions.hands
mpDraw = mp.solutions.drawing_utils

# Open the WebCam
cap = cv2.VideoCapture(0)

# Set the window and it's size
width, height = 960, 720
cv2.namedWindow('Hand Detection', cv2.WINDOW_NORMAL)
cv2.resizeWindow('Hand Detection', width, height)

# Initialize the variable for pipette
pip = -1
# Declare and initialize the Coordinate variable
pre_x = None
pre_y = None
start_coords = None

with mpHands.Hands(
        max_num_hands=1,
        min_detection_confidence=0.5,
        min_tracking_confidence=0.5) as hands:

    while cap.isOpened():
        success, image = cap.read()

        if not success:
            continue

        image = cv2.cvtColor(cv2.flip(image, 1), cv2.COLOR_BGR2RGB)

        results = hands.process(image)

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

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
                PINCH_THRESHOLD = 30  # Value adjustment required
                is_pinch = dist < PINCH_THRESHOLD

                # Update pip only when is_pinch becomes True
                if is_pinch:

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
                        
                cv2.putText(
                    image, text='MID_X : %d  PIP: %d' % (mid_x, pip), org=(10, 30),
                    fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                    color=255, thickness=2)

                if is_pinch:
                    cv2.putText(image, text='SUCCESS!', org=(10, 60),
                                fontFace=cv2.FONT_HERSHEY_SIMPLEX, fontScale=1,
                                color=0, thickness=2)

                # Update previous coordinates
                pre_x = mid_x
                pre_y = mid_y

                mpDraw.draw_landmarks(
                    image, hand_landmarks, mpHands.HAND_CONNECTIONS)

        cv2.imshow('Hand Detection', image)

        if cv2.waitKey(1) & 0xFF == 27:  # Press 'esc' key to exit the program
            break

cap.release()
cv2.destroyAllWindows()
