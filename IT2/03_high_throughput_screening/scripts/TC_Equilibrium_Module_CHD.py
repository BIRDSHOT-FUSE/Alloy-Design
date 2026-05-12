#!/usr/bin/env python
import numpy as np
import pandas as pd
from tc_python import *
from itertools import compress
from tc_python import server
import time
import concurrent.futures
import os.path as path
import time
import os
import traceback


#Pre-Processing Data
def EQUIL(param):
    indices = param["INDICES"]
    comp_df = param["COMP"]
    elements = param["ACT_EL"]
    active_el = elements

    with TCPython() as session: # logging_policy=LoggingPolicy.NONE
        session.disable_caching()

        system = (
            session.
                select_database_and_elements('TCHEA6', active_el).
                get_system())

        eq_calculation = system.with_single_equilibrium_calculation(). \
            set_condition(ThermodynamicQuantity.temperature(), 298)

        for i in indices:
            #Get the composition list and corresponding active_el list
            solidus = comp_df.loc[i]['PROP ST (K)']
            liquidus = comp_df.loc[i]['PROP LT (K)']
            comp = np.array(comp_df.loc[i][active_el])
            #Create equilibrium calculation object and set conditions
            try: # with TCAL7, if that fails then we will try another database

                # Check Point 1
                if len(active_el) == 1:
                    # Do not do anything for unaries
                    #eq_calculation.set_dependent_element(active_el[0])
                    print('')
                else:
                    for j in range(len(active_el)-1):
                        eq_calculation.set_condition(ThermodynamicQuantity.mole_fraction_of_a_component(active_el[j]),
                                                     comp[j])

                temperatures = [25, 500, 600, 650, 700, 800, 900, 2000]
                for temp in temperatures:
                    eq_calculation =  eq_calculation.set_condition(ThermodynamicQuantity.temperature(), temp+273)
                    eq_result = eq_calculation.calculate()

                    #Get all possible phases
                    pnames = eq_result.get_phases()

                    for phase in pnames:
                        #Get mol fraction list for each phase
                        if eq_result.get_value_of('NPM(' + phase + ')') > 0:
                            comp_df.at[i,'EQ {}C {} MOL'.format(temp,phase)] = eq_result.get_value_of('NPM(' + phase + ')')


                #Properties at Solidus
                eq_calculation = eq_calculation.set_condition(ThermodynamicQuantity.temperature(),solidus-1)
                eq_result = eq_calculation.calculate()
                comp_df.at[i, 'EQ ST H (J/mol)']     = eq_result.get_value_of('HM')
                comp_df.at[i, 'EQ ST H (J)']         = eq_result.get_value_of('H')
                comp_df.at[i, 'EQ ST THCD (W/mK)']   = eq_result.get_value_of('THCD')  #eq_result.get_value_of(ThermodynamicQuantity.thermal_conductivity())
                comp_df.at[i, 'EQ ST Density (g/cc)'] =eq_result.get_value_of('BM') / eq_result.get_value_of('VM') / 10 ** 6
                comp_df.at[i, 'EQ ST MASS (g/mol)'] = eq_result.get_value_of('BM')
                comp_df.at[i, 'EQ ST VOL (m3/mol)'] = eq_result.get_value_of('VM')

                pnames = eq_result.get_phases()
                for phase in pnames:
                    #Get mol fraction list for each phase
                    if eq_result.get_value_of('NPM(' + phase + ')') > 0:
                        comp_df.at[i,'EQ ST {} MOL'.format(phase)] = eq_result.get_value_of('NPM(' + phase + ')')

                #Properties at Liquidus
                eq_calculation = eq_calculation.set_condition(ThermodynamicQuantity.temperature(),liquidus+1)
                eq_result = eq_calculation.calculate()
                comp_df.at[i, 'EQ LT H (J/mol)']    = eq_result.get_value_of('HM')  # J/mol
                comp_df.at[i, 'EQ LT H (J)']        = eq_result.get_value_of('H')
                comp_df.at[i, 'EQ LT THCD (W/mK)']  = eq_result.get_value_of('THCD')  # W/mK
                comp_df.at[i, 'EQ LT DVIS (Pa-s)']  = eq_result.get_value_of('DVIS (liquid)')  # Pa-s
                comp_df.at[i, 'EQ LT KVIS (m2/s)']  = eq_result.get_value_of('KVIS (liquid)')
                comp_df.at[i, 'EQ LT Density (g/cc)'] = eq_result.get_value_of('BM') / eq_result.get_value_of('VM') / 10 ** 6
                comp_df.at[i, 'EQ LT VOL (m3/mol)'] = eq_result.get_value_of('VM')
                comp_df.at[i, 'EQ LT Surface Tension (N/m)'] = eq_result.get_value_of('SURF(LIQUID)')

            except Exception as e2:
                print('Exception occurred on line {}:'.format(traceback.extract_tb(e2.__traceback__)[0][1]))
                print(e2)
                
            finally:
                comp_df.to_csv('CalcFiles/EQUIL_AP_OUT_{}.csv'.format(param["INDICES"][0])) #EQUIL_AP stands for equilibrium "all phases"
                continue

    return 'Complete'


