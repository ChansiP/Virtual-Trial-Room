from tkinter import *
from PIL import Image
from PIL import ImageTk
import cv2, threading, os, time
from threading import Thread
from os import listdir
from os.path import isfile, join

import dlib
from imutils import face_utils, rotate_bound
import math


def put_sprite(num):
    global SPRITES, BTNS
    SPRITES[num] = (1 - SPRITES[num])

# Draws sprite over a image
# It uses the alpha chanel to see which pixels need to be reeplaced
# Input: image, sprite: numpy arrays
# output: resulting merged image
def draw_sprite(frame, sprite, x_offset, y_offset):
    (h,w) = (sprite.shape[0], sprite.shape[1])
    (imgH,imgW) = (frame.shape[0], frame.shape[1])

    if y_offset+h >= imgH:     #if sprite gets out of image in the bottom
        sprite = sprite[0:imgH-y_offset,:,:]

    if x_offset+w >= imgW:  #if sprite gets out of image to the right
        sprite = sprite[:,0:imgW-x_offset,:]

    if x_offset < 0:   #if sprite gets out of image to the left
        sprite = sprite[:,abs(x_offset)::,:]
        w = sprite.shape[1]
        x_offset = 0

#for each RGB chanel
    for c in range(3):
        #chanel 4 is alpha: 255 is not transpartne, 0 is transparent background
            frame[y_offset:y_offset+h, x_offset:x_offset+w, c] =  \
            sprite[:,:,c] * (sprite[:,:,3]/255.0) +  frame[y_offset:y_offset+h, x_offset:x_offset+w, c] * (1.0 - sprite[:,:,3]/255.0)
    return frame

#Adjust the given sprite to the head's width and position
#in case of the sprite not fitting the screen in the top, the sprite should be trimed

def adjust_sprite2head(sprite, head_width, head_ypos, ontop = True):
    (h_sprite,w_sprite) = (sprite.shape[0], sprite.shape[1])
    factor = 1.0*head_width/w_sprite
    sprite = cv2.resize(sprite, (0,0), fx=factor, fy=factor)   # adjust to have the same width as head
    (h_sprite,w_sprite) = (sprite.shape[0], sprite.shape[1])

    y_orig =  head_ypos-h_sprite if ontop else head_ypos
    if (y_orig < 0):
            sprite = sprite[abs(y_orig)::,:,:]
            y_orig = 0
    return (sprite, y_orig)


def apply_sprite(image, path2sprite,w,x,y, angle, ontop = True):
    sprite = cv2.imread(path2sprite,-1)
    sprite = rotate_bound(sprite, angle)
    (sprite, y_final) = adjust_sprite2head(sprite, w, y, ontop)
    image = draw_sprite(image,sprite,x, y_final)

def calculate_inclination(point1, point2):
    x1,x2,y1,y2 = point1[0], point2[0], point1[1], point2[1]
    incl = 180/math.pi*math.atan((float(y2-y1))/(x2-x1))
    return incl


def calculate_boundbox(list_coordinates):
    x = min(list_coordinates[:,0])
    y = min(list_coordinates[:,1])
    w = max(list_coordinates[:,0]) - x
    h = max(list_coordinates[:,1]) - y
    return (x,y,w,h)

def detectUpperBody(image):
    cascadePath = "/home/admin1/Documents/Flipkart_Hackathon/BodyDetection/haarcascades_cuda/haarcascade_upperbody.xml"
    result = image.copy()
    imageGray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    cascade = cv2.CascadeClassifier(cascadePath)
    Rect = cascade.detectMultiScale(imageGray, scaleFactor=1.1, minNeighbors=1, minSize=(1,1))
    if len(Rect) <= 0:
	    return False
    else:
	    return Rect

def get_face_boundbox(points, face_part):
    if face_part == 1:
        (x,y,w,h) = calculate_boundbox(points[17:22])
    elif face_part == 2:
        (x,y,w,h) = calculate_boundbox(points[22:27])
    elif face_part == 3:
        (x,y,w,h) = calculate_boundbox(points[36:42])
    elif face_part == 4:
        (x,y,w,h) = calculate_boundbox(points[42:48])
    elif face_part == 5:
        (x,y,w,h) = calculate_boundbox(points[29:36])
    elif face_part == 6:
        (x,y,w,h) = calculate_boundbox(points[0:17])
    elif face_part == 7:

        (x,y,w,h) = calculate_boundbox(points[1:5])
    elif face_part == 8:
        (x,y,w,h) = calculate_boundbox(points[12:16])
    return (x,y,w,h)

