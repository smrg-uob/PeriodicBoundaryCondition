import abaqus
import customKernel
import customKernelSerialize


# Makes sure the registry exists
def create_registry():
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
                unpickled = pickle.loads(container)
                # Delete the container
                del abaqus.mdb.customData.matchers[key]
                # Store the unpickled matcher in the container
                abaqus.mdb.customData.MatcherContainer(key, unpickled)
                # Make sure the wrapped matcher is unpickled
                matcher = unpickled.get_matcher()
                if isinstance(matcher, customKernelSerialize.RawPickledObject):
                    # Unpickle the matcher
                    unpickled_matcher = pickle.loads(container)
                    # Store the unpickled matcher
                    unpickled.set_matcher(unpickled_matcher)
    else:
        # The repository does not exist, initialize it
        abaqus.mdb.customData.Repository('matchers', MatcherContainer)


# Runs the script to match the nodes
def match_nodes(name, model, part, master, slave, ex_m, ex_s, plane, sym):
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
                              plane, sym)
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
    def __init__(self, name, model, part, master, slave, ex_m, ex_s, plane, sym):
        # Set fields
        self.name = name
        self.modelName = model
        self.partName = part
        self.masterName = master
        self.slaveName = slave
        self.masterExemptName = ex_m
        self.slaveExemptName = ex_s
        self.plane_index = plane
        self.sym_index = sym
        # Define status flags
        self.valid = False
        self.matched = False
        self.paired = False
        # Initialize pair set
        self.pairs = set()
        # Initialize statistics
        self.n = 0
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

    # Getter for the symmetry index
    def get_sym_index(self):
        return self.sym_index

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

    # Returns a list of all the nodes to consider for the master surface (takes into account the exemption)
    def get_master_node_list(self):
        # Fetch all nodes from the master surface
        nodes_m = list(self.get_master_surface().nodes)
        set_ex_m = self.get_master_exempts()
        if set_ex_m is not None:
            # Exclude the exempted nodes
            for node in set_ex_m.nodes:
                try:
                    nodes_m.remove(node)
                except ValueError:
                    # Catch the exception, but don't do anything
                    pass
        return nodes_m

    # Returns a list of all the nodes to consider for the slave surface (takes into account the exemption)
    def get_slave_node_list(self):
        # Fetch all nodes from the slave surface
        nodes_s = list(self.get_slave_surface().nodes)
        set_ex_s = self.get_slave_exempts()
        if set_ex_s is not None:
            # Exclude the exempted nodes
            for node in set_ex_s.nodes:
                try:
                    nodes_s.remove(node)
                except ValueError:
                    # Catch the exception, but don't do anything
                    pass
        return nodes_s

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
            self.n = len(nodes_m)

    # Uniquely matches each of the master nodes to a slave node
    def match_nodes(self):
        if self.is_valid() and (not self.is_matched()):
            # reset the pairs
            self.pairs = set()
            # fetch nodes
            nodes_m = self.get_master_node_list()
            nodes_s = self.get_slave_node_list()
            # Store unmatched master and slave nodes
            masters_unmatched = [None] * self.n
            slaves_unmatched = [None] * self.n
            for i in range(0, self.n):
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
                    # Exact matching node found, create a new node pair
                    self.pairs.add(NodePair(master.label, slave.label, self.get_plane_index(), len(self.pairs)))
                    self.exact = self.exact + 1
                    # Remove the matched nodes from the unmatched set
                    masters_unmatched.remove(master)
                    slaves_unmatched.remove(slave)
            # Second, match the remaining nodes with the closest node
            if self.prox > 0:
                from math import sqrt
                for master in list(masters_unmatched):  # iterate over a copy since we will be removing entries
                    # Find closest slave node
                    slave = self.find_closest_slave_node(master, slaves_unmatched)
                    # Create new pair and update the counters
                    pair = NodePair(master.label, slave.label, self.get_plane_index(), len(self.pairs))
                    self.pairs.add(pair)
                    dist = sqrt(self.get_plane().dist_sq(master, slave))
                    # Remove the matched nodes from the unmatched set
                    masters_unmatched.remove(master)
                    slaves_unmatched.remove(slave)
                    # Update statistics
                    if self.mn == 0:
                        self.mn = dist
                        self.mx = dist
                        self.tot = dist
                    else:
                        self.mn = min(dist, self.mn)
                        self.mx = max(dist, self.mx)
                        self.tot = self.tot + dist
            self.matched = True

    # Gets the total number of node pairs
    def get_pair_count(self):
        return self.n

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
            for pair in self.pairs:
                pair.apply_constraint(self.get_model(), self.get_part(), self.name, self.sym_index)
            self.paired = True

    # Removes the constraint for a periodic boundary condition for all paired nodes
    def delete_constraints(self):
        if self.is_paired():
            for pair in self.pairs:
                # Delete constraint
                pair.remove_constraint(self.get_model(), self.name, self.sym_index)

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
                       ', Proximity matches: ' + str(self.get_proximity_count()) + '/' + str(self.get_pair_count()))
            msg.append('From proximity matches: min = ' + str(self.get_min_proximity()) + ', max = ' +
                       str(self.get_max_proximity()) + ', avg = ' + str(self.get_av_proximity()))
        else:
            msg.append('Amount of nodes on the master and slave surfaces are not equal: nodes could not be paired')
        return msg


