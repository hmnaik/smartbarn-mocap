# The file is created to store math related to stereo computation
from VICONMath import transformations as tf
import numpy as np
import cv2 as cv
from VICONSystem import objectVicon, imageVicon

class StereoTrinagulator:
    def __init__(self, camObjects, imageObjects):
        self.viconCameraObjects = camObjects
        self.extrinsicRotationMatrix = np.identity(3) # 3x3
        self.extrinsiceTranslationMatrix = np.matrix([0,0,0]).T # 3x1
        self.triangulatedPoints = []
        self.imageObjects = imageObjects

    def filterPoints(self, img1FeatureDict, img2FeatureDict):
        """
        Filter the points which can be triangulated, expecting mismatch between the two dictionaries and removing non zero entries
        :param img1FeatureDict:
        :param img2FeatureDict:
        :return: returns matched list dict of points which are actually valid for triangulation
        """
        commonFeatures = list( set(img1FeatureDict).intersection(set(img2FeatureDict)) )
        img1FilteredDict = {}
        img2FilteredDict = {}
        emptyPoint = [0,0]
        for point in commonFeatures:
            if img2FeatureDict[point] != emptyPoint and img1FeatureDict[point] != emptyPoint:
                img1FilteredDict[point] = img1FeatureDict[point]
                img2FilteredDict[point] = img2FeatureDict[point]

        return img1FilteredDict,img2FilteredDict


    def getTriangulatedPoints(self):
        # return the points
        assert (len(self.viconCameraObjects) == 2), "Currently triangulation not supported for more than two cameras"
        assert (len(self.imageObjects) == 2), "Currently triangulation not supported for more than two cameras"

        img1FeatureDict = self.imageObjects[0].__getattribute__("featureDict")
        img2FeatureDict = self.imageObjects[1].__getattribute__("featureDict")

        img1filterDict, img2filterDict = self.filterPoints(img1FeatureDict,img2FeatureDict)


        triangulateFeatureDict = {}
        if len(img1filterDict) != 0 and len(img2filterDict) != 0:
            self.triangulatedPoints = triangulatePoints( self.imageObjects[0], self.viconCameraObjects[0], \
                                    self.imageObjects[1], self.viconCameraObjects[1], list(img1filterDict.values()), list(img2filterDict.values()) )

            for feature,index in zip(img1filterDict,range(len(self.triangulatedPoints)) ):
                triangulateFeatureDict[feature] = self.triangulatedPoints[index]

            return triangulateFeatureDict

        else: # Return empty dict if triangulation was not possible due to lack of matching points

            return triangulateFeatureDict




def computeExtrinsic(cam1Rotation, cam1Translation, cam2Rotation, cam2Translation):
    """
    compute extrinsic matrix between the given cameras. Rotation and translation parameters supposed to bring points to
    a common coordinate space from camera space.
    Extrinsics can convert points from cam2 space to cam1 space
    Pv = R_cam1. Pc1 + t_cam1 , Pv = R_cam2 . Pc2 + t_cam2
    :param cam1Rotation: rotation ( C -> V) 3x3 matrix
    :param cam1Translation: translation (C -> V) 3x1 matrix
    :param cam2Rotation: rotation (C -> V) 3x3 matrix
    :param cam2Translation: (C -> V) 3x1 matrix
    :return: Rotation and translation ( C2 -> C1)
    """

    # Rotation
    # rotationCam2toCam1 = inverse(cam1Rotation) . cam2Rotation
    rotationCam2toCam1 = np.dot( np.linalg.inv(cam1Rotation), cam2Rotation)

    # translationCam2toCam1 = inverse(cam1Rotation) . (cam2Translation - cam1Translation)
    translationCam2toCam1 = np.dot ( np.linalg.inv(cam1Rotation), (cam2Translation-cam1Translation))

    return rotationCam2toCam1, translationCam2toCam1

def computeExtrinsicsFromViconCamObject(cam1ViconObject, cam2ViconObject):
    """
    Compute extrinsic parameters from the given vicon camera objects, return rotation and translation for transferring
    cam2 space to cam1 space.
    :param cam1Object: instance of vicon object class (Representing camera)
    :param cam2Object: instance of vicon object class (Representing camera)
    :return: Matrix - 3x3, 3x1
    """

    cam1Rotation, cam1Translation = tf.transformationParamListToMatrix\
        ( cam1ViconObject.__getattribute__("rotation"),cam1ViconObject.__getattribute__("translation") )


    cam2Rotation, cam2Translation = tf.transformationParamListToMatrix\
        ( cam2ViconObject.__getattribute__("rotation"), cam2ViconObject.__getattribute__("translation") )

    rotationCam2ToCam1, translationCam2ToCam1 = computeExtrinsic(cam1Rotation, cam1Translation, cam2Rotation,
                                                                 cam2Translation)

    return rotationCam2ToCam1, translationCam2ToCam1

