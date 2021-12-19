import mediapipe as mp
import cv2
import time


class bodyDetector():
    def __init__(self, mode=False, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.detectionCon = detectionCon
        self.trackCon = trackCon

        self.mp_holistic = mp.solutions.holistic
        self.holistic = self.mp_holistic.Holistic(static_image_mode=self.mode,
                                                  min_detection_confidence=self.detectionCon,
                                                  min_tracking_confidence=self.trackCon)
        self.mp_drawing = mp.solutions.drawing_utils
        self.results = None

    def trackBody(self, image, draw=True):
        imgRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        imgRGB.flags.writeable = False
        # Make Detections
        self.results = self.holistic.process(imgRGB)

        if draw:
            # Draw face Landmarks
            self.mp_drawing.draw_landmarks(image, self.results.face_landmarks, self.mp_holistic.FACEMESH_CONTOURS,
                                      self.mp_drawing.DrawingSpec(color=(80, 110, 10), thickness=1, circle_radius=1),
                                      self.mp_drawing.DrawingSpec(color=(80, 256, 121), thickness=1, circle_radius=1)
                                      )

            # Right Hand
            self.mp_drawing.draw_landmarks(image, self.results.right_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS,
                                      self.mp_drawing.DrawingSpec(color=(80, 22, 10), thickness=2, circle_radius=4),
                                      self.mp_drawing.DrawingSpec(color=(80, 44, 121), thickness=2, circle_radius=2)
                                      )

            # Left Hand
            self.mp_drawing.draw_landmarks(image, self.results.left_hand_landmarks, self.mp_holistic.HAND_CONNECTIONS,
                                      self.mp_drawing.DrawingSpec(color=(121, 22, 76), thickness=2, circle_radius=4),
                                      self.mp_drawing.DrawingSpec(color=(121, 44, 250), thickness=2, circle_radius=2)
                                      )

            # Pose Detections
            self.mp_drawing.draw_landmarks(image, self.results.pose_landmarks, self.mp_holistic.POSE_CONNECTIONS,
                                      self.mp_drawing.DrawingSpec(color=(245, 117, 66), thickness=2, circle_radius=4),
                                      self.mp_drawing.DrawingSpec(color=(245, 66, 230), thickness=2, circle_radius=2)
                                      )

            # Highlight finger tips of right hand
            if self.results.right_hand_landmarks:
                h, w, c = image.shape

                for id, lm in enumerate(self.results.right_hand_landmarks.landmark):
                    if id in (0, 4, 8, 12, 16, 20):
                        cv2.circle(image, (int(lm.x * w), int(lm.y * h)), 15, (255, 0, 255), cv2.FILLED)

        return image


    def findHandPositions(self, image, hand='R', draw=True):

        lmList = []
        h, w, c = image.shape

        if hand == 'R' and self.results.right_hand_landmarks:
            for id, lm in enumerate(self.results.right_hand_landmarks.landmark):
                lmList.append([id, int(lm.x * w), int(lm.y * h)])
        elif hand == 'L' and self.results.left_hand_landmarks:
            for id, lm in enumerate(self.results.left_hand_landmarks.landmark):
                lmList.append([id, int(lm.x * w), int(lm.y * h)])

        return lmList

    def parseHandSign(self, lmList, hand='R'):

        tipIds = [4, 8, 12, 16, 20]
        fingers = []
        cmd = ''

        if len(lmList) != 0:
            # check takeoff or land first
            thumbUp = True if lmList[tipIds[0]][2] < lmList[tipIds[0]-1][2] else False
            thumbDown = True if lmList[tipIds[0]][2] > lmList[tipIds[0]-1][2] else False
            for id in range(1,5):
                if lmList[tipIds[0]-2][2] >= lmList[tipIds[id]][2]:
                    thumbUp = False
                if lmList[tipIds[0]-2][2] <= lmList[tipIds[id]][2]:
                    thumbDown = False

            if thumbUp:
                cmd = 'takeoff'
            elif thumbDown:
                cmd = 'land'
            else:
                # Thumb
                if lmList[tipIds[0]][1] > lmList[tipIds[0]-1][1]:
                    fingers.append(1)
                else:
                    fingers.append(0)
                # Other fingers
                for id in range(1, 5):
                    if lmList[tipIds[id]][2] < lmList[tipIds[id]-2][2]:
                        fingers.append(1)
                    else:
                        fingers.append(0)

                if fingers == [0, 0, 0, 0, 0]:
                    cmd = 'stop'
                elif fingers == [1, 1, 1, 1, 1]:
                    cmd = 'backward'
                elif fingers == [0, 1, 1, 1, 1]:
                    cmd = 'forward'
                elif fingers == [1, 0, 0, 0, 0]:
                    cmd = 'left'
                elif fingers == [0, 0, 0, 0, 1]:
                    cmd = 'right'
                elif fingers == [0, 1, 0, 0, 0]:
                    cmd = 'up'
                elif fingers == [0, 1, 1, 0, 0]:
                    cmd = 'down'
                elif fingers == [1, 1, 0, 0, 1]:
                    cmd = 'left flip'
                elif fingers == [1, 0, 0, 0, 1]:
                    cmd = 'right flip'

        return cmd


def main():
    cap = cv2.VideoCapture(0)
    detector = bodyDetector()
    pTime = time.time()

    while True:
        success, frame = cap.read()
        image = detector.trackBody(frame)
        lmList = detector.findHandPositions(image)
        if len(lmList) != 0:
            print(lmList[4])

        cTime = time.time()
        fps = 1 / (cTime - pTime)
        pTime = cTime

        cv2.putText(image, f'FPS: {int(fps)}', (600,40), cv2.FONT_HERSHEY_PLAIN, 2, (0,0,255), 1)
        cv2.imshow('Body Cam', image)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break



if __name__ == "__main__":
    main()