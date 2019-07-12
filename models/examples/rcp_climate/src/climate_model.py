"""
Created on Wed Jul 10 2019

@author: afiallo1
"""

import numpy as np
import json


def temp_inc(init_data, year):
    json1_data = init_data

    mean_glob_temps = []
    for i in json1_data:
        #print(json1_data)
        for j in json1_data[i]:
            mean_glob_temps.append(json1_data[i][j][year][2])
    return np.mean(mean_glob_temps)

# with open("D:/STW_Models/simon/models/examples/rcp_climate/config/rcp26data.json", 'r') as file:
#     test = json.load(file)
#
# print(temp_inc(test, 1))

