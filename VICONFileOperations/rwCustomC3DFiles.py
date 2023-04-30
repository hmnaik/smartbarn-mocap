"""
The file contains all important helper class to read and write a c3d file. C3D file stores point cloud information per frame and
this case be used to store annotations effectively or create new points that can be further exported to a simple csv file etc.
"""

import ezc3d
import numpy as np
import pandas as pd

class C3dReader:

    def __init__(self, fileName, videoToIRDataCaptureRatio = 0.5, readOutStartIndex = 0):
        """
        Initialize the database class, which stores the information about 3D points reconstructed in vicon space
        :param fileName: str
        :param videoToIRDataCaptureRatio: (0-1) Vicon Frame Rate / Video frame rate
        :param readOutStartIndex:  Frame mapping between 1st frame of vicon and video
        """

        assert (fileName.endswith(".c3d")), "The file extension is not .c3d"

        c = ezc3d.c3d(fileName)
        self.data = c['data']['points']
        self.fileName = fileName
        self.lables = c['parameters']['POINT']['LABELS']['value']
        self.frameRate = c['header']['points']['frame_rate']
        self.firstFrame = c['header']['points']['first_frame']
        self.lastFrame = c['header']['points']['last_frame']
        self.labelledPointIndexs, self.unlabelledPointIndexs = self.findUnlabelledPoints()

        # VICON tracking frame rate rate is higher than camera
        # The implementation is same as extraction of the data points from csv (see rwOperations)
        self.videoCameraFrameRateRatio = videoToIRDataCaptureRatio
        self.startIndex = readOutStartIndex

    def findUnlabelledPoints(self):
        """
        Goes throug the lables of the c3d files and finds out indexes of labelled and unlabelled points
        :return: list of indexes of labelled and unlabelled data
        """
        unlabelledPtIdx = [index for index,label in enumerate(self.lables) if '*' in label]
        labelledPtIdx = [index for index,label in enumerate(self.lables) if '*' not in label]
        return labelledPtIdx, unlabelledPtIdx

    def computeDataFrameNoFromVideoFrameNo(self, videoFrameNo):
        """
        Computes the corresponding data frame number using given video frame number
        :param videoFrameNo: video frame no for which data is required
        :return: data frame no, the frame number registered by VICON system
        """
        assert (videoFrameNo >= 0), "Video frame number can not be less than 0"

        dataFrameNo = ( videoFrameNo * int(1/self.videoCameraFrameRateRatio) ) + 1 + self.startIndex
        return np.floor(dataFrameNo)


    def printMetaData(self):
        """
        Print important informaition from the c3d file
        :return: None
        """
        print("Printing meta data")
        print("File Name:", self.fileName)
        print("Labels:", self.lables)
        print("Frame rate:", self.frameRate)
        print("First frame:", self.firstFrame)
        print("Last frame:", self.lastFrame)
        print("Data shape:", self.data.shape)
        print("Indexes for labelled Points:", self.labelledPointIndexs)
        print("Indexes for unlabelled Points:", self.unlabelledPointIndexs)

    def findLableMapping(self, subjectNames):
        """
        Given subject names it finds indexes of labels that match the subject names i.e. points that belong to same subject
        :param subjectNames: list of strings
        :return: Dictionary of {'Subject Name': List of indexes}
        """
        assert (len(subjectNames) != 0), "No subject names given"
        subjectToDataMapping = {}
        for subject in subjectNames:
            subjectToDataMapping[subject] = [index for index,label in enumerate(self.lables) if subject in label]

        return subjectToDataMapping


    def getFrameData(self, queryframeNo, subjectToDataMapping):
        """
        The method is used to get data stored for a particular frame
        :param queryframeNo: frame number
        :param subjectToDataMapping: index of points mapped to each subject
        :return: dictionary of points {"subject": Points 3XN format}
        """

        assert (queryframeNo >= self.firstFrame), "The query frame number can not be less than the first frame no in data."

        frameNoInDataStructure = queryframeNo
        # if the dataset does not start from 0, the position of data is the matrix will be with offset of the framequery
        if self.firstFrame != 0:
            frameNoInDataStructure = queryframeNo - self.firstFrame

        dataDict = {}
        for subject in subjectToDataMapping:
            index = subjectToDataMapping[subject]
            lenIndex = len(index)
            dataDict[subject] = np.zeros((3,lenIndex))
            for i in range(lenIndex):
                dataDict[subject][:,i] = self.data[0:3, index[i], frameNoInDataStructure]

            # dataDict[subject] =  self.data[0:3,index[0]:index[-1]+1,frameNoInDataStructure]
            # print(dataDict)
            #print("Subject:{0} -- {1}".format(subject,dataDict[subject]))

        return dataDict

    def computeDistanceProfile(self, dataDict):
        print("Compute distance between all points for Nx3 matrix, return NxN upper triangular matrix")

    def computeAngleProfile(self, dataDict):
        print("Compute distance between all points for Nx3 matrix, return NxN upper triangular matrix")


