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
    def __init__(self, form, step):
        # Call super constructor
        abaqusGui.AFXDataDialog.__init__(self, form, 'Periodic Boundary Conditions',
                                         self.APPLY | self.OK | self.CONTINUE | self.CANCEL,
                                         abaqusGui.DIALOG_ACTIONS_SEPARATOR)
        # Save the step
        self.step = step
        # Define command map
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_PBC, OverviewDialog.on_message)
        # Configure apply button: delete periodic boundary (issue command)
        del_btn = self.getActionButton(self.ID_CLICKED_APPLY)
        del_btn.setText('Delete')
        del_btn.disable()
        # Configure continue button: pair periodic boundary (issue command)
        pair_btn = self.getActionButton(self.ID_CLICKED_OK)
        pair_btn.setText('Pair')
        pair_btn.disable()
        # Configure ok button: create new periodic boundary (no command is issued)
        new_btn = self.getActionButton(self.ID_CLICKED_CONTINUE)
        new_btn.setText('New')
        # Configure cancel button: close window
        close_btn = self.getActionButton(self.ID_CLICKED_CANCEL)
        close_btn.setText('Close')
        # First horizontal frame
        frame_1 = abaqusGui.FXHorizontalFrame(p=self)
        # Child vertical frame 1
        frame_1_1 = abaqusGui.FXVerticalFrame(p=frame_1)
        # Combo box to select the different PBCs
        self.cbx_pbx = abaqusGui.AFXComboBox(p=frame_1_1, ncols=24, nvis=1, text='',
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
        self.txt_plane = abaqusGui.AFXTextField(p=aligner, ncols=15, labelText='Plane:')
        self.txt_plane.disable()
        self.txt_mode = abaqusGui.AFXTextField(p=aligner, ncols=15, labelText='Mode:')
        self.txt_mode.disable()
        self.txt_pairs = abaqusGui.AFXTextField(p=aligner, ncols=15, labelText='Pairs:')
        self.txt_pairs.disable()
        self.txt_exempts = abaqusGui.AFXTextField(p=aligner, ncols=15, labelText='Exempts:')
        self.txt_exempts.disable()
        # Tracker for highlighted surfaces
        self.hl_m = ''
        self.hl_s = ''
        # Force initial updates
        self.update_boundaries()

    # Method to get the step associated with the current dialog
    def get_step(self):
        return self.step

    # general callback method for when a user performs an action on a widget,
    # routes the callback forward to the respective callback method for the widget
    def on_message(self, sender, sel, ptr):
        if abaqusGui.SELID(sel) == self.ID_PBC:
            self.on_boundary_selected()

    # callback method for when the user selects a new matcher
    def on_boundary_selected(self):
        count = self.cbx_pbx.getNumItems()
        flag = False
        # remove highlighting
        self.un_highlight()
        # update GUI
        if count <= 0:
            flag = True
        else:
            if is_rep_initialized():
                keys = mdb.customData.matchers.keys()
                index = min(self.cbx_pbx.getCurrentItem(), len(keys)-1)
                if index >= 0:
                    # fetch matcher
                    matcher = mdb.customData.matchers[keys[index]].get_matcher()
                    self.txt_valid.setText(str(matcher.is_valid()))
                    self.txt_matched.setText(str(matcher.is_matched()))
                    self.txt_paired.setText(str(matcher.is_paired()))
                    self.txt_master.setText(matcher.get_master_name())
                    self.txt_slave.setText(matcher.get_slave_name())
                    self.txt_plane.setText(PLANES[matcher.get_plane_index()])
                    self.txt_mode.setText(MODES[matcher.get_mode_index()])
                    self.txt_pairs.setText(str(matcher.get_pair_count()))
                    self.txt_exempts.setText(str(matcher.get_exempt_count()))
                    # highlight
                    self.highlight(matcher)
                else:
                    flag = True
        if flag:
            self.txt_valid.setText('N.A.')
            self.txt_matched.setText('N.A.')
            self.txt_paired.setText('N.A.')
            self.txt_master.setText('N.A.')
            self.txt_slave.setText('N.A.')
            self.txt_plane.setText('N.A.')
            self.txt_mode.setText('N.A.')
            self.txt_pairs.setText('N.A.')
            self.txt_exempts.setText('N.A.')
        self.update_buttons()

    # method which can be called to force an update of the matcher combo box
    def update_boundaries(self):
        if is_rep_initialized():
            reset_combo_box(self.cbx_pbx, mdb.customData.matchers.keys())
        else:
            self.cbx_pbx.clearItems()
            self.cbx_pbx.setMaxVisible(1)
            self.cbx_pbx.disable()
        self.on_boundary_selected()

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

    def highlight(self, matcher):
        self.hl_m = 'hl_m = (mdb.models[\'' + matcher.get_model_name() + '\']' +\
                    '.parts[\'' + matcher.get_part_name() + '\']' +\
                    '.surfaces[\'' + matcher.get_master_name() + '\'],)'
        self.hl_s = 'hl_s = (mdb.models[\'' + matcher.get_model_name() + '\']' +\
                    '.parts[\'' + matcher.get_part_name() + '\']' +\
                    '.surfaces[\'' + matcher.get_slave_name() + '\'])'
        abaqusGui.sendCommand(self.hl_m + '\nhighlight(hl_m)')
        abaqusGui.sendCommand(self.hl_s + '\nhighlight(hl_s)')

    def un_highlight(self):
        if self.hl_m is not '':
            abaqusGui.sendCommand(self.hl_m + '\nunhighlight(hl_m)')
            self.hl_m = ''
        if self.hl_s is not '':
            abaqusGui.sendCommand(self.hl_s + '\nunhighlight(hl_s)')
            self.hl_s = ''

    # Override from parent class
    def processUpdates(self):
        abaqusGui.AFXDataDialog.processUpdates(self)
        # self.on_boundary_selected()

    # Override from parent class
    def hide(self):
        # Undo highlighting
        self.un_highlight()
        # Call super method
        abaqusGui.AFXDataDialog.hide(self)


# Class for the new pbc dialog
class InputDialog(abaqusGui.AFXDataDialog):
    # id values, useful for commands between widgets
    [
        ID_MODEL,
        ID_PART,
        ID_MASTER,
        ID_SLAVE,
        ID_EX_MASTER,
        ID_USE_EX_MASTER,
        ID_EX_SLAVE,
        ID_USE_EX_SLAVE,
        ID_NAME,
        ID_PLANE,
        ID_MODE
    ] = range(abaqusGui.AFXToolsetGui.ID_LAST, abaqusGui.AFXToolsetGui.ID_LAST+11)

    # constructor
    def __init__(self, form, step):
        # Call super constructor
        abaqusGui.AFXDataDialog.__init__(self, form, 'New Periodic Boundary Condition',
                                         self.CONTINUE | self.CANCEL,
                                         abaqusGui.DIALOG_ACTIONS_SEPARATOR)
        # Save the form
        self.form = form
        # Save the step
        self.step = step
        # Define command map
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_MODEL, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_PART, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_MASTER, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_SLAVE, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_EX_MASTER, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_USE_EX_MASTER, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_EX_SLAVE, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_USE_EX_SLAVE, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_PLANE, InputDialog.on_message)
        abaqusGui.FXMAPFUNC(self, abaqusGui.SEL_COMMAND, self.ID_MODE, InputDialog.on_message)
        # Configure the ok button
        ok_btn = self.getActionButton(self.ID_CLICKED_CONTINUE)
        ok_btn.disable()
        ok_btn.setText('Create')
        # Configure the continue button
        close_btn = self.getActionButton(self.ID_CLICKED_CANCEL)
        close_btn.setText('Close')
        # Define the width of the input widgets
        widget_width = 21
        # Horizontal frame to tile widgets horizontally
        frame_h = abaqusGui.FXHorizontalFrame(p=self)
        # Left of frame: configuration
        config = abaqusGui.FXGroupBox(p=frame_h, text='Configuration')
        # Vertical aligner to align widgets vertically in the first column
        aligner = abaqusGui.AFXVerticalAligner(p=config)
        # Add combo box to select the model
        mdls = mdb.models.keys()
        self.cbx_model = abaqusGui.AFXComboBox(p=aligner, ncols=widget_width, nvis=len(mdls), text='Select Model',
                                               tgt=self, sel=self.ID_MODEL)
        index = 0
        for mdl in mdls:
            self.cbx_model.appendItem(text=mdl, sel=index)
            index = index + 1
        # Add combo box to select the part
        self.cbx_part = abaqusGui.AFXComboBox(p=aligner, ncols=widget_width, nvis=0, text='Select Part',
                                              tgt=self, sel=self.ID_PART)
        self.cbx_part.disable()
        # Add combo boxes to select the master surface, but set it as disabled by default
        self.cbx_master = abaqusGui.AFXComboBox(p=aligner, ncols=widget_width, nvis=0, text='Master Surface',
                                                tgt=self, sel=self.ID_MASTER)
        self.cbx_master.disable()
        # Add combo boxes to select the slave surface, but set it as disabled by default
        self.cbx_slave = abaqusGui.AFXComboBox(p=aligner, ncols=widget_width, nvis=0, text='Slave Surface',
                                               tgt=self, sel=self.ID_SLAVE)
        self.cbx_slave.disable()
        # Add a check box to enable the definition of exempts for the master surface, and a selection combo box
        frame_em = abaqusGui.FXHorizontalFrame(p=aligner, opts=0, x=0, y=0, w=0, h=0, pl=0, pr=0, pt=0, pb=0,
                                               hs=abaqusGui.DEFAULT_SPACING, vs=abaqusGui.DEFAULT_SPACING)
        abaqusGui.FXLabel(p=frame_em, text='Master Exempt', ic=None,
                          opts=abaqusGui.LAYOUT_CENTER_Y | abaqusGui.JUSTIFY_LEFT)
        frame_em_sub = abaqusGui.FXHorizontalFrame(p=frame_em, opts=0, x=0, y=0, w=0, h=0, pl=0, pr=0, pt=0, pb=0,
                                                   hs=abaqusGui.DEFAULT_SPACING, vs=abaqusGui.DEFAULT_SPACING)
        self.check_ex_master = abaqusGui.FXCheckButton(p=frame_em_sub, text='', tgt=self, sel=self.ID_USE_EX_MASTER)
        self.cbx_ex_master = abaqusGui.AFXComboBox(p=frame_em_sub, ncols=widget_width - 4, nvis=0, text='',
                                                   tgt=self, sel=self.ID_EX_MASTER)
        self.check_ex_master.disable()
        self.cbx_ex_master.disable()
        # Add a check box to enable the definition of exempts for the master surface, and a selection combo box
        frame_es = abaqusGui.FXHorizontalFrame(p=aligner, opts=0, x=0, y=0, w=0, h=0, pl=0, pr=0, pt=0, pb=0,
                                               hs=abaqusGui.DEFAULT_SPACING, vs=abaqusGui.DEFAULT_SPACING)
        abaqusGui.FXLabel(p=frame_es, text='Slave Exempt', ic=None,
                          opts=abaqusGui.LAYOUT_CENTER_Y | abaqusGui.JUSTIFY_LEFT)
        frame_es_sub = abaqusGui.FXHorizontalFrame(p=frame_es, opts=0, x=0, y=0, w=0, h=0, pl=0, pr=0, pt=0, pb=0,
                                                   hs=abaqusGui.DEFAULT_SPACING, vs=abaqusGui.DEFAULT_SPACING)
        self.check_ex_slave = abaqusGui.FXCheckButton(p=frame_es_sub, text='', tgt=self, sel=self.ID_USE_EX_SLAVE)
        self.cbx_ex_slave = abaqusGui.AFXComboBox(p=frame_es_sub, ncols=widget_width - 4, nvis=0, text='',
                                                   tgt=self, sel=self.ID_EX_SLAVE)
        self.check_ex_slave.disable()
        self.cbx_ex_slave.disable()
        # Add text field for the name
        self.txt_name = abaqusGui.AFXTextField(p=aligner, ncols=widget_width + 2, labelText='PBC Name',
                                               tgt=self, sel=self.ID_NAME)
        # Add combo box to select the plane
        self.cbx_plane = abaqusGui.AFXComboBox(p=aligner, ncols=widget_width, nvis=3, text='Match Plane',
                                               tgt=self, sel=self.ID_PLANE)
        self.cbx_plane.appendItem(text=PLANES[0], sel=0)
        self.cbx_plane.appendItem(text=PLANES[1], sel=1)
        self.cbx_plane.appendItem(text=PLANES[2], sel=2)
        # Add combo box to select the mode
        self.cbx_mode = abaqusGui.AFXComboBox(p=aligner, ncols=widget_width, nvis=2, text='Mode',
                                              tgt=self, sel=self.ID_MODE)
        self.cbx_mode.appendItem(text=MODES[0], sel=0)
        self.cbx_mode.appendItem(text=MODES[1], sel=1)
        # Set currently selected items to -1 (to force an update on first opening of the GUI)
        self.currentModel = -1
        self.currentPart = -1
        self.currentMaster = -1
        self.currentSlave = -1
        self.currentMExempt = -1
        self.currentSExempt = -1
        self.currentName = ''
        self.currentPlane = -1
        self.currentMode = -1
        # Define highlighted sets
        self.highlight_m = ''
        self.highlight_s = ''
        self.highlight_em = ''
        self.highlight_es = ''
        # Force initial updates
        self.on_model_selected()
        self.on_plane_selected()
        self.on_mode_selected()

    # Method to get the step associated with the current dialog
    def get_step(self):
        return self.step

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
        elif abaqusGui.SELID(sel) == self.ID_EX_MASTER:
            self.on_master_exempt_selected()
        elif abaqusGui.SELID(sel) == self.ID_EX_SLAVE:
            self.on_slave_exempt_selected()
        elif abaqusGui.SELID(sel) == self.ID_USE_EX_MASTER:
            self.on_master_exempt_toggled()
        elif abaqusGui.SELID(sel) == self.ID_USE_EX_SLAVE:
            self.on_slave_exempt_toggled()
        elif abaqusGui.SELID(sel) == self.ID_PLANE:
            self.on_plane_selected()
        elif abaqusGui.SELID(sel) == self.ID_MODE:
            self.on_mode_selected()

    def get_selected_model(self):
        count = self.cbx_model.getNumItems()
        if count <= 0:
            return None
        else:
            model_keys = mdb.models.keys()
            return mdb.models[model_keys[self.currentModel]]

    def get_selected_part(self):
        count = min(self.cbx_model.getNumItems(), self.cbx_part.getNumItems())
        if count <= 0:
            return None
        else:
            model = self.get_selected_model()
            part_keys = model.parts.keys()
            return model.parts[part_keys[self.currentPart]]

    # callback method for when the user selects a new slave
    def on_model_selected(self):
        model_index = self.cbx_model.getItemData(self.cbx_model.getCurrentItem())
        # If a different model has been selected, the GUI needs to be updated
        if model_index != self.currentModel:
            # Update the selected model
            self.currentModel = model_index
            #  Reset current selected part:
            self.currentPart = -1
            # Fetch the parts for the model
            models = mdb.models.keys()
            # Update the parts combo box
            reset_combo_box(self.cbx_part, mdb.models[models[model_index]].parts.keys())
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
            empty = []
            # Update the master and slave combo boxes
            reset_combo_box(self.cbx_master, empty)
            reset_combo_box(self.cbx_slave, empty)
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
                surfs = self.get_selected_part().surfaces.keys()
                # Update the master and slave combo boxes
                reset_combo_box(self.cbx_master, surfs)
                reset_combo_box(self.cbx_slave, surfs)
                self.on_master_selected()
                self.on_slave_selected()

    # callback method for when the user selects a new master surface
    def on_master_selected(self):
        # Undo highlighting of previous master
        if self.highlight_m is not '' and self.currentSlave != self.currentMaster:
            abaqusGui.sendCommand(self.highlight_m + '\nunhighlight(m)')
            self.highlight_m = ''
        # Check if there are items in the master list
        count = self.cbx_master.getNumItems()
        if count <= 0:
            # Reset currently selected master
            self.currentMaster = -1
            # Also reset the master exempt selection
            self.currentMExempt = -1
            self.check_ex_master.setCheck(False)
            self.check_ex_master.disable()
            reset_combo_box(self.cbx_ex_master, [])
            self.on_master_exempt_selected()
        else:
            master = self.cbx_master.getItemData(self.cbx_master.getCurrentItem())
            # If a different master has been selected, the GUI needs to be updated
            if master != self.currentMaster:
                # Update the selected master
                self.currentMaster = master
                # Highlight the current master
                self.highlight_m = 'm = (mdb.models[\'' + self.cbx_model.getItemText(self.currentModel) + '\']' +\
                                   '.parts[\'' + self.cbx_part.getItemText(self.currentPart) + '\']' +\
                                   '.surfaces[\'' + self.cbx_master.getItemText(self.currentMaster) + '\'],)'
                abaqusGui.sendCommand(self.highlight_m + '\nhighlight(m)')
                # Reset master exempts
                self.currentMExempt = -1
                self.check_ex_master.setCheck(False)
                self.check_ex_master.enable()
                reset_combo_box(self.cbx_ex_master, self.get_selected_part().sets.keys())
                self.on_master_exempt_selected()

    # callback method for when the user selects a new slave surface
    def on_slave_selected(self):
        # Undo highlighting of previous slave
        if self.highlight_s is not '' and self.currentSlave != self.currentMaster:
            abaqusGui.sendCommand(self.highlight_s + '\nunhighlight(s)')
            self.highlight_s = ''
        # Check if there are items in the slave list
        count = self.cbx_slave.getNumItems()
        if count <= 0:
            # Reset currently selected slave
            self.currentSlave = -1
            # Also reset the slave exempt selection
            self.currentSExempt = -1
            self.check_ex_slave.setCheck(False)
            self.check_ex_slave.disable()
            reset_combo_box(self.cbx_ex_master, [])
            self.on_slave_exempt_selected()
        else:
            slave = self.cbx_slave.getItemData(self.cbx_slave.getCurrentItem())
            # If a different slave has been selected, the GUI needs to be updated
            if slave != self.currentSlave:
                # Update the selected slave
                self.currentSlave = slave
                # Highlight the current slave
                self.highlight_s = 's = (mdb.models[\'' + self.cbx_model.getItemText(self.currentModel) + '\']' +\
                                   '.parts[\'' + self.cbx_part.getItemText(self.currentPart) + '\']' +\
                                   '.surfaces[\'' + self.cbx_slave.getItemText(self.currentSlave) + '\'],)'
                abaqusGui.sendCommand(self.highlight_s + '\nhighlight(s)')
                # Reset slave exempts
                self.currentSExempt = -1
                self.check_ex_slave.setCheck(False)
                self.check_ex_slave.enable()
                reset_combo_box(self.cbx_ex_slave, self.get_selected_part().sets.keys())
                self.on_slave_exempt_selected()

    # callback method for when the user selects a new master exemption set
    def on_master_exempt_selected(self):
        # Undo highlighting of previous master exempt
        if self.highlight_em is not '' and self.currentSExempt != self.currentMExempt:
            abaqusGui.sendCommand(self.highlight_em + '\nunhighlight(em)')
            self.highlight_em = ''
        # Check if there are items in the slave exempt list
        count = self.cbx_ex_master.getNumItems()
        if count <= 0:
            self.currentSExempt = -1
            reset_combo_box(self.cbx_ex_master, [])
            self.check_ex_master.setCheck(False)
            self.check_ex_master.disable()
        else:
            # If a different master has been selected, the GUI needs to be updated
            ex_master = self.cbx_ex_master.getItemData(self.cbx_ex_master.getCurrentItem())
            # Update the selected master exempt
            self.currentMExempt = ex_master
            # Check if the exempt combo box is enabled
            if self.check_ex_master.getCheck():
                # Make sure the combo box is enabled
                self.cbx_ex_master.enable()
                # Highlight the current master exempt
                self.highlight_em = 'em = (mdb.models[\'' + self.cbx_model.getItemText(self.currentModel) + '\']' +\
                                   '.parts[\'' + self.cbx_part.getItemText(self.currentPart) + '\']' +\
                                   '.sets[\'' + self.cbx_ex_master.getItemText(self.currentMExempt) + '\'],)'
                abaqusGui.sendCommand(self.highlight_em + '\nhighlight(em)')
            else:
                # Disable the combo box
                self.cbx_ex_master.disable()

    # callback method for when the user selects a new slave exemption set
    def on_slave_exempt_selected(self):
        # Undo highlighting of previous slave exempt
        if self.highlight_es is not '' and self.currentSExempt != self.currentMExempt:
            abaqusGui.sendCommand(self.highlight_es + '\nunhighlight(es)')
            self.highlight_es = ''
        # Check if there are items in the slave exempt list
        count = self.cbx_ex_slave.getNumItems()
        if count <= 0:
            self.currentSExempt = -1
            reset_combo_box(self.cbx_ex_slave, [])
            self.check_ex_slave.setCheck(False)
            self.check_ex_slave.disable()
        else:
            # If a different slave has been selected, the GUI needs to be updated
            ex_slave = self.cbx_ex_slave.getItemData(self.cbx_ex_slave.getCurrentItem())
            # Update the selected slave exempt
            self.currentSExempt = ex_slave
            # Check if the exempt combo box is enabled
            if self.check_ex_slave.getCheck():
                # Make sure the combo box is enabled
                self.cbx_ex_slave.enable()
                # Highlight the current slave exempt
                self.highlight_es = 'es = (mdb.models[\'' + self.cbx_model.getItemText(self.currentModel) + '\']' +\
                                   '.parts[\'' + self.cbx_part.getItemText(self.currentPart) + '\']' +\
                                   '.sets[\'' + self.cbx_ex_slave.getItemText(self.currentSExempt) + '\'],)'
                abaqusGui.sendCommand(self.highlight_es + '\nhighlight(es)')
            else:
                # Disable the combo box
                self.cbx_ex_slave.disable()

    # callback method for when the user toggles the master exemption checkbox
    def on_master_exempt_toggled(self):
        # check if the check box is ticked
        if self.check_ex_master.getCheck():
            # Enable the combo box
            self.cbx_ex_master.enable()
        else:
            # Disable the combo box
            self.cbx_ex_master.disable()
        # Update the selection (this takes care of highlighting etc.)
        self.on_master_exempt_selected()

    # callback method for when the user toggles the slave exemption checkbox
    def on_slave_exempt_toggled(self):
        # check if the check box is ticked
        if self.check_ex_slave.getCheck():
            # Enable the combo box
            self.cbx_ex_slave.enable()
        else:
            # Disable the combo box
            self.cbx_ex_slave.disable()
        # Update the selection (this takes care of highlighting etc.)
        self.on_slave_exempt_selected()

    # Fetches the index of the set for the exempted nodes of the master (can return -1, indicating none is selected)
    def get_master_exempt_index(self):
        if self.check_ex_master.getCheck():
            return self.currentMExempt
        else:
            return -1

    # Fetches the index of the set for the exempted nodes of the slave (can return -1, indicating none is selected)
    def get_slave_exempt_index(self):
        if self.check_ex_slave.getCheck():
            return self.currentSExempt
        else:
            return -1

    # callback method for when the user selects a new match plane
    def on_plane_selected(self):
        self.currentPlane = self.cbx_plane.getItemData(self.cbx_plane.getCurrentItem())

    # callback method for when the user selects a new mode
    def on_mode_selected(self):
        self.currentMode = self.cbx_mode.getItemData(self.cbx_mode.getCurrentItem())

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

    # Override from parent class
    def hide(self):
        # Undo highlighting of master surface
        if self.highlight_m is not '':
            abaqusGui.sendCommand(self.highlight_m + '\nunhighlight(m)')
            self.highlight_m = ''
        # Undo highlighting of slave surface
        if self.highlight_s is not '':
            abaqusGui.sendCommand(self.highlight_s + '\nunhighlight(s)')
            self.highlight_s = ''
        # Undo highlighting of master exempt
        if self.highlight_em is not '':
            abaqusGui.sendCommand(self.highlight_em + '\nunhighlight(em)')
            self.highlight_em = ''
        # Undo highlighting of slave exempt
        if self.highlight_es is not '':
            abaqusGui.sendCommand(self.highlight_es + '\nunhighlight(es)')
            self.highlight_es = ''
        # Call super method
        abaqusGui.AFXDataDialog.hide(self)


