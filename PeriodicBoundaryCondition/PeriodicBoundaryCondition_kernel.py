import abaqus
import customKernel
import customKernelSerialize
import pickle


# Makes sure the registry exists
def create_registry():
    debug_message('Creating registry')
    if hasattr(abaqus.mdb.customData, 'matchers'):
        # The repository exists, now make sure it is unpickled
        if isinstance(abaqus.mdb.customData.matchers, customKernelSerialize.RawPickledObject):
            debug_message('Matcher repository has not been unpickled, unpickling manually')
            # Unpickle the matchers
            unpickled_objects = pickle.loads(abaqus.mdb.customData.matchers.pickleString)
            # Delete the unpickled repository and method
            del abaqus.mdb.customData.matchers
            del abaqus.mdb.customData.MatcherContainer
            # Reinitialize the repository
            abaqus.mdb.customData.Repository('matchers', MatcherContainer)
            # Repopulate the registry
            for key in unpickled_objects.keys():
                # fetch unpickled matcher
                container = unpickled_objects[key]
                # store the matcher in a new container in the registry
                abaqus.mdb.customData.MatcherContainer(container.get_name(), container.get_matcher())
    else:
        # The repository does not exist, initialize it
        abaqus.mdb.customData.Repository('matchers', MatcherContainer)


# Runs the script to match the nodes
def match_nodes(name, model, part, master, slave, plane, sym):
    debug_message('Matching nodes for ' + name)
    # fetch matcher
    if not abaqus.mdb.customData.matchers.has_key(name):
        # Fetch objects and keys
        model_keys = abaqus.mdb.models.keys()
        model_obj = abaqus.mdb.models[model_keys[model]]
        part_keys = model_obj.parts.keys()
        part_obj = model_obj.parts[part_keys[part]]
        surf_keys = part_obj.surfaces.keys()
        # Create new matcher
        matcher = NodeMatcher(name, model_keys[model], part_keys[part],
                              surf_keys[master], surf_keys[slave], PLANES[plane], sym)
        # Store the matcher in the custom data
        abaqus.mdb.customData.MatcherContainer(name, matcher)
    matcher = abaqus.mdb.customData.matchers[name].get_matcher()
    # Match the nodes if necessary
    if not matcher.is_matched():
        matcher.match_nodes()


# Runs the script to apply the constraints
def apply_constraints(name):
    debug_message('Pairing nodes for ' + name)
    # fetch matcher
    if abaqus.mdb.customData.matchers.has_key(name):
        matcher = abaqus.mdb.customData.matchers[name].get_matcher()
        matcher.apply_constraints()
    else:
        debug_message('No such constraint')
        pass


def remove_constraints(name):
    debug_message('Removing constraints for ' + name)
    # fetch matcher
    if abaqus.mdb.customData.matchers.has_key(name):
        matcher = abaqus.mdb.customData.matchers[name].get_matcher()
        matcher.delete_constraints()
        del abaqus.mdb.customData.matchers[name]
    else:
        debug_message('No such constraint')
        pass


# Wrapper class to store matchers in the mdb custom data, also helps with the manual unpickling
class MatcherContainer(customKernel.CommandRegister):
    def __init__(self, name, matcher):
        # Super constructor
        customKernel.CommandRegister.__init__(self)
        # Set name
        self.name = name
        # Store matcher
        self.matcher = matcher

    def get_name(self):
        return self.name

    def get_matcher(self):
        return self.matcher


