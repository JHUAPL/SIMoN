from climate_model import pr_model
from netCDF4 import MFDataset


rcp26 = MFDataset('rcp26/pr/pr_Amon_GFDL-CM3_rcp26_r1i1p1*nc')
rcp85 = MFDataset('rcp85/pr/pr_Amon_GFDL-CM3_rcp85_r1i1p1*nc')

year1 = rcp26.variables['time_bnds'][120:]

print(year1)
