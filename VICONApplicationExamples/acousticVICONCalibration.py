import pandas as pd
import os
import glob
from VICONFileOperations import rwCustomC3DFiles
from VICONFileOperations import rwOperations
import numpy as np
import logging
from VICONMath import absoluteOrientation
from VICONMath import transformations
from mpl_toolkits import mplot3d
import matplotlib.pyplot as plt

logging.basicConfig(level=logging.DEBUG)
logging.basicConfig(filename='app.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')

def getFiles(dataDir, printInfo = False):
    """
    The function returns .csv and .csv files from the given directory
    :param dataDir: string path to directory
    :param printInfo: bool
    :return: list of .csv and .csv files
    """
    # Get 3d files
    c3dFiles = glob.glob(dataDir + "\*.c3d")
    if printInfo:
        print(f"Files = {c3dFiles}")

    csvFiles = glob.glob(dataDir + "\*.csv")
    if printInfo:
        print(f"Files = {csvFiles}")

    return csvFiles, c3dFiles

# This will be needed for dynamic calibration
def processFilterSaveVICONData(dataDir,featureList, extension="filtered"):
    csvFiles, c3dFiles = getFiles(dataDir, printInfo= True)
    # Read nexus source file and save only the center point information
    for file in csvFiles:
        parentDirectory = getParentDirectoryFromFile(file)
        logging.debug(f"Evaluating file:{file}")
        fileBaseName = os.path.basename(file)
        nexusDataReader = rwOperations.NexusDatabaseReader(file, featureList)
        dataFrame = nexusDataReader.__getattribute__("dataFrame")
        # Get data from sub frame
        subFrame = dataFrame[["Frame","X","Y","Z"]]
        # Drop all the frames which do not have core point positions
        subFrame = subFrame.dropna(axis = 0)
        # Save file at csv

        fileName = fileBaseName.split(".")[0]
        saveFileName = os.path.join(parentDirectory,fileName)
        saveFileName = saveFileName + "_" + extension + ".csv"
        logging.debug(f"Evaluating file:{saveFileName}")
        subFrame.to_csv(saveFileName)


def getLocation(list, sensorPositions):

    #Check if all 10 sessions are same
    sessionName = list[0]
    count = list.count(sessionName)
    if count is not len(list):
        assert ("All names on the list are not the same")

    matchedLocation = ""
    for position in sensorPositions:
        if position in sessionName:
            matchedLocation =  position
            break
        else:
            matchedLocation =  "NA"

    return matchedLocation


def getXYZ(subFrame):
    positionsDict = {}

    positionsDict["X"] = subFrame.X.mean()
    positionsDict["X_SD"] = subFrame.X.std()

    positionsDict["Y"] = subFrame.Y.mean()
    positionsDict["Y_SD"] = subFrame.Y.std()

    positionsDict["Z"] = subFrame.Z.mean()
    positionsDict["Z_SD"] = subFrame.Z.std()

    return positionsDict

def getParentDirectoryFromDir(dir):
    # Process the file and create a trajectory
    parentDir = dir.split("\\")[0:-1]
    glue = "\\"
    newDir = glue.join(parentDir)
    return newDir

def getParentDirectoryFromFile(file):
    # Process the file and create a trajectory
    dirName = os.path.dirname(file)
    parentDir = dirName.split("\\")[0:-1]
    glue = "\\"
    newDir = glue.join(parentDir)
    return newDir

