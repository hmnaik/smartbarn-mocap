"""
The code in this file allows us to stream the camera footage from the phone connected to the same WLAN network with the computer.
"""


import urllib3
import cv2
import numpy as np
import ssl


def readUsingSSL():
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    url = 'http://192.168.2.101:8080/shot.jpg'

    while True:
        http = urllib3.PoolManager()
        r = http.request('GET', url)
        imgNp = np.array(bytearray(r.data), dtype=np.uint8)
        img = cv2.imdecode(imgNp, -1)
        cv2.imshow('temp',cv2.resize(img,(600,400)))
        q = cv2.waitKey(1)
        if q == ord("q"):
            break

    cv2.destroyAllWindows()

### Code 2: This works flawless
def readUsingOpenCV():
    url = 'http://192.168.2.101:8080/video'
    cap = cv2.VideoCapture(url)
    while(True):
        ret, frame = cap.read()
        if frame is not None:
            cv2.imshow('frame',frame)
        q = cv2.waitKey(1)
        if q == ord("q"):
            break
    cv2.destroyAllWindows()


if __name__ == "__main__":
    readUsingOpenCV()

    readUsingSSL()