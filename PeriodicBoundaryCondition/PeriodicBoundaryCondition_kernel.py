import abaqus
import abaqusConstants
import customKernel
import customKernelSerialize
from math import sqrt


# Makes sure the registry exists
def create_registry():
    # Check if the repository exists or not
    if hasattr(abaqus.mdb.customData, 'matchers'):
        # The repository exists, now make sure it is unpickled
        if (isinstance(abaqus.mdb.customData.matchers, customKernelSerialize.RawPickledObject) or
                isinstance(abaqus.mdb.customData.MatcherContainer, customKernelSerialize.RawPickledObject)):
            # If the repository is in an unpickled state, we need to unpickle it manually
            import pickle
            # Unpickle the matchers if necessary
            if isinstance(abaqus.mdb.customData.matchers, customKernelSerialize.RawPickledObject):
                unpickled = pickle.loads(abaqus.mdb.customData.matchers.pickleString)
            else:
                unpickled = abaqus.mdb.customData.matchers
            # Delete the unpickled data
            del abaqus.mdb.customData.matchers
            del abaqus.mdb.customData.MatcherContainer
            # Reinitialize the repository
            abaqus.mdb.customData.Repository('matchers', MatcherContainer)
            # Repopulate the registry
            for key in unpickled.keys():
                # fetch unpickled matcher
                container = unpickled[key]
                # store the matcher in a new container in the registry
                abaqus.mdb.customData.MatcherContainer(container.get_name(), container.get_matcher())
        # Make sure the containers are unpickled as well
        for key in abaqus.mdb.customData.matchers.keys():
            container = abaqus.mdb.customData.matchers[key]
            if isinstance(container, customKernelSerialize.RawPickledObject):
                # If the matcher is in an unpickled state, we need to unpickle it manually
                import pickle
                # Unpickle the container
                container = pickle.loads(container)
                # Delete the container
                del abaqus.mdb.customData.matchers[key]
                # Store the unpickled matcher in the container
                abaqus.mdb.customData.MatcherContainer(key, container)
            # Make sure the wrapped matcher is unpickled as well
            matcher = container.get_matcher()
            if isinstance(matcher, customKernelSerialize.RawPickledObject):
                import pickle
                # Unpickle the matcher
                unpickled_matcher = pickle.loads(matcher)
                # Store the unpickled matcher
                container.set_matcher(unpickled_matcher)
    else:
        # The repository does not exist, initialize it
        abaqus.mdb.customData.Repository('matchers', MatcherContainer)


# Runs the script to match the nodes
def match_nodes(name, model, part, master, slave, ex_m, ex_s, plane, mode):
    # Create a new matcher if one does not exist yet
    if not abaqus.mdb.customData.matchers.has_key(name):
        # Fetch objects and keys
        model_keys = abaqus.mdb.models.keys()
        model_obj = abaqus.mdb.models[model_keys[model]]
        part_keys = model_obj.parts.keys()
        part_obj = model_obj.parts[part_keys[part]]
        surf_keys = part_obj.surfaces.keys()
        set_keys = part_obj.sets.keys()
        # Create new matcher
        matcher = NodeMatcher(name, model_keys[model], part_keys[part], surf_keys[master], surf_keys[slave],
                              '' if ex_m < 0 else set_keys[ex_m], '' if ex_s < 0 else set_keys[ex_s],
                              plane, mode)
        # Store the matcher in the custom data
        abaqus.mdb.customData.MatcherContainer(name, matcher)
    # Fetch the matcher
    matcher = abaqus.mdb.customData.matchers[name].get_matcher()
    # Match the nodes if necessary
    if not matcher.is_matched():
        matcher.match_nodes()


# Runs the script to apply the constraints
def apply_constraints(name):
    # fetch matcher
    if abaqus.mdb.customData.matchers.has_key(name):
        matcher = abaqus.mdb.customData.matchers[name].get_matcher()
        matcher.apply_constraints()


