# First prototype for the file to create annotation from the given image file and save them in respective feature

import cv2 as cv
import numpy as np
from VICONSystem import videoVicon as vid
from VICONFileOperations import rwOperations as rwOp
from VICONFileOperations import settingsGenerator
import pandas as pd
import os

def setPoint(point,x,y):
    point[0] = x
    point[1] = y

def unselected(event, x, y, flags, param ):
    if event == cv.EVENT_LBUTTONDOWN:
        print("No mode selected")

def boundingBox(event, x, y, flags, point ):
    if event == cv.EVENT_LBUTTONDOWN:
        point["x"] = x
        point["y"] = y
    if event == cv.EVENT_RBUTTONDOWN:
        point["width"] = x - point["x"]
        point["height"] = y - point["y"]


class imageAnnotationTool:

    def __init__(self, settingsDict):
        """
        Initialize the class for annotation of images
        :param videoFiles: Lise of video files
        :param path: path for reading features
        """
        videoFiles = settingsDict["videoFiles"]
        rootDir = settingsDict["rootDirectory"]
        # Iterate through path anf provide global path
        for file in range(len(videoFiles)):
            videoFiles[file] = os.path.join(rootDir, videoFiles[file])

        print("Init class for image annotation")
        self.videoFiles = videoFiles
        self.stepSize = int(settingsDict["stepSize"])
        self.startFrame = int(settingsDict["startFrame"])
        self.endFrame = int(settingsDict["endFrame"])
        self.frameInfoFile = os.path.join(rootDir, settingsDict["framesToCaptureFile"])
        self.image = []
        self.features = rwOp.readFeaturesFromFile(os.path.join(rootDir,settingsDict["customFeatureFile"]))
        self.dataPoints, self.dataBaseKeyPoints = self.createDatabase()
        self.point = [0,0]
        self.toggleAnnotationView = True

        # test
        self.frameToAnnotate = self.loadFrameInfo()
        self.createAnnotationDict()

    def createAnnotationDict(self):
        self.annotationDict = {0:"unselected"}
        for id in range(1,len(self.features)+1):
            self.annotationDict[id] = self.features[id-1]

    def pointAssignment(self, event, x, y, flags, point):
        if event == cv.EVENT_LBUTTONDOWN:
            setPoint(point, x, y)
        elif event == cv.EVENT_RBUTTONDOWN:
            setPoint(point, 0, 0)

    def loadFrameInfo(self):
        """
        Loads the information about frames to use for a file
        """
        # assert (os.path.exists(self.frameInfoFile) == True), "File does not exist"
        framesToAnnotate = []
        if not os.path.exists(self.frameInfoFile):
            print("File does not exist.")
            return framesToAnnotate

        # Open file and read annotation frames
        file = open(self.frameInfoFile)
        lines = [line.rstrip('\n') for line in file]
        # Read point information from the file
        for line in lines:
            if line.isdigit():
                framesToAnnotate.append(line)

        return framesToAnnotate

    def createDatabase(self):
        """
        Create data base related structure
        :return:
        """
        defaultDataSeries = {"frame":0}
        for feature in self.features:
            defaultDataSeries[str(feature)+"_x"] = 0
            defaultDataSeries[str(feature)+"_y"] = 0

        dataFrame = pd.DataFrame(columns = list(defaultDataSeries))


        return defaultDataSeries,dataFrame

    def readFeaturePointsFromFile(self, path):
        """
        Loads features from the given file path
        :param : Path to text file with all required featues
        :return: return list of features
        """
        features = []
        assert (os.path.exists(path) == True), "File for custom features does not exist"
        if os.path.exists(path):
            file = open(path)
            lines = [line.rstrip('\n') for line in file]
            # Read point information from the file
            for line in lines:
                features.append(str(line))

        return features


    def getkeypointInfo(self, str):
        if (str is not "unselected"):
            x = self.dataPoints[str+"_x"]
            y = self.dataPoints[str+"_y"]
            return x,y

    def setKeypointInfo(self, str, point):
        if (str is not "unselected"):
            self.dataPoints[str + "_x"] = point[0]
            self.dataPoints[str + "_y"] = point[1]
            return True
        else:
            return False

    def getColor(self, keyPoint):
        if keyPoint == self.features[0]:
            return (255, 0 , 0 )
        elif keyPoint == self.features[1]:
            return (0,255,0)
        elif keyPoint == self.features[2]:
            return (0,0,255)
        elif keyPoint == self.features[3]:
            return (255,255,0)
        elif keyPoint == self.features[4]:
            return (255, 0 , 255)
        elif keyPoint == self.features[5]:
            return (0, 255, 255)
        elif keyPoint == self.features[6]:
            return (255, 150, 255)
        else:
            return (125, 125, 125)

    def drawKeypoints(self, image, mode, frameNo):
        # Draw all the key points if the annotation view is True
        if self.toggleAnnotationView:
            for featureName in self.features:
                keyPoint = self.getkeypointInfo(featureName)
                color = self.getColor(featureName)
                if keyPoint != [0, 0] :
                    cv.circle(image, keyPoint, 10, color, 2)
                    cv.line(image, (keyPoint[0] - 10, keyPoint[1]),(keyPoint[0]+10,keyPoint[1]),color , 1)
                    cv.line(image, (keyPoint[0], keyPoint[1] - 10), (keyPoint[0] , keyPoint[1]+ 10), color, 1)
        else: # Draw only require feature point if only current view is required
            keyPoint = self.getkeypointInfo(mode)
            color = (255,255,255)
            if keyPoint != [0,0] and mode != "unselected":
                cv.circle(image, keyPoint, 10, color, 2)
                cv.line(image, (keyPoint[0] - 10, keyPoint[1]), (keyPoint[0] + 10, keyPoint[1]), color, 1)
                cv.line(image, (keyPoint[0], keyPoint[1] - 10), (keyPoint[0], keyPoint[1] + 10), color, 1)

        font = cv.FONT_HERSHEY_SIMPLEX
        cv.putText(image, "Annotation Mode :" + mode , (500, 50), font, 1,
                    (255, 255, 255), 2, cv.LINE_AA)
        cv.putText(image, "Frame No :" + str(frameNo), (500, 100), font, 1,
                   (255, 255, 255), 2, cv.LINE_AA)


    def getRoi(self, height, width , size = 200):
        x = self.point[0]
        y = self.point[1]
        roi = [0 , 0, 200, 200]

        roi[0] = x - size
        if roi[0] < 0:
            roi[0] = 0

        roi[1] = x + size
        if roi[1] > width:
            roi[1] = width - 1

        roi[2] = y - size
        if roi[2]< 0:
            roi[2] = 0

        roi[3]= y + size
        if roi[3] > height:
            roi[3] = height -1

        return roi

    def printAnnotationInfo(self):
        print("Keybord Commands")
        print("w-s-a-d : Move one pixel in relative direction")
        print("h : help information")
        print("q : Quit")
        print("b : back")
        print("r : reset annotations")
        print("n : Next frame")
        for id in self.annotationDict:
            print(id , ":", self.annotationDict[id])

    def saveData(self, filePath): # Saving databaseto csv file
        self.dataBaseKeyPoints.to_csv(filePath, index = False)

    def updateDataBase(self, frameNo, csvFileName):
        self.dataPoints["frame"] = frameNo
        # if entry exists we just modify the existing entry
        list = self.dataBaseKeyPoints["frame"].tolist()
        if frameNo in self.dataBaseKeyPoints["frame"].tolist():
            index = self.dataBaseKeyPoints["frame"].tolist().index(frameNo)
            self.dataBaseKeyPoints.loc[index] = self.dataPoints
        else : # if entry does not exist we add a new
            self.dataBaseKeyPoints = self.dataBaseKeyPoints.append(self.dataPoints, ignore_index=True)

        self.saveData(csvFileName)

    def resetAnnotations(self):
        self.point = [0, 0]
        for feature in self.features:
            self.setKeypointInfo(feature, self.point)
        print("Erasing all points : ", self.dataPoints)

    def loadDatabaseFromcsv(self,filename):
        """
        Given file name load database from existing csv file
        :param filename: str (.csv)
        :return: None
        """
        self.dataBaseKeyPoints = pd.read_csv(filename, index_col= False)
        if self.dataBaseKeyPoints.empty:
            print("Database from loaded file is empty : ", filename)

    def loadFromDatabase(self, frameNo):
        self.dataPoints["frame"] = frameNo
        if frameNo in self.dataBaseKeyPoints["frame"].tolist():
            index = self.dataBaseKeyPoints["frame"].tolist().index(frameNo)
            dataSeries = self.dataBaseKeyPoints.loc[index]
            self.dataPoints = dataSeries.to_dict()
            print("Method 1", self.dataPoints)
        else:
            self.resetAnnotations()
        return

    def run(self):
        # Creating video objects
        videoObjects = []

        for i in range(len(self.videoFiles)):
            # destroy pre existing windows
            cv.destroyAllWindows()
            videoObjects.append(vid.VideoVicon(self.videoFiles[i], i))
            windowName = videoObjects[i].__getattribute__("windowName")
            csvFileName = os.path.join(os.path.dirname(self.videoFiles[i]), windowName + ".csv")

            if os.path.exists(csvFileName):
                self.loadDatabaseFromcsv(csvFileName)
                print("File already exists, loading database from file")
            else:
            # reset the database entries
               self.dataBaseKeyPoints = self.dataBaseKeyPoints.iloc[0:0]
            # Reset annotations before starting annotations, it is not carried from one video to another.
               self.resetAnnotations()

            mode = "unselected"
            cv.namedWindow(windowName, cv.WINDOW_NORMAL)
            cv.setMouseCallback(windowName, unselected , mode)
            # For bounding box view
            cv.namedWindow("bBoxWindow", cv.WINDOW_NORMAL)

            # Finding no of frames to run the algorithm
            frameCount = videoObjects[i].totalFrameCount
            frameNo = self.startFrame

            if self.startFrame == self.endFrame or self.startFrame > self.endFrame or self.endFrame == 0:
                print("Start and end frames given same therefore ")
                self.endFrame = frameCount

            assert (self.endFrame <= frameCount), "Video sequence has less frames than defined as end frame in settings"

            # Prepare the list of files to be annotated either from the annotation selector or create custom list based on
            # the start, end and steps information given in the settings file.
            if len(self.frameToAnnotate):
                print("Preparing frames for annotation based on the selected files through annotation selector tool.")
                listOfFrames = self.frameToAnnotate
                print(listOfFrames)
            else: # else check out frames with given start and end sequence
                print("Preparing frames for annotation using the settings file.")
                listOfFrames = list(range(self.startFrame, self.endFrame, self.stepSize))
                print(listOfFrames)

            # Load information about annotation if it exists in the .csv file
            id = 0
            self.loadFromDatabase(int(listOfFrames[id]))

            while 0 <= id < len(listOfFrames):

                frameNo = int(listOfFrames[id])
                image = videoObjects[i].getFrame(frameNo)
                clone = image.copy()

                # Update points
                self.setKeypointInfo(mode, self.point)
                # Draw points on the image
                self.drawKeypoints(clone, mode, frameNo)

                height, width, channel = clone.shape

                if (self.point[0] != 0 and self.point[1] != 0):
                    roi = self.getRoi(height, width, 100 )
                    roiWidth = roi[3] - roi[2] # x2 - x1
                    roiHeight = roi[1] - roi[0] # y2 - y1
                    roiImage = clone[roi[2]:roi[3] , roi[0]:roi[1], :]
                    resized = cv.resize(roiImage, (400,400), interpolation = cv.INTER_AREA)
                    clone[0:resized.shape[0], 0:resized.shape[1]] = resized
                    cv.imshow("bBoxWindow", np.array(resized))

                cv.imshow(windowName, clone)

                k = cv.waitKey(10)

                keys = [ord(str(x)) for x in list(self.annotationDict)]

                if k in keys:
                    index = keys.index(k)
                    print("Mode", self.annotationDict[index])
                    mode = self.annotationDict[index]
                    if mode != "unselected":
                        self.point = [self.getkeypointInfo(mode)[0], self.getkeypointInfo(mode)[1]]
                        cv.setMouseCallback(windowName, self.pointAssignment, self.point)
                    else:
                        cv.setMouseCallback(windowName, unselected, self.point)

                if k == ord('w'):
                    self.point[1] -= 1 # Subtract y coordinate

                if k == ord('a'):
                    self.point[0] -= 1  # Subtract x coordinate

                if k == ord('s'):
                    self.point[1] += 1  # add 1 unit y coordinate

                if k == ord('d'):
                    self.point[0] += 1  # add 1 unit x coordinate

                if k == ord('r'): # Erase annotations
                    self.resetAnnotations()

                if k == ord('h'): # Help print key info
                    self.printAnnotationInfo()

                if k == ord('i'): # Info
                    self.toggleAnnotationView = not self.toggleAnnotationView

                if k == ord('q'):  # Quit
                    #Save final data
                    self.updateDataBase(frameNo, csvFileName)
                    # Clear the data
                    self.dataBaseKeyPoints = self.dataBaseKeyPoints.iloc[0:0]
                    # destroy the existing video window
                    cv.destroyAllWindows()
                    break

                if k == ord('b'): # Go back
                    # make mode unselected
                    mode = "unselected"
                    if id != 0:
                        id -= 1
                        frameNo = int(listOfFrames[id])
                        self.loadFromDatabase(frameNo)
                    else:
                        print("Can not go back. Frame : ", frameNo, "\n Start Frame : ", self.startFrame )

                if k == ord('n'): # Next image
                    self.updateDataBase(frameNo,csvFileName)
                    id += 1
                    mode = "unselected"
                    if id < len(listOfFrames):
                        frameNo = int(listOfFrames[id])
                        self.loadFromDatabase(frameNo)
                    continue


if __name__ == "__main__":

    # Example will use this class to make small application of viewing the video files
    settingsObject = settingsGenerator.xmlSettingsParser("D:\\BirdTrackingProject\\20190618_PigeonPostureDataset\\settings_session02.xml")
    annotator = imageAnnotationTool(settingsObject.settingsDict)
    annotator.run()
