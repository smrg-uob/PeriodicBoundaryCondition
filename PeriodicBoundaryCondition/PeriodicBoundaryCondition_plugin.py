import abaqusGui
import abaqusConstants
import os
import PeriodicBoundaryCondition_DB
from kernelAccess import mdb


# Class for the plugin, the code is implemented as a procedure running to different steps.
# The code is designed as such that the automatic issuing of commands by Abaqus is avoided.
# The procedure will only loop through the inner step sequence (see the Abaqus GUI Toolkit User Manual 7.2.1)
# Kernel commands are issued manually where necessary, and the procedure is exited when the user closes the GUI
class Plugin(abaqusGui.AFXForm):
    # Constants defining flags for the different steps
    STEP_OVERVIEW = 0
    STEP_NEW = 1
    STEP_CONFIRM = 2
    STEP_ERROR = 3
    STEP_CLOSE = 4

    # An array holding the names of each step (useful for debugging)
    STEPS = ['OVERVIEW', 'NEW', 'CONFIRM', 'ERROR', 'CLOSE']

    def __init__(self, owner):
        # Call super constructor
        abaqusGui.AFXForm.__init__(self, owner)
        # Define step tracker
        self.next_step = self.STEP_OVERVIEW

    def get_current_step(self):
        return self.getCurrentDialog().get_step()

    # Getter for the next step
    def get_next_dialog(self):
        if self.next_step == self.STEP_OVERVIEW:
            return self.get_overview_dialog()
        elif self.next_step == self.STEP_NEW:
            return self.get_input_dialog()
        elif self.next_step == self.STEP_CONFIRM:
            return self.get_confirm_dialog()
        else:
            return None

    # Create the overview step
    def get_overview_dialog(self):
        return PeriodicBoundaryCondition_DB.OverviewDialog(self, self.STEP_OVERVIEW)

    # Create the input step
    def get_input_dialog(self):
        return PeriodicBoundaryCondition_DB.InputDialog(self, self.STEP_NEW)

    # Create a confirmation or error dialog after creating a new pbc
    def get_confirm_dialog(self):
        # Fetch the feedback
        matcher = mdb.customData.matchers[self.getCurrentDialog().get_current_name()].get_matcher()
        valid = matcher.is_valid()
        lines = matcher.get_status_messages()
        # Construct dialog
        if valid:
            name = self.getCurrentDialog().get_current_name()
            return PeriodicBoundaryCondition_DB.ConfirmDialog(self, self.STEP_CONFIRM, name, lines)
        else:
            return PeriodicBoundaryCondition_DB.ErrorDialog(self, self.STEP_ERROR, lines)

    # Issues the command to initialize the registry
    def issue_init(self):
        cmd = abaqusGui.AFXGuiCommand(mode=self, method='create_registry',
                                      objectName='PeriodicBoundaryCondition_kernel', registerQuery=False)
        issue_command(cmd)
        # Return True indicating the command was issued
        return True

    # Issues the command to match nodes
    def issue_match(self):
        # Check if the name already exists
        name = self.getCurrentDialog().get_current_name()
        if mdb.customData.matchers.has_key(name):
            # The name already exists: display an error message
            abaqusGui.showAFXErrorDialog(abaqusGui.getAFXApp().getAFXMainWindow(),
                                         'A constraint with this name already exists')
            # Return false indicating the command was not issued
            return False
        else:
            # The name does not exist yet: issue the command
            cmd = abaqusGui.AFXGuiCommand(mode=self, method='match_nodes',
                                          objectName='PeriodicBoundaryCondition_kernel', registerQuery=False)
            abaqusGui.AFXStringKeyword(cmd, 'name', True, name)
            abaqusGui.AFXIntKeyword(cmd, 'model', True, self.getCurrentDialog().currentModel, False)
            abaqusGui.AFXIntKeyword(cmd, 'part', True, self.getCurrentDialog().currentPart, False)
            abaqusGui.AFXIntKeyword(cmd, 'master', True, self.getCurrentDialog().currentMaster, False)
            abaqusGui.AFXIntKeyword(cmd, 'slave', True, self.getCurrentDialog().currentSlave, False)
            abaqusGui.AFXIntKeyword(cmd, 'ex_m', True, self.getCurrentDialog().get_master_exempt_index())
            abaqusGui.AFXIntKeyword(cmd, 'ex_s', True, self.getCurrentDialog().get_slave_exempt_index())
            abaqusGui.AFXIntKeyword(cmd, 'plane', True, self.getCurrentDialog().currentPlane, False)
            abaqusGui.AFXIntKeyword(cmd, 'mode', True, self.getCurrentDialog().currentMode, False)
            issue_command(cmd)
            # Return True indicating the command was issued
            return True

    # Issues the command to pair nodes
    def issue_pair(self):
        # Issue command
        cmd = abaqusGui.AFXGuiCommand(mode=self, method='apply_constraints',
                                                objectName='PeriodicBoundaryCondition_kernel')
        abaqusGui.AFXStringKeyword(cmd, 'name', True, self.getCurrentDialog().get_current_name())
        issue_command(cmd)
        # Update the overview window
        self.getCurrentDialog().update_boundaries()
        # Return True indicating the command was issued
        return True

    # Issues the command to remove a pairing of nodes
    def issue_remove(self):
        # Issue command
        cmd = abaqusGui.AFXGuiCommand(mode=self, method='remove_constraints',
                                                  objectName='PeriodicBoundaryCondition_kernel')
        abaqusGui.AFXStringKeyword(cmd, 'name', True, self.getCurrentDialog().get_current_name())
        issue_command(cmd)
        # Update the overview window
        self.getCurrentDialog().update_boundaries()
        # Return True indicating the command was issued
        return True

    # ----------------
    # Method overrides
    # ----------------

    # Called when the mode is activated
    def activate(self):
        # Set first step
        self.next_step = self.STEP_OVERVIEW
        # Make sure the registry is initialized
        self.issue_init()
        # Call super method
        abaqusGui.AFXForm.activate(self)

    # Called when the mode is deactivated
    def deactivate(self):
        # Call super method
        abaqusGui.AFXForm.deactivate(self)

    # Override from AFXForm to return the first dialog
    def getFirstDialog(self):
        # simply forward to the general dialog selection method
        return self.get_next_dialog()

    # Override from AFXForm to return the next dialog in the inner step loop
    def getNextDialog(self, prev):
        # simply forward to the general dialog selection method
        return self.get_next_dialog()

    # Override from AFXForm to return the next dialog in the outer step loop
    def getLoopDialog(self):
        # simply forward to the general dialog selection method
        return self.get_next_dialog()

    # Override to verify the keyword values in the inner loop, return true to continue the code flow
    def verifyCurrentKeywordValues(self):
        # Return true to continue
        return True

    # Override from AFXForm to perform custom checks, return true to continue the code flow
    def doCustomChecks(self):
        # We will use this method to control what command is to be issued and what the next step is
        btn = self.getPressedButtonId()
        step = self.get_current_step()
        if step == self.STEP_OVERVIEW:
            if btn == abaqusGui.AFXDialog.ID_CLICKED_APPLY:
                # Apply button in overview dialog: remain in the overview and delete the currently selected constraint
                self.next_step = self.STEP_OVERVIEW
                self.issue_remove()
            elif btn == abaqusGui.AFXDialog.ID_CLICKED_CONTINUE:
                # Ok button in overview dialog: opens the new constraint dialog, but do not issue a command
                self.next_step = self.STEP_NEW
            elif btn == abaqusGui.AFXDialog.ID_CLICKED_OK:
                # Continue button in overview dialog: remain in the overview and pair the currently selected constraint
                self.next_step = self.STEP_OVERVIEW
                self.issue_pair()
            elif btn == abaqusGui.AFXDialog.ID_CLICKED_CANCEL:
                # Cancel button in overview dialog: close the dialog
                pass
        elif step == self.STEP_NEW:
            if btn == abaqusGui.AFXDialog.ID_CLICKED_CONTINUE:
                # Apply button in overview dialog: show confirmation dialog and match nodes
                if self.issue_match():
                    self.next_step = self.STEP_CONFIRM
                else:
                    self.next_step = self.STEP_NEW
            elif btn == abaqusGui.AFXDialog.ID_CLICKED_CANCEL:
                # Continue button in overview dialog: go back to the overview
                self.next_step = self.STEP_OVERVIEW
        elif step == self.STEP_CONFIRM:
            if btn == abaqusGui.AFXDialog.ID_CLICKED_CONTINUE:
                # Apply button in confirm dialog: go back to the overview and pair nodes
                self.issue_pair()
                self.next_step = self.STEP_OVERVIEW
            elif btn == abaqusGui.AFXDialog.ID_CLICKED_CANCEL:
                # Continue button in confirm dialog: go back to the overview
                self.next_step = self.STEP_OVERVIEW
        elif step == self.STEP_ERROR:
            # Continue button in error dialog: go back to the overview
            self.next_step = self.STEP_OVERVIEW
        elif step == self.STEP_CLOSE:
            # Close the gui and do not issue a command
            self.next_step = self.STEP_CLOSE
        return True

    # Override to verify the keyword values in the outer loop, return true to continue the code flow
    def verifyKeywordValues(self):
        # Return true to continue
        return True

    # Override from AFXProcedure to perform custom tasks
    def doCustomTasks(self):
        pass

    # Override to prevent the automatic flow from issuing commands
    def issueCommands(self, writeToReplay, writeToJournal):
        pass

    # Method override
    def okToCancel(self):
        return False


