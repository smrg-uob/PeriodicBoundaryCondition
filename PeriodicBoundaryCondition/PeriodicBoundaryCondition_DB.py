import abaqusGui
import kernelAccess
from kernelAccess import mdb


# Class for the initial overview GUI
class OverviewDialog(abaqusGui.AFXDataDialog):
    # id values, useful for commands between widgets
    [
        ID_PBC
    ] = range(abaqusGui.AFXToolsetGui.ID_LAST, abaqusGui.AFXToolsetGui.ID_LAST+1)

    # constructor
    def __init__(self, form):
        # Call super constructor
        abaqusGui.AFXDataDialog.__init__(self, form, 'Periodic Boundary Conditions',
                                         self.APPLY | self.OK | self.CONTINUE | self.CANCEL,
                                         abaqusGui.DIALOG_ACTIONS_SEPARATOR)
        # Define command map
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_PBC, OverviewDialog.on_message)
        # Configure apply button: delete periodic boundary (issue command)
        del_btn = self.getActionButton(self.ID_CLICKED_APPLY)
        del_btn.setText('Delete')
        del_btn.disable()
        # Configure ok button: pair periodic boundary (issue command)
        pair_btn = self.getActionButton(self.ID_CLICKED_OK)
        pair_btn.setText('Pair')
        pair_btn.disable()
        # Configure continue button: create new periodic boundary (no command is issued)
        new_btn = self.getActionButton(self.ID_CLICKED_CONTINUE)
        new_btn.setText('New')
        # Configure cancel button: close window
        close_btn = self.getActionButton(self.ID_CLICKED_CANCEL)
        close_btn.setText('Close')
        # First horizontal frame
        frame_1 = abaqusGui.FXHorizontalFrame(p=self)
        # Child vertical frame 1
        frame_1_1 = abaqusGui.FXVerticalFrame(p=frame_1)
        self.cbx_pbx = abaqusGui.AFXComboBox(p=frame_1_1, ncols=23, nvis=1, text='',
                                               tgt=self, sel=self.ID_PBC)
        # Add status text fields
        aligner = abaqusGui.AFXVerticalAligner(p=frame_1_1)
        self.txt_valid = abaqusGui.AFXTextField(p=aligner, ncols=15, labelText='Valid:')
        self.txt_valid.disable()
        self.txt_matched = abaqusGui.AFXTextField(p=aligner, ncols=15, labelText='Matched:')
        self.txt_matched.disable()
        self.txt_paired = abaqusGui.AFXTextField(p=aligner, ncols=15, labelText='Paired:')
        self.txt_paired.disable()
        self.txt_master = abaqusGui.AFXTextField(p=aligner, ncols=15, labelText='Master:')
        self.txt_master.disable()
        self.txt_slave = abaqusGui.AFXTextField(p=aligner, ncols=15, labelText='Slave:')
        self.txt_slave.disable()
        self.txt_pairs = abaqusGui.AFXTextField(p=aligner, ncols=15, labelText='Pairs:')
        self.txt_pairs.disable()
        # Force initial updates
        self.update_boundaries()

    # general callback method for when a user performs an action on a widget,
    # routes the callback forward to the respective callback method for the widget
    def on_message(self, sender, sel, ptr):
        if abaqusGui.SELID(sel) == self.ID_PBC:
            self.on_boundary_selected()

    # callback method for when the user selects a new matcher
    def on_boundary_selected(self):
        count = self.cbx_pbx.getNumItems()
        flag = False
        if count <= 0:
            flag = True
        else:
            if is_rep_initialized():
                keys = mdb.customData.matchers.keys()
                index = min(self.cbx_pbx.getCurrentItem(), len(keys)-1)
                if index >= 0:
                    matcher = mdb.customData.matchers[keys[index]].get_matcher()
                    self.txt_valid.setText(str(matcher.is_valid()))
                    self.txt_matched.setText(str(matcher.is_matched()))
                    self.txt_paired.setText(str(matcher.is_paired()))
                    self.txt_master.setText(matcher.get_master_name())
                    self.txt_slave.setText(matcher.get_slave_name())
                    self.txt_pairs.setText(str(matcher.get_pair_count()))
                else:
                    flag = True
        if flag:
            self.txt_valid.setText('N.A.')
            self.txt_matched.setText('N.A.')
            self.txt_paired.setText('N.A.')
            self.txt_master.setText('N.A.')
            self.txt_slave.setText('N.A.')
            self.txt_pairs.setText('N.A.')
        self.update_buttons()

    # method which can be called to force an update of the matcher combo box
    def update_boundaries(self):
        if is_rep_initialized():
            reset_combo_box(self.cbx_pbx, mdb.customData.matchers.keys())
        else:
            self.cbx_pbx.clearItems()
            self.cbx_pbx.setMaxVisible(1)
            self.cbx_pbx.disable()

    def try_select_boundary(self, name):
        pass

    # method to update the states of the action buttons based on the currently selected matcher
    def update_buttons(self):
        del_btn = self.getActionButton(self.ID_CLICKED_APPLY)
        pair_btn = self.getActionButton(self.ID_CLICKED_OK)
        if self.cbx_pbx.getNumItems() <= 0:
            del_btn.disable()
            pair_btn.disable()
        else:
            del_btn.enable()
            matcher = self.get_current_matcher()
            if matcher is None or matcher.is_paired():
                pair_btn.disable()
            else:
                pair_btn.enable()

    # fetches the currently selected matcher object
    def get_current_matcher(self):
        if self.cbx_pbx.getNumItems() > 0 and is_rep_initialized():
            keys = mdb.customData.matchers.keys()
            index = min(self.cbx_pbx.getCurrentItem(), len(keys)-1)
            if index < 0:
                return None
            else:
                return mdb.customData.matchers[keys[index]].get_matcher()
        else:
            return None

    # method to fetch the currently defined name (must be implemented in all dialogs from which commands will be issued)
    def get_current_name(self):
        if self.cbx_pbx.getNumItems() > 0:
            # Return the name
            return self.cbx_pbx.getItemText(self.cbx_pbx.getCurrentItem())
        else:
            # Return empty string
            return ''

    def processUpdates(self):
        abaqusGui.AFXDataDialog.processUpdates(self)
        self.on_boundary_selected()