# Class for a dialog to confirm the user to apply the constraints after matching
class ConfirmDialog(abaqusGui.AFXDataDialog):
    # constructor
    def __init__(self, form, step, name, lines):
        # Call super constructor
        abaqusGui.AFXDataDialog.__init__(self, form, 'Confirm',
                                         self.CONTINUE | self.CANCEL,
                                         abaqusGui.DIALOG_ACTIONS_SEPARATOR)
        # Save the step
        self.step = step
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

    # Method to get the step associated with the current dialog
    def get_step(self):
        return self.step

    # method to fetch the currently defined name (must be implemented in all dialogs from which commands will be issued)
    def get_current_name(self):
        return self.name

    # method must be defined here as a pair command can be issued from this dialog, which will call this method
    def update_boundaries(self):
        # nothing to update
        pass


# Class for a dialog to inform the user that constraints can not be applied
class ErrorDialog(abaqusGui.AFXDataDialog):
    # constructor
    def __init__(self, form, step, lines):
        # Save the step
        self.step = step
        # Call super constructor
        abaqusGui.AFXDataDialog.__init__(self, form, 'Error', self.CANCEL,
                                         abaqusGui.DIALOG_ACTIONS_SEPARATOR)
        # Configure the continue button
        no_btn = self.getActionButton(self.ID_CLICKED_CANCEL)
        no_btn.setText('OK')
        # Display text
        for line in lines:
            abaqusGui.FXLabel(p=self, text=line)

    # Method to get the step associated with the current dialog
    def get_step(self):
        return self.step


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
        # Limit the maximum amount of visible items, else items can appear off screen
        cbx.setMaxVisible(min(10, len(keys)))
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


