import cv2
import mediapipe as mp
from collections import deque
from math import acos, pi, hypot, atan, sqrt, sin, cos
import serial
import time


def length_hand(x, y, z):
    x1 = x[5] - x[0]
    y1 = y[5] - y[0]
    z1 = z[5] - z[0]

    return hypot(x1, y1, z1)


def length_index_finger(x, y, z):
    x1 = x[8] - x[0]
    y1 = y[8] - y[0]
    z1 = z[8] - z[0]

    return hypot(x1, y1, z1) / length_hand(x, y, z)


def length_middle_finger(x, y, z):
    x1 = x[12] - x[0]
    y1 = y[12] - y[0]
    z1 = z[12] - z[0]
    return hypot(x1, y1, z1) / length_hand(x, y, z)


def length_ring_finger(x, y, z):
    x1 = x[16] - x[0]
    y1 = y[16] - y[0]
    z1 = z[16] - z[0]
    return hypot(x1, y1, z1) / length_hand(x, y, z)


def length_pinky_finger(x, y, z):
    x1 = x[20] - x[0]
    y1 = y[20] - y[0]
    z1 = z[20] - z[0]
    return hypot(x1, y1, z1) / length_hand(x, y, z)


def length_thumb_finger(x, y, z):
    x1 = x[4] - x[0]
    y1 = y[4] - y[0]
    z1 = z[4] - z[0]
    return hypot(x1, y1, z1) / length_hand(x, y, z)


def find_lengths(x, y, z):
    lengths = [0] * 6
    lengths[0] = length_index_finger(x, y, z)
    lengths[1] = length_middle_finger(x, y, z)
    lengths[2] = length_ring_finger(x, y, z)
    lengths[3] = length_pinky_finger(x, y, z)
    lengths[4] = length_thumb_finger(x, y, z)
    lengths[5] = length_hand(x, y, z)

    return lengths


def find_coords(x, y, z):
    return [x[4], y[4], x[8], y[8]]


last_lengths = deque()
last_coords = deque()
size = 15


def median_filter(a, last):
    res = [0] * len(a)

    last.append(a)
    if len(last) > size:
        last.popleft()
    for i in range(len(a)):
        t = [v[i] for v in last]
        t.sort()
        res[i] = t[len(t) // 2]

    return res


palm = [0] * 5
fist = [0] * 5
up = 0
down = 0
calibrate_flag = 1


def calibrate(x, y, z):
    global calibrate_flag, palm, fist, up, down, last_lengths
    if calibrate_flag == 1:
        cv2.putText(image, 'Show palm', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0))
        if cv2.waitKey(1) & 0xFF == ord('a'):
            palm = median_filter(find_lengths(x, y, z), last_lengths)
            calibrate_flag = 2
    elif calibrate_flag == 2:
        cv2.putText(image, 'Show fist', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0))
        if cv2.waitKey(1) & 0xFF == ord('a'):
            fist = median_filter(find_lengths(x, y, z), last_lengths)
            calibrate_flag = 3


my_serial = serial.Serial('COM5', 115200)
palm_instruction = [5, 5, 5, 3]
hand = 50
servoAngle = [0, -90, 270, 90, 0, 0, 90]


def move(shift, h, alfa):
    global servoAngle
    if 180 >= alfa >= 0:
        b = 90
        if shift != 0:
            b = atan(h / shift)
        len = sqrt(h ** 2 + shift ** 2)
        print(len, hand, shift)
        a = 0
        if len / 2 <= hand:
            a = acos(len / 2 / hand)

        a = a * 180 / pi
        b = b * 180 / pi

        sum_angle = servoAngle[0] + servoAngle[1] + servoAngle[2]
        # sum_angle = 180
        servoAngle[0] = int(a + b)
        servoAngle[1] = int(-2 * a)
        servoAngle[2] = sum_angle - servoAngle[0] - servoAngle[1]

        sum_alfa = servoAngle[3] + servoAngle[4]
        servoAngle[3] = int(alfa)
        servoAngle[4] = int(sum_alfa - servoAngle[3])
        servoAngle[4] = max(-90, min(90, servoAngle[4]))


height = 10


