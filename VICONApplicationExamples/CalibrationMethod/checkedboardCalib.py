import numpy as np
import cv2
import glob
import os


def saveCalib(file, data):
    fs = cv2.FileStorage(file, cv2.FILE_STORAGE_WRITE)
    fs.write("mtx", data["mtx"])
    fs.write("dist", data["dist"])
    fs.write("newcameramtx", data["newcameramtx"])
    fs.write("roi", data["roi"])
    fs.release()

def readCalib(name):
    fn = cv2.FileStorage(name, cv2.FILE_STORAGE_READ)
    mtx = fn.getNode("mtx")
    mtxMat = mtx.mat()
    dist = fn.getNode("dist")
    distMat = dist.mat()
    newcameramtx = fn.getNode("newcameramtx")
    newcameramtxMat = newcameramtx.mat()
    roi = fn.getNode("roi")
    roi = roi.mat()
    data = {"mtx": mtxMat, "dist": distMat, "newcameramtx": newcameramtxMat, "roi":roi}
    return data

# termination criteria
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
objp = np.zeros((7*9,3), np.float32)
objp[:,:2] = np.mgrid[0:9,0:7].T.reshape(-1,2)

# Arrays to store object points and image points from all the images.
objpoints = [] # 3d point in real world space
imgpoints = [] # 2d points in image plane.

video = "D:\\BirdTrackingProject\\Calibration\\20192203_videoCalibHemal02.2122725.20190322105141.avi"
#video = "D:\\BirdTrackingProject\\Calibration\\20192203_videoCalibHemal02.2122725.20190322105706.avi"
#20192203_videoCalibHemal04.2122725.20190322164813
calibResult = "D:\\BirdTrackingProject\\VICON_DataRead\\VICONApplicationExamples\\calibResult\\"
cap = cv2.VideoCapture(video)
calibFile = "D:\\BirdTrackingProject\\VICON_DataRead\\VICONApplicationExamples\\calibResult\\calib.xml"
mtx = 0
dist = 0
newcameramtx = 0
roi = 0
calibrated = False
cv2.namedWindow("testWindow",cv2.WINDOW_NORMAL)
while True:

    frameNo = cap.get(cv2.CAP_PROP_POS_FRAMES)
    print("Next frame no : ", frameNo)
    retImg, img = cap.read()
    if retImg is False:
        print('Board not found')
        break

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    # Find the chess board corners
    ret, corners = cv2.findChessboardCorners(gray, (9,7),None)

    if ret == False:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frameNo + 10)
        print("grabbing next frame")
        continue

    corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
    img = cv2.drawChessboardCorners(img, (9, 7), corners2, ret)
    cv2.imshow('testWindow',img)


    k = cv2.waitKey(0)
    if k == ord('n'):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frameNo+30)
        continue

    if k == ord('s'):
        cap.set(cv2.CAP_PROP_POS_FRAMES, frameNo + 10)
        objpoints.append(objp)
        imgpoints.append(corners2)

    if k == ord ('q'):
        cv2.destroyAllWindows()
        break

    if k == ord('c'):
        print('Calibrating')
        ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(objpoints, imgpoints, gray.shape[::-1], None, None)
        h, w = img.shape[:2]
        newcameramtx, roi = cv2.getOptimalNewCameraMatrix(mtx, dist, (w, h), 1, (w, h))
        calibrated = True
        data = {"mtx" : mtx , "dist" : dist, "newcameramtx":newcameramtx, "roi":roi}
        saveCalib(calibFile,data)

    if k == ord('u'):
        # undistort
        if(os.path.exists(calibFile)) :
            print("Using Data From File")
            calibData = readCalib(calibFile)
            mtx = calibData["mtx"]
            dist = calibData["dist"]
            newcameramtx = calibData["newcameramtx"]
            roi = calibData["roi"]

        dst = cv2.undistort(img, mtx, dist, None, newcameramtx)
        # crop the image
        #todo : Change this to see more image
        print(" Shape ", roi.shape)
        x, y, w, h = roi.tolist()
        x = int(x[0])
        y = int(y[0])
        w = int(w[0])
        h = int(h[0])
        dst = dst[y:y + h, x:x + w]
        cv2.imwrite(calibResult + 'calibresult_classic' + str(frameNo) + '.png', dst)

    if k == ord('m') :
        h, w = img.shape[:2]
        mapx, mapy = cv2.initUndistortRectifyMap(mtx, dist, None, newcameramtx, (w, h), 5)
        dst = cv2.remap(img, mapx, mapy, cv2.INTER_LINEAR)
        # crop the image
        x, y, w, h = roi
        dst = dst[y:y + h, x:x + w]
        cv2.imwrite(calibResult + 'calibresult_mapping' + str(frameNo) + '.png', dst)




