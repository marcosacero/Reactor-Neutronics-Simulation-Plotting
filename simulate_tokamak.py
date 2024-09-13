#!/usr/bin/env python3

""" simulate_tokamak.py: obtains a few netronics parameters for a basic tokamak geometry. """
""" run with python3 simulate_tokamak.py | tqdm >> /dev/null """
""" outputs results to files called simulation_results.json """

__author__      = "Marcos Acero"


import re 
import openmc
import os
import json
import numpy as np
from tqdm import tqdm
import sys
from openmc import ZPlane


def make_geometry_tallies(batches,nps,inner_radius,breeder_thickness,pressure,temperature_in_K,multiplier_thickness): 

    hydrogen = openmc.Material(name='dense hydrogen')
    hydrogen.add_nuclide("H2",1.0/2.0,"ao") # H2 g/mol = 2.014
    hydrogen.add_nuclide("H3",1.0/2.0,"ao") # H3 g/mol = 3.016
    H_density = pressure*(2.014+3.016)/(temperature_in_K*82.05)
    hydrogen.set_density("g/cm3",H_density) 
    
    pb = openmc.Material(name="pb")
    pb.add_element('Pb',1.0,"ao")
    pb.set_density("g/cm3",11.34)

    li = openmc.Material(name="Li")
    li.add_nuclide("Li6",0.40*1.0/1.0,"ao")
    li.add_nuclide("Li7",(1-0.40)*1.0/1.0,"ao")
    li.set_density("g/cm3",0.512)

    mats = openmc.Materials([hydrogen,pb,li]) # all materials created must be put in here
    mats.export_to_xml('materials.xml')







    #GEOMETRY#

    box = openmc.model.rectangular_prism(500,500,boundary_type='vacuum') \
    & -ZPlane(250, boundary_type='vacuum') \
    & +ZPlane(-250, boundary_type='vacuum')
    
    innerinner = openmc.Sphere(r=5)
    inner = openmc.Sphere(r=5+inner_radius)
    neutronmultiplier = openmc.Sphere(r=5+inner_radius+multiplier_thickness)
    breeder = openmc.Sphere(r=5+inner_radius+multiplier_thickness+breeder_thickness)
    surfaces = [innerinner, inner, neutronmultiplier, breeder]

    s1, s2, s3, s4, s5 = openmc.model.subdivide(surfaces)
    outside = box & ~openmc.Union((s1, s2, s3, s4))
    regions = [s1, s2, s3, s4, outside]
    fills = [None,hydrogen,pb,li,None]
    names = [mat.name if hasattr(mat,"name") else "" for mat in fills]
    cells = [openmc.Cell(region=reg,fill=fill,name=name) for reg, fill, name in zip(regions, fills,names)]
    root = openmc.Universe(cells=cells)
    geom = openmc.Geometry(root)
    geom.export_to_xml()
    







    #SIMULATION SETTINGS#

    point = openmc.stats.Point((0, 0, 0))
    src = openmc.Source(space=point)
    src.energy=openmc.stats.Discrete([14.0E6],[1.0])

    settings = openmc.Settings()
    settings.run_mode = 'fixed source'
    settings.source = src
    settings.batches = batches
    settings.inactive = 5
    settings.particles = nps
    settings.export_to_xml()





    #TALLIES#

    particle_filter = openmc.ParticleFilter('neutron')
    multiplier_cell = openmc.CellFilter(cells[2])
    breeder_cell = openmc.CellFilter(cells[3])
    surface_filter_after_multi = openmc.SurfaceFilter(neutronmultiplier)
    surface_filter_after_breeder = openmc.SurfaceFilter(breeder)
    energy_bins = np.linspace(0, 24e6, 25)
    energy_filter = openmc.EnergyFilter(energy_bins)

    flux1 = openmc.Tally(name='neutron_flux_multiplier')
    flux1.filters = [multiplier_cell,particle_filter]
    flux1.scores = ['flux']

    flux2 = openmc.Tally(name='neutron_flux_breeder')
    flux2.filters = [breeder_cell,particle_filter]
    flux2.scores = ['flux']

    current1 = openmc.Tally(name='neutrons_after_multiplier')
    current1.filters = [surface_filter_after_multi,particle_filter]
    current1.scores = ['current']

    current2 = openmc.Tally(name='neutrons_after_breeder')
    current2.filters = [surface_filter_after_breeder,particle_filter]
    current2.scores = ['current']

    current1energy = openmc.Tally(name='neutron_energy_after_multiplier')
    current1energy.filters = [surface_filter_after_multi,particle_filter,energy_filter]
    current1energy.scores = ['current']

    current2energy = openmc.Tally(name='neutron_energy_after_breeder')
    current2energy.filters = [surface_filter_after_breeder,particle_filter,energy_filter]
    current2energy.scores = ['current']
    
    tallies = openmc.Tallies([flux1,flux2,current1,current2,current1energy,current2energy])
    tallies.export_to_xml()









    #RUN OPENMC #
    model = openmc.model.Model(geom, mats, settings, tallies)
    
    model.run()







    #RETRIEVING TALLY RESULTS

    sp = openmc.StatePoint('statepoint.'+str(batches)+'.h5')
    
    json_output= {'inner_radius':inner_radius,
                  'breeder_thickness':breeder_thickness,
                  'multiplier_thickness':multiplier_thickness,
                  'pressure':pressure,
                  'temperature_in_K':temperature_in_K}

    # Non-energy/bin based tallies
    tallies_to_retrieve = ['neutron_flux_multiplier', 'neutron_flux_breeder', 'neutrons_after_multiplier', 'neutrons_after_breeder']
    for tally_name in tallies_to_retrieve:
        tally = sp.get_tally(name=tally_name)
        tally_result = tally.sum[0][0][0]/batches #for some reason the tally sum is a nested list 
        tally_std_dev = tally.std_dev[0][0][0]/batches #for some reason the tally std_dev is a nested list 

        json_output[tally_name] = {'value':tally_result,
                                   'std_dev':tally_std_dev}
        
    # Energy/bin based tallies
    spectra_tallies_to_retrieve = ['neutron_energy_after_multiplier', 'neutron_energy_after_breeder']
    for spectra_name in spectra_tallies_to_retrieve:
        spectra_tally = sp.get_tally(name=spectra_name)
        spectra_tally_result = [entry[0][0] for entry in spectra_tally.mean]
        spectra_tally_std_dev = [entry[0][0] for entry in spectra_tally.std_dev]
        rmean = np.array(spectra_tally_result)
        rstddev = np.array(spectra_tally_std_dev)
        sumr = np.sum(rmean)
        energy = 1e6
        sumenergy = 0
        sumstddevenergy = 0
        for elem in rmean:
            sumenergy += elem*energy/sumr
            energy = energy + 1e6
        energy = 1e6
        for elem in rstddev:
            sumstddevenergy += elem*energy/sumr
            energy = energy + 1e6

        json_output[spectra_name] = {'value': sumenergy,
                                     'std_dev': sumstddevenergy,
                                     'energy_groups':list(energy_bins)}

    return json_output







results = []
num_simulations = 50
c = 0
    
for i in tqdm(range(0,num_simulations)):
    temperature = 270+(10*c)
    result = make_geometry_tallies(batches=30,
                                nps=int(1E4),
                                inner_radius=20, # centimeters
                                breeder_thickness=40, # centimeters
                                pressure=2, # atm
                                temperature_in_K=temperature, # Kelvin
                                multiplier_thickness=10, # centimeters
                                )
    results.append(result)
    c=c+1

output_filename = 'simulation_results.json'
with open(output_filename, mode='w', encoding='utf-8') as f:
    json.dump(results, f)