# Class for the plugin GUI
class InputDialog(abaqusGui.AFXDataDialog):
    # id values, useful for commands between widgets
    [
        ID_MODEL,
        ID_PART,
        ID_MASTER,
        ID_SLAVE,
        ID_NAME,
        ID_PLANE,
        ID_SYM
    ] = range(abaqusGui.AFXToolsetGui.ID_LAST, abaqusGui.AFXToolsetGui.ID_LAST+7)

    # constructor
    def __init__(self, form):
        # Call super constructor
        abaqusGui.AFXDataDialog.__init__(self, form, 'New Periodic Boundary Condition',
                                         self.CONTINUE | self.CANCEL,
                                         abaqusGui.DIALOG_ACTIONS_SEPARATOR)
        # Define command map
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_MODEL, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_PART, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_MASTER, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_SLAVE, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_PLANE, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_SYM, InputDialog.on_message)
        # Configure the ok button
        ok_btn = self.getActionButton(self.ID_CLICKED_CONTINUE)
        ok_btn.disable()
        ok_btn.setText('Create')
        # Configure the continue button
        close_btn = self.getActionButton(self.ID_CLICKED_CANCEL)
        close_btn.setText('Close')
        # Build dialog layout
        frame_h = abaqusGui.FXHorizontalFrame(p=self)
        # Left of frame: configuration
        config = abaqusGui.FXGroupBox(p=frame_h, text='Configuration')
        aligner = abaqusGui.AFXVerticalAligner(p=config)
        # Add combo box to select the model
        mdls = mdb.models.keys()
        self.cbx_model = abaqusGui.AFXComboBox(p=aligner, ncols=16, nvis=len(mdls), text='Select Model',
                                               tgt=self, sel=self.ID_MODEL)
        index = 0
        for mdl in mdls:
            self.cbx_model.appendItem(text=mdl, sel=index)
            index = index + 1
        # Add combo box to select the part
        self.cbx_part = abaqusGui.AFXComboBox(p=aligner, ncols=16, nvis=0, text='Select Part',
                                              tgt=self, sel=self.ID_PART)
        self.cbx_part.disable()
        # Add combo boxes to select the master and slave surfaces, but set them as disabled by default
        # TODO: find some way to select these surfaces from the viewport and highlight them
        self.cbx_master = abaqusGui.AFXComboBox(p=aligner, ncols=16, nvis=0, text='Master Surface',
                                                tgt=self, sel=self.ID_MASTER)
        self.cbx_slave = abaqusGui.AFXComboBox(p=aligner, ncols=16, nvis=0, text='Slave Surface',
                                               tgt=self, sel=self.ID_SLAVE)
        self.cbx_master.disable()
        self.cbx_slave.disable()
        # Add text field for the name
        self.txt_name = abaqusGui.AFXTextField(p=aligner, ncols=16, labelText='PBC Name',
                                               tgt=self, sel=self.ID_NAME)
        # Add combo box to select the plane
        self.cbx_plane = abaqusGui.AFXComboBox(p=aligner, ncols=0, nvis=3, text='Match Plane',
                                               tgt=self, sel=self.ID_PLANE)
        self.cbx_plane.appendItem(text='XY-plane', sel=0)
        self.cbx_plane.appendItem(text='XZ-plane', sel=1)
        self.cbx_plane.appendItem(text='YZ-plane', sel=2)
        # Add combo box to select the symmetry
        self.cbx_sym = abaqusGui.AFXComboBox(p=aligner, ncols=0, nvis=3, text='Symmetry',
                                             tgt=self, sel=self.ID_SYM)
        self.cbx_sym.appendItem(text='Asymmetric', sel=0)
        self.cbx_sym.appendItem(text='Symmetric', sel=1)
        self.cbx_sym.appendItem(text='Ignore', sel=2)
        # Right of frame: exemptions
        frame_v = abaqusGui.FXVerticalFrame(p=frame_h)
        g_ex_m = abaqusGui.FXGroupBox(p=frame_v, text='Exclude Master Edges', opts=abaqusGui.LIST_MULTIPLESELECT)
        self.lst_ex_master = abaqusGui.AFXList(p=g_ex_m, nvis=4, sel=0)
        self.lst_ex_master.disable()
        g_ex_s = abaqusGui.FXGroupBox(p=frame_v, text='Exclude Slave Edges', opts=abaqusGui.LIST_MULTIPLESELECT)
        self.lst_ex_slave = abaqusGui.AFXList(p=g_ex_s, nvis=4, sel=0)
        self.lst_ex_slave.disable()
        # Set currently selected items to -1 (to force an update on first opening of the GUI)
        self.currentModel = -1
        self.currentPart = -1
        self.currentMaster = -1
        self.currentSlave = -1
        self.currentName = ''
        self.currentPlane = -1
        self.currentSym = - 1
        # Force initial updates
        self.on_model_selected()
        self.on_plane_selected()
        self.on_sym_selected()

    # method to fetch the currently defined name (must be implemented in all dialogs from which commands will be issued)
    def get_current_name(self):
        return self.currentName

    # general callback method for when a user performs an action on a widget,
    # routes the callback forward to the respective callback method for the widget
    def on_message(self, sender, sel, ptr):
        if abaqusGui.SELID(sel) == self.ID_MODEL:
            self.on_model_selected()
        elif abaqusGui.SELID(sel) == self.ID_PART:
            self.on_part_selected()
        elif abaqusGui.SELID(sel) == self.ID_MASTER:
            self.on_master_selected()
        elif abaqusGui.SELID(sel) == self.ID_SLAVE:
            self.on_slave_selected()
        elif abaqusGui.SELID(sel) == self.ID_PLANE:
            self.on_plane_selected()
        elif abaqusGui.SELID(sel) == self.ID_SYM:
            self.on_sym_selected()

    # callback method for when the user selects a new slave
    def on_model_selected(self):
        model = self.cbx_model.getItemData(self.cbx_model.getCurrentItem())
        # If a different model has been selected, the GUI needs to be updated
        if model != self.currentModel:
            # Update the selected model
            self.currentModel = model
            #  Reset current selected part:
            self.currentPart = -1
            # Fetch the parts for the model
            models = mdb.models.keys()
            # Update the parts combo box
            reset_combo_box(self.cbx_part, mdb.models[models[model]].parts.keys())
            self.on_part_selected()

    # callback method for when the user selects a new part
    def on_part_selected(self):
        # Check if there are items in the part list
        count = self.cbx_part.getNumItems()
        if count <= 0:
            # Reset currently selected master
            self.currentPart = -1
            self.currentMaster = -1
            self.currentSlave = -1
            surfs = []
            # Update the master and slave combo boxes
            reset_combo_box(self.cbx_master, surfs)
            reset_combo_box(self.cbx_slave, surfs)
            self.on_master_selected()
            self.on_slave_selected()
        else:
            part = self.cbx_part.getItemData(self.cbx_part.getCurrentItem())
            # If a different part has been selected, the GUI needs to be updated
            if part != self.currentPart:
                # Update the selected part
                self.currentPart = part
                #  Reset current selected master and slave:
                self.currentMaster = -1
                self.currentSlave = -1
                # Fetch the surfaces for the part
                models = mdb.models.keys()
                model = self.cbx_model.getItemData(self.cbx_model.getCurrentItem())
                parts = mdb.models[models[model]].parts.keys()
                surfs = mdb.models[models[model]].parts[parts[part]].surfaces.keys()
                # Update the master and slave combo boxes
                reset_combo_box(self.cbx_master, surfs)
                reset_combo_box(self.cbx_slave, surfs)
                self.on_master_selected()
                self.on_slave_selected()

    # callback method for when the user selects a new master surface
    def on_master_selected(self):
        # Check if there are items in the master list
        count = self.cbx_master.getNumItems()
        if count <= 0:
            # Reset currently selected master
            self.currentMaster = -1
        else:
            master = self.cbx_master.getItemData(self.cbx_master.getCurrentItem())
            # If a different master has been selected, the GUI needs to be updated
            if master != self.currentMaster:
                # Update the selected master
                self.currentMaster = master
                # Update master exempts
                self.populate_exempts(master, self.lst_ex_master)

    # callback method for when the user selects a new slave surface
    def on_slave_selected(self):
        # Check if there are items in the slave list
        count = self.cbx_slave.getNumItems()
        if count <= 0:
            # Reset currently selected slave
            self.currentSlave = -1
        else:
            slave = self.cbx_slave.getItemData(self.cbx_slave.getCurrentItem())
            # If a different slave has been selected, the GUI needs to be updated
            if slave != self.currentSlave:
                # Update the selected slave
                self.currentSlave = slave
                # Update slave exempts
                self.populate_exempts(slave, self.lst_ex_slave)

    # callback method for when the user selects a new match plane
    def on_plane_selected(self):
        self.currentPlane = self.cbx_plane.getItemData(self.cbx_plane.getCurrentItem())

    # callback method for when the user selects a new symmetry setting
    def on_sym_selected(self):
        self.currentSym = self.cbx_sym.getItemData(self.cbx_sym.getCurrentItem())

    # method to update the state of the create button based on the current user inputs
    def update_action_button_state(self):
        m = self.cbx_master.getNumItems()
        s = self.cbx_slave.getNumItems()
        ok_button = self.getActionButton(self.ID_CLICKED_CONTINUE)
        name = self.txt_name.getText()
        if name and (m > 0 and s > 0):
            master = self.cbx_master.getItemData(self.cbx_master.getCurrentItem())
            slave = self.cbx_slave.getItemData(self.cbx_slave.getCurrentItem())
            if master == slave:
                ok_button.disable()
            else:
                ok_button.enable()
        else:
            ok_button.disable()

    # method to populate the exempts widget with edges to exempt
    def populate_exempts(self, surface, exempt_list):
        # Fetch the edges
        models = mdb.models.keys()
        model = self.cbx_model.getItemData(self.cbx_model.getCurrentItem())
        parts = mdb.models[models[model]].parts.keys()
        part = self.cbx_part.getItemData(self.cbx_part.getCurrentItem())
        surfs = mdb.models[models[model]].parts[parts[part]].surfaces.keys()
        surf = mdb.models[models[model]].parts[parts[part]].surfaces[surfs[surface]]
        edges = surf.edges
        # Clear the list
        exempt_list.clearItems()
        # Fetch edges
        for edge in edges:
            debug_message('Edge: ' + str(edge))
        # Enable the list
        exempt_list.enable()

    # Override from parent class
    def processUpdates(self):
        abaqusGui.AFXDataDialog.processUpdates(self)
        self.update_action_button_state()
        self.currentName = self.txt_name.getText()
        if self.cbx_master.getNumItems() <= 0:
            self.cbx_master.disable()
        else:
            self.cbx_master.enable()
        if self.cbx_slave.getNumItems() <= 0:
            self.cbx_slave.disable()
        else:
            self.cbx_slave.enable()


