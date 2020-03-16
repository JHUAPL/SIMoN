# SIMoN Visualization

At every increment step, each model outputs its data for that increment step as a dictionary. The dictionary maps geographic IDs to values for the corresponding region. The particular IDs will depend on the geographic granularity. This dictionary is stored as a JSON document in a Mongo database. Since the data maps each region to a single value, it can be visualized on a choropleth map.

## Export data

SIMoN stores all of the data outputs from the models as documents in a Mongo database (the `simon_mongodb` container). You can retrieve a single document and save it as a JSON file using the `export.sh` bash script in the `viz` directory.

```
./export.sh <model_name> <year>
```
where `year` will be equal to its corresponding increment step plus the initial year. For example,
```
./export.sh gfdl_cm3 2035
```
will retrieve the annual data that the GFDL CM3 model projected for the year 2035. (If the initial year, increment step 0, is 2016, then 2035 is increment step 19.)

## Plot data (requires [Python 3.6+](https://www.python.org/downloads/))

Once you've retrieved a document and saved it as a JSON file, plot the data on a choropleth map using the `plot.py` script in the `viz` directory. (You can also use the `Plot.ipynb` Jupyter notebook.) Just make sure to pip install `requirements.txt` first.
```
pip install -r requirements.txt
python plot.py --data <your_mongo_doc>.json
```
For example,
```
python plot.py --data 2035_gfdl_cm3.json
```

Other command line options:
  * `--data`: path to the JSON file created by `export.sh`.
  * `--shapefile_dir`: path to the directory of shapefiles.
  * `--projection`: EPSG coordinate reference system to use for plotting.
  * `--width`: pixel width of the plot.
  * `--height`: pixel height of the plot.
  * `--show`: display the plot.
  * `--save`: write the plot to a file.

A new HTML file will be created in the `viz` directory. Open this file in a web browser to display the Bokeh visualization.
![evaporation](demo/2035_evaporation.png)
![precipitation](demo/2035_precipitation.png)