image_path = ''

def add_sprite(img):
    global image_path
    image_path = img

    put_sprite(int(img.rsplit('/',1)[0][-1]))


def cvloop(run_event):
    global panelA
    global SPRITES
    global image_path
    i = 0
    video_capture = cv2.VideoCapture(0)
    (x,y,w,h) = (0,0,10,10)

    
    detector = dlib.get_frontal_face_detector()

    model = "data/shape_predictor_68_face_landmarks.dat"
    predictor = dlib.shape_predictor(model)

    while run_event.is_set():
        ret, image = video_capture.read()
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        faces = detector(gray, 0)

        for face in faces:
            (x,y,w,h) = (face.left(), face.top(), face.width(), face.height())

            shape = predictor(gray, face)
            shape = face_utils.shape_to_np(shape)
            incl = calculate_inclination(shape[17], shape[26])


            is_mouth_open = (shape[66][1] -shape[62][1]) >= 10

            if SPRITES[0]:

                apply_sprite(image,image_path,w,x,y+40, incl, ontop = True)


            if SPRITES[1]:
                (x1,y1,w1,h1) = get_face_boundbox(shape, 6)
                apply_sprite(image,image_path,w1,x1,y1+275, incl)


            if SPRITES[3]:
                (x3,y3,_,h3) = get_face_boundbox(shape, 1)
                apply_sprite(image,image_path,w,x,y3, incl, ontop = False)


            (x0,y0,w0,h0) = get_face_boundbox(shape, 6)

            if SPRITES[4]:
                (x3,y3,w3,h3) = get_face_boundbox(shape, 7)
                apply_sprite(image, image_path,w3,x3-20,y3+25, incl)
                (x3,y3,w3,h3) = get_face_boundbox(shape, 8)
                apply_sprite(image, image_path,w3,x3+20,y3+25, incl)

            if SPRITES[5]:
                findRects = []
                upperPath = "/home/admin1/Documents/Flipkart_Hackathon/BodyDetection/haarcascades_cuda/haarcascade_upperbody.xml"
                imageGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                upperCascade = cv2.CascadeClassifier(upperPath)
                upperRect = upperCascade.detectMultiScale(imageGray, scaleFactor=1.1, minNeighbors=1, minSize=(1,1))

                if len(upperRect) > 0:
                    findRects.append(upperRect[0])
                    print(findRects)

                for obj in findRects:
                    print(obj)

                    draw_sprite(image,obj[0],obj[1])

         # OpenCV represents image as BGR; PIL but RGB, we need to change the chanel order

        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
         # conerts to PIL format
        image = Image.fromarray(image)
        # Converts to a TK format to visualize it in the GUI
        image = ImageTk.PhotoImage(image)
        # Actualize the image in the panel to show it
        panelA.configure(image=image)
        panelA.image = image

    video_capture.release()

# Initialize GUI object
root = Tk()
root.title("E-Dressing- Face")
this_dir = os.path.dirname(os.path.realpath(__file__))
btn1 = None

def try_on(image_path):
    btn1 = Button(root, text="Try it ON", command = lambda:add_sprite(image_path))
    btn1.pack(side="top", fill="both", expand="no", padx="5", pady="5")
# Create the panel where webcam image will be shown
panelA = Label(root)
panelA.pack( padx=10, pady=10)

# Variable to control which sprite you want to visualize
SPRITES = [0,0,0,0,0,0]
BTNS = [btn1]

try_on(sys.argv[1])
run_event = threading.Event()
run_event.set()
action = Thread(target=cvloop, args=(run_event,))
action.setDaemon(True)
action.start()

# Function to close all properly, aka threads and GUI
def terminate():
        global root, run_event, action
        run_event.clear()
        time.sleep(1)
        root.destroy()

# When the GUI is closed it actives the terminate function
root.protocol("WM_DELETE_WINDOW", terminate)
root.mainloop()
