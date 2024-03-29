# The file contains list of functions which will draw the content on the given image file
import cv2 as cv
from VICONDrawingOperations import generatePointsOp as pointGen


def getColor( keyPoint):
    if "beak" in keyPoint :
        return (255, 0, 0)
    elif "nose" in keyPoint :
        return (0, 255, 0)
    elif "eyes" in keyPoint :
        return (0, 0, 255)
    elif "leftShoulder" in keyPoint :
        return (255, 255, 0)
    elif "rightShoulder" in keyPoint :
        return (255, 0, 255)
    elif "tail" in keyPoint :
        return (0, 255, 255)
    elif "1" in keyPoint:
        return (150,0,0)
    elif "2" in keyPoint:
        return (150,150,255)
    elif "3" in keyPoint:
        return (0,150,0)
    elif "4" in keyPoint:
        return (0,0,150)
    else:
        return (255,200,200)

def drawCoordinateAxis(undistortedImage, axisPointsImgSpace):
    """
    Draws coordinate system in the image based on the given points. Format : Origin, XAxis, YAxis, ZAxis
    """
    # Color FOrmat is BGR
    # Red - X Axis
    cv.line(undistortedImage, (int(axisPointsImgSpace[0][0]), int(axisPointsImgSpace[0][1])),
            (int(axisPointsImgSpace[1][0]), int(axisPointsImgSpace[1][1])), (0, 0, 255), 3)
    # Green - Y Axis
    cv.line(undistortedImage, (int(axisPointsImgSpace[0][0]), int(axisPointsImgSpace[0][1])),
            (int(axisPointsImgSpace[2][0]), int(axisPointsImgSpace[2][1])), (0, 255, 0), 3)
    # Blue - Z Axis
    cv.line(undistortedImage, (int(axisPointsImgSpace[0][0]), int(axisPointsImgSpace[0][1])),
            (int(axisPointsImgSpace[3][0]), int(axisPointsImgSpace[3][0])), (255, 0, 0), 3)

def drawPoint(undistortedImage, point, size = 5, color = (255,255,0) ):
    """
    Draws point on the given image
    :param undistortedImage: Image Matrix
    :param point: point to draw
    :param size: int
    """
    cv.circle(undistortedImage,(int(point[0]),int(point[1])),
                   size , color,-1)

def drawMarkerPoints (undistortedImage, markerProjections, size = 5):
    """
    Projects markers on the image, markers belong to single pattern
    """
    for i in range(len(markerProjections)):
        cv.circle(undistortedImage,(int(markerProjections[i][0]),int(markerProjections[i][1]) ),
                   size , (0,255,0),-1)


def drawBoundingBox(undistortedImage, bBoxPoints):
    # Line 1-4, 1-2, 1-5
    cv.line(undistortedImage, (int(bBoxPoints[0][0]), int(bBoxPoints[0][1])),
            (int(bBoxPoints[3][0]), int(bBoxPoints[3][1])), (0, 255, 0), 1)
    cv.line(undistortedImage, (int(bBoxPoints[0][0]), int(bBoxPoints[0][1])),
            (int(bBoxPoints[1][0]), int(bBoxPoints[1][1])), (0, 255, 0), 1)
    cv.line(undistortedImage, (int(bBoxPoints[0][0]), int(bBoxPoints[0][1])),
            (int(bBoxPoints[4][0]), int(bBoxPoints[4][1])), (0, 255, 0), 1)

    # Line 3-2, 3-7, 3-4
    cv.line(undistortedImage, (int(bBoxPoints[2][0]), int(bBoxPoints[2][1])),
            (int(bBoxPoints[1][0]), int(bBoxPoints[1][1])), (0, 255, 0), 1)
    cv.line(undistortedImage, (int(bBoxPoints[2][0]), int(bBoxPoints[2][1])),
            (int(bBoxPoints[6][0]), int(bBoxPoints[6][1])), (0, 255, 0), 1)
    cv.line(undistortedImage, (int(bBoxPoints[2][0]), int(bBoxPoints[2][1])),
            (int(bBoxPoints[3][0]), int(bBoxPoints[3][1])), (0, 255, 0), 1)

    # Line 6-2, 6-7, 6-5
    cv.line(undistortedImage, (int(bBoxPoints[5][0]), int(bBoxPoints[5][1])),
            (int(bBoxPoints[1][0]), int(bBoxPoints[1][1])), (0, 255, 0), 1)
    cv.line(undistortedImage, (int(bBoxPoints[5][0]), int(bBoxPoints[5][1])),
            (int(bBoxPoints[6][0]), int(bBoxPoints[6][1])), (0, 255, 0), 1)
    cv.line(undistortedImage, (int(bBoxPoints[5][0]), int(bBoxPoints[5][1])),
            (int(bBoxPoints[4][0]), int(bBoxPoints[4][1])), (0, 255, 0), 1)

    # Line 8-5, 8-7, 8-4
    cv.line(undistortedImage, (int(bBoxPoints[7][0]), int(bBoxPoints[7][1])),
            (int(bBoxPoints[4][0]), int(bBoxPoints[4][1])), (0, 255, 0), 1)
    cv.line(undistortedImage, (int(bBoxPoints[7][0]), int(bBoxPoints[7][1])),
            (int(bBoxPoints[6][0]), int(bBoxPoints[6][1])), (0, 255, 0), 1)
    cv.line(undistortedImage, (int(bBoxPoints[7][0]), int(bBoxPoints[7][1])),
            (int(bBoxPoints[3][0]), int(bBoxPoints[3][1])), (0, 255, 0), 1)

def main():
    print("Hello this is main function, its just drawing things man")
    markerPoints = pointGen.getMarkerPoints("9mm_02.mp")
    bboxPoints = pointGen.getBoundingBox([0,0,0])
    coordinateAxis = pointGen.getCoordinatePoints(100)
    point = [ 200 , 200 ]

    img = cv.imread("C:\\Users\\hnaik\\Desktop\\bird_rainbow.jpg")
    cv.namedWindow("testWindow", cv.WINDOW_AUTOSIZE)

    while(True):
        cv.imshow("testWindow", img)
        drawBoundingBox(img,bboxPoints)
        drawCoordinateAxis(img,coordinateAxis)
        drawMarkerPoints(img,markerPoints)
        drawPoint(img,point)
        k = cv.waitKey(10)
        if k == ord("q"):
            break

if __name__ == '__main__':
    main()