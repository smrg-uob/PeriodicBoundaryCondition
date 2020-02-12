from abaqusConstants import *
from abaqusGui import *
from kernelAccess import mdb, session
import os

thisPath = os.path.abspath(__file__)
thisDir = os.path.dirname(thisPath)

# Code for the plugin GUI
class PeriodicBoundaryCondition_DB(AFXDataDialog):
    # id values, useful for commands between widgets
    [
        ID_MODEL,
        ID_PART,
        ID_MASTER,
        ID_SLAVE
    ] = range(AFXToolsetGui.ID_LAST, AFXToolsetGui.ID_LAST+4)

    # constructor
    def __init__(self, form):
        # Call super constructor
        AFXDataDialog.__init__(self, form, 'Periodic Boundary Condition', self.OK | self.CANCEL, DIALOG_ACTIONS_SEPARATOR)
        # Configure the Apply button
        okBtn = self.getActionButton(self.ID_CLICKED_OK)
        okBtn.disable()
        okBtn.setText('Apply')
        # Add combo box to select the model
        mdls = mdb.models.keys()
        self.cbx_model = AFXComboBox(p=self, ncols=0, nvis=len(mdls), text='Select Model', tgt=form.kw_model, sel=0)
        index = 0
        for mdl in mdls:
            self.cbx_model.appendItem(text=mdl, sel=index)
            index = index + 1
        # Add combo box to select the part
        self.cbx_part = AFXComboBox(p=self, ncols=0, nvis=0, text='Select Part', tgt=form.kw_part, sel=0)
        self.cbx_part.disable()
        # Set currently selected part and model to -1 (to force an update on first opening of the GUI)
        self.currentModel = -1
        self.currentPart = -1
        # Add combo boxes to select the master and slave surfaces, but set them as disabled by default
        # TODO: find some way to select these surfaces from the viewport and highlight them
        self.cbx_master = AFXComboBox(p=self, ncols=0, nvis=0, text='Master Surface', tgt=form.kw_master, sel=0)
        self.cbx_slave = AFXComboBox(p=self, ncols=0, nvis=0, text='Slave Surface', tgt=form.kw_slave, sel=0)
        self.cbx_master.disable()
        self.cbx_slave.disable()
        # Add text field for the name
        self.txt_name = AFXTextField(p=self, ncols=16, labelText='PBC Name', tgt=form.kw_name, sel=0)
        # Add combo box to select the plane
        self.cbx_plane = AFXComboBox(p=self, ncols=0, nvis=3, text='Match Plane', tgt=form.kw_plane, sel=0)
        self.cbx_plane.appendItem(text='XY-plane', sel=0)
        self.cbx_plane.appendItem(text='XZ-plane', sel=1)
        self.cbx_plane.appendItem(text='YZ-plane', sel=2)
        # Add combo box to select the symmetry
        self.cbx_symm = AFXComboBox(p=self, ncols=0, nvis=3, text='Symmetry', tgt=form.kw_symm, sel=0)
        self.cbx_symm.appendItem(text='Asymmetric', sel=0)
        self.cbx_symm.appendItem(text='Symmetric', sel=1)
        self.cbx_symm.appendItem(text='Ignore', sel=2)
        # Define command map
        FXMAPFUNC(self, SEL_COMMAND, self.ID_MODEL, PeriodicBoundaryCondition_DB.onModelSelected)
        FXMAPFUNC(self, SEL_COMMAND, self.ID_PART, PeriodicBoundaryCondition_DB.onPartSelected)
        FXMAPFUNC(self, SEL_COMMAND, self.ID_MASTER, PeriodicBoundaryCondition_DB.onMasterSelected)
        FXMAPFUNC(self, SEL_COMMAND, self.ID_SLAVE, PeriodicBoundaryCondition_DB.onSlaveSelected)
        # Add transitions
        self.addTransition(form.kw_model, AFXTransition.GE, 0, self, MKUINT(self.ID_MODEL, SEL_COMMAND), None)
        self.addTransition(form.kw_part, AFXTransition.GE, 0, self, MKUINT(self.ID_PART, SEL_COMMAND), None)
        self.addTransition(form.kw_master, AFXTransition.GE, 0, self, MKUINT(self.ID_MASTER, SEL_COMMAND), None)
        self.addTransition(form.kw_slave, AFXTransition.GE, 0, self, MKUINT(self.ID_SLAVE, SEL_COMMAND), None)

    def onModelSelected(self, sender, sel, ptr):
        model = self.cbx_model.getItemData(self.cbx_model.getCurrentItem())
        # If a different model has been selected, the GUI needs to be updated
        if model != self.currentModel:
            # Update the selected model
            self.currentModel = model
            # Fetch the parts for the model
            models = mdb.models.keys()
            parts = mdb.models[models[model]].parts.keys()
            # Update the parts combo box
            self.cbx_part.clearItems()
            if len(parts) > 0:
                index = 0
                for part in parts:
                    self.cbx_part.appendItem(text=part, sel=index)
                    index = index + 1
                self.cbx_part.setMaxVisible(len(parts))
                self.cbx_part.enable()
            else:
                self.cbx_part.setMaxVisible(0)
                self.cbx_part.disable()
            # Check and update the action button
            self.updateActionButtonState()


    def onPartSelected(self, sender, sel, ptr):
        part = self.cbx_part.getItemData(self.cbx_part.getCurrentItem())
        # If a different part has been selected, the GUI needs to be updated
        if part != self.currentPart:
            # Update the selected part
            self.currentPart = part
            # Fetch the surfaces for the part
            models = mdb.models.keys()
            model = self.cbx_model.getItemData(self.cbx_model.getCurrentItem())
            parts = mdb.models[models[model]].parts.keys()
            surfs = mdb.models[models[model]].parts[parts[part]].surfaces.keys()
            # Update the master and slave combo boxes
            self.cbx_master.clearItems()
            self.cbx_slave.clearItems()
            if len(surfs) > 0:
                # Add the part's surfaces and enable the widgets if the part has defined surfaces
                index = 0
                for surf in surfs:
                    self.cbx_master.appendItem(surf, index)
                    self.cbx_slave.appendItem(surf, index)
                    index = index + 1
                self.cbx_master.setMaxVisible(len(surfs))
                self.cbx_slave.setMaxVisible(len(surfs))
                self.cbx_master.enable()
                self.cbx_slave.enable()
            else:
                # Disable the widgets if the part has no defined surfacess
                self.cbx_master.setMaxVisible(0)
                self.cbx_slave.setMaxVisible(0)
                self.cbx_master.disable()
                self.cbx_slave.disable()
            # Check and update the action button
            self.updateActionButtonState()

    def onMasterSelected(self, sender, sel, ptr):
        # Check and update the action button
        self.updateActionButtonState()

    def onSlaveSelected(self, sender, sel, ptr):
        # Check and update the action button
        self.updateActionButtonState()

    def updateActionButtonState(self):
        m = self.cbx_master.getNumItems()
        s = self.cbx_slave.getNumItems()
        okBtn = self.getActionButton(self.ID_CLICKED_OK)
        name = self.txt_name.getText()
        if (name) and (m > 0 and s > 0):
            master = self.cbx_master.getItemData(self.cbx_master.getCurrentItem())
            slave = self.cbx_slave.getItemData(self.cbx_slave.getCurrentItem())
            if master == slave:
                okBtn.disable()
            else:
                okBtn.enable()
        else:
            okBtn.disable()

def debugMessage(msg):
    getAFXApp().getAFXMainWindow().writeToMessageArea(msg)