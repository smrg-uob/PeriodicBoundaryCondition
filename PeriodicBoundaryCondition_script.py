from abaqus import *
from abaqusConstants import *
import mesh
import sys

# This command will be called when the "Apply" button is clicked
#  - kw_model: integer representing the index of the considered model
#  - kw_part: integer representing the index of the considered part
#  - kw_master: integer representing the index of the master surface
#  - kw_slave: integer representing the index of the slave surface
#  - kw_name: name of the pbc, used for the naming of the newly created sets and equations
#  - kw_plane: integer representing the match plane (xy, xz, yz)
#  - kw_symm: integer representing the normal direction symmetry  (0 = asymmetric, 1 = symmetric, 3 = ignore)
def createPBC(kw_model, kw_part, kw_master, kw_slave, kw_name, kw_plane, kw_symm):
    # Extract master and slave nodes
    modelKeys = mdb.models.keys()
    model = mdb.models[modelKeys[kw_model]]
    partKeys = model.parts.keys()
    part = model.parts[partKeys[kw_part]]
    surfKeys = part.surfaces.keys()
    master = part.surfaces[surfKeys[kw_master]].nodes
    slave = part.surfaces[surfKeys[kw_slave]].nodes
    n_m = len(master)
    n_s = len(slave)
    # Check if there is an equal amount of nodes in both surfaces
    if n_m != n_s:
        # TODO: show message box instead
        debugMessage('FAILED: Number of nodes in master (' + str(n_m) + ') and slave (' + str(n_s) + ') planes do not match')
        return
    # Define match plane
    planes = (MatchPlane(0, 1), MatchPlane(0, 2), MatchPlane(1, 2))
    plane = planes[kw_plane]
    # Initialize node matcher
    matcher = NodeMatcher(master, slave)
    # Match nodes
    debugMessage('')
    debugMessage('MATCHING NODES')
    matcher.matchNodes(plane)
    # TODO: show message box with matching accuracy and ask user if it is OK to continue, or to abort
    # Apply constraints
    debugMessage('')
    debugMessage('APPLYING CONSTRAINTS')
    matcher.applyConstraints(model, part, kw_name, kw_symm)

# A helper class to match the master and slave nodes, and apply the constraint for periodic boundary conditions
class NodeMatcher:
    def __init__(self, n_m, n_s):
        # Keep track of total number of nodes
        self.n = len(n_m)
        # Initialize pairs
        self.pairs = [None]*self.n
        # Store unmatched master and slave nodes
        self.m_unm = [None]*self.n
        self.s_unm = [None]*self.n
        for i in range(0, self.n):
            self.m_unm[i] = n_m[i]
            self.s_unm[i] = n_s[i]

    # Uniquely matches each of the master nodes to a slave node
    def matchNodes(self, plane):
        # Define a running index, counters and statistics
        index = 0
        matched = 0
        unmatched = 0
        mn = 0
        mx = 0
        tot = 0
        # First match all nodes whose coordinates match exactly
        for master in list(self.m_unm):    # (iterate over a copy since we will be removing entries)
            slave = self.findMatchingSlaveNode(master, plane)
            if slave == None:
                # No exact matching node found, continue, but do not increment the index
                unmatched = unmatched + 1
                continue
            else:
                # Exact matching node found, create a new node pair and increment the index
                self.pairs[index] = NodePair(master, slave, plane)
                index = index + 1
                matched = matched + 1
                # Remove the matched nodes from the unmatched set
                self.m_unm.remove(master)
                self.s_unm.remove(slave)
        # Second, match the remaining nodes with the closest node
        if unmatched > 0:
            from math import sqrt
            for master in list(self.m_unm):    # (iterate over a copy since we will be removing entries)
                # Find closest slave node
                slave = self.findClosestSlaveNode(master, plane)
                # Create new pair and update the counters
                self.pairs[index] = NodePair(master, slave, plane)
                dist = sqrt(self.pairs[index].distSq())
                index = index + 1
                # Remove the matched nodes from the unmatched set
                self.m_unm.remove(master)
                self.s_unm.remove(slave)
                # Update statistics
                if mn == 0:
                    mn = dist
                    mx = dist
                    tot = dist
                else:
                    mn = min(dist, mn)
                    mx = max(dist, mx)
                    tot = tot + dist
        # Report statistics
        debugMessage('Exact matches: ' + str(matched) + '/' + str(self.n) + ', Proximity matches: ' + str(unmatched) + '/' + str(self.n))
        debugMessage('From proximity matches: min = ' + str(mn) + ', max = ' + str(mx) + ', avg = ' + str(tot/unmatched))

    # Applies the constraint for a periodic boundary condition to all paired nodes
    def applyConstraints(self, model, part, name, sym):
        index = 1
        for pair in self.pairs:
            pair.applyConstraint(model, part, 'pbc_' + name + '_node' + str(index), sym)
            index = index + 1

    # Finds the exact matching slave node from the unmatched nodes to a given master node
    # Returns None if no exact matching slave node is found
    def findMatchingSlaveNode(self, masterNode, plane):
        slaveNode = None
        for node in self.s_unm:
            if plane.doNodesMatch(masterNode, node):
                slaveNode = node
                break
        return slaveNode

    # Finds the closest slave node from the unmatched nodes to a given master node
    def findClosestSlaveNode(self, masterNode, plane):
        slaveNode = None
        dist = -1
        for node in self.s_unm:
            # Calculate squared distance
            newDist = plane.distSq(masterNode, node)
            # If the distance is smaller than the current closest node, update both
            if (newDist < dist) or (dist < 0):
                slaveNode = node
                dist = newDist
        return slaveNode

# A class which represent two paired nodes: one master and one slave.
# A pointer to the matching plane is stored as well
class NodePair:
    # Constructor
    def __init__(self, m, s, plane):
        self.master = m
        self.slave = s
        self.plane = plane

    # Returns the distance squared between the two nodes, in the match plane
    def distSq(self):
        return self.plane.distSq(self.master, self.slave)

    # Applies the constraint for a periodic boundary condition to the two nodes
    def applyConstraint(self, model, part, name, sym):
        self.plane.applyConstraint(model, part, self.master, self.slave, name, sym)

# A class which represents a match plane
# Contains functionality to check if two nodes are matching, to calculate the projected distance,
# and apply the constraint for a periodic boundary condition
# (currently only works for the XY-, XZ- and YZ-planes)
# TODO: extend for any arbitrary plane
class MatchPlane:
    def __init__(self, i, j):
        self.i = i
        self.j = j

    def doNodesMatch(self, n1, n2):
        c1 = n1.coordinates
        c2 = n2.coordinates
        return (c1[self.i] == c2[self.i]) and (c1[self.j] == c2[self.j])

    def distSq(self, n1, n2):
        c1 = n1.coordinates
        c2 = n2.coordinates
        d_i = c1[self.i] - c2[self.i]
        d_j = c1[self.j] - c2[self.j]
        return d_i*d_i + d_j*d_j

    def applyConstraint(self, model, part, master, slave, name, sym):
        # Define the sets
        set_master = name+'_master'
        nodes_master = model.rootAssembly.instances[part.name + '-1'].nodes.sequenceFromLabels((master.label,))
        model.rootAssembly.Set(name=set_master, nodes=nodes_master)
        set_slave = name+'_slave'
        nodes_slave = model.rootAssembly.instances[part.name + '-1'].nodes.sequenceFromLabels((slave.label,))
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


def debugMessage(msg):
    print(msg)