# Artificial class to quickly create a pick button and allow more control over it (unused currently)
class PickButton (abaqusGui.FXButton):
    # Constructor
    def __init__(self, parent, form, keyword, text, geometry, quantity, type_text, highlight_level):
        # Create necessary parent widgets
        self.frame = abaqusGui.FXHorizontalFrame(p=parent, opts=0, x=0, y=0, w=0, h=0, pl=0, pr=0, pt=0, pb=0,
                                                 hs=abaqusGui.DEFAULT_SPACING, vs=abaqusGui.DEFAULT_SPACING)
        self.frame.setSelector(99)
        self.label = abaqusGui.FXLabel(p=self.frame, text=text + ' ' + ' (None)', ic=None,
                                       opts=abaqusGui.LAYOUT_CENTER_Y | abaqusGui.JUSTIFY_LEFT)
        self.handler = PickHandler(form, keyword, 'Pick ' + type_text + ' ', geometry, quantity, self.label,
                                   highlight_level)
        # Call super constructor
        abaqusGui.FXButton.__init__(self, p=self.frame, text='\tPick ' + type_text + ' in Viewport',
                                    ic=abaqusGui.afxGetIcon('select', abaqusGui.AFX_ICON_SMALL),
                                    tgt=self.handler, sel=abaqusGui.AFXMode.ID_ACTIVATE,
                                    opts=abaqusGui.BUTTON_NORMAL | abaqusGui.LAYOUT_CENTER_Y,
                                    x=0, y=0, w=0, h=0, pl=2, pr=2, pt=1, pb=1)

    # Utility method to remove the highlighting and deselect the item, forwarded to the handler
    def reset_selection(self):
        self.handler.reset_selection()


