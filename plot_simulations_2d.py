""" plot_simulations_2d.py: Plots the results from simulate_tokamak.py. """
""" run with python3 plot_simulations_2d.py | tqdm >> /dev/null """
""" outputs html file via your choice of name. """

__author__      = "Marcos Acero"

from plotly.offline import download_plotlyjs, plot
from plotly.graph_objs import Scatter, Layout
import json
import pandas as pd
from pandas import json_normalize

with open('simulation_results.json') as f:
            results = json.load(f)
    
# PLOTS RESULTS #

results_df = json_normalize(data=results)

text_values = {}

for breeder_thickness_value in [40]: # change depending on what variables through which you'd like to cycle

    df_filtered = results_df[results_df['breeder_thickness']==breeder_thickness_value]

    text_value = []
    for i,tp,p,bt,mt in zip(df_filtered['inner_radius'],
                                    df_filtered['temperature_in_K'],
                                    df_filtered['pressure'],
                                    df_filtered['breeder_thickness'],
                                    df_filtered['multiplier_thickness'],
                                    ):
            text_value.append('inner_radius =' +str(i) +'<br>'+
                            'temperature_in_K ='+str(tp) +'<br>'+
                            'pressure_in_Pa ='+str(p) +'<br>'+
                            'breeder_thickness ='+str(bt) +'<br>'+
                            'multiplier_thickness ='+str(mt)
                            )
            
    text_values[breeder_thickness_value] = text_value

    traces={}
    for x_axis_name in ['temperature_in_K']: # change or add other variables to see plots with a different x-axis
    
        traces[x_axis_name] = []

        for tally_name in ['neutron_flux_multiplier', 'neutron_flux_breeder', 'neutrons_after_multiplier', 'neutrons_after_breeder',
                           'neutron_energy_after_multiplier', 'neutron_energy_after_breeder']:
            
            tally = df_filtered[tally_name+'.value']
            tally_std_dev = df_filtered[tally_name+'.std_dev']
            
            traces[x_axis_name].append(Scatter(x=df_filtered[x_axis_name],
                                    y= tally,
                                    mode = 'markers',
                                    hoverinfo='text' ,
                                    text=text_values[breeder_thickness_value],
                                    error_y= {'array':tally_std_dev},
                                    name = tally_name
                                    )
                            )

            layout_ef = {'title':tally_name+' and '+x_axis_name,
                        'hovermode':'closest',
                    'xaxis':{'title':x_axis_name},
                    'yaxis':{'title':tally_name},
                    }
            plot({'data':traces[x_axis_name],
                    'layout':layout_ef},
                    filename=tally_name+'_vs_'+x_axis_name+'_breeder'+str(breeder_thickness_value)+'.html'
                    )