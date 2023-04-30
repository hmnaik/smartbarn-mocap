"""
This file shows an example of using the custom 2D annotations and triangulating them to create 3D annotations.

"""


import cv2 as cv
import numpy as np
from VICONMath import transformations as tf
import os
from VICONSystem import systemInit as system
from VICONFileOperations import rwOperations as fileOp
from VICONSystem import objectVicon as viconObj
from VICONSystem import videoVicon as videoObj
from VICONSystem import imageVicon as imageObj
from VICONMath import stereoComputation as stereo
import pandas as pd
from VICONFileOperations import settingsGenerator

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

def createDatabase(customFeatures):
    """
    Create databse structure for storage of triangulated 3D features
    :return:
    """

    defaultDataSeries = {"frame": 0}
    for feature in customFeatures:
        defaultDataSeries[str(feature) + "_x"] = 0
        defaultDataSeries[str(feature) + "_y"] = 0
        defaultDataSeries[str(feature) + "_z"] = 0

    dataFrame = pd.DataFrame(columns=list(defaultDataSeries))

    return defaultDataSeries, dataFrame

def avgList(listOfFeatures):
    """
    Give the avg from the list
    :param listOfFeatures : List of features
    :return: avg out values
    """
    avg = 0
    noOfZeroes = listOfFeatures.count(0)
    length = len(listOfFeatures) - noOfZeroes
    if length != 0:
        avg = sum(listOfFeatures)/length

    return avg


def getFinalPoints(dataFrame3DFeatures, features):
    """
    Get final points from the triangulated annotations
    :param dataFrame3DFeatures: Dataframe of features
    :param features: name of custom features
    :return: dict of normalised points
    """
    dict = {}
    for feature in features :
        # Get coordinates of the features
        xFeatures = dataFrame3DFeatures[feature+ "_x"].tolist()
        yFeatures = dataFrame3DFeatures[feature + "_y"].tolist()
        zFeatures = dataFrame3DFeatures[feature + "_z"].tolist()

        # Average all coordinates
        xAvg = avgList(xFeatures)
        yAvg = avgList(yFeatures)
        zAvg = avgList(zFeatures)

        # create dict entry for avg point
        dict[feature] = [xAvg, yAvg, zAvg]

    return dict

def compute2DError(projectedPoints, originalAnnotations):
    """
    Compute 2D error between the annotated point and the reprojected 2D point after triangulation
    :param dict : projectedPoints: projection of all triangulated points on image space
    :param dict : triangulatedPoints: selected 2D annotation
    :return: dict : 2D error dictionary
    """
    errorDict = {}
    for feature in originalAnnotations:
        poin2D = originalAnnotations[feature]
        # Check if the required feature is annotated or not, if not we skip that feature
        if feature in projectedPoints.keys() :
            projectedPoint2D = projectedPoints[feature]
        else:
            continue

        error = np.sqrt( (poin2D[0]-projectedPoint2D[0]) * (poin2D[0]-projectedPoint2D[0]) +
                         (poin2D[1] - projectedPoint2D[1]) * (poin2D[1] - projectedPoint2D[1]) )
        errorDict[feature] = error

    return errorDict