# A helper class to match the master and slave nodes, and apply the constraint for periodic boundary conditions
class NodeMatcher:
    def __init__(self, name, model, part, master, slave, plane, sym):
        # Set fields
        self.name = name
        self.modelName = model
        self.partName = part
        self.masterName = master
        self.slaveName = slave
        self.plane = plane
        self.sym = sym
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

    def get_name(self):
        return self.name

    def get_model_name(self):
        return self.modelName

    def get_part_name(self):
        return self.partName

    def get_master_name(self):
        return self.masterName

    def get_slave_name(self):
        return self.slaveName

    def get_plane(self):
        return self.plane

    def get_sym(self):
        return self.sym

    def get_model(self):
        return abaqus.mdb.models[self.get_model_name()]

    def get_part(self):
        return self.get_model().parts[self.get_part_name()]

    def get_master_surface(self):
        return self.get_part().surfaces[self.get_master_name()]

    def get_slave_surface(self):
        return self.get_part().surfaces[self.get_slave_name()]

    def get_pair_count(self):
        return self.n

    def is_valid(self):
        return self.valid

    def is_paired(self):
        return self.paired

    def is_matched(self):
        return self.matched

    def check_validity(self):
        # Validate from existing constraint
        # TODO: try to fetch from existing constraint
        # Validate from new constraint
        nodes_m = self.get_master_surface().nodes
        nodes_s = self.get_slave_surface().nodes
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
            nodes_m = self.get_master_surface().nodes
            nodes_s = self.get_slave_surface().nodes
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
                    self.pairs.add(NodePair(master.label, slave.label, self.plane, len(self.pairs)))
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
                    pair = NodePair(master.label, slave.label, self.plane, len(self.pairs))
                    self.pairs.add(pair)
                    dist = sqrt(self.plane.dist_sq(master, slave))
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

    def get_exact_count(self):
        return self.exact

    def get_proximity_count(self):
        return self.prox

    def get_min_proximity(self):
        return self.mn

    def get_max_proximity(self):
        return self.mx

    def get_av_proximity(self):
        return self.tot / self.get_pair_count()

    # Applies the constraint for a periodic boundary condition to all paired nodes
    def apply_constraints(self):
        if self.is_matched() and (not self.is_paired()):
            for pair in self.pairs:
                pair.apply_constraint(self.get_model(), self.get_part(), self.name, self.sym)
            self.paired = True

    def delete_constraints(self):
        if self.is_paired():
            for pair in self.pairs:
                # Delete constraint
                pair.remove_constraint(self.get_model(), self.name, self.sym)

    # Finds the exact matching slave node from the unmatched nodes to a given master node
    # Returns None if no exact matching slave node is found
    def find_matching_slave_node(self, master, slaves):
        slave = None
        for node in slaves:
            if self.plane.do_nodes_match(master, node):
                slave = node
                break
        return slave

    # Finds the closest slave node from the unmatched nodes to a given master node
    def find_closest_slave_node(self, master, slaves):
        slave = None
        dist = -1
        for node in slaves:
            # Calculate squared distance
            new_dist = self.plane.dist_sq(master, node)
            # If the distance is smaller than the current closest node, update both
            if (new_dist < dist) or (dist < 0):
                slave = node
                dist = new_dist
        return slave

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
        self.plane = plane
        self.index = index

    def get_master_label(self):
        return self.master_label

    def get_slave_label(self):
        return self.slave_label

    # Applies the constraint for a periodic boundary condition to the two nodes
    def apply_constraint(self, model, part, name, sym):
        self.plane.apply_constraint(model, part, self.get_master_label(), self.get_slave_label(),
                                    'pbc_' + name + '_node_' + str(self.index), sym)

    def remove_constraint(self, model, name, sym):
        self.plane.remove_constraint(model, 'pbc_' + name + '_node_' + str(self.index), sym)


# A class which represents a match plane
# Contains functionality to check if two nodes are matching, to calculate the projected distance,
# and apply the constraint for a periodic boundary condition
# (currently only works for the XY-, XZ- and YZ-planes)
# TODO: extend for any arbitrary plane
class MatchPlane:
    def __init__(self, i, j):
        self.i = i
        self.j = j

    def do_nodes_match(self, n1, n2):
        c1 = n1.coordinates
        c2 = n2.coordinates
        return (c1[self.i] == c2[self.i]) and (c1[self.j] == c2[self.j])

    def dist_sq(self, n1, n2):
        c1 = n1.coordinates
        c2 = n2.coordinates
        d_i = c1[self.i] - c2[self.i]
        d_j = c1[self.j] - c2[self.j]
        return d_i * d_i + d_j * d_j

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


def debug_message(msg):
    print(msg)


def inspect_object(obj):
    import inspect
    members = inspect.getmembers(obj)
    for member in members:
        debug_message('---------------------')
        debug_message(str(member))
    debug_message('---------------------')


PLANES = (MatchPlane(0, 1), MatchPlane(0, 2), MatchPlane(1, 2))