# Runs the script to remove the constraints
def remove_constraints(name):
    # fetch matcher
    if abaqus.mdb.customData.matchers.has_key(name):
        matcher = abaqus.mdb.customData.matchers[name].get_matcher()
        matcher.delete_constraints()
        del abaqus.mdb.customData.matchers[name]


# Wrapper class to store matchers in the mdb custom data, also helps with the manual unpickling
class MatcherContainer(customKernel.CommandRegister):
    # Constructor
    def __init__(self, name, matcher):
        # Super constructor
        customKernel.CommandRegister.__init__(self)
        # Set name
        self.name = name
        # Store matcher
        self.matcher = matcher

    # Getter for the name
    def get_name(self):
        return self.name

    # Getter for the matcher
    def get_matcher(self):
        return self.matcher

    # Setter for the matcher
    def set_matcher(self, matcher):
        self.matcher = matcher


# A helper class to match the master and slave nodes, and apply the constraint for periodic boundary conditions
class NodeMatcher:
    def __init__(self, name, model, part, master, slave, ex_m, ex_s, plane, mode):
        # Set fields
        self.name = name
        self.modelName = model
        self.partName = part
        self.masterName = master
        self.slaveName = slave
        self.masterExemptName = ex_m
        self.slaveExemptName = ex_s
        self.plane_index = plane
        self.mode_index = mode
        # Define status flags
        self.valid = False
        self.matched = False
        self.paired = False
        # Initialize pair sets
        self.pairs = list()
        # Initialize statistics
        self.number = 0
        self.exempts = 0
        self.exact = 0
        self.prox = 0
        self.mn = 0
        self.mx = 0
        self.tot = 0
        # Validate
        self.check_validity()

    # getter for the name of the periodic boundary condition
    def get_name(self):
        return self.name

    # getter for the name of the model
    def get_model_name(self):
        return self.modelName

    # getter for the name of the part
    def get_part_name(self):
        return self.partName

    # getter for the name of the master surface
    def get_master_name(self):
        return self.masterName

    # getter for the name of the slave surface
    def get_slave_name(self):
        return self.slaveName

    # Getter for the match plane index
    def get_plane_index(self):
        return self.plane_index

    # Getter for the mode index
    def get_mode_index(self):
        return self.mode_index

    # Fetches the match plane
    def get_plane(self):
        return PLANES[self.get_plane_index()]

    # Fetches the model Abaqus object
    def get_model(self):
        return abaqus.mdb.models[self.get_model_name()]

    # Fetches the part Abaqus object
    def get_part(self):
        return self.get_model().parts[self.get_part_name()]

    # Fetches the master surface Abaqus object
    def get_master_surface(self):
        return self.get_part().surfaces[self.get_master_name()]

    # Fetches the slave surface Abaqus object
    def get_slave_surface(self):
        return self.get_part().surfaces[self.get_slave_name()]

    # Fetches the master exempt Abaqus set (can be None)
    def get_master_exempts(self):
        if self.masterExemptName is '':
            return None
        return self.get_part().sets[self.masterExemptName]

    # Fetches the slave exempt Abaqus set (can be None)
    def get_slave_exempts(self):
        if self.slaveExemptName is '':
            return None
        return self.get_part().sets[self.slaveExemptName]

    # Getter for the flag which tracks if the match configuration is valid
    def is_valid(self):
        return self.valid

    # Getter for the flag which tracks if the node pairs have been matched
    def is_matched(self):
        return self.matched

    # Getter for the flag which tracks if the node pairs have been paired
    def is_paired(self):
        return self.paired

    # Returns a list of all the nodes to consider for the master surface (ignores the exemption)
    def get_master_node_list(self):
        # Fetch all nodes from the master surface
        return list(self.get_master_surface().nodes)

    # Returns a list of all the nodes to consider for the slave surface (ignores the exemption)
    def get_slave_node_list(self):
        # Fetch all nodes from the slave surface
        return list(self.get_slave_surface().nodes)

    # Returns a list of all the exempted master nodes
    def get_master_exempt_list(self):
        set_ex_m = self.get_master_exempts()
        if set_ex_m is None:
            return list()
        return list(set_ex_m.nodes)

    # Returns a set of all the exempted slave nodes
    def get_slave_exempt_list(self):
        set_ex_s = self.get_slave_exempts()
        if set_ex_s is None:
            return list()
        return list(set_ex_s.nodes)

    # Checks if the matching setup is valid before execution
    # (meaning the master and slaves contain an equal number of nodes)
    def check_validity(self):
        nodes_m = self.get_master_node_list()
        nodes_s = self.get_slave_node_list()
        n_m = len(nodes_m)
        n_s = len(nodes_s)
        self.valid = n_m == n_s
        # Keep track of total number of nodes
        if self.is_valid():
            self.number = len(nodes_m)

    # Uniquely matches each of the master nodes to a slave node
    def match_nodes(self):
        if self.is_valid() and (not self.is_matched()):
            # reset the pairs
            self.pairs = list()
            # fetch nodes
            nodes_m = self.get_master_node_list()
            nodes_s = self.get_slave_node_list()
            # fetch exempts
            exempts_m = self.get_master_exempt_list()
            exempts_s = self.get_slave_exempt_list()
            # Store unmatched master and slave nodes
            masters_unmatched = [None] * self.number
            slaves_unmatched = [None] * self.number
            for i in range(0, self.number):
                masters_unmatched[i] = nodes_m[i]
                slaves_unmatched[i] = nodes_s[i]
            # First match all nodes whose coordinates match exactly
            for master in list(masters_unmatched):  # iterate over a copy since we will be removing entries
                slave = self.find_matching_slave_node(master, slaves_unmatched)
                if slave is None:
                    # No exact matching node found, continue
                    self.prox = self.prox + 1
                    continue
                else:
                    # Check for exemption
                    excl = False
                    if master in exempts_m:
                        excl = True
                    if slave in exempts_s:
                        excl = True
                    if excl:
                        self.exempts += 1
                    else:
                        # Exact matching node found, create a new node pair
                        self.pairs.append(NodePair(self.get_name(), master.label, slave.label,
                                                   master.coordinates, slave.coordinates,
                                                   self.get_plane_index(), excl, len(self.pairs)))
                        self.exact = self.exact + 1
                    # Remove the matched nodes from the unmatched set
                    masters_unmatched.remove(master)
                    slaves_unmatched.remove(slave)
            # Second, match the remaining nodes with the closest node
            if self.prox > 0:
                for master in list(masters_unmatched):  # iterate over a copy since we will be removing entries
                    # Find closest slave node
                    slave = self.find_closest_slave_node(master, slaves_unmatched)
                    # Check for exemption
                    excl = False
                    if master in exempts_m:
                        excl = True
                    if slave in exempts_s:
                        excl = True
                    if excl:
                        self.exempts += 1
                    else:
                        # Create new pair and update the counters
                        pair = NodePair(self.get_name(), master.label, slave.label,
                                        master.coordinates, slave.coordinates,
                                        self.get_plane_index(), excl, len(self.pairs))
                        self.pairs.append(pair)
                        dist = sqrt(self.get_plane().dist_sq(master, slave))
                        # Update statistics
                        if self.mn == 0:
                            self.mn = dist
                            self.mx = dist
                            self.tot = dist
                        else:
                            self.mn = min(dist, self.mn)
                            self.mx = max(dist, self.mx)
                            self.tot = self.tot + dist
                    # Remove the matched nodes from the unmatched set
                    masters_unmatched.remove(master)
                    slaves_unmatched.remove(slave)
            self.matched = True

    # Gets the total number of node pairs
    def get_pair_count(self):
        return self.number

    # Gets the total number of exempted node pairs
    def get_exempt_count(self):
        return self.exempts

    # Gets the number of node pairs which were exactly matched
    def get_exact_count(self):
        return self.exact

    # Gets the number of node pairs which were matched by proximity
    def get_proximity_count(self):
        return self.prox

    # Gets the minimum distance of the node pairs matched by proximity
    def get_min_proximity(self):
        return self.mn

    # Gets the maximum distance of the node pairs matched by proximity
    def get_max_proximity(self):
        return self.mx

    # Gets the average distance of the node pairs matched by proximity
    def get_av_proximity(self):
        return 0 if self.get_proximity_count() is 0 else self.tot / self.get_proximity_count()

    # Applies the constraint for a periodic boundary condition to all paired nodes
    def apply_constraints(self):
        if self.is_matched() and (not self.is_paired()):
            # Define the sets for each node pair
            for pair in self.pairs:
                # Create the sets
                pair.create_sets(self.get_model(), self.get_part())
            # Define a running index
            index = 0
            # Define the datum ID (-1 means no datum should be used, and the global coordinate system will be used)
            datum_id = -1
            # For axial periodic boundary conditions, a cylindrical coordinate system needs to be defined and used
            if self.get_mode_index() == 1:
                # Create a cylindrical coordinate system and store its id
                datum_id = self.get_plane().create_cylindrical_datum('CSYS_PBC_' + self.get_name(), self.get_model()).id
            # Add the constraints for the displacements
            for pair_index in range(0, len(self.pairs)):
                # Increment the index
                index += 1
                # Fetch the pair
                pair = self.pairs[pair_index]
                # Do not apply the constraint in case of an exempted node pair
                if pair.is_exempted():
                    continue
                # Define the  terms
                if self.get_mode_index() == 0:
                    terms_i = self.define_translational_terms(pair_index, self.get_plane().get_first_axis_index() + 1,
                                                              datum_id)
                    terms_j = self.define_translational_terms(pair_index, self.get_plane().get_second_axis_index() + 1,
                                                              datum_id)
                    terms_k = self.define_translational_terms(pair_index, self.get_plane().get_normal_axis_index() + 1,
                                                              datum_id)
                else:
                    axis_index = self.get_plane().get_normal_axis_index() + 1
                    terms_i = self.define_axial_terms(pair_index, self.get_plane().get_first_axis_index() + 1,
                                                      axis_index, datum_id)
                    terms_j = self.define_axial_terms(pair_index, self.get_plane().get_second_axis_index() + 1,
                                                      axis_index, datum_id)
                    terms_k = self.define_axial_terms(pair_index, self.get_plane().get_normal_axis_index() + 1,
                                                      axis_index, datum_id)
                # Define the names
                name_i = 'eq_' + AXES[self.get_plane().get_first_axis_index()] + '_' + pair.get_name()
                name_j = 'eq_' + AXES[self.get_plane().get_second_axis_index()] + '_' + pair.get_name()
                name_k = 'eq_' + AXES[self.get_plane().get_normal_axis_index()] + '_' + pair.get_name()
                # Add the equations
                if len(terms_i) > 0:
                    self.get_model().Equation(name=name_i, terms=terms_i)
                if len(terms_j) > 0:
                    self.get_model().Equation(name=name_j, terms=terms_j)
                if len(terms_k) > 0:
                    self.get_model().Equation(name=name_k, terms=terms_k)
            # Update paired status
            self.paired = True

    # Defines the terms for a translational constraint: (u_i - u'_i) - (u_j - u'_j)  = 0
    def define_translational_terms(self, pair_index, axis_index, datum_id):
        # Define list
        terms = list()
        next_index = pair_index + 1
        # Do not add constraints to the last node
        if next_index < len(self.pairs):
            # Fetch the pair
            pair = self.pairs[pair_index]
            # Add the terms for the own pair
            if datum_id < 0:
                terms.append((1.0, pair.get_master_set_name(), axis_index))
                terms.append((-1.0, pair.get_slave_set_name(), axis_index))
            else:
                terms.append((1.0, pair.get_master_set_name(), axis_index, datum_id))
                terms.append((-1.0, pair.get_slave_set_name(), axis_index, datum_id))
            # Add the terms for the next pair
            next_pair = self.pairs[next_index]
            if datum_id < 0:
                terms.append((-1.0, next_pair.get_master_set_name(), axis_index))
                terms.append((1.0, next_pair.get_slave_set_name(), axis_index))
            else:
                terms.append((-1.0, next_pair.get_master_set_name(), axis_index, datum_id))
                terms.append((1.0, next_pair.get_slave_set_name(), axis_index, datum_id))
        # Return the terms
        return terms

    # Defines the terms for an axial constraint:
    def define_axial_terms(self, pair_index, axis_index, axial_index, datum_id):
        if axis_index == axial_index:
            # In case of the axial direction, the translational constraints can be used
            return self.define_translational_terms(pair_index, axis_index, datum_id)
        else:
            # For the radial and hoop directions, specific constraints need to be applied
            if axial_index == 3:
                # The XY-plane is the polar plane
                if axis_index == 1:
                    # return the radial terms
                    return self.define_radial_terms(pair_index, 0, 1, datum_id)
                else:
                    # return the hoop terms
                    return self.define_hoop_terms(pair_index, 0, 1, datum_id)
            elif axial_index == 2:
                # The XZ-plane is the polar plane
                if axis_index == 1:
                    # return the radial terms
                    return self.define_radial_terms(pair_index, 0, 2, datum_id)
                else:
                    # return the hoop terms
                    return self.define_hoop_terms(pair_index, 0, 2, datum_id)
            else:
                # The YZ-plane is the polar plane
                if axis_index == 2:
                    # return the radial terms
                    return self.define_radial_terms(pair_index, 1, 2, datum_id)
                else:
                    # return the hoop terms
                    return self.define_hoop_terms(pair_index, 1, 2, datum_id)

    # Defines the terms for a radial constraint: (u_i - u'_i) = 0
    def define_radial_terms(self, pair_index, radial_index, hoop_index, datum_id):
        # Fetch the pair
        pair = self.pairs[pair_index]
        # Define list
        terms = list()
        terms.append((1, pair.get_master_set_name(), radial_index + 1, datum_id))
        terms.append((-1, pair.get_slave_set_name(), radial_index + 1, datum_id))
        # Return the terms
        return terms

    # Defines the terms for a hoop constraint: (u_i - u'_i)/r_i - (u_j - u'_j)/r_j = 0
    def define_hoop_terms(self, pair_index, radial_index, hoop_index, datum_id):
        # Define list
        terms = list()
        next_index = pair_index + 1
        # Do not constrain the last node
        if next_index < len(self.pairs):
            # Add the terms for the own pair
            pair = self.pairs[pair_index]
            self.add_hoop_terms(terms, pair, radial_index, hoop_index, False, datum_id)
            # Add the terms for the next pair
            next_pair = self.pairs[next_index]
            self.add_hoop_terms(terms, next_pair, radial_index, hoop_index, True, datum_id)
        # Return the terms
        return terms

    @staticmethod
    def add_hoop_terms(terms, pair, radial_index, hoop_index, inverse, datum_id):
        # Define master radius
        c_m = pair.get_master_coordinates()
        r_m = sqrt(c_m[radial_index]*c_m[radial_index] + c_m[hoop_index]*c_m[hoop_index])
        # Define slave radius (can differ slightly in case the pair is not an exact match)
        c_s = pair.get_slave_coordinates()
        r_s = sqrt(c_s[radial_index]*c_s[radial_index] + c_s[hoop_index]*c_s[hoop_index])
        # Append to the list
        f = -1 if inverse else 1
        terms.append((1.0*f/r_m, pair.get_master_set_name(), hoop_index + 1, datum_id))
        terms.append((-1.0*f/r_s, pair.get_slave_set_name(), hoop_index + 1, datum_id))

    # Removes the constraint for a periodic boundary condition for all paired nodes
    def delete_constraints(self):
        if self.is_paired():
            if self.get_mode_index() == 1:
                # Delete the cylindrical coordinate system
                try:
                    datum_name = 'CSYS_PBC_' + self.get_name()
                    del self.get_model().rootAssembly.features[datum_name]
                except KeyError:
                    pass
            for pair in self.pairs:
                # Delete the sets
                pair.remove_sets(self.get_model())
                # Skip the removal of the equations in case of an exempted node pair as they will not exist
                if pair.is_exempted():
                    continue
                # Delete the equations
                try:
                    del self.get_model().constraints[
                        'eq_' + AXES[self.get_plane().get_first_axis_index()] + '_' + pair.get_name()]
                except KeyError:
                    pass
                try:
                    del self.get_model().constraints[
                        'eq_' + AXES[self.get_plane().get_second_axis_index()] + '_' + pair.get_name()]
                except KeyError:
                    pass
                try:
                    del self.get_model().constraints[
                        'eq_' + AXES[self.get_plane().get_normal_axis_index()] + '_' + pair.get_name()]
                except KeyError:
                    pass

    # Finds the exact matching slave node from the unmatched nodes to a given master node
    # Returns None if no exact matching slave node is found
    def find_matching_slave_node(self, master, slaves):
        slave = None
        for node in slaves:
            if self.get_plane().do_nodes_match(master, node):
                slave = node
                break
        return slave

    # Finds the closest slave node from the unmatched nodes to a given master node
    def find_closest_slave_node(self, master, slaves):
        slave = None
        dist = -1
        for node in slaves:
            # Calculate squared distance
            new_dist = self.get_plane().dist_sq(master, node)
            # If the distance is smaller than the current closest node, update both
            if (new_dist < dist) or (dist < 0):
                slave = node
                dist = new_dist
        return slave

    # Gets the status message for the confirmation dialog between the matching and pairing steps
    def get_status_messages(self):
        msg = []
        if self.is_valid():
            msg.append('Exact matches: ' + str(self.get_exact_count()) + '/' + str(self.get_pair_count()) +
                       ', Proximity matches: ' + str(self.get_proximity_count()) + '/' + str(self.get_pair_count()) +
                       ', Exempts: ' + str(self.get_exempt_count()) + '/' + str(self.get_pair_count()))
            msg.append('From proximity matches: min = ' + str(self.get_min_proximity()) + ', max = ' +
                       str(self.get_max_proximity()) + ', avg = ' + str(self.get_av_proximity()))
        else:
            msg.append('Amount of nodes on the master and slave surfaces are not equal: nodes could not be paired')
        return msg