# Utility method to issues a command to the kernel
def issue_command(cmd):
    abaqusGui.sendCommand(cmd.getCommandString())


# Utility method to print a message to the console
def debug_message(msg):
    abaqusGui.getAFXApp().getAFXMainWindow().writeToMessageArea(msg)


# Step class override to allow for cleaner code (getters) and debugging
class DialogStep(abaqusGui.AFXDialogStep):
    # Constructor
    def __init__(self, name, form, dialog):
        abaqusGui.AFXDialogStep.__init__(self, form, dialog)
        self.name = name
        self.form = form
        self.dialog = dialog

    # Getter for the name
    def get_name(self):
        return self.name

    # Getter for the form
    def get_form(self):
        return self.form

    # Getter for the dialog
    def get_dialog(self):
        return self.dialog

    # Method override
    def onCancel(self):
        # Call super method
        abaqusGui.AFXDialogStep.onCancel(self)

    # Method override
    def onDone(self):
        # Call super method
        abaqusGui.AFXDialogStep.onDone(self)

    # Method override
    def onExecute(self):
        # Call super method
        abaqusGui.AFXDialogStep.onExecute(self)

    # Method override
    def onResume(self):
        # Call super method
        abaqusGui.AFXDialogStep.onResume(self)

    # Method override
    def onSuspend(self):
        # Call super method
        abaqusGui.AFXDialogStep.onSuspend(self)


# Code for the registration of the plug-in
thisPath = os.path.abspath(__file__)
thisDir = os.path.dirname(thisPath)
toolset = abaqusGui.getAFXApp().getAFXMainWindow().getPluginToolset()
toolset.registerGuiMenuButton(
    buttonText='Periodic Boundary Condition', 
    object=Plugin(toolset),
    messageId=abaqusGui.AFXMode.ID_ACTIVATE,
    icon=None,
    kernelInitString='import PeriodicBoundaryCondition_kernel',
    applicableModules=abaqusConstants.ALL,
    version='2.0',
    author='Xavier van Heule',
    description='A plugin to easily create periodic boundary conditions on 3D geometry',
    helpUrl='https://github.com/smrg-uob/PeriodicBoundaryCondition/blob/master/README.md'
)
