'''
The file allows for selection of frames for annotation based on projection of the markers on the image.
The projections are VICON markers transferred to image space from 3D space.
Using the rotation and translation data provided by the tracker software.
The image projection indicate accuracy of the marker tracking.
'''

import cv2 as cv
from VICONSystem import systemInit as system
from VICONFileOperations import settingsGenerator
import os
from VICONFileOperations import rwOperations

# Debug Function to print the calibration Information
def printCalibInformation(camInstances):
    for cam in camInstances:
        camera = cam.getCameraParam()
        print("intrinsicParam : " , camera["intrinsicParam"])
        print("extrinsicRotation : ", camera["extrinsicRotation"])
        print("extrinsicTranslation : ",camera["extrinsicTranslation"])
        print("distortionParam : ", camera["distortionParam"])
        print("Cam ID", camera["serialNo"])
        print("Camera Type", camera["cameraType"])

def getFeaturesInViconSpace(viconObjects,transformationParamDict):
    featureDictViconSpace = {}
    # Loop through objects, if tracked then transfer those feature from object space to vicon space
    for j in range(len(viconObjects)):
        objName = viconObjects[j].__getattribute__("name")
        if transformationParamDict[objName + "_validity"] == True:
            viconObjects[j].setTransformationParameters(transformationParamDict[objName + "_rotation"],
                                                        transformationParamDict[objName + "_translation"])
            featureDictViconSpace.update(viconObjects[j].transferFeaturesToViconSpace())

    return featureDictViconSpace

def getFeaturesInCameraSpace(viconCamObjects,featureDictViconSpace):
    for j in range(len(viconCamObjects)):  # Loop through camera objects and find image projections
        viconCamObjects[j].clearFeatures()
        # Dictionary operations
        featureDictCamSpace = viconCamObjects[j].transferFeaturesToObjectSpace(featureDictViconSpace)
        viconCamObjects[j].setFeatures(featureDictCamSpace)
        print("CameraFeatures : ", featureDictCamSpace)
    return True

def getFeaturesInImageSpace(imageObjects,viconCamObjects):
    for j in range(len(viconCamObjects)):  # Loop through camera objects and find image projections
        imageObjects[j].clearFeatures()
        imageFeaturesDict = imageObjects[j].projectFeaturesFromCamSpaceToImageSpace(viconCamObjects[j].featureDict)
        imageObjects[j].setFeatures(imageFeaturesDict)
        print("ImageFeatures : ", imageFeaturesDict)

def videoWriter(windowNames, FPS = 30, imageWidth = 1920, imageHeight = 1080):
    videoOut = []
    for i in range(len(windowNames)):
        name = windowNames[i] + "output.mp4"
        videoOut.append(cv.VideoWriter(name, 0x00000020, FPS, (imageWidth, imageHeight), True))  # 400,400
    return videoOut

def releaseVideos(videoOut):
    """
    Release the holder for video if video output is stored
    :param videoOut: videoOutput Objects
    :return: bool
    """
    for video in videoOut:
        video.release()

    return True

def makeEntryToFile(fileName, frameNo):
    assert (os.path.exists(fileName)), "File does no exist"
    file = open(fileName, 'a')
    file.write(str(frameNo))
    file.write("\n")
    file.close()


