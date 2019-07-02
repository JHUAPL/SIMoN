import numpy as np
from netCDF4 import Dataset, MFDataset


d1 = Dataset('rcp26/pr/pr_Amon_GFDL-CM3_rcp26_r1i1p1_201601-202012.nc')  # 5 years
allData = MFDataset('rcp26/pr/pr_Amon_GFDL-CM3_rcp26_r1i1p1*nc')  # 95 years

# args: netCDF4 Dataset object
# Generate dictionary of precipitation data for each lat,lon value
def pr_model(pr_data):
    precip = list(pr_data.variables['pr'])  # Precip values, saved as 3-tuple
    lats = list(pr_data.variables['lat'])  # Latitude degrees north, saved as centroid of square
    lons = list(pr_data.variables['lon'])  # Longitude degrees east, saved as centroid of square

    new_pr = {}

    # Iterate through squares of lat,lon
    for i in range(len(lats)):
        # Create dictionary of latitutdes
        new_pr[float((lats[i]))] = {}

        for j in range(len(lons)):
            # Create nested dict of longitudes for each latitude
            new_pr[float(lats[i])][float(lons[j])] = []

            # Iterate through years, save as list of pr_values for each lat,lon square
            year = []
            for k in range(len(precip)):
                precipitation = precip[k][i][j]
                year.append(precipitation)
                # Choose point to break off year and sum up months within, add to list
                if (k + 1) % 12 == 0:
                    new_pr[float((lats[i]))][float(lons[j])].append(sum(year) * 31536000)
                    year = []  # Clear months in year
    return new_pr

def evap_model(evs_data):

    new_evs = {}
    evap = list(evs_data.variables['evspsbl'])  # Evp values, saved as 3-tuple

# # # NOTE: Some of these values are negative, let Victoria know when she gets back
    lats = list(evs_data.variables['lat'])  # Latitude degrees north, saved as centroid of square
    lons = list(evs_data.variables['lon']) # Longitude degrees east, saved as centroid of square
    new_ev = {}

    for i in range(len(lats)):
        new_ev[float((lats[i]))] = {}
        for j in range(len(lons)):
            new_ev[float(lats[i])][float(lons[j])] = []
            year = []
            for k in range(len(evap)):
                evaporation = evap[k][i][j]
                year.append(evaporation)
                if (k + 1) % 12 == 0:
                    new_ev[float((lats[i]))][float(lons[j])].append(sum(year) * 31536000)
                    year = []

    return new_evs

def tas_model(tas_data):
    new_tas = {}
    temps = list(tas_data.variables['tas'])  # Precip values, saved as 3-tuple
    lats = list(tas_data.variables['lat'])  # Latitude degrees north, saved as centroid of square
    lons = list(tas_data.variables['lon'])  # Longitude degrees east, saved as centroid of square
    for i in range(len(lats)):

        new_tas[float((lats[i]))] = {}

        for j in range(len(lons)):
            new_tas[float(lats[i])][float(lons[j])] = []
            year = []
            for k in range(len(temps)):
                temperature = temps[k][i][j]
                year.append(temperature)

                if (k + 1) % 12 == 0:
                    new_tas[float((lats[i]))][float(lons[j])].append(np.mean(year))
                    year = []
    return new_tas

# # # TODO: Confirm if rain moves towards poles as time passes on for different RCPs
