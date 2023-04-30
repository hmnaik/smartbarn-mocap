""""
The file is created to start your own annotation sequence for computing 3D position of custom features.
The code follows following 3 steps.
1. First selection of frames for annotation (Implemented in AnnotationFrameSelector.Py)
2. Opens annotating tool to capture 2D positions
3. 2D positions from different images are triangulated and 3D positions w.r.t corresponding 6-DOF pattern  are saved in separate file.
"""

from VICONSystem import videoVicon
from VICONDrawingOperations import imageAnnotation
from VICONApplicationExamples import createFeaturesUsingAnnotation
from VICONFileOperations import settingsGenerator

def main(settingFile):

    # Settings generator to create settings file if not available or read settings file
    projectSettings = settingsGenerator.xmlSettingsParser(settingFile)
    settings = projectSettings.settingsDict

    # Select the frames for annotation ( without projection of the markers on the image) --
    # todo : Add the implementation from annotationFrameSelector
    videoVicon.defineVideoFramesForAnnotation(settings)

    #Invoke the annotation tool, allows annotation of features based on the custom features file defined in the settings file.
    annotationToolObject = imageAnnotation.imageAnnotationTool(settings)
    annotationToolObject.run()

    # Triangulate the feature created using the provided annotation and show projection on the image to accept or reject the
    # annotation. The back projection must align with the features in both the images.
    createFeaturesUsingAnnotation.createTriangulatedFeatures(projectSettings)

if __name__ == "__main__":
    defaultSettingFile = "D:\\BirdTrackingProject\\20190620_PigeonPostureDataset4\\settings_session07.xml"
    main(defaultSettingFile)