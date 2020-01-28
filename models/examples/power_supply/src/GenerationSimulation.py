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
    counties['Fuel Used (MMBtu)'] = counties.apply(lambda x: (x['MMBtu per MWh']) * (x.demand_x),axis=1)
    counties['CO2 Emissions (tons)'] = counties.apply(lambda x: (x['Tons CO2 per MWh']) * (x.demand_x),axis=1)
    counties['Water Used (Mgal)'] = counties.apply(lambda x: (x['Mgal_per_MWh']) * (x.demand_x),axis=1)
    counties = counties[['county','Fuel Used (MMBtu)','CO2 Emissions (tons)','Water Used (Mgal)']].set_index('county')
    
#    data = counties.to_dict(orient='index')
 
    co2 = {}
    h2o = {}
    for index, row in counties.iterrows():
        co2[index] = row['CO2 Emissions (tons)']
        h2o[index] = row['Water Used (Mgal)']
    

    return co2, h2o
#water usage (withdrawals and consumption in the 860, we care about consumption), emissions of co2 (may also be in the 860), 923 should have total power produced by each power plant (would match regional demand), aggregating up then dividing by the state population, instead of doing on the state level, we want to instead do it on the nerc level, supply can be on nerc level,wrapper between the supply and demand does the granularity work so we don't have to worry about state vs. NERC, change the input file, he broke it out and was calculating stuff on counties, would adjust and repopulate, do on NERC and calculate on the NERC level, the point in the supply model is to make power demand equal to power supply on the nerc level, need to find the aggregation and disaggregation pairing
#want to be able to do it in county nercs
#1. read in P.P. data
# P.P. I.D./County/Nerc/type/..
# Max Capacity / 2016 Annual Predictions/C.F.?
# CO2/Water Consumption
#want it to be in popwer plant data
# once we read in powerplant data, we have county demand, NERC Match: we are going to aggregate the powerplant data on nerc, and we will have county demand from the power demand model, it will say much power, SIMON will turn the county demand into nerc demand from the wrappers, will have a NERC demand read in, the NERC emand read in needs to be fulfilled by the power plants, we will aggregate all the pp data based off of nerc and then calculate a scaling factor
# we will calculate scaling factor for county demand NERC match, it will be a regional nerc scaling factor for each NERC, we are going to take that scaling factor and apply it back to each pp and output co2 and water consumption, we are then going to take the scaling factor and go back to the powerplant level
#we want supply and demand on the nerc level and then to depend what it means for each individual powerplant, want supply to match demand on nerc and then break it out at county level, maybe should not let powerplants be at maximum capacity, is there a different kind of capacity, or is it just historical use
#capacity? there is generally a capacity factor which is like the maximum loading like if you took an integral over power usage (coal = 90%), might need a distribution network
#2. county demand nerc match
#3. scale p.p. data
#4. aggregate it to anything you want, you want it as tight as possible so probably countynerc
## will be easily able to do things and we will be happy the nerc is there, still being processed at powerplant but given a scaling factor

