# PeriodicBoundaryCondition
A plugin for Abaqus CAE 2018 to define periodic boundary conditions to 3D geometry

The latest version can be downloaded from the [Releases](https://github.com/smrg-uob/PeriodicBoundaryCondition/releases).

To install, copy all the .py files to your Abaqus plugin directory.
When done correctly, the plugin should appear in Abaqus CAE under the plugins item on the menu ribbon:

![Plugin](https://github.com/smrg-uob/PeriodicBoundaryCondition/blob/master/doc/plugin.png?raw=true)

## Periodic Boundary Conditions 
Periodic boundary conditions can be used to model an infinite or semi-infinite domain using its unit cell.
See [this paper](https://github.com/smrg-uob/PeriodicBoundaryCondition/blob/master/doc/UC-Chapter_Revised_Final_updated.pdf) for more details.

In summary, a periodic boundary condition between two surfaces can be added in Abaqus by applying a relevant constraint between each of their nodes.
This plugin allows to easily add periodic boundary conditions to an Abaqus model.

## User interface 
Before using the plugin to apply the periodic boundary condition, the following prerequisites are required:
* The two surfaces need to be defined as a surface on the part
* The two surfaces need to be meshed
* If any exempts are to be defined, these should defined in specific sets

### Overview window
When launching the plugin from the menu bar, the following dialog window will show up:

![User Interface](https://github.com/smrg-uob/PeriodicBoundaryCondition/blob/master/doc/gui_overview.png?raw=true)

This gives an overview of all Periodic Boundary Conditions which are applied in the current model, as well as their status.
After selecting any item from the dropdown menu, the following data will be displayed in the text fields:
 * Valid: If this is False, it means that the master and slave surfaces do not have an equal amount of nodes, it is impossible to continue. An invalid Periodic Boundary Condition can be removed by clicking the Delete button.
 * Matched: This indicates if each of the nodes of the slave surface has been matched with one of the nodes of the master surface. At this point, no modifications have been made to the mdb yet.
 * Paired: This indicates if the constraints have been applied as sets and equations in the mdb. If this is True, the paired nodes should be highlighted with yellow circles in the 'Interaction' Module of Abaqus CAE. If this is False, the nodes can be paired by clicking the 'Pair' Button
 * The Master and Slave fields indicate the name of the master and the slave surfaces.
 * Plane gives the used match plane (XY, XZ or YZ).
 * Mode gives the periodicity mode (Translational or Axial)
 * Pairs gives the total amount of node pairs for the current Periodic Boundary Constraint.
 * Exempts gives the number of exempted node pairs
 
 The buttons, from left to right, are used to:
 * Pair the currently selected periodic boundary condition
 * Create a new periodic boundary condition
 * Delete the currently selected periodic boundary condition
 * Close the window

### New Periodic Boundary Condition Window
After clicking the 'New' button, the following window appears:

![User Interface](https://github.com/smrg-uob/PeriodicBoundaryCondition/blob/master/doc/gui_new.png?raw=true)

The user interface consists of the following items:
* Select Model: select the relevant model (usually you will only have one active model, which will be "Model-1")
* Select the part: select the relevant part on which the two surfaces are defined
* Select the master surface: this lists all the surfaces defined on the chosen part
* Select the slave surface: this also lists all the surfaces defined on the chosen part
* Select the set to exempt from the master surface, all nodes in these set will be ignored while pairing nodes. This can, for instance, be used for edges which would otherwise be overconstrained due to another boundary condition on a neighbouring face (by unchecking the box, no exemptions will be made).
* Select the set to exempt from the slave surface, all nodes in these set will be ignored while pairing nodes. This can, for instance, be used for edges which would otherwise be overconstrained due to another boundary condition on a neighbouring face (by unchecking the box, no exemptions will be made).
* PBC Name: the plugin will create sets and equation constraints for each node, this name will be used to identify them, and must be unique.
* Match plane: the plane over which the periodic symmetry should be defined (this should be parallel with the two planes, but is not required)
* Mode: this can be set to either translational or axial, translational is used for periodicity in the cartesian directions, while axial is used for cylindrical periodicity in the axial direction.

The two buttons will invoke the following:
* Create button: once a valid combination of inputs are selected (different master and slave surfaces and name defined), this button will become enabled and can be clicked to define the constraints
* Close button: can be clicked at any time to close the dialog window, no changes will be made to the model.

#### Node Matching
The plugin will try to match the relevant nodes between the two surfaces. If the two surfaces do not contain an equal amount of nodes, the code will abort without making any changes to the model and an error message will be printed in the console.

The code will try to match nodes with their exact coordinates, and in case this is not possible, the closest node will be searched instead. A confirmation dialog with statistics on this will be displayed, for instance: 

![User Interface](https://github.com/smrg-uob/PeriodicBoundaryCondition/blob/master/doc/gui_confirm.png?raw=true)

This means that out of 836 nodes, 825 exact matches were found and 11 nodes were exempted. In this case, all non-exempted node pairs could be matched exactly. In case some nodes were matched by proximity,  the minimum, maximum and average in-plane distance will be reported. In case these statistics can be considered acceptable, for instance when the average mismatch distance is multiple orders of magnitude smaller than the node spacing, one can go ahead by clicking the 'Yes' button after which the program will continue to pair the nodes.

In case the node pairing is deemed unacceptable, one can click the 'No' button, and the program will not apply any constraints.
The new entry will appear on the overview dialog with False as the 'Paired' status. It is possible to pair the nodes anyway, or delete the constraint in order to alter the mesh, for instance in order to apply meshing rules to enforce the nodes on both faces to better match.

#### Node Pairing
Before pairing the nodes, the code will not apply any modifications to the mdb. By pairing matched node pairs, individual sets for each node are created by the code, which are then used to apply constraints to the mdb under the form of equations.
These modifications will be undone when a Periodic Boundary Condition with paired nodes is deleted from the Overview dialog.

##### Translational
For translational periodicity, the following equations will be added for each node pair (except the last):
```
u_(i) - u'_(i) = u_(i+1) - u'_(i+1)
v_(i) - v'_(i) = v_(i+1) - v'_(i+1)
w_(i) - w'_(i) = w_(i+1) - w'_(i+1)
```
In which `u`, `v` and `w` are the displacements of the node indicated by the index `i` in the `x`, `y` and `z` directions respectively. Non-primed displacements indicate nodes on the master surface and primed displacements indicate nodes on the slave surface.

To implement translational periodicity in all three directions, for instance on a representative cube, the following procedure can be applied:
1. Apply a periodic boundary condition on the two faces for the first direction without any exempted edges.
2. Apply a periodic boundary condition on the two faces for the second direction, and apply an exemption for the edges which are shared with the master surface for the first direction on the master and slave surfaces of the second direction (1 edge is exempted on each of the two faces).
3. Apply a periodic boundary condition on the two faces for the third direction, and apply an exemption for the edges which are shared with the master surface for the first direction or the second direction on the master and slave surfaces of the third direction (2 edges are exempted on each of the two faces).

##### Axial
Abaqus natively supports axisymmetric or cyclic symmetry, but only in the circumferential direction (see [here](https://abaqus-docs.mit.edu/2017/English/SIMACAECAERefMap/simacae-t-itnhelpcyclicsymmetry.htm) on how to implement cyclic symmetry in Abaqus).
This can be completed in the axial direction by applying axial periodicity using this plugin. The following equations will be added for each node pair (expect the last):
```
u_(i) - u'_(i) = 0
v_(i)/r_(i) - v'_(i)/r_(i) = v_(i+1)/r_(i+1) - v'_(i+1)/r_(i+1)
w_(i) - w'_(i) = w_(i+1) - w'_(i+1)
```
In which `u`, `v` and `w` are the displacements of the node indicated by the index `i` in the `r`, `t` and `z` directions respectively and  `r` is the  `r` coordinate of the node. Non-primed displacements indicate nodes on the master surface and primed displacements indicate nodes on the slave surface.

To implement full cylindrical periodicity the following procedure can be applied:
1. Apply cyclic symmetry using the native Abaqus functionality as explained [here](https://abaqus-docs.mit.edu/2017/English/SIMACAECAERefMap/simacae-t-itnhelpcyclicsymmetry.htm).
2. Apply an axial periodic boundary condition on the top and bottom faces for the axial direction, apply an exemption for the edges which are shared with the master surface from step 1 on the master and slave surfaces from step 2.

## Limitations
Currently the plugin suffers from the following limitations:
* The surfaces for the periodic boundary conditions must be defined on the same part: if your model contains periodic symmetry between surfaces on different parts, these must be merged into one part first. In case this is not possible, the plugin can not be applied.
* The plugin only works for 3D geometries, the plugin can not be applied for 2D geometries
* The plugin only allows periodic symmetry in the x-, y- and z-directions, therefore the model should be built or rotated in order to have the periodic planes parallel to one of the base planes. In case this is impossible, the plugin can not be applied
* Remeshing: as the periodic boundary conditions are defined as constraints on the nodes, these must be deleted before modifying the mesh and applied again after the remeshing has been done.