# A class which represent two paired nodes: one master and one slave.
# A pointer to the matching plane is stored as well
class NodePair:
    # Constructor
    def __init__(self, m, s, plane, index):
        self.master_label = m
        self.slave_label = s
        self.plane_index = plane
        self.index = index

    # Getter for the master label
    def get_master_label(self):
        return self.master_label

    # Getter for the slave label
    def get_slave_label(self):
        return self.slave_label

    def get_plane(self):
        return PLANES[self.plane_index]

    # Applies the constraints and sets for a periodic boundary condition on the two nodes
    def apply_constraint(self, model, part, name, sym):
        self.get_plane().apply_constraint(model, part, self.get_master_label(), self.get_slave_label(),
                                    'pbc_' + name + '_node_' + str(self.index), sym)

    # Removes the constraints and sets for the periodic boundary condition on the two nodes
    def remove_constraint(self, model, name, sym):
        self.get_plane().remove_constraint(model, 'pbc_' + name + '_node_' + str(self.index), sym)


# A class which represents a match plane
# Contains functionality to check if two nodes are matching, to calculate the projected distance,
# and apply the constraint for a periodic boundary condition
# (currently only works for the XY-, XZ- and YZ-planes)
# TODO: extend for any arbitrary plane
class MatchPlane:
    # Constructor
    def __init__(self, i, j):
        self.i = i
        self.j = j

    # Checks if nodes match, meaning the in-plane coordinates are equal
    def do_nodes_match(self, n1, n2):
        c1 = n1.coordinates
        c2 = n2.coordinates
        return (c1[self.i] == c2[self.i]) and (c1[self.j] == c2[self.j])

    # Calculates the  in-plane distance between two nodes
    def dist_sq(self, n1, n2):
        c1 = n1.coordinates
        c2 = n2.coordinates
        d_i = c1[self.i] - c2[self.i]
        d_j = c1[self.j] - c2[self.j]
        return d_i * d_i + d_j * d_j

    # Creates the sets and constraints for a periodic boundary condition between two nodes
    def apply_constraint(self, model, part, master_label, slave_label, name, sym):
        # Define the sets
        set_master = name + '_master'
        nodes_master = model.rootAssembly.instances[part.name + '-1'].nodes.sequenceFromLabels((master_label,))
        model.rootAssembly.Set(name=set_master, nodes=nodes_master)
        set_slave = name + '_slave'
        nodes_slave = model.rootAssembly.instances[part.name + '-1'].nodes.sequenceFromLabels((slave_label,))
        model.rootAssembly.Set(name=set_slave, nodes=nodes_slave)
        # Add the constraints for the in plane displacements
        axes = ['x', 'y', 'z']
        model.Equation(name='eq_' + axes[self.i] + '_' + name,
                       terms=((1.0, set_master, self.i + 1), (-1.0, set_slave, self.i + 1)))
        model.Equation(name='eq_' + axes[self.j] + '_' + name,
                       terms=((1.0, set_master, self.j + 1), (-1.0, set_slave, self.j + 1)))
        # Add the constraint for the normal displacement
        k = 3 - self.i - self.j
        if sym == 0:
            # Asymmetric
            model.Equation(name='eq_' + axes[k] + '_' + name,
                           terms=((1.0, set_master, k + 1), (-1.0, set_slave, k + 1)))
        elif sym == 1:
            # Symmetric
            model.Equation(name='eq_' + axes[k] + '_' + name,
                           terms=((1.0, set_master, k + 1), (1.0, set_slave, k + 1)))
        else:
            # Ignore
            return

    # Deletes the sets and constraints for a periodic boundary condition between two nodes
    def remove_constraint(self, model, name, sym):
        # Delete the constraints
        axes = ['x', 'y', 'z']
        del model.constraints['eq_' + axes[self.i] + '_' + name]
        del model.constraints['eq_' + axes[self.j] + '_' + name]
        if sym == 0 or sym == 1:
            k = 3 - self.i - self.j
            del model.constraints['eq_' + axes[k] + '_' + name]
        # Delete the sets
        del model.rootAssembly.sets[name + '_master']
        del model.rootAssembly.sets[name + '_slave']


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


# Static array of the three possible match planes
PLANES = (MatchPlane(0, 1), MatchPlane(0, 2), MatchPlane(1, 2))
