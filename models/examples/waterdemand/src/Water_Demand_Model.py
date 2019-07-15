'''
will return a dictionary of water consumption per year per county
'''

import json
import pandas as pd


def Water_Demand_Simulation(countypop,rate):

    water={}
    for i in rate.keys():
      if i in countypop.keys():
          water[i]= (countypop[i]*rate[i])
      else:
          water[i]=(0)
    #with open('water_demand_2015.json', 'w') as file:
    #    file.write(json.dumps(data))
    return water