def get_instruction(lengths, coords):
    global height
    th = [coords[0], coords[1]]
    index = [coords[2], coords[3]]

    if all([(lengths[i] - fist[i]) / (palm[i] - fist[i]) < 0.8 for i in range(5)]):
        print('STOP')
        return

    if (lengths[1] - fist[1]) / (palm[1] - fist[1]) < 0.8 and (lengths[2] - fist[2]) / (palm[2] - fist[2]) > 0.8:
        height += 3
    elif (lengths[2] - fist[2]) / (palm[2] - fist[2]) < 0.8 and (lengths[1] - fist[1]) / (palm[1] - fist[1]) > 0.8:
        height -= 3

    if (lengths[4] - fist[4]) / (palm[4] - fist[4]) < 0.8 \
            and (lengths[1] - fist[1]) / (palm[1] - fist[1]) < 0.8 \
            and (lengths[2] - fist[2]) / (palm[2] - fist[2]) < 0.8:
        servoAngle[-1] += 3
    elif (lengths[4] - fist[4]) / (palm[4] - fist[4]) > 0.8 \
            and (lengths[1] - fist[1]) / (palm[1] - fist[1]) < 0.8 \
            and (lengths[2] - fist[2]) / (palm[2] - fist[2]) < 0.8:
        servoAngle[-1] -= 3

    height = min(2 * hand, max(0, height))

    X, Y = w // 2, h - 100

    x, y = int(index[0]), int(index[1])
    print(x, y)
    cv2.line(image, (x, y), (X, Y), (255, 255, 255), 3)
    shift = sqrt((X - x) ** 2 + (Y - y) ** 2)
    alfa = acos((x-X) / shift)
    alfa = int(180 * alfa / pi)
    if y > Y:
        alfa = 360 - alfa
    move(shift / 5, height, alfa)
    return servoAngle


def write_instruction(lengths, coords):
    get_instruction(lengths, coords)
    print(servoAngle)

    a = 0
    x1, y1 = 0, 0
    for i in range(0, 3):
        a += servoAngle[i]
        x2 = int(cos(a / 180 * pi) * hand) + x1
        y2 = int(-sin(a / 180 * pi) * hand) + y1

        cv2.line(image, (int(x1 * cos((servoAngle[3]) * pi / 180)) + 500, y1 + 200),
                 (int(x2 * cos((servoAngle[3]) * pi / 180)) + 500, y2 + 200), (255, 255, 255), 3)
        x3, y3 = x1, y1
        x1, y1 = x2, y2

    x1 = int(x3 * cos(servoAngle[3] * pi / 180) + 500)
    y1 = int(x3 * -sin(servoAngle[3] * pi / 180) + 400)
    x2 = x1 + int(hand * cos((servoAngle[3] + servoAngle[4]) * pi / 180))
    y2 = y1 + int(hand * -sin((servoAngle[3] + servoAngle[4]) * pi / 180))
    cv2.line(image, (500, 400), (x1, y1), (255, 255, 255), 3)
    cv2.line(image, (x1, y1), (x2, y2), (255, 255, 255), 3)
    my_serial.write(bytes([254]))
    my_serial.write(bytes([max(0, min(180, servoAngle[3]))]))
    # print(my_serial.read(1), end='')
    my_serial.write(bytes([max(0, min(180, servoAngle[0]))]))
    # print(my_serial.read(1), end='')
    my_serial.write(bytes([max(0, min(180, abs(servoAngle[1])))]))
    # print(my_serial.read(1), end='')
    my_serial.write(bytes([max(0, min(180, 270 - servoAngle[2]))]))
    # print(my_serial.read(1), end='')
    my_serial.write(bytes([max(0, min(180, servoAngle[4] + 90))]))  # надо подумать
    # print(my_serial.read(1), end='')
    my_serial.write(bytes([max(0, min(180, servoAngle[6]))]))
    # print(my_serial.read(1), end='')
    my_serial.write(bytes([max(0, min(180, servoAngle[5]))]))
    # print(my_serial.read(1), end='')
    print(my_serial.read())
    time.sleep(0.01)


cap = cv2.VideoCapture(0)  # Камера
ret, frame = cap.read()
(h, w) = frame.shape[:2]
hands = mp.solutions.hands.Hands(max_num_hands=1)  # Объект ИИ для определения ладони
draw = mp.solutions.drawing_utils  # Для рисования ладони

while True:
    # Закрытие окна
    if cv2.waitKey(1) & 0xFF == 27:
        break

    if cv2.waitKey(1) & 0xFF == ord('r'):
        calibrate_flag = 1

    success, image = cap.read()  # Считываем изображение с камеры
    # image = cv2.flip(image)  # Отражаем изображение для корректной картинки
    imageRGB = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)  # Конвертируем в rgb
    results = hands.process(imageRGB)  # Работа mediapipe

    if results.multi_hand_landmarks:
        for handLms in results.multi_hand_landmarks:
            x, y, z = [], [], []
            for id, lm in enumerate(handLms.landmark):
                h, w, c = image.shape
                cx, cy = int(lm.x * w), int(lm.y * h)
                x.append(lm.x * w)
                y.append(lm.y * h)
                z.append(lm.z * w)

            if len(x) == 21:
                median_filter(find_lengths(x, y, z), last_lengths)
                median_filter(find_coords(x, y, z), last_coords)
                if calibrate_flag != 3:
                    calibrate(x, y, z)
                else:
                    write_instruction(median_filter(find_lengths(x, y, z), last_lengths),
                                      find_coords(x, y, z))
            else:
                cv2.putText(image, 'Show hand', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0))

            draw.draw_landmarks(image, handLms, mp.solutions.hands.HAND_CONNECTIONS)  # Рисуем ладонь
    else:
        cv2.putText(image, 'Show hand', (50, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0))

    cv2.imshow("Hand", image)  # Отображаем картинку
