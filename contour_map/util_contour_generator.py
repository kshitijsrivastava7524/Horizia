"""
Model exported as python.
Name : Contour Generator
Group : 
With QGIS : 34404
"""

from typing import Any, Optional

from qgis.core import QgsProcessing
from qgis.core import QgsProcessingAlgorithm
from qgis.core import QgsProcessingContext
from qgis.core import QgsProcessingFeedback, QgsProcessingMultiStepFeedback
from qgis.core import QgsProcessingParameterRasterLayer
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterVectorDestination
from qgis import processing


class ContourGenerator(QgsProcessingAlgorithm):

    def initAlgorithm(self, config: Optional[dict[str, Any]] = None):
        self.addParameter(QgsProcessingParameterRasterLayer('input_dem', 'Input DEM', defaultValue=None))
        self.addParameter(QgsProcessingParameterNumber('contour_interval', 'Contour Interval', type=QgsProcessingParameterNumber.Double, defaultValue=100))
        self.addParameter(QgsProcessingParameterVectorDestination('Contour_result', 'contour_result', type=QgsProcessing.TypeVectorLine, createByDefault=True, defaultValue=None))

    def processAlgorithm(self, parameters: dict[str, Any], context: QgsProcessingContext, model_feedback: QgsProcessingFeedback) -> dict[str, Any]:
        # Use a multi-step feedback, so that individual child algorithm progress reports are adjusted for the
        # overall progress through the model
        feedback = QgsProcessingMultiStepFeedback(1, model_feedback)
        results = {}
        outputs = {}

        # Contour
        alg_params = {
            'BAND': 1,
            'CREATE_3D': False,
            'EXTRA': '',
            'FIELD_NAME': 'ELEV',
            'IGNORE_NODATA': False,
            'INPUT': parameters['input_dem'],
            'INTERVAL': parameters['contour_interval'],
            'NODATA': None,
            'OFFSET': 0,
            'OUTPUT': parameters['Contour_result']
        }
        outputs['Contour'] = processing.run('gdal:contour', alg_params, context=context, feedback=feedback, is_child_algorithm=True)
        results['Contour_result'] = outputs['Contour']['OUTPUT']
        return results

    def name(self) -> str:
        return 'Contour Generator'

    def displayName(self) -> str:
        return 'Contour Generator'

    def group(self) -> str:
        return ''

    def groupId(self) -> str:
        return ''

    def createInstance(self):
        return self.__class__()