#
def triangulatePoints( image1Object, viconCam1Object, image2Object, viconCam2Object, img1Points, img2Points):
    """
    Computer triangulated features from given image and camera objects, In 3D space of camera 1
    :param image1Object: instance of image object
    :param viconCam1Object: instance of vicon camera object
    :param image2Object: instance of image object
    :param viconCam2Object: instance of vicon camera object
    :return: List of 3D points
    """

    # Transformation matrix to transfer points from cam1 space to cam2 space.
    rotationMatrix, translationMatrix = computeExtrinsicsFromViconCamObject(viconCam2Object,viconCam1Object)
    # Here we want points triangulated in camera space of cam 1, therefore
    # The problem is written as p_img1 = [I|0].P ; p_img2 = [R|T].P , where R|T are extrinsics which convert point from Cam1 Space to Cam2 space
    # Projection matrix converts points from their respective systems to image space
    projectionMatrixCam1 = image1Object.projectionMatrix(np.identity(3),np.zeros((3,1)))
    projectionMatrixCam2 = image2Object.projectionMatrix(rotationMatrix,translationMatrix)


    # Traingulate as per convention of opencv
    pointMat1  = np.matrix(img1Points).T
    pointMat2 = np.matrix(img2Points).T
    trinagulatedPointsHomogenous = cv.triangulatePoints(projectionMatrixCam1,projectionMatrixCam2,np.float32(pointMat1),np.float32(pointMat2))
    triangulatedPointsArray = cv.convertPointsFromHomogeneous(trinagulatedPointsHomogenous.T)
    triangulatedPointsMatrix = np.matrix(triangulatedPointsArray)


    return triangulatedPointsMatrix.tolist()


def unitTest():
    # FYI : Inverted angles as stored in the file
    rotationCam1 = [-0.79697172135980876, 0.009835241003934278, 0.056076936965809787, 0.60132746530298287]
    translationCam1 = [-701.064504485933, -6173.2248621199, 1830.24808693825]

    rotationCam2 = [-0.81076800905996049, 0.054559504141392628, 0.0021970336343607915, 0.5828152958150663]
    translationCam2 = [850.291199882066, -6140.97372597712, 1799.50732862305]

    viconCam1Object = objectVicon.ObjectVicon(rotationCam1, translationCam1)
    viconCam2Object = objectVicon.ObjectVicon(rotationCam2, translationCam2)


    cam1Points = {"pt1": [1415.76135949, - 570.12878565, 7724.00698054],
                  "pt2": [1427.61481598, - 588.07764951, 7708.65018457]}#,
                #  "pt3":[1433.03420332, - 579.43874105, 7728.08209005],
                # "pt4":[1439.77318296, - 598.69765411, 7698.82965911]}

    viconCam1Object.setFeatures(cam1Points)

    cam2Points = {"pt1": [-1234.85662192, - 766.81522397, 7683.50233825],
                  "pt2": [-1221.04911448, - 784.27677376, 7669.25648468]}#,
                  # "pt3": [-1218.38418345, - 776.46947527, 7689.59225813],
                  # "pt4":[-1207.68252667, - 794.63670145, 7660.8268148] }

    viconCam2Object.setFeatures(cam2Points)

    # Check if the points can be transferred from one space to another
    rotationMatrix, translationMatrix = computeExtrinsicsFromViconCamObject(viconCam1Object, viconCam2Object)

    cam2PointsMatrix = np.matrix(list(cam2Points.values()))
    computedCam1Points = tf.transformPoints(cam2PointsMatrix.T, rotationMatrix, translationMatrix)
    print(computedCam1Points.T)
    cam1PointsMatrix = np.matrix(list(cam1Points.values()))
    computedCam2Points = tf.invertPoints(cam1PointsMatrix.T, np.linalg.inv(rotationMatrix), translationMatrix)
    print(computedCam2Points.T)

    # Compute distortion and camera intrinsics
    distortionCam1 = np.array([[4.25332001e-08, - 1.08721554e-14, 8.49506484e-21, 0.00000000e+00,  0.00000000e+00]])
    instrinsicMatCam1 = np.array([[2.64432999e+03, 0.00000000e+00, 9.03959271e+02],
                                  [0.00000000e+00, 2.64432999e+03, 5.47311174e+02],
                                  [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
    image1Object = imageVicon.ImageVicon(0, np.matrix(distortionCam1), np.matrix(instrinsicMatCam1))
    intrinsicMatCam2 = np.array([[2.65038182e+03, 0.00000000e+00, 9.42225603e+02],
                                 [0.00000000e+00, 2.65038182e+03, 5.61402414e+02],
                                 [0.00000000e+00, 0.00000000e+00, 1.00000000e+00]])
    distortionCam2 = np.array([[3.33683465e-08, 1.19327826e-15, 2.94259160e-21, 0.00000000e+00,  0.00000000e+00]])
    image2Object = imageVicon.ImageVicon(1, np.matrix(distortionCam2), np.matrix(intrinsicMatCam2))

    img1Points = image1Object.projectFeaturesFromCamSpaceToImageSpace(cam1Points)
    img2Points = image2Object.projectFeaturesFromCamSpaceToImageSpace(cam2Points)

    image1Object.setFeatures(img1Points)
    image2Object.setFeatures(img2Points)

    triangulatorObject = StereoTrinagulator([viconCam1Object,viconCam2Object],[image1Object,image2Object])
    triangulatedPoints = triangulatorObject.getTriangulatedPoints()# triangulatePoints(image1Object, viconCam1Object, image2Object, viconCam2Object)
    print("Triangulated Points", triangulatedPoints)


    # Testing the filter function for the traingulation and filtering
    t1 = {"s1" : [0,0], "s2" : [0,0], "s3" : [10,20], "s4" : [11,26], "s5" : [33,34], "s7" : [1,1]}
    t2 = {"s1": [0, 0], "s2": [0, 0], "s3": [10, 20], "s8": [11, 26], "s4": [33, 34]}
    filter, filter2 = triangulatorObject.filterPoints(t1,t2)
    print(filter,filter2)


if __name__ == "__main__":

    unitTest()
