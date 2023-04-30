"""
Example code: Data visualization
The example shows the method to read data directly from the Nexus output (3D points in vicon space)
and project them directly on the image space.
"""

import cv2 as cv
import pandas as pd
from VICONSystem import systemInit as system
from VICONFileOperations import settingsGenerator
import os
from VICONFileOperations import rwOperations
from VICONMath import mathPointOperations as pointOp

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
        #print("CameraFeatures : ", featureDictCamSpace)
    return True

def getFeaturesInImageSpace(imageObjects,viconCamObjects):
    for j in range(len(viconCamObjects)):  # Loop through camera objects and find image projections
        imageObjects[j].clearFeatures()
        imageFeaturesDict = imageObjects[j].projectFeaturesFromCamSpaceToImageSpace(viconCamObjects[j].featureDict)
        imageObjects[j].setFeatures(imageFeaturesDict)
        #print("ImageFeatures : ", imageFeaturesDict)


def releaseVideos(videoOut):
    """
    Release the holder for video if video output is stored
    :param videoOut: videoOutput Objects
    :return: bool
    """
    for video in videoOut:
        video.release()

    return True

def createFeaturesForNexus(trackingObjects):
    list = []
    for object in trackingObjects:
        for i in range(0,4):
            list.append(object + str(i+1))

    return list

def updateDistDataFrame(frameNo, dict1, dict2, dataFrame):
    allObjectFeatures = dataFrame.columns
    allObjectFeatures["Frame"] = frameNo
    distanceDict = pointOp.pointDistance3D(dict1, dict2)
    allObjectFeatures.update(distanceDict)
    dataFrame.append(allObjectFeatures)

def main(settingsFile, writeVideo = False):

    projectSettings = settingsGenerator.xmlSettingsParser(settingsFile)
    directoryName = projectSettings.settingsDict["rootDirectory"]

    # Hacking the file path
    nexusDataset = os.path.join(directoryName, "nexus\\20190618_PigeonPostureDataset_session02_skeleton.csv")

    nexusFeatures = []
    if os.path.exists(nexusDataset):
        trackingObjects = projectSettings.settingsDict["objectsToTrack"]
        swapTrackingObjects = [trackingObjects[1],trackingObjects[0]]
        nexusFeatures = createFeaturesForNexus(swapTrackingObjects)

    # Part 1 : Get system information
    """
    First part of software gets information about the current session, associated .csv files produced by vicon
    and calibration information for video cameras,
    """
    viconSystemData = system.VICONSystemInit(projectSettings,directoryName)

    # Part 2 : Read data frame and create vicon objects
    dataObject = viconSystemData.dataObject # fileOp.TrackerDatabaseReader(viconSystemData.dataFileName, objectsToTrack)  # Read the csv file
    nexusDataObject = rwOperations.NexusDatabaseReader(nexusDataset,nexusFeatures)

    viconObjects = viconSystemData.viconObjects

    # Create video objects
    videoFiles = viconSystemData.sessionVideoFiles #  __getattribute__("sessionVideoFiles")
    #viconSystemData.loadCustomTrackingFeaturesToTrackingObjects()
    videoObjects = viconSystemData.viconVideoObjects
    viconCamObjects = viconSystemData.viconCameraObjets
    imageObjects = viconSystemData.viconImageObjects

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

    dataBaseObjects = []
    featureFile = os.path.join(directoryName, projectSettings.settingsDict["customFeatureFile"])
    featureList = rwOperations.readFeaturesFromFile(featureFile)
    dataBaseFiles = projectSettings.settingsDict["annotationDataBaseFiles"]
    for dataBaseFile in dataBaseFiles:
        path = os.path.join(directoryName, dataBaseFile)
        dataBaseObjects.append( rwOperations.annotationDatabase(path, featureList, resetPreviousAnnotations= True) )

    allObjectFeatures = {"Frame": 0}
    for object in viconObjects:
        objectFeatures = object.featureDict
        allObjectFeatures.update(objectFeatures)

    testDataFrame = pd.DataFrame(columns= list(allObjectFeatures))

    pause = False
    # Part 3 : Process frame information ( Frame by Frame or All together)
    startValue = 150
    for i in range(startValue,maxFrameNo,2):

        print("Processing data for Frame No : ", i)
        prevFeatureDictViconSpaceNexus = {}
        if i != startValue :
            prevFeatureDictViconSpaceNexus = featureDictViconSpaceNexus.copy()

        featureDictViconSpaceNexus = nexusDataObject.getDataForVideoFrame(i)
        print("Feature Nexus ", featureDictViconSpaceNexus)
        # Get all rotation and translation
        transformationParamDict = dataObject.getDataForVideoFrame(i)
        featureDictViconSpace = getFeaturesInViconSpace(viconObjects,transformationParamDict)
        print("Feature  : ", featureDictViconSpace)


        # Add frame number
        if i != startValue:
        #updateDistDataFrame(i,prevFeatureDictViconSpaceNexus,featureDictViconSpaceNexus, testDataFrame)
            allObjectFeatures["Frame"] = i
            distanceDict = pointOp.pointDistance3D(prevFeatureDictViconSpaceNexus, featureDictViconSpaceNexus)
            allObjectFeatures.update(distanceDict)
            testDataFrame = testDataFrame.append(allObjectFeatures, ignore_index = True)


        featureDictViconSpace.update(featureDictViconSpaceNexus)
        #print("Feature Updated : ", featureDictViconSpace)


        if len(featureDictViconSpace) == 0:
            print("No tracking data skip Projection for frame : ", i)
            continue

        getFeaturesInCameraSpace(viconCamObjects,featureDictViconSpace)
        getFeaturesInImageSpace(imageObjects,viconCamObjects)

        # Get image frame and draw the information on image space
        for j in range(len(videoObjects)):
            tempImage = videoObjects[j].getFrame(i)
            if tempImage is not None:
                #imageObjects[j].drawFeatures(image= tempImage, pointSize= 2)
                imageObjects[j].drawPosture(tempImage)
                imageObjects[j].drawFeatures(tempImage)
                bBoxDict = imageObjects[j].drawBoundingBox(tempImage, border = 10)
                dataBaseObjects[j].updateDataBase(i, imageObjects[j].featureDict, viconCamObjects[j].featureDict, bBoxDict)
                roiImage = imageObjects[j].getRoiOnKeypoint("body_leftShoulder",tempImage)

                font = cv.FONT_HERSHEY_SIMPLEX
                cv.putText(tempImage, "frameCount : " + str(i) + "/" + str(maxFrameNo), (10, 50), font, 1,
                           (255, 255, 255), 2, cv.LINE_AA)
                cv.putText(tempImage, "Head1 : " + str(featureDictViconSpace["head1"]), (10, 100), font, 1,
                           (255, 255, 255), 2, cv.LINE_AA)

                # Display the image
                cv.imshow(windowNames[j], tempImage)

        waitValue = 10
        if pause :
            waitValue = 0

        k = cv.waitKey(waitValue)
        if k == ord('q'):
            testDataFrame.to_csv("distData.csv", index= False)
            cv.destroyAllWindows()
            break

        if k == ord('p'):
            pause = not pause

        if k == ord('n'):
            continue


if __name__ == '__main__':
    # In this section we pass the arguments required for the main function to perform any operation.
    # Mostly it is the system information for calibration and the location of the VICON file
    settingsFile = "D:\\BirdTrackingProject\\20190618_PigeonPostureDataset\\settings_session02.xml"

    main(settingsFile)