class AudioViconStaticCalibration:

    def __init__(self, viconDataDirectory, acousticDataDirectory, calibrationlocations ):

        logging.info("Calibration class instance created")
        # Save directory information
        self.viconDataDir = viconDataDirectory
        self.acousticDataDir = acousticDataDirectory
        self.positions = calibrationlocations

        # Variables for vicon calibration
        self.featuresVicon = []
        self.featureOfInterest = ""
        self.maxNoPoints = 10
        self.summaryViconPositions = pd.DataFrame()
        self.viconPositionsfileName = ""
        self.directoryName = ""
        self.parentDir = ""
        self.normalizedPositions = pd.DataFrame()
        self.normalizedPositionsFileName = ""

        # Variables for acoustic calibration
        self.acousticPositionsFileName = ""

        # Variables used for calibration
        self.acousticLocationID = [] # Saves list of locations from the acoustic file
        self.acousticPoints = np.zeros(1) # 3XN format points based on positions w.r.t acoustic file
        self.viconLocationID = [] # Saves list of locations from the vicon file
        self.viconPoints = np.zeros(1) # 3XN format points based on positions w.r.t vicon file
        #self.viconPoints = 0
        #self.viconFile = viconDataFile
        #self.acousticFile = acousticDataFile
        #self.rotation = 0
        #self.translation = 0

        self.commonFeatues = self.positions.copy()


        print("Files")

    def loadPositions(self):
        """
        Load positions of the location of sensor for static calibration. The files used are internally created in a earlier step,
        each file is processed and a location based matrix is created.
        :return: Bool
        """
        # Load points from .csv files
        self.acousticLocationID, self.acousticPoints = self.loadPositionsFromDataFile(self.acousticPositionsFileName)
        logging.debug(f"Acoustic Locations:{self.acousticLocationID} and Points(3xN format) = {self.acousticPoints.size}")
        # list, ndarray (3xN)
        if len(self.acousticLocationID) != self.acousticPoints.shape[1]:
            logging.error(f"Size mismatch: Acoustic Locations:{len(self.acousticLocationID)} and Points(3xN format) = {self.acousticPoints.size}")
            return False

        self.viconLocationID, self.viconPoints = self.loadPositionsFromDataFile(self.normalizedPositionsFileName)
        logging.debug(f"Vicon Locations:{self.viconLocationID} and Points(3xN format) = {self.viconPoints.size}")

        # list, ndarray (3xN)
        if len(self.viconLocationID) != self.viconPoints.shape[1]:
            logging.debug(f"Size mismatch: Vicon Locations:{len(self.viconLocationID)} and Points(3xN format) = {self.viconPoints.size}")
            return False

        return True


    def updateViconPoints(self, points):
        self.viconPoints = points

    def updateAcousticPoints(self,points):
        self.acousticPoints = points

    def extractPointsFromFile(self, csvfile, features):
        print("dd")

    def updatePoints(self, system = "" ):
        """
        Updates list of points based on given list of features
        :param system: str "vicon" or "acoustic"
        :return: 3xN array with updates list
        """

        #match locations and find overlap
        if system == "vicon":
            points = self.viconPoints.copy()
            locationID = self.viconLocationID.copy()
        elif system == "acoustic":
            points = self.acousticPoints.copy()
            locationID = self.acousticLocationID.copy()
        else:
            logging.critical("No system given for updating points")
            return np.zeros( (3,len(self.commonFeatues )) )

        updatedPoints = np.ones( (3,len(self.commonFeatues)) )
        # Go through each location in common feature and filter points
        for idx, feature in enumerate(self.commonFeatues):
            index = locationID.index(feature)
            # Save selected features in a new matrix
            updatedPoints[:,idx] = points[:,index]

        return updatedPoints

    # Add extensions if required
    def addExtensionToPositions(self, extensions):
        """
        Adding extension to positions, if more extensions were added to specify locations like high, low etc.
        :return:
        """
        lst = []
        for ext in extensions:
            lst = lst + [i + "_" + ext for i in self.positions]
        self.positions = lst

    def extractPositionsFromAllViconSessions(self, csvFiles, summaryColumns):

        logging.debug("Loading vicon files")
        summaryDataFrame = pd.DataFrame(columns=summaryColumns)

        for file in csvFiles:

            logging.debug(f"Evaluating file:{file}")
            fileBaseName = os.path.basename(file)
            nexusDataReader = rwOperations.NexusDatabaseReader(file, self.featuresVicon)

            # Get filtered data frame i.e. for all those frames where at least one point is detected in the pattern
            dataFrame = nexusDataReader.__getattribute__("dataFrame")
            print(f"Size:{dataFrame.shape}")
            frameData = dataFrame["Frame"]  # Save frame information
            summaryDataDict = {}
            summaryDataDict["Session"] = fileBaseName  # Save information about the session
            iterator = 0

            # Go through the frames
            # todo: Randomize frame numbers
            for frameNo in frameData:
                if nexusDataReader.getFrameData(frameNo):
                    print(f" Frame: {frameNo} - Data:{nexusDataReader.featureDict}")
                    frameDataDict = nexusDataReader.featureDict  # Access the feature dict in the class already for the current frame
                    point = frameDataDict[self.featureOfInterest]  # get data for the point of interest
                    if np.any(np.isnan(point)):  # If data is NaN
                        logging.warning(f" @{frameNo}:{point} -> NaN")
                    else:  # If data is not NaN
                        logging.debug(f"@{frameNo}:{point} -> No NaN")
                        #print(f"{featureList[0]}:{point} -> No NaN")
                        iterator = iterator + 1
                        summaryDataDict["Frame"] = frameNo
                        summaryDataDict["X"] = point[0]
                        summaryDataDict["Y"] = point[1]
                        summaryDataDict["Z"] = point[2]
                        summaryDataFrame = summaryDataFrame.append(summaryDataDict, ignore_index=True)
                else:
                    logging.warning(f"No data available for query frame: {frameNo} - Data: None")
                    #print(f" Frame: {frameNo} - Data: None")

                if iterator == self.maxNoPoints:
                    break

        return summaryDataFrame

    def processAcousticData(self):

        # Get the files from given location and put them in a list
        csvFiles, c3dFiles = getFiles(self.acousticDataDir, printInfo=False)
        if len(csvFiles) > 1:
            logging.warning("There are more than 1 acoustic data files in the directory. Only support single file for now.")
            return False

        self.acousticPositionsFileName = csvFiles[0]
        return True

    def processViconData(self, featureList, pointOfinterest, maxNoOfPoints=10):
        """
        Given location of session files, the function will take the processed Nexus files (ASCII) and take information of
        sequences from each session file and combine the information to create a singke file.
        The combine information of each session in one single file and stored
        :param featureList: Features/Marker names as defined in the .csv file
        :param pointOfinterest: marker that is required for the calibration (center on the panel)
        :param maxNoOfPoints: No of points to be considered for computing normalized position
        :return: bool
        """
        # Define new variables
        self.featuresVicon = featureList
        self.featureOfInterest = pointOfinterest
        self.maxNoPoints = maxNoOfPoints

        dataDir = self.viconDataDir
        #sensorPositions = self.positions

        # Get the files from given location and put them in a list
        csvFiles, c3dFiles = getFiles(dataDir, printInfo=False)

        # Create a new data frame which will store the combined data
        summaryFileColumns = ["Session", "Frame", "X", "Y", "Z"]
        self.summaryViconPositions = pd.DataFrame(columns=summaryFileColumns)

        self.directoryName = dataDir.split("\\")[-1]
        self.parentDir = getParentDirectoryFromDir(dataDir)
        # Stage 1 : Go though all the files
        logging.debug(f"Loading all the files {csvFiles}")
        self.summaryViconPositions = self.extractPositionsFromAllViconSessions(csvFiles = csvFiles, summaryColumns= summaryFileColumns )
        if self.summaryViconPositions.empty:
            logging.warning("Loaded positions from nexus csv files are empty.")
            return False

        # Store the extracted positions as .csv file, with the name of the directory
        self.viconPositionsfileName = os.path.join(self.parentDir, self.directoryName + ".csv")
        self.summaryViconPositions.to_csv(self.viconPositionsfileName, index=False)
        logging.debug(f"Saving file:{self.viconPositionsfileName}")

        # Normlaized the data from each session to get one single position for each value
        normalizedPositionsColumns = ["Position", "X", "X_SD", "Y", "Y_SD", "Z", "Z_SD"]
        logging.debug(f"Computing normalized points for nexus points")
        self.normalizedPositions = self.computeNormalizedViconPositions(normalizedPositionsColumns)
        if self.normalizedPositions.empty:
            logging.warning("Computed normalized points file is empty.")
            return False

        self.normalizedPositionsFileName = os.path.join(self.parentDir, self.directoryName + "_normalized" + ".csv")
        self.normalizedPositions.to_csv(self.normalizedPositionsFileName, index=False)
        logging.debug(f"Saving file:{self.normalizedPositionsFileName}, Points: {self.normalizedPositions.shape}")

        return True

    def computeNormalizedViconPositions(self, summaryColumns ):

        # Read the combined data and create a new file
        combineData = pd.read_csv(self.viconPositionsfileName)

        # Create new data frame empty
        # Create a new data frame which will store the combined data
        normalizedPositions = pd.DataFrame(columns=summaryColumns)

        # Find number of recorded locations
        noOfRecordedLocations = int(combineData.shape[0] / self.maxNoPoints)
        positionDict = {}
        initialPoint = 0
        # Loop through locations to save information
        for iterator in range(noOfRecordedLocations):
            finalPoint = initialPoint + self.maxNoPoints  # Get all the positions recorded from one specific session
            subFrame = combineData.iloc[initialPoint:finalPoint]
            location = getLocation(list(subFrame["Session"]), self.positions)
            if location is not "NA":
                positionDict["Position"] = location
                positionDict.update(getXYZ(subFrame))

            normalizedPositions = normalizedPositions.append(positionDict, ignore_index=True)
            initialPoint = initialPoint + self.maxNoPoints

        return normalizedPositions

    def calibrate(self):
        """
        Function computes the relationship between vicon and acoustic coordinate system
        :return: Bool True/False
        """
        # Load positions of the point
        if self.loadPositions() == False:
            logging.error("Could not load 3D positions")
            return False


        # Compare location ID that exist in both acoustic data and vicon data and filter the files to have only those
        #
        self.commonFeatues = list(set(self.viconLocationID) & set(self.acousticLocationID))

        # Update points based on common features
        updatedViconPoints = self.updatePoints("vicon")
        updatedAcousticPoints = self.updatePoints("acoustic")

        # Bring acoustic points to mm scale (given in meters)
        updatedAcousticPoints = updatedAcousticPoints*1000

        # Acoustic to Vicon Save the updated points
        if updatedAcousticPoints.shape[1] == updatedViconPoints.shape[1]:
            self.updateViconPoints(updatedViconPoints)
            self.updateAcousticPoints(updatedAcousticPoints)
        else:
            logging.error("No of acoustic points and vicon points are different can not proceed to calibration")
            return False

        logging.info("Common points found between acoustic and vicon system going for full calibration")

        rot, trans = absoluteOrientation.findPoseFromPoints(updatedAcousticPoints,updatedViconPoints)
        transformedPoisitionsInViconFrame = transformations.transformPoints(updatedAcousticPoints, rot, trans)
        error_custom = transformations.rmsError(transformedPoisitionsInViconFrame,
                                                updatedViconPoints)

        errorPP = transformations.rmsErrorPerPoint(transformedPoisitionsInViconFrame,
                                                updatedViconPoints)

        self.visualizeData(updatedViconPoints,transformedPoisitionsInViconFrame,errorPP)

        print(f"Original Points {updatedViconPoints} \n Transformed points {transformedPoisitionsInViconFrame}")
        print("Rot: {}, trans:{}".format(rot, trans))
        print("Error: {} \ Per point error {}".format(error_custom,errorPP))

        return True

    def loadPositionsFromDataFile(self, file):
        """
        Load points from the summary file prepared by the program, for both acoustic and vicon
        :param file: str path
        :return: list, ndarray (3xN)
        """

        dFrame = pd.read_csv(file)
        dPoints = dFrame[["Position","X","Y","Z"]]
        # Remove non existing points
        dPoints = dPoints.dropna()
        # Identify locations
        locations  = list(dPoints["Position"].values)
        # Get points for each location
        points = dPoints[["X","Y","Z"]].values
        points = np.array(points) # convert to arrays
        points = points.T

        return locations, points


    # def loadPointsViconDataFile(self, file):
    #     print("vicon positions")
    #     dataFrame = pd.read_csv(file)
    #     dPoints = dataFrame[["Position","X","Y","Z"]]
    #     # Remove non existing points
    #     dPoints = dPoints.dropna()
    #     locations  = dPoints["Position"].values
    #     points = dPoints[["X", "Y", "Z"]].values
    #     points = np.array(points)  # convert to arrays
    #     points = points.T
    #     return locations, points

    def computeAlignment(self):
        print("Function to computer R/T between points")

        # Select points

    def compareErrors(self, point1, point2):
        print("Compare points and provide error profile between each points")

    def translateViconToAcoustic(self, pointsVicon):
        print("Transfer points to acoustic coordinate system")

        #return pointsAcoustic

    def translateAcousticToVicon(self, pointsAcoustic):
        print("Transfer points to vicon coordinate system")

    def visualizeData(self):
        print("Viz data")

        fig = plt.figure()
        ax = plt.axes(projection = "3d")


