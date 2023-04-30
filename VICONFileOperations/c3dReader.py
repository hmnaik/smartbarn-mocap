import c3d
import numpy as np
import os
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from VICONDrawingOperations import makeMovie



def print_metadata(reader):
    print('Header information:\n{}'.format(reader.header))
    print('Labels {}'.format(reader.point_labels)) # Printing all the labels available in the stream
    print('First frame in data: {}'.format(reader.first_frame())) # The frame rate of recorded data
    print('Frame rate:{}'.format(reader.point_rate)) # Frame date of data capture
    print('Parameter blocks: {}'.format(reader.parameter_blocks())) #

def readBasicStructureOfC3D(file):
    with open('D:/ownCloud/BarnPaperData/testData/Trial02_Clipped.c3d','rb') as handle:
        reader = c3d.Reader(handle)
        # Print details of the .c3d file for overview
        print_metadata(reader)
        # draw labels
        handle.close()


def get_xyz(points, pair):
    firstPointIndex = pair[0]
    secondPointIndex = pair[1]
    x = np.array([ points[firstPointIndex,0],points[secondPointIndex,0]  ])
    y = np.array([ points[firstPointIndex,1],points[secondPointIndex,1]  ])
    z = np.array([ points[firstPointIndex,2],points[secondPointIndex,2]  ])

    return [x,y,z]

def normalize(featurePoints, rootPointIndex):
    rootPoint = featurePoints[rootPointIndex,:]
    m,n = featurePoints.shape
    normalizeMat = np.tile(rootPoint,(m,1))
    assert (normalizeMat.shape == featurePoints.shape), "Size mismatch during normalization"
    normalizedPoints = featurePoints - normalizeMat

    return normalizedPoints

def validate(featurePoints):
    """
    Function validates if all values are present
    :param featurePoints:
    :return:
    """
    m,n = featurePoints.shape
    validationStatus = [True,True,True,True]
    for i in range(m):
        if np.array_equal(featurePoints[i, :], np.zeros((3)) ):
            validationStatus[i] = False

    return validationStatus

def getColor(pair):
    lcolor = "#3498db" #"#3498db"
    rcolor = "#e74c3c" #"#e74c3c"
    black = 'b'
    if 2 in pair:
        return lcolor
    if 3 in pair:
        return rcolor
    else:
        return black

def sampleAppPostureExtraction(fileName):
    with open(fileName, 'rb') as handle:
        reader = c3d.Reader(handle)
        # Define size for the graph
        width = 7
        height = 5

        files = []
        pretext = 'img'
        angle = 0
        imageIndex = 0

        for i, points, analog in reader.read_frames():
            # Read points foo each frame
            print("points{}:{}".format(points.shape, points[0:4, :]))
            featurePoints = points[0:4, 0:3]
            status = validate(featurePoints)
            rootPosition = 0
            if False in status:
                continue
            # normalize point data for plotting in same position
            featurePoints = normalize(featurePoints, rootPosition)
            rootPoint = featurePoints[rootPosition, :]
            m, n = featurePoints.shape
            normalizeMat = np.tile(rootPoint, (m, 1))

            fig = plt.figure()
            ax = fig.add_subplot(111, projection='3d')
            ax.figure.set_size_inches(width, height)
            ax.set_aspect('equal')
            # Define connecting pairs for the posture by making list of indexes
            pairs = {'body': [0, 1],
                     'lWing1': [0, 2],
                     'lWind2': [1, 2],
                     'rWing1': [0, 3],
                     'rWing2': [1, 3]}
            # Plot each pair of posture on the graph with specific box and viewing angle
            for pair in pairs:
                [x, y, z] = get_xyz(featurePoints, pairs[pair])
                ax.plot(x, y, z, lw=2, c=getColor(pairs[pair]))
                RADIUS = 500  # space around the subject
                xroot, yroot, zroot = 0, 0, 0
                ax.set_xlim3d([-RADIUS + xroot, RADIUS + xroot])
                ax.set_zlim3d([-RADIUS + zroot, RADIUS + zroot])
                ax.set_ylim3d([-RADIUS + yroot, RADIUS + yroot])
                ax.view_init(elev=None, azim=angle)
                ax.legend()

            figName = "temp/{0}{1}.jpeg".format(pretext, imageIndex)
            imageIndex += 1
            ax.figure.savefig(figName)
            plt.close(fig)
            files.append(figName)

        fileName = "video/output.mp4"
        fileFormat = "temp/{0}%d.jpeg".format(pretext)
        makeMovie.make_video_from_images(fileFormat, fileName, displayImages=True)
        for f in files:
            os.remove(f)
        files.clear()



if __name__ == '__main__':

    fileName = 'D:/ownCloud/BarnPaperData/testData/Trial02_Clipped.c3d'
    readBasicStructureOfC3D(fileName)
    sampleAppPostureExtraction(fileName)