# Pick handler class to handle the picking of objects (unused currently)
class PickHandler(abaqusGui.AFXProcedure):
    # Instance counter
    count = 0

    # Constructor
    def __init__(self, form, keyword, prompt, entities_to_pick, nr_to_pick, label, highlight_level):
        # Store fields
        self.form = form
        self.keyword = keyword
        self.prompt = prompt
        self.entities_to_pick = entities_to_pick
        self.nr_to_pick = nr_to_pick
        self. label = label
        self.label_text = label.getText()
        self.highlight_level = highlight_level
        # Super constructor
        abaqusGui.AFXProcedure.__init__(self, form.getOwner())
        # Increment counter and set name
        PickHandler.count = PickHandler.count + 1
        self.setModeName('PickHandler%d' % PickHandler.count)

    # Utility method to remove the highlighting and deselect the item
    def reset_selection(self):
        # Remove highlighting
        if self.keyword.getValue() and self.keyword.getValue()[0] != '<':
            abaqusGui.sendCommand(self.keyword.getSetupCommands() + '\nunhighlight(%s)' % self.keyword.getValue())
        # Reset keyword value
        self.keyword.setValueToDefault()
        # Reset the label
        self.label.setText(self.label_text.replace('Picked', 'None'))

    # Override from AFXProcedure to get the first step, return the pick step
    def getFirstStep(self):
        debug_message('Code reached first step in pick handler')
        return abaqusGui.AFXPickStep(self, self.keyword, self.prompt, self.entities_to_pick,
                                     self.nr_to_pick, self.highlight_level, sequenceStyle=abaqusGui.TUPLE)

    # Override from AFXProcedure to get the first step, used to change the label
    def getNextStep(self, prev):
        self.label.setText(self.label_text.replace('None', 'Picked'))
        return None

    # Override from AFXProcedure when the procedure is deactivated, use it to highlight the selected geometry
    def deactivate(self):
        abaqusGui.AFXProcedure.deactivate(self)
        # Send a command to highlight the selected face
        if self.keyword.getValue() and self.keyword.getValue()[0] != '<':
            abaqusGui.sendCommand(self.keyword.getSetupCommands() + '\nhighlight(%s)' % self.keyword.getValue())


# Arrays with the names of the match planes and mode options
PLANES = ['XY-plane', 'XZ-plane', 'YZ-plane']
MODES = ['Translational', 'Axial']


# Utility method to print a message to the console
def debug_message(msg):
    abaqusGui.getAFXApp().getAFXMainWindow().writeToMessageArea(msg)