if __name__ == '__main__':

    ##########################################################################
    # Initialize variables and load the data
    print(os.getcwd())
    results_df = pd.read_csv('FLARE-survivors-5at-10x_prop.csv')  # Read the CSV file into a pandas DataFrame
    elements = sorted(['Ti','V','Ta','Nb','Mo','Zr','Cr','Hf','Fe','Re','W'])
    savename = 'prop_out'  # Define the name for saving output
    ##########################################################################

    # Reorganize dataframe to have ordered sequence of element groups 
    # (to minimize Thermo-Calc initializations and improve efficiency)
    tic = time.time()  # Start the timer to measure time taken
    Els = list()  # Initialize a list to hold unique element combinations
    prev_active_el = []  # Store the previously active elements
    for row in range(results_df.shape[0]):  # Iterate over each row in the dataframe
        comp = results_df.iloc[row][elements]  # Get the composition for the current row
        active_el = list(compress(elements, list(comp > 0)))  # Extract elements that have a non-zero composition
        if active_el not in Els:  # If this combination of elements hasn't been added yet
            Els.append(active_el)  # Add it to the list of element combinations
        prev_active_el = active_el  # Update the previous active elements
        toc = time.time()  # Measure time taken for each iteration
        print(f"{round(row / results_df.shape[0] * 100, 3)} % Done Gathering Systems in {round(toc - tic, 3)} secs")

    
    results_df = results_df.reset_index(drop=True)  # Reset the index for the new DataFrame

    # Create a directory for saving calculation files if it doesn't exist
    if not path.exists("CalcFiles"):
        os.mkdir("CalcFiles")

    indices = results_df.index  # Get the index values from the DataFrame

    prev_active_el = []  # Initialize the previous active element tracker
    parameters = []  # List to hold calculation parameters
    count = 0  # Counter for tracking progress

    # Group the calculations into sets for efficient processing
    for i in indices:  # Loop over the rows of the DataFrame
        comp = results_df.loc[i][elements+['PROP LT (K)','PROP ST (K)']]
        active_el = list(compress(elements, list(comp > 0)))  # Extract non-zero elements

        # Check if the current active elements differ from the previous ones or if the count reaches a threshold
        if (active_el != prev_active_el) or (count == 200):
            try:
                new_calc_dict["COMP"] = results_df.loc[new_calc_dict["INDICES"]]  # Assign the composition to the dictionary
                new_calc_dict["ACT_EL"] = prev_active_el  # Assign the previous active elements
                # Check if the result set already exists
                if not os.path.exists(f"CalcFiles/EQUIL-Results-Set-{new_calc_dict['INDICES'][0]}"):
                    parameters.append(new_calc_dict)  # Add the new calculation set to the parameters list
                else:
                    print(f"******Calculation Already Completed: Start Index {new_calc_dict['INDICES'][0]} \n")  # Inform the user
                new_calc_dict = {"INDICES": [], "COMP": [], "ACT_EL": []}  # Reset the calculation dictionary
            except Exception as e:
                new_calc_dict = {"INDICES": [], "COMP": [], "ACT_EL": []}  # Handle any exceptions that occur
            count = 0  # Reset the count for the next group of calculations

        new_calc_dict["INDICES"].append(i)  # Add the index to the current calculation set
        prev_active_el = active_el  # Update the previous active elements
        count += 1  # Increment the counter

    # Add the last calculation set after the loop
    new_calc_dict["COMP"] = results_df.loc[new_calc_dict["INDICES"]]  # Assign the composition to the dictionary
    new_calc_dict["ACT_EL"] = prev_active_el  # Assign the previous active elements
    if not os.path.exists(f"CalcFiles/PROP-Results-Set-{new_calc_dict['INDICES'][0]}"):
        parameters.append(new_calc_dict)  # Add the final calculation set
        print(f"**Calculation Added to list: Start Index {new_calc_dict['INDICES'][0]} \n")
    else:
        print(f"**Calculation Already Completed: Start Index {new_calc_dict['INDICES'][0]} \n")

    print("*****Calculation Sets Generated*****\n")  # Indicate that the calculation sets have been generated

    completed_calculations = []  # List to keep track of completed calculations
    del results_df  # Delete the original DataFrame as it's no longer needed

    # Use a ProcessPoolExecutor to process the calculations concurrently
    with concurrent.futures.ProcessPoolExecutor(20) as executor:
        for result_from_process in zip(parameters, executor.map(EQUIL, parameters)):  # Map the Property function to parameters
            params, results = result_from_process  # Extract the parameters and results from the processed tasks
            if results == "Calculation Completed":
                completed_calculations.append('Completed')  # Mark the calculation as completed

