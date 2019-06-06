# -*- coding: utf-8 -*-
"""
Created on Wed Jul 11 15:14:47 2018

@author: ponzodj1
"""

import pandas as pd

def gen_sim(demand,prof):

    
    # multiply by county demand to yield county generation profile
    # aggregate up to state level to apply profile then project back down
    counties = pd.DataFrame(demand,index=['demand']).T.reset_index().rename(columns={'index':'county'})
    counties['state'] = counties.county.apply(lambda x: x[:-3])
    state_demand = counties.groupby('state')['demand'].sum()
    state_prof = pd.DataFrame(prof).T.reset_index().rename(columns={'index':'state'})
    state_demand = state_demand.to_frame().reset_index()
    counties = pd.merge(counties, state_demand, on='state',how='left')
    counties = pd.merge(counties, state_prof, on='state',how='left')
    counties['Fuel Used (MMBtu)'] = counties.apply(lambda x: (x.demand_y * x['MMBtu per MWh']) * (x.demand_x / x.demand_y),axis=1)
    counties['CO2 Emissions (tons)'] = counties.apply(lambda x: (x.demand_y * x['Tons CO2 per MWh']) * (x.demand_x / x.demand_y),axis=1)
    counties['Water Used (Mgal)'] = counties.apply(lambda x: (x.demand_y * x['Mgal_per_MWh']) * (x.demand_x / x.demand_y),axis=1)
    counties = counties[['county','Fuel Used (MMBtu)','CO2 Emissions (tons)','Water Used (Mgal)']].set_index('county')
    
#    data = counties.to_dict(orient='index')
 
    co2 = {}
    h2o = {}
    for index, row in counties.iterrows():
        co2[index] = row['CO2 Emissions (tons)']
        h2o[index] = row['Water Used (Mgal)']
    

    return co2, h2o