# Class for a dialog to confirm the user to apply the constraints after matching
class ConfirmDialog(abaqusGui.AFXDataDialog):
    # constructor
    def __init__(self, form, name, lines):
        # Call super constructor
        abaqusGui.AFXDataDialog.__init__(self, form, 'Confirm',
                                         self.CONTINUE | self.CANCEL,
                                         abaqusGui.DIALOG_ACTIONS_SEPARATOR)
        # Configure the ok button
        yes_btn = self.getActionButton(self.ID_CLICKED_CONTINUE)
        yes_btn.setText('Yes')
        # Configure the continue button
        no_btn = self.getActionButton(self.ID_CLICKED_CANCEL)
        no_btn.setText('No')
        # Store data
        self.name = name
        # Display text
        for line in lines:
            abaqusGui.FXLabel(p=self, text=line)

    # method to fetch the currently defined name (must be implemented in all dialogs from which commands will be issued)
    def get_current_name(self):
        return self.name


# Class for a dialog to inform the user that constraints can not be applied
class ErrorDialog(abaqusGui.AFXDataDialog):
    # constructor
    def __init__(self, form, lines):
        # Call super constructor
        abaqusGui.AFXDataDialog.__init__(self, form, 'Error', self.CANCEL,
                                         abaqusGui.DIALOG_ACTIONS_SEPARATOR)
        # Configure the continue button
        no_btn = self.getActionButton(self.ID_CLICKED_CANCEL)
        no_btn.setText('OK')
        # Display text
        for line in lines:
            abaqusGui.FXLabel(p=self, text=line)


