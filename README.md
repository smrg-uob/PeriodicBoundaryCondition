# PeriodicBoundaryCondition
A plugin for Abaqus to define periodic boundary conditions to 3D geometry

The latest version can be downloaded from the [Releases](https://github.com/smrg-uob/PeriodicBoundaryCondition/releases).

To install, copy all the .py files to your Abaqus plugin directory.
When done correctly, the plugin should appear in Abaqus CAE under the plugins item on the menu ribbon:

![Plugin](https://github.com/smrg-uob/PeriodicBoundaryCondition/blob/master/doc/plugin.png?raw=true)

## Periodic Boundary Conditions 
Periodic boundary conditions can be used to model an infinite or semi-infinite domain using its unit cell.
See [this paper](https://github.com/smrg-uob/PeriodicBoundaryCondition/blob/master/doc/applying%20periodic%20boundary%20conditions%20in%20finite%20element%20analysis.pdf) for more details.

In summary, a periodic boundary condition between two surfaces can be added in Abaqus by applying a relevant constraint between each of their nodes.
This plugin allows to easily add periodic boundary conditions to an Abaqus model.

## User interface 
Before using the plugin to apply the periodic boundary condition, the following prerequisites are required:
* The two surfaces need to be defined as a surface on the part
* The two surfaces need to be meshed

When launching the plugin from the menu bar, the following dialog window will show up:

![User Interface](https://github.com/smrg-uob/PeriodicBoundaryCondition/blob/master/doc/gui.png?raw=true)

The user interface consists of the following items:
* Select Model: select the relevant model (usually you will only have one active model, which will be "Model-1")
* Select the part: select the relevant part on which the two surfaces are defined
* Select the master surface: this lists all the surfaces defined on the chosen part
* Select the slave surface: this also lists all the surfaces defined on the chosen part
* PBC Name: the plugin will create sets and equation constraints for each node, this name will be used to identify them
* Match plane: the plane over which the periodic symmetry should be defined (this should be parallel with the two planes, but is not required)
* Symmetry: the symmetry to use for the component normal to the match plane
* Apply button: once a valid combination of inputs are selected (different master and slave surfaces and name defined), this button will become enabled and can be clicked to define the constraints
* Cancel button: can be clicked at any time to close the dialog window, no changes will be made to the model.

### Node Pairing
The plugin will try to match the relevant nodes between the two surfaces. If the two surfaces do not contain an equal amount of nodes, the code will abort without making any changes to the model and an error message will be printed in the console.

The code will try to match nodes with their exact coordinates, and in case this is not possible, the closest node will be searched instead. Statistics on this will be printed in the console, for example:
```
MATCHING NODES
Exact matches: 1258/1349, Proximity matches: 91/1349
From proximity matches: min = 2.4043267377e-15, max = 0.00159704241642, avg = 0.000530004372106
```
This means that out of 1349 nodes, 1258 exact matches were found and 91 were matched based on the closest node. From the latter 91 node pairs, the minimum destance was 2.40E-15 mm, the maximum 1.60E-3 mm, and the average 5.30E-4 mm. Since, in this case, the nodes are spaced with an average of 0.1 mm, this is considered acceptable.

In case the node pairing is deemed unacceptable, the meshes of the surface will need to be altered, and meshing rules which force the meshes to be equal should be implemented.

### Symmetry
The constraints in the chosen match plane will be applied such that the displacements in the plane of both nodes in each pair are equal. For instance for the XY-plane, this would be:
```
Ux_1 - Ux_2 = 0
Uy_1 - Uy_2 = 0
```

For the constraints normal to the match plane, one can choose between three options:
1. Asymmetric
2. Symmetric
3. Ignore

An asymmetric constraint (left) will apply equal displacements to each node pair, similar as to the in-plane directions, while a symmetric constraint (right) will apply displacements in the opposite direction. Applying an asymmetric constraint loses symmetry of the domain, but conserves compliance of the repetitive unit cell. A symmetric constraint does the opposite, this is illustrated in the figure below.
By choosing ignore, no constraints will be added in the normal direction, and it is up to the user to define these.
Which type of symmetry should be chosen is up to the user, in some cases (such as uniaxial tension), asymmetric symmetry will lead to rigid body motion instead of deformation, while in others it leads to absurd results (such as torsion + tension).

![Symmetry](https://github.com/smrg-uob/PeriodicBoundaryCondition/blob/master/doc/drawing.svg)

## Limitations
Currently the plugin suffers from the following limitations:
* The surfaces for the periodic boundary conditions must be defined on the same part: if your model contains periodic symmetry between surfaces on different parts, these must be merged into one part first. In case this is not possible, the plugin can not be applied.
* The plugin only works for 3D geometries, the plugin can not be applied for 2D geometries
* The plugin only allows periodic symmetry in the x-, y- and z-directions, therefore the model should be built or rotated in order to have the periodic planes parallel to one of the base planes. In case this is impossible, the plugin can not be applied