# A class which represent two paired nodes: one master and one slave.
# A pointer to the matching plane is stored as well
class NodePair:
    # Constructor
    def __init__(self, name, m, s, c_m, c_s, plane, exempted, index):
        self.name = 'pbc_' + name + '_node_' + str(index)
        self.master_label = m
        self.slave_label = s
        self.master_coordinates = c_m
        self.slave_coordinates = c_s
        self.plane_index = plane
        self.exempted = exempted
        self.index = index

    # Getter for the name of the pair
    def get_name(self):
        return self.name

    # Getter for the master label
    def get_master_label(self):
        return self.master_label

    # Getter for the slave label
    def get_slave_label(self):
        return self.slave_label

    # Getter for the coordinates of the master node
    def get_master_coordinates(self):
        return self.master_coordinates

    # Getter for the coordinates of the slave node
    def get_slave_coordinates(self):
        return self.slave_coordinates

    # Checks if this node pair is exempted from the pbc
    def is_exempted(self):
        return self.exempted

    # Getter for the index
    def get_index(self):
        return self.index

    # Getter for the match plane
    def get_plane(self):
        return PLANES[self.plane_index]

    # Creates the name for the set for the master node
    def get_master_set_name(self):
        return self.get_name() + '_master'

    # Creates the name for the set for the slave node
    def get_slave_set_name(self):
        return self.get_name() + '_slave'

    # Creates the sets for the master and slave nodes
    def create_sets(self, model, part):
        # Set for the master node
        set_master = self.get_master_set_name()
        master_label = self.get_master_label()
        nodes_master = model.rootAssembly.instances[part.name + '-1'].nodes.sequenceFromLabels((master_label,))
        model.rootAssembly.Set(name=set_master, nodes=nodes_master)
        # Set for the slave node
        set_slave = self.get_slave_set_name()
        slave_label = self.get_slave_label()
        nodes_slave = model.rootAssembly.instances[part.name + '-1'].nodes.sequenceFromLabels((slave_label,))
        model.rootAssembly.Set(name=set_slave, nodes=nodes_slave)

    # Removes the sets for the master and slave nodes
    def remove_sets(self, model):
        # Delete the sets
        del model.rootAssembly.sets[self.get_master_set_name()]
        del model.rootAssembly.sets[self.get_slave_set_name()]


