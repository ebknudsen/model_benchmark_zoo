from model_benchmark_zoo import TwoTouchingCuboids
import openmc
import math

def test_compare():
    # materials used in both simulations
    mat1 = openmc.Material(name='1')
    mat1.add_nuclide('Fe56', 1)
    mat1.set_density('g/cm3', 1)
    mat2 = openmc.Material(name='2')
    mat2.add_nuclide('Fe56', 1)
    mat2.set_density('g/cm3', 1)
    my_materials = openmc.Materials([mat1, mat2])

    # geometry used in both simulations
    common_geometry_object = TwoTouchingCuboids(
        materials=my_materials, width1=10, width2=4)
    # just writing a CAD step file for visulisation
    common_geometry_object.export_stp_file("TwoTouchingCuboids.stp")

    mat1_filter = openmc.MaterialFilter(mat1)
    tally1 = openmc.Tally(name='mat1_flux_tally')
    tally1.filters = [mat1_filter]
    tally1.scores = ['flux']

    mat2_filter = openmc.MaterialFilter(mat2)
    tally2 = openmc.Tally(name='mat2_flux_tally')
    tally2.filters = [mat2_filter]
    tally2.scores = ['flux']
    my_tallies = openmc.Tallies([tally1, tally2])

    my_settings = openmc.Settings()
    my_settings.batches = 10
    my_settings.inactive = 0
    my_settings.particles = 500
    my_settings.run_mode = 'fixed source'

    # Create a DT point source
    my_source = openmc.Source()
    my_source.space = openmc.stats.Point((0, 0, 0))
    my_source.angle = openmc.stats.Isotropic()
    my_source.energy = openmc.stats.Discrete([14e6], [1])
    my_settings.source = my_source

    # making openmc.Model with CSG geometry
    csg_model = common_geometry_object.csg_model()
    csg_model.materials = my_materials
    csg_model.tallies = my_tallies
    csg_model.settings = my_settings

    output_file_from_csg = csg_model.run()

    # extracting the tally result from the CSG simulation
    with openmc.StatePoint(output_file_from_csg) as sp_from_csg:
        csg_result1 = sp_from_csg.get_tally(name="mat1_flux_tally")
        csg_result2 = sp_from_csg.get_tally(name="mat2_flux_tally")

    # making openmc.Model with DAGMC geometry and specifying mesh sizes to get a good representation of a TwoTouchingCuboids
    dag_model = common_geometry_object.dagmc_model_with_cad_to_dagmc(min_mesh_size=0.01, max_mesh_size=0.5)
    dag_model.materials = my_materials
    dag_model.tallies = my_tallies
    dag_model.settings = my_settings

    output_file_from_cad = dag_model.run()

    # extracting the tally result from the DAGMC simulation
    with openmc.StatePoint(output_file_from_cad) as sp_from_cad:
        cad_result1 = sp_from_cad.get_tally(name="mat1_flux_tally")
        cad_result2 = sp_from_cad.get_tally(name="mat2_flux_tally")
 
    assert math.isclose(cad_result1.mean, csg_result1.mean)
    assert math.isclose(cad_result2.mean, csg_result2.mean)
