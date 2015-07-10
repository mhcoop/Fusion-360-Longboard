#Author-Autodesk Inc
#Description-Create basic longboard shape
#Based on Bolt.py
#Edited by Myles Cooper on 7.7.2015

import adsk.core, adsk.fusion, traceback
import math

defaultBoardName = 'Board'
defaultCamber = 0
defaultWheelbase = 71.12
defaultKickLength = 10.16
defaultKickAngle = math.pi/12


# global set of event handlers to keep them referenced for the duration of the command
handlers = []
app = adsk.core.Application.get()
if app:
    ui = app.userInterface

newComp = None

def createNewComponent():
    # Get the active design.
    product = app.activeProduct
    design = adsk.fusion.Design.cast(product)
    rootComp = design.rootComponent
    allOccs = rootComp.occurrences
    newOcc = allOccs.addNewComponent(adsk.core.Matrix3D.create())
    return newOcc.component

class BoardCommandExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            unitsMgr = app.activeProduct.unitsManager
            command = args.firingEvent.sender
            inputs = command.commandInputs

            board = Board()
            for input in inputs:
                if input.id == 'boardName':
                    board.boardName = input.value
                elif input.id == 'camber':
                    board.camber = input.valueOne
                elif input.id == 'wheelbase':
                    board.wheelbase = input.valueOne
                elif input.id == 'kickLength':
                    board.kickLength = input.valueOne
                elif input.id == 'kickAngle':
                    board.kickAngle = input.valueOne                    
               
            board.buildBoard();
            args.isValidResult = True

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class BoardCommandDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        try:
            # when the command is done, terminate the script
            # this will release all globals which will remove all event handlers
            adsk.terminate()
        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class BoardCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):    
    def __init__(self):
        super().__init__()        
    def notify(self, args):
        try:
            cmd = args.command
            onExecute = BoardCommandExecuteHandler()
            cmd.execute.add(onExecute)
            onExecutePreview = BoardCommandExecuteHandler()
            cmd.executePreview.add(onExecutePreview)
            onDestroy = BoardCommandDestroyHandler()
            cmd.destroy.add(onDestroy)
            # keep the handler referenced beyond this function
            handlers.append(onExecute)
            handlers.append(onExecutePreview)
            handlers.append(onDestroy)

            #allow correct display units on sliders by redefining unitsMgr
            unitsMgr = app.activeProduct.unitsManager
            lengthUnits = unitsMgr.defaultLengthUnits
            
            #define the inputs
            inputs = cmd.commandInputs
            inputs.addStringValueInput('boardName', 'Board Name', defaultBoardName)
            inputs.addFloatSliderCommandInput('camber', 'Camber',lengthUnits,-1.27,1.27)#-.5 - .5"
            inputs.addFloatSliderCommandInput('wheelbase','Wheelbase',lengthUnits,50.8,91.44)#20 - 36"
            inputs.addFloatSliderCommandInput('kickLength','Kicktail Length',lengthUnits,0,20.32)#0 - 8"
            inputs.addFloatSliderCommandInput('kickAngle','Kicktail Angle','deg',0,math.pi/6)

        except:
            if ui:
                ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

