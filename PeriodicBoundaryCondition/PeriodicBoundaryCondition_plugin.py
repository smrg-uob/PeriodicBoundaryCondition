import abaqusGui
import abaqusConstants
import os
import PeriodicBoundaryCondition_DB
from kernelAccess import mdb


class Plugin(abaqusGui.AFXProcedure):
    STEP_OVERVIEW = 0
    STEP_NEW = 1
    STEP_CONFIRM = 2
    STEP_CLOSE = 3

    STEPS = ['OVERVIEW', 'NEW', 'CONFIRM', 'CLOSE']

    def __init__(self, owner):
        # Call super constructor
        abaqusGui.AFXProcedure.__init__(self, owner)
        # Define step tracker
        self.currentStep = self.STEP_OVERVIEW

    # Getter for the next step
    def get_next_step(self):
        if self.currentStep == self.STEP_OVERVIEW:
            return self.get_overview_step()
        elif self.currentStep == self.STEP_NEW:
            return self.get_input_step()
        elif self.currentStep == self.STEP_CONFIRM:
            return self.get_confirm_step()
        else:
            return None

    # Create the overview step
    def get_overview_step(self):
        return DialogStep('Overview', self,  PeriodicBoundaryCondition_DB.OverviewDialog(self))

    # Create the input step
    def get_input_step(self):
        return DialogStep('Input', self,  PeriodicBoundaryCondition_DB.InputDialog(self))

    # Create a confirmation or error dialog after creating a new pbc
    def get_confirm_step(self):
        # Fetch the feedback
        matcher = mdb.customData.matchers[self.getCurrentDialog().get_current_name()].get_matcher()
        valid = matcher.is_valid()
        lines = matcher.get_status_messages()
        # Construct dialog
        if valid:
            dialog = PeriodicBoundaryCondition_DB.ConfirmDialog(self, self.getCurrentDialog().get_current_name(), lines)
        else:
            dialog = PeriodicBoundaryCondition_DB.ErrorDialog(self, lines)
        # Return the step
        return DialogStep('Confirm', self, dialog)

    # Issues the command to initialize the registry
    def issue_init(self):
        cmd = abaqusGui.AFXGuiCommand(mode=self, method='create_registry',
                                                 objectName='PeriodicBoundaryCondition_kernel', registerQuery=True)
        issue_command(cmd)

    # Issues the command to match nodes
    def issue_match(self):
        # Check if name already exists
        name = self.getCurrentDialog().get_current_name()
        if mdb.customData.matchers.has_key(name):
            # Display error message
            abaqusGui.showAFXErrorDialog(abaqusGui.getAFXApp().getAFXMainWindow(),
                                         'A constraint with this name already exists')
            # Return false indicating the command was not issued
            return False
        else:
            # Issue the command
            cmd = abaqusGui.AFXGuiCommand(mode=self, method='match_nodes',
                                          objectName='PeriodicBoundaryCondition_kernel', registerQuery=True)
            abaqusGui.AFXIntKeyword(cmd, 'model', True, self.getCurrentDialog().currentModel, False)
            abaqusGui.AFXIntKeyword(cmd, 'part', True, self.getCurrentDialog().currentPart, False)
            abaqusGui.AFXIntKeyword(cmd, 'master', True, self.getCurrentDialog().currentMaster, False)
            abaqusGui.AFXIntKeyword(cmd, 'slave', True, self.getCurrentDialog().currentSlave, False)
            abaqusGui.AFXStringKeyword(cmd, 'name', True, name)
            abaqusGui.AFXIntKeyword(cmd, 'plane', True, self.getCurrentDialog().currentPlane, False)
            abaqusGui.AFXIntKeyword(cmd, 'sym', True, self.getCurrentDialog().currentSym, False)
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
        self.currentStep = self.STEP_OVERVIEW
        # Initialize the registry
        self.issue_init()
        # Call super method
        abaqusGui.AFXProcedure.activate(self)

    # Called when the mode is deactivated
    def deactivate(self):
        # Set close step
        # self.currentStep = self.STEP_CLOSE
        # Call super method
        abaqusGui.AFXProcedure.deactivate(self)

    # Override from AFXProcedure to return the first step
    def getFirstStep(self):
        # simply forward to the general step selection method
        return self.get_next_step()

    # Override from AFXProcedure to return the next step in the inner step loop
    def getNextStep(self, prev_step):
        return self.get_next_step()

    # Override from AFXProcedure to return the next step in the outer step loop
    def getLoopStep(self):
        # We should never get here
        return None

    # Override to verify the keyword values in the inner loop
    def verifyCurrentKeywordValues(self):
        # Return true to continue
        return True

    # Override from AFXProcedure to perform custom checks, return true to continue the code flow
    def doCustomChecks(self):
        # We will use this method to control what command is to be issued and what the next step is
        btn = self.getPressedButtonId()
        if self.currentStep == self.STEP_OVERVIEW:
            if btn == abaqusGui.AFXDialog.ID_CLICKED_APPLY:
                # Apply button in overview dialog: remain in the overview and delete the currently selected constraint
                self.currentStep = self.STEP_OVERVIEW
                self.issue_remove()
            elif btn == abaqusGui.AFXDialog.ID_CLICKED_OK:
                # Ok button in overview dialog: remain in the overview and pair the currently selected constraint
                self.currentStep = self.STEP_OVERVIEW
                self.issue_pair()
            elif btn == abaqusGui.AFXDialog.ID_CLICKED_CONTINUE:
                # Continue button in overview dialog: opens the new constraint dialog, but do not issue a command
                self.currentStep = self.STEP_NEW
            elif btn == abaqusGui.AFXDialog.ID_CLICKED_CANCEL:
                # Cancel button in overview dialog: close the dialog
                pass
        elif self.currentStep == self.STEP_NEW:
            if btn == abaqusGui.AFXDialog.ID_CLICKED_CONTINUE:
                # Apply button in overview dialog: show confirmation dialog and match nodes
                if self.issue_match():
                    self.currentStep = self.STEP_CONFIRM
                else:
                    self.currentStep = self.STEP_NEW
            elif btn == abaqusGui.AFXDialog.ID_CLICKED_OK:
                # Continue button in overview dialog: go back to the overview
                self.currentStep = self.STEP_OVERVIEW
        elif self.currentStep == self.STEP_CONFIRM:
            if btn == abaqusGui.AFXDialog.ID_CLICKED_CONTINUE:
                # Apply button in confirm dialog: go back to the overview and pair nodes
                self.issue_pair()
                self.currentStep = self.STEP_OVERVIEW
            elif btn == abaqusGui.AFXDialog.ID_CLICKED_CANCEL:
                # Continue button in confirm dialog: go back to the overview
                self.currentStep = self.STEP_OVERVIEW
        elif self.currentStep == self.STEP_CLOSE:
            # Close the gui and do not issue a command
            self.currentStep = self.STEP_CLOSE
        return True

    # Override to verify the keyword values in the outer loop
    def verifyKeywordValues(self):
        # Return true to continue
        return True

    # Override from AFXProcedure to perform custom tasks, return true to continue the code flow
    def doCustomTasks(self):
        pass

    # Override to prevent the automatic flow from issuing commands
    def issueCommands(self, writeToReplay, writeToJournal):
        return

    # Method override
    def okToCancel(self):
        return self.currentStep == self.STEP_CLOSE or self.currentStep == self.STEP_OVERVIEW


# Issues a general command
def issue_command(cmd):
    abaqusGui.sendCommand(cmd.getCommandString())


# Method to print a message to the terminal
def debug_message(msg):
    abaqusGui.getAFXApp().getAFXMainWindow().writeToMessageArea(msg)


# Class override to allow for cleaner code (getters) and debugging
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
        abaqusGui.AFXDialogStep.onCancel(self)

    # Method override
    def onDone(self):
        abaqusGui.AFXDialogStep.onDone(self)

    # Method override
    def onExecute(self):
        abaqusGui.AFXDialogStep.onExecute(self)

    # Method override
    def onResume(self):
        abaqusGui.AFXDialogStep.onResume(self)

    # Method override
    def onSuspend(self):
        abaqusGui.AFXDialogStep.onSuspend(self)


# Register the plug-in
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
    version='1.0',
    author='Xavier van Heule',
    description='A plugin to easily create periodic boundary conditions on 3D geometry',
    helpUrl='https://github.com/smrg-uob/PeriodicBoundaryCondition/blob/master/README.md'
)