if __name__ == '__main__':

    # Define logging status
    logging.basicConfig(level=logging.DEBUG)
    # Define the path of vicon directories to process, preferred data is Nexus ascii files
    viconMeasurementsDir = "D:\ownCloud\BarnPaperData\AcousticCalibrationExperiments_20210511\AudioCalibration2021\AC01_ExportData"
    viconMeasurementsDir= r"C:\Users\naik\ownCloud\BarnPaperData\AcousticCalibrationExperiments_20210511\AudioCalibration2021\AC01_ExportData"
    # Define the path of acoustic directories
    acousticMeasurementsDir = "D:\ownCloud\BarnPaperData\AcousticCalibrationExperiments_20210511\AudioCalibration2021\AC01_AcousticData"
    acousticMeasurementsDir = r"C:\Users\naik\ownCloud\BarnPaperData\AcousticCalibrationExperiments_20210511\AudioCalibration2021\AC01_AcousticData"
    # Define the locations that are reflectec in the calibration sequence names, there are typically position names where device was placed
    positions = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L"]

    ## Initialize the calibration class
    staticCalibrationObject = AudioViconStaticCalibration(viconDataDirectory= viconMeasurementsDir, acousticDataDirectory= acousticMeasurementsDir, calibrationlocations= positions )
    # Extension for the locations
    extensions = ["high", "low"]
    staticCalibrationObject.addExtensionToPositions(extensions)

    featureListAcousticDevice = ["AC01_C", "AC012", "AC013", "AC014", "AC015", "AC016"] # Name of markers given in the vicon software
    featureOfinterest = "AC01_C"
    pointsToProcess = 10
    statusVicon = staticCalibrationObject.processViconData(featureList= featureListAcousticDevice, pointOfinterest= featureOfinterest, maxNoOfPoints= pointsToProcess  )

    if statusVicon:
        logging.info(" Vicon dataprocess success, going towards calibration")
    else:
        logging.warning("Error in vicon processing")

    statusAcoustic = staticCalibrationObject.processAcousticData()

    if statusAcoustic:
        logging.info("Going towards calibration")
    else:
        logging.warning("Error in vicon processing")

    staticCalibrationObject.calibrate()
    #acousticDeviceData = r"C:\Users\naik\ownCloud\BarnPaperData\AcousticCalibrationExperiments_20210511\AudioCalibration2021\AC02_ExportData"
    # Calibrate the files



    #processNexusFilesCombineData(dataDir= acousticDeviceData, featureList= featureListAcousticDevice, pointOfinterest= featureOfinterest, sensorPositions= positions)
    #processFilterSaveVICONData(acousticDeviceData,featureListAcousticDevice)

    #songData = "D:\ownCloud\BarnPaperData\AcousticCalibrationExperiments_20210511\BirdSongsAudioVicon2021\ExportData"
    #featureListSongData = ["phone1", "phone2", "phone3", "phone4"]
    #processVICONData(songData,featureListSongData)


    # Calibration process : Input ( Location of .csv files )
    # viconDataFile = r"D:\ownCloud\BarnPaperData\AcousticCalibrationExperiments_20210511\AudioCalibration2021\AC01_CalibrationPositions.csv"
    # acousticDataFile= r"D:\ownCloud\BarnPaperData\AcousticCalibrationExperiments_20210511\AudioCalibration2021\AC01_AcousticData\AC01_AcousticTriangulationData.csv"
    # locations = ["A","B","C","D","E","F","G","H","I","J","K","L"]
    #
    # calibrationObject = AudioViconStaticCalibration(viconDataFile= viconDataFile, acousticDataFile= acousticDataFile, locations= locations)
    # calibrationObject.calibrate()