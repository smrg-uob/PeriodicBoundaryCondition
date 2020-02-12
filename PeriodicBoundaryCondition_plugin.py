from abaqusGui import *
from abaqusConstants import ALL
import os, osutils

class PeriodicBoundaryCondition_plugin(AFXForm):
    def __init__(self, owner):
        # Construct the parent class.
        AFXForm.__init__(self, owner)
        # Command for OK button press
        self.cmd = AFXGuiCommand(mode=self, method='runScript', objectName='PeriodicBoundaryCondition_kernel')
        # Define keywords
        self.kw_model = AFXIntKeyword(self.cmd, 'kw_model', True, 0, False)
        self.kw_part = AFXIntKeyword(self.cmd, 'kw_part', True, 0, False)
        self.kw_master = AFXIntKeyword(self.cmd, 'kw_master', True, 0, False)
        self.kw_slave = AFXIntKeyword(self.cmd, 'kw_slave', True, 0, False)
        self.kw_name = AFXStringKeyword(self.cmd, 'kw_name', True, '')
        self.kw_plane = AFXIntKeyword(self.cmd, 'kw_plane', True, 0, False)
        self.kw_symm = AFXIntKeyword(self.cmd, 'kw_symm', True, 0, False)

    def getFirstDialog(self):
        # Reload the code for the dialog
        import PeriodicBoundaryCondition_DB
        reload(PeriodicBoundaryCondition_DB)
        # Show dialog window
        return PeriodicBoundaryCondition_DB.PeriodicBoundaryCondition_DB(self)

    def doCustomChecks(self):
        return True

    def okToCancel(self):
        # Method override, no need to cancel during context changes
        return False


# Register the plug-in
thisPath = os.path.abspath(__file__)
thisDir = os.path.dirname(thisPath)
toolset = getAFXApp().getAFXMainWindow().getPluginToolset()
toolset.registerGuiMenuButton(
    buttonText='Periodic Boundary Condition', 
    object=PeriodicBoundaryCondition_plugin(toolset),
    messageId=AFXMode.ID_ACTIVATE,
    icon=None,
    kernelInitString='import PeriodicBoundaryCondition_kernel',
    applicableModules=ALL,
    version='1.0',
    author='Xavier van Heule',
    description='A plugin to easily create periodic boundary conditions on 3D geometry',
    helpUrl='N/A'
)
