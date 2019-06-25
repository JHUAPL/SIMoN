'''
will return a dictionary of water consumption per year per county
'''

import json
import pandas as pd

with open('models/examples/population/config/county_populations.json','r') as file:
   cty = json.loads([x for x in file][0])
with open('models/examples/waterdemand/config/rates.json','r') as file:
   waterdemand=json.loads([x for x in file][0])

cty={str(k).zfill(5):v for k, v in cty.items()}

def Water_Demand_Simulation(countypop,rate):

    water={}
    for i in rate.keys():
      if i in countypop.keys():
          water[i]= (countypop[i]['2015']*rate[i])
      else:
          water[i]=(0)
    #with open('water_demand_2015.json', 'w') as file:
    #    file.write(json.dumps(data))
    return water