class Board:
    def __init__(self):
        self._boardName = defaultBoardName
        self._camber = defaultCamber
        self._wheelbase = defaultWheelbase
        self._kickLength = defaultKickLength
        self._kickAngle = defaultKickAngle
       
    #properties
    @property
    def boardName(self):
        return self._boardName
    @boardName.setter
    def boardName(self, value):
        self._boardName = value

    @property
    def camber(self):
        return self._camber
    @camber.setter
    def camber(self, value):
        self._camber = value
        
    @property
    def wheelbase(self):
        return self._wheelbase
    @wheelbase.setter
    def wheelbase(self, value):
        self._wheelbase = value
        
    @property
    def kickLength(self):
        return self._kickLength
    @kickLength.setter
    def kickLength(self, value):
        self._kickLength = value
        
    @property
    def kickAngle(self):
        return self._kickAngle
    @kickAngle.setter
    def kickAngle(self, value):
        self._kickAngle = value

    def buildBoard(self):
        global newComp
        newComp = createNewComponent()
        if newComp is None:
            ui.messageBox('New component failed to create', 'New Component Failed')
            return

        # Create a new sketch.
        sketches = newComp.sketches
        xyPlane = newComp.xYConstructionPlane
        sketch = sketches.add(xyPlane)
        truckMountLength = 12.7 #5". flat length given for truck mounts
        
        #Define centerline & origin
        origin = adsk.core.Point3D.create(0,0,0)
        originPoint = sketch.sketchPoints.add(origin)
        centerLine = sketch.sketchCurves.sketchLines.addByTwoPoints(adsk.core.Point3D.create(0,2.54,0),origin)
        centerLine.isConstruction = True
        centerLine.isFixed = True
        
        #define landmark points for sketch geometry
        baseEdgeL = adsk.core.Point3D.create(-(self.wheelbase-(truckMountLength/2))/2,0,0)
        baseEdgeLPt = sketch.sketchPoints.add(baseEdgeL)        
        baseEdgeR = adsk.core.Point3D.create((self.wheelbase-(truckMountLength/2))/2,0,0)
        baseEdgeRPt = sketch.sketchPoints.add(baseEdgeR)
        camberPt = adsk.core.Point3D.create(0,self.camber,0)
        camberPoint = sketch.sketchPoints.add(camberPt)
        kickEdgeL = adsk.core.Point3D.create(-(self.wheelbase+(truckMountLength*1.5))/2,0,0)
        kickEdgeR = adsk.core.Point3D.create((self.wheelbase+(truckMountLength*1.5))/2,0,0)
        tipL = adsk.core.Point3D.create(kickEdgeL.x-self.kickLength*math.cos(self.kickAngle),self.kickLength*math.sin(self.kickAngle),0)        
        tipR = adsk.core.Point3D.create(kickEdgeR.x+self.kickLength*math.cos(self.kickAngle),self.kickLength*math.sin(self.kickAngle),0)

        #create sketch geometry, all lines created left->right
        if self.camber == 0: #board base and right truck mount
            boardBase = sketch.sketchCurves.sketchLines.addByTwoPoints(baseEdgeL,baseEdgeR)
        else:
            boardBase = sketch.sketchCurves.sketchArcs.addByThreePoints(baseEdgeL,camberPt,baseEdgeR)     
        kickTailL = sketch.sketchCurves.sketchLines.addByTwoPoints(tipL,kickEdgeL)#left kicktail
        kickTailR = sketch.sketchCurves.sketchLines.addByTwoPoints(kickEdgeR,tipR)#right kicktail
        truckMountL = sketch.sketchCurves.sketchLines.addByTwoPoints(kickEdgeL,baseEdgeL)#left truck mount
        truckMountR = sketch.sketchCurves.sketchLines.addByTwoPoints(baseEdgeR,kickEdgeR)#right truck mount      

        #Deleting kickTails if unused.
        if kickTailL.length == 0:
            kickTailL.deleteMe()
            kickTailR.deleteMe()
            
        #adding constraints to geometry
        originPoint.isfixed = True
        sketch.geometricConstraints.addCoincident(camberPoint,centerLine)
        sketch.geometricConstraints.addMidPoint(camberPoint,boardBase)
        sketch.geometricConstraints.addHorizontal(truckMountL)
        sketch.geometricConstraints.addSymmetry(truckMountL,truckMountR,centerLine)
        if kickTailL.isValid == True:        
            sketch.geometricConstraints.addSymmetry(kickTailL,kickTailR,centerLine)
            sketch.geometricConstraints.addCoincident(kickTailL.endSketchPoint,truckMountL.startSketchPoint)
        sketch.geometricConstraints.addCoincident(truckMountL.endSketchPoint,baseEdgeLPt) 
        sketch.geometricConstraints.addCoincident(truckMountR.startSketchPoint,baseEdgeRPt) 
        if self.camber > 0:
            sketch.geometricConstraints.addCoincident(baseEdgeLPt,boardBase.endSketchPoint)
            sketch.geometricConstraints.addCoincident(baseEdgeRPt,boardBase.startSketchPoint)
        else:
            sketch.geometricConstraints.addCoincident(baseEdgeLPt,boardBase.startSketchPoint)
            sketch.geometricConstraints.addCoincident(baseEdgeRPt,boardBase.endSketchPoint)

        #Surface extrude [from "Stitch" example code]
        features = newComp.features
        extrudeFeatures = features.extrudeFeatures
        opencurves = adsk.core.ObjectCollection.create()
        if kickTailL.isValid == True:
            opencurves.add(kickTailL)
        opencurves.add(truckMountL)
        opencurves.add(boardBase)
        opencurves.add(truckMountR)
        if kickTailR.isValid == True:
            opencurves.add(kickTailR)

        openProfile = newComp.createOpenProfile(opencurves,True)
        extrudeFeatureInput = extrudeFeatures.createInput(openProfile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation)
        extrudeFeatureInput.isSolid = False
        extrudeFeatureInput.setDistanceExtent(True, adsk.core.ValueInput.createByReal(15.24))#6" symmetric
        extrudeFeature = extrudeFeatures.add(extrudeFeatureInput)

        #from "Bolt" example code
        bd = extrudeFeature.bodies
        bd.name = self.boardName

def main():
    try:
        commandDefinitions = ui.commandDefinitions
        #check the command exists or not
        cmdDef = commandDefinitions.itemById('Board')
        if not cmdDef:
            cmdDef = commandDefinitions.addButtonDefinition('Board',
                    'Create Longboard',
                    'Create a longboard deck.') # relative resource file path is specified

        onCommandCreated = BoardCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        # keep the handler referenced beyond this function
        handlers.append(onCommandCreated)
        inputs = adsk.core.NamedValues.create()
        cmdDef.execute(inputs)
        

        # prevent this module from being terminate when the script returns, because we are waiting for event handlers to fire
        adsk.autoTerminate(False)
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
main()
