import glob
import os
from VICONFileOperations import loadVICONCalib
from VICONFileOperations import rwOperations
from VICONFileOperations import rwCustomC3DFiles
from VICONSystem import objectVicon
from VICONMath import transformations as tf
from VICONSystem import videoVicon
from VICONSystem import imageVicon
import cv2 as cv
from VICONSystem import camera
import numpy as np

# VICON System class initialise the system and loads the important information regarding the session and VICON settings
# Camera calibration and path for processing the video files
class VICONSystemInit:

    def __init__(self, projectSettings, directoryName = None):
        """
        Constructor for initialising vicon system. Gets the root folder of VICON and Session to be worked on and created required
        file names for the .csv file and .xcp file. Also generates name for the video files.
        :param dirName: Directory which has vicon session data
        :param sessionName: Name of the recording session
        """
        self.settingsDict = projectSettings.settingsDict
        directoryName = projectSettings.settingsDict["rootDirectory"]

        # Directory name for the vicon system and session name
        if os.path.exists(directoryName):
            self.rootDirectory = directoryName
        else:
            raise ValueError("Given directory does not exist")
        self.sessionName = projectSettings.settingsDict["session"]

        # Generate information about the VICON session
        self.dataFileName =  self.generateCSVFileName()
        self.calibFileName = self.generateCalibFileName()

        # Get information about camera objects
        self.cameraInstances = self.loadCalibInfo()
        self.customCameraInstances = []
        self.sessionVideoFiles = self.generateVideoFileNames()
        self.cameraInstances = self.filterObjectBasedOnVideoFile()

        # Load CSV file and create object
        self.dataObject = self.loadDataFile()
        self.c3dDataObject = self.loadc3dFile()
        # Create objects for camera and objects
        self.viconObjects = self.loadVICONObjects()
        self.viconCameraObjets = self.loadVICONCameraObjects()
        self.viconVideoObjects = self.loadVideoObjects()
        self.viconImageObjects = self.loadImageObjects()

    def loadDataFile(self):
        print("Load data file")
        dataFileName = os.path.join(self.rootDirectory,self.settingsDict["dataFile"])
        # todo: videoToIRDataCaptureRatio should be saved in the settings file
        dataObject = rwOperations.TrackerDatabaseReader(dataFileName, self.settingsDict["objectsToTrack"])  # Read the csv file
        return dataObject

    def loadc3dFile(self):
        print("Load c3d data file")
        dataFileName = os.path.join(self.rootDirectory, self.settingsDict["c3dFileStream"])
        c3dDataObject = rwCustomC3DFiles.C3dReader(dataFileName)
        return c3dDataObject



    def loadCustomTrackingFeaturesToTrackingObjects(self):
        """
        Load the custom tracking features to the given vicon object
        :return:
        """
        customFilePath = os.path.join(self.rootDirectory, self.settingsDict["customFeatureFile3D"])
        for trackingObject in self.viconObjects:
            trackingObject.readFeaturePointsFromFile(customFilePath)


    def addCustomCameraInstances(self,
                                 type = "custom",
                                 id= 666,
                                 rot = [0, 0, 0, 1],
                                 translation = [0, 0, 0],
                                 k = np.identity(3),
                                 dist= np.zeros((1,5))
                                 ):
        """
        Creating the default custom camera instance
        :param type: string : Name of the camera
        :param id: string : Custom id given to the camera
        :param rot: list : Rotation
        :param translation: list : Translation
        :param k: list : Intrinsic parameters
        :param dist: list : Distortion parameters
        :return: None
        """
        print("No of custom cameras attached: ", len(self.customCameraInstances))
        cameraInstance = camera.Camera()
        cameraInstance.setCameraInfo(type,id)
        cameraInstance.setExtrinsicParam(rot, translation)
        cameraInstance.setIntrinsicParam(k, dist)
        self.customCameraInstances.append(cameraInstance)
        print("Added 1 camera instance: ", len(self.customCameraInstances))


    def loadVICONObjects(self):
        print("Load objects classes ")
        viconObjects = []
        for object in self.settingsDict["objectsToTrack"]:
            viconObject = objectVicon.ObjectVicon(name=object)
            objPath = os.path.join(self.rootDirectory, object + ".mp")
            viconObject.readFeaturePointsFromFile(objPath)
            viconObjects.append(viconObject)

        return viconObjects

    def loadVideoObjects(self):
        # Create video instances
        videoObjects = []

        for serialNo in self.settingsDict["cameras"]:
            videoObject = videoVicon.VideoVicon(self.sessionVideoFiles[str(serialNo)], int(serialNo))
            videoObjects.append(videoObject)

        return videoObjects

    def loadImageObjects(self, customObjects = False):

        imageObjects = []
        if customObjects:
            cameraInstances = self.customCameraInstances
        else:
            cameraInstances = self.cameraInstances

        for cam in cameraInstances:
            # Create image instances, to store camera param and image features
            camParam = cam.getCameraParam()
            intrinsicMat = camParam["intrinsicParam"]
            distortionMat = camParam["distortionParam"]
            serialNo = camParam["serialNo"]
            imageObjects.append(imageVicon.ImageVicon(serialNo, distortionMat, intrinsicMat))

        return imageObjects

    def loadVICONCameraObjects(self, customObjects = False):
        """
        Load camera objects
        :return: list of cam objects
        """
        viconCamObjects = []

        if customObjects:
            cameraInstances = self.customCameraInstances
        else:
            cameraInstances = self.cameraInstances

        for camera in cameraInstances:
            # Go through the instances and create camera object just like vicon object
            camParam = camera.getCameraParam()
            # Create camera object and add features to camera object from all possible vicon objects
            # The rotation parameters given in the calibration file are given to manipulate data from vicon space to camera space
            # We designed a new class called Object, this class is designed to store rotation and translation information
            # to transfer features to the vicon space
            rotation = camParam["extrinsicRotation"]
            inverseRotation = tf.invertQuaternion(rotation)
            viconCamObject = objectVicon.ObjectVicon(inverseRotation, camParam["extrinsicTranslation"],
                                                     camParam["serialNo"])
            print("Rotation: ", inverseRotation, "\n Translation: ", camParam["extrinsicTranslation"])

            for viconObject in self.viconObjects:  # Add features from each object to the camera object
                viconCamObject.setFeatures(viconObject.__getattribute__("featureDict"))

            viconCamObjects.append(viconCamObject)

        return viconCamObjects

    def verifyPath(self, path):
        """
        Verify the validity of the path otherwise return exception
        :param path: str
        :return: bool
        """
        return os.path.exists(path)

    def filterObjectBasedOnVideoFile(self):
        """
        Remove camera objects not having video files to support video tracking
        :return:
        """
        updatedCamObjects = []
        for i in range(len(self.cameraInstances)):
            if str(self.cameraInstances[i].__getattribute__("cameraID")) in self.sessionVideoFiles:
                updatedCamObjects.append(self.cameraInstances[i])

        return updatedCamObjects

    def setCalibFileName(self, name):
        """
        Sets custom file location for the calibration file. *.xcp
        :param name: File Name
        :return: None
        """
        self.calibFileName = name

    def setDataFileName(self,name):
        """
        Sets custom file location for the data file. *.csv
        :param name: File Name
        :return: None
        """
        self.dataFileName = name

    def printSysteInfo(self):
        """
        Prints all the information about the VICON system, obtained for the given file
        :return: None
        """
        print("File Path: ", self.rootDirectory)
        print("Session Name : ", self.sessionName)
        print("Data File Name", self.dataFileName)
        print("Calib File Name", self.calibFileName)
        print("Video Files", self.sessionVideoFiles)


    def generateCSVFileName(self):
        """
        Creates name of the CSV file from the given vicon directory and session info
        :return: csv file for the exported
        """
        # create CSV file from given directory and session name
        # File Name = Foldername_sessionName.csv
        csvFile = os.path.join(self.rootDirectory, self.settingsDict["dataFile"])

        # Verification of Data
        if not os.path.exists(csvFile):
            print("Looking for : ", csvFile)
            raise ValueError(" Error while generating *.csv name using VICON convention, Check given Session name or File does not exist ")

        return csvFile

    def generateCalibFileName(self):
        # Generate file name for the calibration file from the given info

        calibFileName = os.path.join(self.rootDirectory, self.settingsDict["calibFile"])
        # Verification of Data
        if not os.path.exists(calibFileName):
            raise ValueError(" Error while generating *.xcp name using VICON convention, Check given Session name or File does not exist ")

        return calibFileName



    def loadCalibInfo(self):
        """
        Reads the calibration information from the given .xcp file
        :return: list of instances of class Camera
        """
        camObjects = loadVICONCalib.readCalibrationFromXCP(self.calibFileName)
        return camObjects

    # def getCameraCalibration(self):
    #     """
    #     Returns list of objects of class camera, read from the given .xcp file
    #     :return: list of Object camera
    #     """
    #     return self.camObjects

    def generateVideoFileNames(self):
        """
        Generates video files based on the given location of the file and the session name
        :return: Dict (Serial No : Video File)
        """
        sessionVideoFiles = {}
        for camera, videoFile in zip (self.settingsDict["cameras"], self.settingsDict["videoFiles"]):
            filePath = os.path.join(self.rootDirectory, videoFile)
            sessionVideoFiles[str(camera)] = filePath

        return sessionVideoFiles

    def generate2DAnnotationFileNames(self):
        """
        Generate file names for the 2D annotation data for each camera,
        :return: Dict (Serial No: *.csv file)
        """
        assert (len(self.sessionVideoFiles) != 0),"No video files, can not generate annotation file names"
        annotationFilesDict = {}

        for camera, annotationFileName in zip(self.settingsDict["cameras"],self.settingsDict["annotationFiles"]):
            filePath = os.path.join(self.rootDirectory,annotationFileName)
            annotationFilesDict[str(camera)] = filePath

        return annotationFilesDict


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




if __name__ == '__main__':
    # In this section we pass the arguments required for the main function to perform any operation.
    # Mostly it is the system information for calibration and the location of the VICON file

    settingsFile = "D:\\BirdTrackingProject\\20190618_PigeonPostureDataset\\settings_session02.xml"

    from VICONFileOperations import settingsGenerator
    projectSettings = settingsGenerator.xmlSettingsParser(settingsFile)
    viconSystemData = VICONSystemInit(projectSettings)
    viconSystemData.printSysteInfo()
    # Get all the VICON camera instances
    camInstances = viconSystemData.cameraInstances
    printCalibInformation(camInstances)

    # create name for the annotation file
    dict = viconSystemData.generate2DAnnotationFileNames()

    # OR another way to access the information is this way
    print( " Camera type : " ,camInstances[0].cameraType)
    print(" Camera type : ", camInstances[0].extrinsicRotation)