# A class which represents a match plane
# Contains functionality to check if two nodes are matching, to calculate the projected distance,
# and apply the constraint for a periodic boundary condition
# (currently only works for the XY-, XZ- and YZ-planes)
# TODO: extend for any arbitrary plane
class MatchPlane:
    # Constructor
    def __init__(self, i, j):
        self.i = min(i, j)
        self.j = max(i, j)

    def get_first_axis_index(self):
        return self.i

    def get_second_axis_index(self):
        return self.j

    def get_normal_axis_index(self):
        return 3 - self.i - self.j

    # Checks if nodes match, meaning the in-plane coordinates are equal
    def do_nodes_match(self, n1, n2):
        c1 = n1.coordinates
        c2 = n2.coordinates
        return (c1[self.i] == c2[self.i]) and (c1[self.j] == c2[self.j])

    # Calculates the square of the in-plane distance between two nodes
    def dist_sq(self, n1, n2):
        c1 = n1.coordinates
        c2 = n2.coordinates
        d_i = c1[self.i] - c2[self.i]
        d_j = c1[self.j] - c2[self.j]
        return d_i * d_i + d_j * d_j

    # Creates and returns a cylindrical coordinate system datum
    def create_cylindrical_datum(self, name, model):
        normal = self.get_normal_axis_index()
        if normal == 0:
            # X axis is the axial direction
            return model.rootAssembly.DatumCsysByThreePoints(coordSysType=abaqusConstants.CYLINDRICAL, origin=(0, 0, 0),
                                                             point1=(0, 1, 0), point2=(0, 0, 1), name=name)
        elif normal == 1:
            # Y axis is the axial direction
            return model.rootAssembly.DatumCsysByThreePoints(coordSysType=abaqusConstants.CYLINDRICAL, origin=(0, 0, 0),
                                                             point1=(1, 0, 0), point2=(0, 0, 1), name=name)
        else:
            # Z axis is the axial direction
            return model.rootAssembly.DatumCsysByThreePoints(coordSysType=abaqusConstants.CYLINDRICAL, origin=(0, 0, 0),
                                                             point1=(1, 0, 0), point2=(0, 1, 0), name=name)


# Utility method to print a message to the console
def debug_message(msg):
    print(msg)


# Utility method to inspect an object and print its attributes and methods to the console
def inspect_object(obj):
    import inspect
    members = inspect.getmembers(obj)
    for member in members:
        debug_message('---------------------')
        debug_message(str(member))
    debug_message('---------------------')


# Static arrays of the three possible match planes and axis labels
PLANES = (MatchPlane(0, 1), MatchPlane(0, 2), MatchPlane(1, 2))
AXES = ['x', 'y', 'z']
