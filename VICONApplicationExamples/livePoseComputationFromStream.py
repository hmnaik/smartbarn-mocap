"""
 Example code: Closed loop application
 The file is designed show an example of how to read the vicon datastream and compute the pose of the object from the 3D position of markers,
 The script also compares the pose with the results computed by the tracker software.
 Use case : The script is useful to learn how to computer pose of pattern from marker positions and error.
 A valid comparioson with vicon pose is possible. If the object is defined well it should result in similar results both in vicon and custom pose compuration.
 Vicon does do some additional tricks and optimizations that we do not know and pose may differ. However, on good datasets it should not differ a lot.
"""

from vicon_dssdk import ViconDataStream
from VICONMath import absoluteOrientation
from VICONFileOperations import rwOperations
import numpy as np
from VICONMath import transformations

def main(**kwargs):
    #call for the vicon client
    client = ViconDataStream.Client()
    print('Connecting')
    while not client.IsConnected():
        print('.')
        if kwargs and kwargs['IP']:
            remoteAddress = kwargs['IP']
            client.Connect(remoteAddress + ':801')
        else:
            client.Connect('localhost:801')

    #To control stream reading
    i = 0

    #Read marker positions
    subjectPath = kwargs['path']
    subjectNames = kwargs['subjects']

    markerPositionsinSubjectFrameDict = {}
    for subject in subjectNames:
        markerPositionsArray = rwOperations.readFeaturePointsFromViconFileAsArray(path=subjectPath + "{}.mp".format(subject))
        markerPositionsinSubjectFrameDict[subject] = markerPositionsArray

    try:
        while client.IsConnected() and i < 10:

            rotation_matrix_vicon = 0
            translation_vicon = 0
            #Enable required readout
            client.EnableMarkerData()
            client.EnableSegmentData()


            if client.GetFrame():
                # Get the frame data
                #client.ClearSubjectFilter()
                #client.AddToSubjectFilter('object1')
                #client.GetFrame()
                # Part 1 - Set reading configuration
                frame = client.GetFrameNumber()
                subjects = client.GetSubjectNames()
                print('Frame: {}, Subjects: {} '.format(frame,subjects))
                for subject in subjects:
                    print("Subject for pose : {}".format(subject))
                    segments = client.GetSegmentNames(subject)
                    for segment in segments:
                        """
                        Important: Note that the R/t is not streamed with Nexus, It is only streamed with Tracker 
                        """
                        rotation_quat, occlusion = client.GetSegmentGlobalRotationQuaternion(subject, segment)
                        translation_vicon, occlusion = client.GetSegmentGlobalTranslation(subject, segment)

                        if occlusion is True:
                            print("The subject is occluded or it is filtered by the stream reader.")

                        # rotation_euler, occlusion = client.GetSegmentGlobalRotationEulerXYZ(subject, segment)
                        translation_vicon = np.array(translation_vicon)# tuple to array conversion
                        translation_vicon = translation_vicon.reshape(3,1)
                        rotation_quat_list = list(rotation_quat)
                        print("Rotation: {} , Translations: {} ".format(rotation_quat, translation_vicon))
                        #Convert the list to a matrix
                        rotation_matrix_vicon = transformations.quaternionViconListToMatrix(rotation_quat_list)

                    """Printing quality of the pose according to the VICON computation"""
                    try:
                        print('Object Quality: ', client.GetObjectQuality(subject))  # ONLY for Tracker
                    except ViconDataStream.DataStreamException as e:
                        print('Not present', e)

                    """
                    Important: Not that marker names are in sequence and useful for computer R/t without the help of 
                    the Nexus or tracker, could be useful when Nexus is used for streaming. 
                    """
                    markerNames = client.GetMarkerNames(subject)
                    markerPositions = []
                    for markerName, parentSegment in markerNames:
                        point, occlusion = client.GetMarkerGlobalTranslation(subject, markerName)
                        # print("{}:{}".format(markerName,point))
                        markerPositions.append(point)

                    # Computing rotation translation of the object with custom code
                    markerPositionsInViconFrame = np.array(markerPositions)
                    if markerPositionsInViconFrame.shape == (4, 3):
                        markerPositionsInViconFrame = markerPositionsInViconFrame.T

                    try:
                        markerPositionsInSubjectFrame = markerPositionsinSubjectFrameDict[subject]
                    except ValueError:
                        print("The subject names do not match with the stream")

                    # Computing Error using transformation computed with VICON
                    transformedMarkerPositionsInViconFrame = transformations.transformPoints(markerPositionsInSubjectFrame, rotation_matrix_vicon, translation_vicon)
                    error = transformations.rmsError(transformedMarkerPositionsInViconFrame,markerPositionsInViconFrame)
                    print("Vicon Error:{}, Vicon Points:{} ".format(error, transformedMarkerPositionsInViconFrame.T))

                    "If the quality of the object is not good, the 6-DOF pose is optimized by vicon based on unknown factors," \
                    "this improves the pose but if we computer 6-DOF pose using 3D points in the stream and the points in the .mp file." \
                    "they are different. This means pose is computed not using the 3D points but using some other factor."

                    # Computing error with Rotation and translation parameters computed using point positions
                    rot,trans = absoluteOrientation.findPoseFromPoints(markerPositionsInSubjectFrame, markerPositionsInViconFrame)
                    transformedMarkerPoisitionsInViconFrame = transformations.transformPoints(markerPositionsInSubjectFrame,rot,trans)
                    error_custom = transformations.rmsError(transformedMarkerPoisitionsInViconFrame,
                                                     markerPositionsInViconFrame)
                    quat = transformations.rotMatrixToQuat(rot)
                    print("Rot: {}, quatertiona:{}, trans:{}".format(rot, quat, trans))
                    print("Custom Error:{}, Custom Points:{} ".format( error_custom, transformedMarkerPoisitionsInViconFrame.T))

                i+=1

    except ViconDataStream.DataStreamException as e:
        print('Error', e)

    print('client disconnected')
    client.Disconnect()


if __name__ == '__main__':
    # Send the
    testDataPath = "..\\VICONTestData\\"
    subjectList = ["cat"] #'["object1","object2"]
    main(IP = '10.0.21.11', path = testDataPath, subjects = subjectList )
    #main()