# Utility method to reset a combo box based on the keys it should display (to avoid code repetition)
def reset_combo_box(cbx, keys):
    # Clear the current items
    cbx.clearItems()
    if len(keys) > 0:
        # Keys exist, therefore the combo box should be populated with them
        index = 0
        for key in keys:
            cbx.appendItem(text=key, sel=index)
            index = index + 1
            cbx.setMaxVisible(len(keys))
            cbx.enable()
    else:
        # Keys do not exist, therefore disable the combo box
        cbx.setMaxVisible(1)
        cbx.disable()


# Utility method to check if the matcher repository is initialized
def is_rep_initialized():
    # Check if the custom data has the matchers initialized
    if hasattr(mdb.customData, 'matchers'):
        # If the matchers attribute exists, it could be in an unpickled state, which we can detect
        matchers = mdb.customData.matchers
        try:
            # If this is a fresh mdb on which the plugin has never been run,
            # the RawPickledObjectProxy will not be loaded, which is why this
            # needs to be encapsulated in a try except statement
            return not isinstance(matchers, kernelAccess.RawPickledObjectProxy)
        except Exception:
            return True
    else:
        return False


# Utility method to print a message to the console
def debug_message(msg):
    abaqusGui.getAFXApp().getAFXMainWindow().writeToMessageArea(msg)
