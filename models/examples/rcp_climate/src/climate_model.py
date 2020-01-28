"""
Created on Wed Jul 10 2019

@author: afiallo1
"""

import numpy as np
import json


def temp_inc(init_data, year):
    json1_data = init_data
    mean_glob_temps = []
    with open("/opt/src/weights.json") as f:
        weights = json.load(f)

    single_year_US = {}
    # Go through the json divided into lat,lon grid squares

    for i in json1_data:
        if 50 >= float(i) >= 23:
            # Convert to format that plays nice with mongodb; only get U.S squares
            single_year_US[i.replace('.', '_')] = {}
        for j in json1_data[i]:
            # Use two outputs, single global mean temperature and gridded climate data
            mean_glob_temps.append(json1_data[i][j][year][3])

            # Contiguous U.S bounded by (49 N, 122W), (24N 66W)
            if 50 >= float(i) >= 23 and -65 >= float(j) >= -130:
                single_year_US[i.replace('.', '_')][j.replace('.', '_')] = (
                    json1_data[i][j][year][0], json1_data[i][j][year][1], json1_data[i][j][year][2],
                    json1_data[i][j][year][3]-273.15
                )

    # Apply weights
    weighted_sum = np.sum([a*b for a, b in zip(mean_glob_temps, weights)])

    # Output: Global average (C) +
    # grid of U.S (precipitation (mm), evaporation (mm), surface runoff (mm), surface temp(C))
    translated = {}
    for lat, lat_values in single_year_US.items():
        for lon, lon_values in lat_values.items():
            print(lat, lon)
            num = 144*(float(lat.replace("_", ".")) + 89)/2 + (float(lon.replace("_", ".")) + 180 - 1.25)/2.5
            translated["climate{:.1f}".format(num)] = lon_values[0]

    return weighted_sum-273.15, translated #single_year_US

# # test
#
#
# with open("D:/STW_Models/simon/models/examples/rcp_climate/config/rcp26data.json", 'r') as file:
#     test = json.load(file)
# v1, v2 = temp_inc(test, 0)
# print(v2)

# with open('climate_data_year0.json', 'w') as outf:
#     json.dump(v2, outf)