def main(settingsFile, writeVideo = False):
    projectSettings = settingsGenerator.xmlSettingsParser(settingsFile)
    directoryName = projectSettings.settingsDict["rootDirectory"]

    # Part 1 : Get system information
    """
    First part of software gets information about the current session, associated .csv files produced by vicon
    and calibration information for video cameras,
    """
    viconSystemData = system.VICONSystemInit(projectSettings,directoryName)
    viconSystemData.printSysteInfo()

    # Part 2 : Read data frame and create vicon objects
    dataObject = viconSystemData.dataObject # fileOp.TrackerDatabaseReader(viconSystemData.dataFileName, objectsToTrack)  # Read the csv file
    c3dDataObject = viconSystemData.c3dDataObject
    viconObjects = viconSystemData.viconObjects

    videoObjects = viconSystemData.viconVideoObjects
    viconCamObjects = viconSystemData.viconCameraObjets
    imageObjects = viconSystemData.viconImageObjects


    #setting up 3D File
    c3dDataObject.printMetaData()
    subjects = projectSettings.settingsDict["objectsToTrack"]
    subjects = ["backpack","head"] # todo : Important to know which names exist in the c3d data
    subjectToLableMapping = c3dDataObject.findLableMapping(subjectNames=subjects)

    # Define window names
    windowNames = []
    maxFrameNo = []
    for video in videoObjects:
        windowNames.append(video.windowName)
        cv.namedWindow(video.windowName, cv.WINDOW_NORMAL)
        maxFrameNo.append(video.totalFrameCount)

    # Check if all videos have same number of frames and reassigns the variable to one single value
    if maxFrameNo.count(maxFrameNo[0]) == len(maxFrameNo):
        maxFrameNo = maxFrameNo[0]

    # Video writing
    if writeVideo:
        videoOut = videoWriter(windowNames, FPS=30)

    fileToAnnotate = os.path.join(directoryName, projectSettings.settingsDict["framesToCaptureFile"])
    if os.path.exists(fileToAnnotate):
        file = open(fileToAnnotate, 'a')
        file.close()
    else:
        # If the file does not exist then it is created
        file = open(fileToAnnotate, 'w')
        file.close()

    frameNo = 0
    stepSize = 100

    # Part 3 : Process frame information ( Frame by Frame or All together)
    while 0 <= frameNo <= maxFrameNo:

        # Get all rotation and translation
        transformationParamDict = dataObject.getDataForVideoFrame(frameNo)

        markerPositions = c3dDataObject.getFrameData(frameNo, subjectToLableMapping)
        print("Positions:", markerPositions)

        featureDictViconSpace = getFeaturesInViconSpace(viconObjects,transformationParamDict)

        if len(featureDictViconSpace) == 0:
            print("No tracking data skip Projection for frame : ", frameNo)
            frameNo =+ stepSize
            continue

        getFeaturesInCameraSpace(viconCamObjects,featureDictViconSpace)
        getFeaturesInImageSpace(imageObjects,viconCamObjects)

        # Get image frame and draw the information on image space
        for j in range(len(videoObjects)):
            tempImage = videoObjects[j].getFrame(frameNo)
            font = cv.FONT_HERSHEY_SIMPLEX
            cv.putText(tempImage, "frameCount : " + str(frameNo) + "/" + str(maxFrameNo), (10, 50), font, 1,
                       (255, 255, 255), 2, cv.LINE_AA)
            cv.putText(tempImage, "Step Size : " + str(stepSize), (10, 150), font, 1,
                       (255, 255, 255), 2, cv.LINE_AA)
            if tempImage is not None:
                imageObjects[j].drawFeatures(tempImage)
                cv.imshow(windowNames[j], tempImage)

        k = cv.waitKey(10)
        if k == ord('q'):
            cv.destroyAllWindows()
            if writeVideo:
                releaseVideos(videoOut)
            # Exit the program
            break

        if k == ord('+'):
            stepSize += 100

        if k == ord('-'):
            stepSize -= 50

        if k == ord('n'):
            frameNo += stepSize
            continue

        if k == ord('b'):
            frameNo -= stepSize

        if k == ord('s'):
            makeEntryToFile(fileToAnnotate, frameNo)  # ,captureStatus)

        if k == ord('h'):
            print("+ : increase step size by 100 \n")
            print("- : increase step size by 50 \n ")
            print("n : Next frame \n ")
            print("b : previous frame \n ")
            print("S : Enter frame status in log file \n ")

        print("Program terminated frame No/totalFrame : ", frameNo, "/", maxFrameNo)


if __name__ == '__main__':
    # In this section we pass the arguments required for the main function to perform any operation.
    # Mostly it is the system information for calibration and the location of the VICON file

    settingsFile = "D:\\BirdTrackingProject\\20190618_PigeonPostureDataset\\settings_session02.xml"

    main(settingsFile)
