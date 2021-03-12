import cv2
import numpy as np

net = cv2.dnn.readNetFromCaffe("res10_300x300_ssd_iter_140000.prototxt", "res10_300x300_ssd_iter_140000.caffemodel")

def find_faces(img, net, confidence=0.7):
    (h, w) = img.shape[:2]
    mean = np.mean(img,axis=(0,1))
    #resized_img = cv2.resize(img, (300, 300))
    blob = cv2.dnn.blobFromImage(img, 1.0,
        (300, 300), mean)

    faces = []

    net.setInput(blob)
    detections = net.forward()
    for i in range(0, detections.shape[2]):
        # extract the confidence (i.e., probability) associated with the
        # prediction
        conf = detections[0, 0, i, 2]
        # filter out weak detections by ensuring the `confidence` is
        # greater than the minimum confidence
        if conf < confidence:
            continue
        # compute the (x, y)-coordinates of the bounding box for the
        # object
        box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
        (startX, startY, endX, endY) = box.astype("int")
        faces.append((conf, startX, startY, endX, endY))
    return faces

def draw_face_box(img, faces):
    for i in range(len(faces)):
        (conf, startX, startY, endX, endY) = faces[i]
        # draw the bounding box of the face along with the associated
        # probability
        text = f"{conf * 100:.2f}%"
        y = startY - 10 if startY - 10 > 10 else startY + 10
        cv2.rectangle(img, (startX, startY), (endX, endY),
            (0, 0, 255), 2)
        cv2.putText(img, text, (startX, y),
            cv2.FONT_HERSHEY_SIMPLEX, 0.45, (0, 0, 255), 2)
