import random
import time

from PyQt5.QtCore import pyqtSignal, pyqtSlot, QObject

import piveilance.generators
import piveilance.generators
from piveilance.cameras import PlaceholderCamera, parseCameraType
from piveilance.layout import WindowGeometry, Layout, View
from piveilance.util import *


class LayoutManager(QObject):
    setCamOptions = pyqtSignal(object)

    def __init__(self, widget, grid, config):
        super(LayoutManager, self).__init__()

        self.camIds = []
        self.start = time.time()
        self.widget = widget
        self.grid = grid


        self.globalConfig = config
        layout_id = config['configuration']['layout']
        generator_id = config['configuration']['generator']
        view_id = config['configuration']['view']

        self.setLayout(layout_id)
        self.setGenerator(generator_id)
        self.setView(view_id)



        print()

      # self.maxCams = max(int(self.layoutConfig.get('max_allowed', 0)), 0)
     #   self.setLayoutSyle(parseLayout(self.layoutConfig.get('style', 'flow')))
        #self.camConfig = camConfig
        #self.layoutConfig = layoutConfig
      #  self.refresh = layoutConfig.get_float('list_refresh', 10)
      #  self.maxCams = max(layoutConfig.get_int('max_allowed', 0), 0)
      #  self.generatorType = getattr(piveilance.generators, self.camConfig.get('type', 'PiCamGenerator'))
    #    self.setLayout(parseLayout(layoutConfig.get('style', 'flow')))
    #     self.generator = self.generatorType(self.camConfig)
    #     self.generator.updateCameras.connect(self.recieveData)
    #     self.generator.start()



    @pyqtSlot(name="resize")
    def resizeEventHandler(self, triggerRedraw=False):
        self.arrange(triggerRedraw)

    @pyqtSlot(object, name="data")
    def recieveData(self, data, triggerRedraw=False):

        if (not self.camIds or time.time() - self.start > self.generator.listRefresh):
            newCams = list(data.keys())
            if newCams and not compareIter(newCams, self.camIds):
                triggerRedraw = True
            self.camIds = newCams
            self.start = time.time()
            random.shuffle(self.camIds)
            if triggerRedraw:
                self.arrange(True)

    def arrange(self, triggerRedraw=False):
        if not self.camIds:
            return

        preCols = WindowGeometry.cols
        self.updateWindowGeometry()

        if triggerRedraw or WindowGeometry.cols != preCols:
            c = {n: self.generator.createCamera(n) for n in self.camIds}
            self.camObj = self.layout.style.buildLayout(c, self.getPlaceholder)
            self.clearLayout()

            for n, c in self.camObj.items():
                self.grid.addWidget(c, *c.position)
                self.grid.addWidget(c.label, *c.position)

              #  self.setCamOptions.connect(c.setOptions)

        for c in self.camObj.values():
            c.size = WindowGeometry.frameSize
            c.setFrameSize()

       # self.setCamOptions.emit(self.globalConfig['cameras'])

    def getPlaceholder(self, name, position=None):
        return PlaceholderCamera(name, position, self.camConfig)

    def clearLayout(self):
        for i in reversed(range(self.grid.count())):
            self.grid.takeAt(i).widget().deleteLater()

    def setLayout(self, layoutId):
        self.layout = self.getLayout(layoutId)

    def setLayoutSyle(self, layoutStyle):
        self.layout.style = layoutStyle

    def setView(self, viewId):
        self.view = self.getView(viewId)

    def setGenerator(self, generatorId):
        self.generator = self.getGenerator(generatorId)
        self.generator.updateCameras.connect(self.recieveData)
        self.generator.start()

    def setContentMargin(self, margins):
        m = margins if not self.view.stretch else (0, 0, 0, 0)
        self.grid.setContentsMargins(*m)

    def updateWindowGeometry(self):
        maxCams = self.layout.maxAllowed
        n = maxCams if maxCams else len(self.camIds)
        w = self.widget.frameGeometry().width()
        h = self.widget.frameGeometry().height()
        WindowGeometry.update(width=w, height=h, numCams=n)
        WindowGeometry.update(**self.layout.calculate(w, h, n))
        WindowGeometry.calculateAllProperties()
       # self.camConfig['size'] = WindowGeometry.frameSize
        self.setContentMargin(WindowGeometry.margins)

    def getLayout(self, layoutId):
        newLayout = self.globalConfig['layouts'].get(layoutId)
        if not newLayout:
            raise ValueError("No layout found for id: '{}'".format(layoutId))
        newLayout['styleName'] = newLayout.pop('style_name', None)
        newLayout['maxAllowed'] = newLayout.pop('max_allowed', None)
        return Layout(**newLayout)

    def getView(self, viewId):
        view = self.globalConfig['views'].get(viewId)
        if not view:
            raise ValueError("No view found for id: '{}'".format(viewId))
        view['fontRatio'] = view.pop('font_ratio', None)
        return View(**view)

    def getGenerator(self, generatorId):

        generatorConfig = self.globalConfig['generators'].get(generatorId)
        if not generatorConfig:
            raise ValueError("No generator found for id: '{}'".format(generatorId))

        generatorConfig['dataUrl'] = generatorConfig.pop('data_url', None)
        generatorConfig['updateInterval'] = generatorConfig.pop('update_interval', None)
        generatorConfig['listRefresh'] = generatorConfig.pop('list_refresh', None)
        generatorConfig['cameraRepo'] = self.globalConfig['cameras']

        try:
            generatorType = getattr(piveilance.generators, generatorConfig['type'])
        except KeyError:
            raise ValueError("Missing generator type - this field is required")
        except AttributeError:
            raise ValueError("Invalid generator type specified: '{}'.  "
                             "Allowed are [PiCamGenerator]".format(generatorConfig['type']))
        return generatorType(**generatorConfig)