############################ -------------------- Random file testing functions ------------------------------

def readFile (file):
    c = ezc3d.c3d(file)
    # The ezc3d is used to read the c3d as dictionary based structure
    # Mainly consists of 3 parts ['parameters']['data']['header']
    # Header can be used to read all the specification of the data and Data has the data stored in form of matrix
    # The labels can be retrieved from the parameters section
    parameters = c['parameters']
    print("FPS: ", c['parameters']['POINT']['RATE']['value'])
    print("Labels: ",c['parameters']['POINT']['LABELS']['value'])
    print(c['parameters']['POINT']['USED']['value'][0])  # Print the number of points used

    point_data = c['data']['points']

    header =  c['header']
    print("Frame rate: ", c['header']['points']['frame_rate'])
    print("First frame: ", c['header']['points']['first_frame'])
    print("Last frame: ", c['header']['points']['last_frame'])

    print(point_data.shape)
    data = point_data[0:4,0:4,:]
    print(data[:,:,1])
    print(data.shape)

    return data
    #points_residuals = c['data']['meta_points']['residuals']
    #analog_data = c['data']['analogs']


def writeFile(file, data):
    # Load an empty c3d structure
    c3d = ezc3d.c3d()
    # todo: It is always better to steal header and parameter from other c3d file or orginal file
    #
    # Fill it with random data
    c3d['parameters']['POINT']['RATE']['value'] = [100]
    c3d['parameters']['POINT']['LABELS']['value'] = ('point1', 'point2', 'point3', 'point4')
    #np.random.rand(4, 5, 100)
    c3d['data']['points'] = data
    # Write the data
    c3d.write(file)

def unitTest(fileName):

    data = readFile(fileName)
    #Create File
    tempFilePath = "..\\VICONTestData\\newData.c3d"
    writeFile(tempFilePath, data)
    data = readFile(tempFilePath)


if __name__ == '__main__':
    file = "20190618_PigeonPostureDataset_session02_skeleton.c3d"
    file2 = "D:\\BirdTrackingProject\\StarlingTest\\20190108_20birds1_07_filtered.c3d"
    fileName = '..\\VICONTestData\\' + file
    # unitTest(fileName)
    c3d = C3dReader(file2)
    c3d.printMetaData()
    #subjects = ["body","head"]
    subjects = ["nb01", "nb02", "nb03", "nb04", "nb05", "nb06", "nb07", "nb08", "nb09", "nb10", "nb11", "nb12", "nb13",
                "nb14", "nb15", "nb16", "nb17", "nb18", "nb19", "nb20"]
    subjectToLableMapping = c3d.findLableMapping(subjectNames= subjects)
    queryframe = c3d.firstFrame
    markerPositions = c3d.getFrameData( 19975, subjectToLableMapping)
    for subject in subjects:
        print(" Marker positions in 3XN format {0}{1}:{2}".format(subject,markerPositions[subject].shape,markerPositions[subject]))


