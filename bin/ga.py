#!/usr/bin/python
import numpy as np
import sys
import os
from fafoom import *
import fafoom.run_utilities as run_util
from fafoom.utilities import sdf2xyz, check_for_clashes
#Need to correctly write the one-line blacklist:
np.set_printoptions(suppress=True)
# Decide for restart or a simple run.
opt = run_util.simple_or_restart()
p_file = sys.argv[1]
if sys.argv is None:
    if os.path.exists(os.path.join(os.getcwd(), 'parameters.txt')):
        p_file = os.path.join(os.getcwd(), 'parameters.txt')
    else:
        pass
        #Assign default parameters for calculation

# Build a dictionary from two section of the parameter file.
params = file2dict(p_file, ['GA settings', 'Run settings'])

dict_default = {'energy_var': 0.001, 'selection': "roulette_wheel",
                'fitness_sum_limit': 1.2, 'popsize': 10,
                'prob_for_crossing': 1.0, 'max_iter': 30,
                'iter_limit_conv': 20, 'energy_diff_conv': 0.001}
# Set defaults for parameters not defined in the parameter file.
params = set_default(params, dict_default)
energy_function = run_util.detect_energy_function(params)

cnt_max = 2500
population = []
blacklist = []
min_energy = []
#=======================================================================
if opt == "simple":
    mol = MoleculeDescription(p_file)
    # Assign the permanent attributes to the molecule.
    mol.get_parameters()
    mol.create_template_sdf()
    # Check for potential degree of freedom related parameters.
    linked_params = run_util.find_linked_params(mol, params)
    volume = mol.volume
    print_output('Atoms: {}, Bonds: {}'.format(mol.atoms, mol.bonds))
    print_output('\n___Initialization___\n')
    cnt = 0
    # Generate sensible and unique 3d structures.
    while len(population) < params['popsize'] and cnt < cnt_max:
        # print_output("New trial")
        Structure.index = len(population)
        str3d = Structure(mol)
        str3d.generate_structure()
        if not str3d.is_geometry_valid():
            cnt += 1
            continue
        else:
            if str3d not in blacklist:
                if not check_for_clashes(str3d.sdf_string, os.path.join(mol.constrained_geometry_file)):
                    if 'centroid' not in mol.dof_names:
                        str3d.adjust_position()
                    else:
                        cnt+=1
                        continue
                if 'centroid' not in mol.dof_names:
                    if not str3d.check_position(volume):
                        str3d.adjust_position()
                name = 'structure_{}'.format(str3d.index)
                # Perform the local optimization
                run_util.optimize(str3d, energy_function, params, name)
                run_util.check_for_kill()
                str3d.send_to_blacklist(blacklist) #Blacklist
                population.append(str3d)
                print_output('{}\nEnergy: {}'.format(str3d, float(str3d)))
                run_util.relax_info(str3d)
                # cnt += 1
            else:
                #print_output(blacklist) #Blacklist
                print_output("Geomerty of "+str(str3d)+" is fine, but already known.")
                cnt += 1
    if cnt == cnt_max:
        print_output("The allowed number of trials for building the "
                     "population has been exceeded. The code terminates.")
        sys.exit(0)
    print_output("___Initialization completed___")
    population.sort()
    print_output("Initial population after sorting: ")
    for i in range(len(population)):
        print_output('{:<}   {:>}'.format(population[i], float(population[i])))
    min_energy.append(population[0].energy)
    #print_output("Blacklist: " + ', '.join([str(v) for v in blacklist])) #Blacklist
    iteration = 0


if opt == "restart":
    # Reconstruct the molecule, population, blacklist and the state of the run.
    print_output(" \n ___Restart will be performed___")
    mol = MoleculeDescription(p_file)
    # Assign the permanent attributes to the molecule.
    mol.get_parameters()
    mol.create_template_sdf()
    # with open("backup_mol.dat", 'r') as inf:
    #     mol = eval(inf.readline())
    with open("backup_population.dat", 'r') as inf:
        for line in inf:
            population.append(eval(line))
    with open("backup_blacklist.dat", 'r') as inf:
        for line in inf:
            blacklist.append(eval(line))
    with open("backup_min_energy.dat", 'r') as inf:
        for line in inf:
            min_energy.append(eval(line))
    with open("backup_iteration.dat", 'r') as inf:
        iteration_tmp = eval(inf.readline())
    linked_params = run_util.find_linked_params(mol, params)
    population.sort()
    for i in range(len(population)):
        print_output(str(population[i])+" "+str(float(population[i])))
    print_output("Blacklist: " + ', '.join([str(v) for v in blacklist]))
    iteration = iteration_tmp+1
    linked_params = run_util.find_linked_params(mol, params)
    Structure.index = len(blacklist)
    print_output(" \n ___Reinitialization completed___")
    remover_dir('structure_{}'.format(len(blacklist) + 1))
    remover_dir('structure_{}'.format(len(blacklist) + 2))
    # remover_dir('generation_'+str(iteration)+'_child1')
    # remover_dir('generation_'+str(iteration)+'_child2')


