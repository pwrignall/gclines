# gclines

Basic script for taking an input of airport pairs and outputting those airport pairs and a series of points connecting them, representing great circles.

## Set up

1. Clone this repository

2. Install required packages with `pip install -r requirements.txt`

## Instructions

1. Download [airports.csv](https://davidmegginson.github.io/ourairports-data/airports.csv) from [OurAirports](https://ourairports.com/data/) and save it to your working directory

2. In the same directory, create a file named `routes.csv` and populate it with the airport pairs you're interested in plotting. It should have headings "from" and "to", looking like this:

    ```csv
    from,to
    KUL,SIN
    HKG,TPE
    CGK,SIN
    HKG,PVG
    CGK,KUL
    ```

3. Run the script using e.g. `python gclines.py`. Four output files should get generated.

    Two CSVs:

    a. `airport_points.csv`: a comma-separated file containing a distinct list of the airports from `routes.csv` with
    five columns. `iata_code`, `name`, `loc_name` (the 'municipality' column from OurAirports), `latitude`, `longitude`.

    b. `route_points.csv`: a comma-separated file containing three columns. `route`, an airport pair route label.
    `latitude` and `longitude`, decimal columns corresponding to the series of great circle points.

    And two GeoJSONs:

    c. `airport_points.geojson`: a GeoJSON format file containing a distinct list of the airports from `routes.csv` as
    a FeatureCollection. 

    d. `airport_lines.geojson`: a GeoJSON format file containing the route lines as a FeatureCollection.


### Disclaimer

Minimally tested on Windows and Ubuntu. The script is a simple script, containing no unit tests, data validation or sanitisation.