def createTriangulatedFeatures(projectSettings):
    """
    Read the settings from the given file and read
    :param settingsDict: dict
    :return: None
    """
    settingsDict = projectSettings.settingsDict
    directoryName = settingsDict["rootDirectory"]
    sessionName = settingsDict["session"]
    objectsToTrack = settingsDict["objectsToTrack"]

    # Part 1 : Load system information from calibration file i.e. calib, video files, .csv files and so on.
    viconSystemData = system.VICONSystemInit(projectSettings,sessionName)
    viconSystemData.printSysteInfo()

    dataObject = viconSystemData.dataObject
    viconObjects = viconSystemData.viconObjects

    # Create video objects
    videoFiles = viconSystemData.sessionVideoFiles  # __getattribute__("sessionVideoFiles")
    viconCamObjects = viconSystemData.viconCameraObjets
    videoObjects = viconSystemData.viconVideoObjects
    imageObjects = viconSystemData.viconImageObjects

    # Define window names
    windowNames = []
    maxFrameNo = []
    for video in videoObjects:
        windowNames.append(video.windowName)
        cv.namedWindow(video.windowName, cv.WINDOW_NORMAL)
        maxFrameNo.append(video.totalFrameCount)

    # Part 2 : Preapre files and features for triangultion of annotated features
    # Initialise class to read image annotations
    annotationFiles = viconSystemData.generate2DAnnotationFileNames()
    featureFileName = os.path.join(directoryName, settingsDict["customFeatureFile"])
    outputFeatureFileName =  os.path.join(directoryName, settingsDict["customFeatureFile3D"])
    customFeatures = fileOp.readFeaturesFromFile(featureFileName)

    imageAnnotationReaderObjects = []
    commonAnnotatedFrames = []
    for annotationImageID in annotationFiles:
        annotationObject = fileOp.ImageAnnotationDatabaseReader(annotationFiles[annotationImageID], customFeatures)
        commonAnnotatedFrames.append(annotationObject.data["frame"].tolist() )
        imageAnnotationReaderObjects.append(annotationObject)


    # Check if all videos have same number of frames and reassigns the variable to one single value
    if maxFrameNo.count(maxFrameNo[0]) == len(maxFrameNo):
        maxFrameNo = maxFrameNo[0]
    else:
        raise ValueError("Videos do not have same frame count.")

    # Create data frame for the triangulated features
    defaultTraingulatedFeatureDict3D, dataFrame3DFeatures = createDatabase(customFeatures)
    triagulatedPointsDatabasePath =  os.path.join(directoryName, settingsDict["dataFile3D"])

    # Create a triangulator class which would compute traingulated points for the given cameras
    stereoTriangulator = stereo.StereoTrinagulator(viconCamObjects, imageObjects)

    # Part 3 : Process frame wise information and triangular the features given in the annotation file
    for frameNo in commonAnnotatedFrames[0]:

        #Clear features stored in image class and camera object class, since they change per frame
        for j in range(len(viconCamObjects)):
            viconCamObjects[j].clearFeatures()
            imageObjects[j].clearFeatures()

        for j in range(len(viconObjects)):
            viconObjects[j].removeSelectedFeatures(customFeatures)

        # Go through the image annotation databse and get features of image point
        featureDicts = []
        for i in range(len(imageAnnotationReaderObjects)):
                featureDict = imageAnnotationReaderObjects[i].getDataForVideoFrame(frameNo)
                imageObjects[i].setFeatures(featureDict)
                featureDicts.append(featureDict)

        # Traingulate points
        triangulatedDict = stereoTriangulator.getTriangulatedPoints()

        if len(triangulatedDict) == 0:
            print(" No traingulated features for frame no : ", frameNo)
            continue

        # Set features in cam space and transform features to vicon space
        viconCamObjects[0].setFeatures(triangulatedDict)
        featureDictViconSpace = viconCamObjects[0].transferFeaturesToViconSpace()

        print("feature dict" , featureDictViconSpace)

        # Get rotation and translation information of tracking objects for given frame
        transformationParamDict = dataObject.getDataForVideoFrame(frameNo)
        traingulatedFeatureDict3D = defaultTraingulatedFeatureDict3D.copy()
        traingulatedFeatureDict3D["frame"] = frameNo

        for object,j in zip( objectsToTrack,range(len(viconObjects)) ):
            # If transformation is valid then transfer features into object space
            if transformationParamDict[object+"_validity"]:
                # If transformation is valid it is stored
                viconObjects[j].setTransformationParameters(transformationParamDict[object + "_rotation"],
                                                            transformationParamDict[object + "_translation"])

                featureDictObjectSpace = viconObjects[j].transferFeaturesToObjectSpace(featureDictViconSpace)
                #print("Features Object Space: ", featureDictObjectSpace)

                objectSpecificFeatureDict = {}
                # For each feature transferred to an object space, we check if it belongs a tracking object object
                for feature in featureDictObjectSpace:
                    if object in feature:  # object name must be in feature name
                        point3D = featureDictObjectSpace[feature]
                        objectSpecificFeatureDict[feature] = point3D
                        traingulatedFeatureDict3D[feature + '_x'] = point3D[0]
                        traingulatedFeatureDict3D[feature + '_y'] = point3D[1]
                        traingulatedFeatureDict3D[feature + '_z'] = point3D[2]

                # Set features for the object.
                viconObjects[j].setFeatures(objectSpecificFeatureDict)
                print("Object Points", viconObjects[j].__getattribute__("featureDict"))

            else:
                print("Invalid transformation for object : ", object, "for frame : ", frameNo )

        # Transfer all the points from object space to vicon space (Feature points + Newly traingulated points
        transferredFeatureDictViconSpace = {}
        for i in range(len(viconObjects)):
            dict = viconObjects[i].transferFeaturesToViconSpace()
            transferredFeatureDictViconSpace.update(dict)

        # Now transfer all points from VICON object space to Camera space
        for j in range(len(viconCamObjects)): # Loop through camera objects and find image projections
            # Dictionary operations
            featureDictCamSpace = viconCamObjects[j].transferFeaturesToObjectSpace(transferredFeatureDictViconSpace)
            #print("Features vicon -> camera space : ", featureDictCamSpace)
            viconCamObjects[j].setFeatures(featureDictCamSpace)
            imageFeaturesDict = imageObjects[j].projectFeaturesFromCamSpaceToImageSpace(featureDictCamSpace)
            imageObjects[j].setFeatures(imageFeaturesDict)
            # print("image Projections Features: ", imageObjects[j].__getattribute__("featureDict"))

            error = compute2DError(imageFeaturesDict, featureDicts[j])
            # print("Error for cam ", j, " points : ", error)

        for j in range(len(videoObjects)):
            image = videoObjects[j].getFrame(frameNo)

            font = cv.FONT_HERSHEY_SIMPLEX
            cv.putText(image, "frameNo : " + str(frameNo), (10, 50), font, 1,
                       (255, 255, 255), 2, cv.LINE_AA)
            cv.putText(image, " Press : A-ccept, R-eject, Q-uit, N-ext", (350, 50), font, 1,
                       (255, 255, 255), 2, cv.LINE_AA)
            # cv.putText(image, " Press R to reject ", (10, 200), font, 1,
            #            (255, 255, 255), 2, cv.LINE_AA)

            if image is not None:
                imageObjects[j].drawFeatures(image, 2)
                cv.imshow(windowNames[j],image)

        k = cv.waitKey(0)
        if k == ord('q'):
            cv.destroyAllWindows()
            break

        if k == ord('a'):
            print("Accept Annotation")
            dataFrame3DFeatures = dataFrame3DFeatures.append(traingulatedFeatureDict3D, ignore_index=True)
            dataFrame3DFeatures.to_csv(triagulatedPointsDatabasePath, index=False)  # Save each entry in the file
            #traingulatedFeatureDict3D = {}
        if k == ord('r'):
            print("Reject Annotation")

        if k == ord('n'):
            continue

    # After triangulation go through all triangulated points and create a single feature.
    finalPointDict = getFinalPoints(dataFrame3DFeatures, customFeatures)
    print("Final Point Dict: ", finalPointDict)
    fileOp.writeFeaturePointsToFile(outputFeatureFileName, finalPointDict)

def main(settingsFile):
    projectSettings = settingsGenerator.xmlSettingsParser(settingsFile)
    createTriangulatedFeatures(projectSettings)


if __name__ == '__main__':
    # In this section we pass the arguments required for the main function to perform any operation.
    # Mostly it is the system information for calibration and the location of the VICON file

    settingsFile = "D:\\BirdTrackingProject\\20190618_PigeonPostureDataset\\settings_session02.xml"
    main(settingsFile)