def mutate_and_relax(candidate, name, iteration, cnt_max, **kwargs):
    print_output('__{}__'.format(name))
    found = False
    cnt = 0
    while found is False and cnt < cnt_max:
        Structure.index = len(blacklist)
        candidate_backup = Structure(candidate)
        if candidate in blacklist:
            print_output('Candidate in blacklist')
            print_output('Perform hard_mutate')
            candidate.hard_mutate(**kwargs) #Mutate, since already in blacklist
            if not candidate.is_geometry_valid(): #Check geometry after mutation
                print_output('Geometry is not valid')
                candidate = candidate_backup #Reset structure
                cnt+=1
                continue
            else:
                if not check_for_clashes(candidate.sdf_string, os.path.join(mol.constrained_geometry_file)):
                    print_output('Clash found')
                    if 'centroid' not in mol.dof_names: #If optimization for the COM is turned off
                        candidate.adjust_position() #Adjust position in z direction
                    else:
                        print_output('Centroid found -- skipp')
                        candidate = candidate_backup #Clash found so structure will be resetted
                        cnt+=1
                        continue
                name = 'structure_{}'.format(candidate.index)
                run_util.optimize(candidate, energy_function, params, name)
                run_util.check_for_kill()
                candidate.send_to_blacklist(blacklist) #Blacklist
                print_output('{}\nEnergy: {}'.format(candidate, float(candidate)))
                # print_output(str(candidate)+": energy: "+str(float(candidate))+", is temporary added to the population")
                run_util.relax_info(candidate)
                found = True
                population.append(candidate)
        elif candidate not in blacklist:
            print_output('Candidate not in blacklist')
            candidate.mutate(**kwargs) #Mutatte with some probability
            if not candidate.is_geometry_valid():
                print_output('Geometry is not fine')
                candidate = candidate_backup # Rebuild the structure
                cnt += 1
                continue
            else:
                if not check_for_clashes(candidate.sdf_string, os.path.join(mol.constrained_geometry_file)):
                    print_output('Clash found')
                    if 'centroid' not in mol.dof_names:
                        print_output('Perform adjust')
                        candidate.adjust_position()
                    else:
                        print_output('Perform hard_mutate')
                        candidate.hard_mutate(**kwargs)
                        if not check_for_clashes(candidate.sdf_string, os.path.join(mol.constrained_geometry_file)):
                            candidate = candidate_backup
                            cnt+=1
                            continue
                name = 'structure_{}'.format(candidate.index)
                run_util.optimize(candidate, energy_function, params, name)
                run_util.check_for_kill()
                candidate.send_to_blacklist(blacklist) #Blacklist
                print_output('{}\nEnergy: {}'.format(candidate, float(candidate)))
                # print_output(str(candidate)+": energy: "+str(float(candidate))+", is temporary added to the population")
                run_util.relax_info(candidate)
                found = True
                population.append(candidate)
        if cnt == cnt_max:
            raise Exception("The allowed number of trials for generating a unique child has been exceeded.")

while iteration < params['max_iter']:
    print_output(' \n ___Start of iteration {}___'.format(iteration))
    (parent1, parent2, fitness) = selection(population, params['selection'],
                                            params['energy_var'],
                                            params['fitness_sum_limit'])
    param = np.random.rand()
    print_output('Try to crossover.')
    cnt = 0
    while param < params['prob_for_crossing'] and cnt < cnt_max:
        print_output('Values for {} parent_1'.format(parent1))
        run_util.str_info(parent1)
        print_output('Values for {} parent_2'.format(parent2))
        run_util.str_info(parent2)
        print_output('\n')
        child1, child2 = Structure.crossover(parent1, parent2)
        if child1.is_geometry_valid_after_crossover() and child2.is_geometry_valid_after_crossover():
            if not check_for_clashes(child1.sdf_string, os.path.join(mol.constrained_geometry_file)):
                print_output('Clash found')
                if 'centroid' not in mol.dof_names:
                    print_output('Perform adjust')
                    child1.adjust_position()
                else:
                    Structure.index = len(blacklist)
                    cnt += 1
                    continue
            if not check_for_clashes(child2.sdf_string, os.path.join(mol.constrained_geometry_file)):
                print_output('Clash found')
                if 'centroid' not in mol.dof_names:
                    print_output('Perform adjust')
                    child2.adjust_position()
                else:
                    Structure.index = len(blacklist)
                    cnt += 1
                    continue
            break
        else:
            Structure.index = len(blacklist)
            cnt += 1
            continue
    else:
        child1, child2 = Structure(parent1), Structure(parent2)
        print_output('No crossover was performed. Children are copies of parents.')
        # Delete inherited attributes.
        for child in child1, child2:
            attr_list = ["initial_sdf_string", "energy"]
            for attr in attr_list:
                delattr(child, attr)
            for dof in child.dof:
                delattr(dof, "initial_values")
    print_output('Values for {} child_1'.format(child1))
    run_util.str_info(child1)
    print_output('Values for {} child_2'.format(child2))
    run_util.str_info(child2)
    print_output('\n')
    try:
        mutate_and_relax(child1, "child1", iteration, cnt_max, **linked_params)
    except Exception as exc:
        print_output(exc)
        sys.exit(0)
    try:
        mutate_and_relax(child2, "child2", iteration, cnt_max, **linked_params)
    except Exception as exc:
        print_output(exc)
        sys.exit(0)
    population.sort()
    print_output("Sorted population: " + ', '.join([str(v) for v in population]))
    del population[-1]
    del population[-1]
    print_output("Sorted population after removing two structures with highest"
                 " energy: " + ', '.join([str(v) for v in population]))
    min_energy.append(population[0].energy)
    print_output("Current population after sorting: ")
    for i in range(len(population)):
        print_output('{:<}   {:>}'.format(population[i], float(population[i])))
    print_output("Lowest energies in run: {}".format(min_energy))
    run_util.perform_backup(mol, population, blacklist, iteration, min_energy)
    run_util.check_for_convergence(iteration, params, min_energy)
    run_util.check_for_kill()
    iteration += 1