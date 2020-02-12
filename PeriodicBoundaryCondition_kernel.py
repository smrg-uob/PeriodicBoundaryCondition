# This is a proxy kernel script to allow reloading the actual kernel script in order to facilitate debugging
def runScript(kw_model, kw_part, kw_master, kw_slave, kw_name, kw_plane, kw_symm):
    import PeriodicBoundaryCondition_script
    # Reload the script
    reload(PeriodicBoundaryCondition_script)
    # Run the script
    PeriodicBoundaryCondition_script.createPBC(kw_model, kw_part, kw_master, kw_slave, kw_name, kw_plane, kw_symm)