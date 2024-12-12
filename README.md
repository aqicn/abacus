# AirBacus - Open Air Quality Data Store

AirBacus is an open-air quality data store. You can use this repo to download
the historical and real-time data from any AirBacus data store.

## Configuration

Before starting, make sure to get a valid token from aqicn.org/data-platform/

You then need to edit the `airbacus.ini` file with the correct configuration for
the token as well as the airbacus server:

```ini
[airbacus]
server = https://your-airbacus-server-endpoint/

[waqi]
; Get your own free token from https://aqicn.org/data-platform/token/
token = dummy-token-for-test-purpose-only
```

## Setup

The script needs the `requests` and `sseclient` libraries in order to download the
data.

```bash
pip install requests client
```

## historical data download

Check the example in the `app.py` file:

python app.py

```python
import airbacus

airbacusStore = airbacus.Store()

stations = airbacusStore.allStations()
print("There are %d stations" % len(stations))

# Download the first one
for station in stations:
    
    print("The station %s is named %s and is located %s" % (station.id(), station.name(), station.geo()))
    
    readings = station.download()
    if readings is None:
        continue

    csv = readings.csv()
    print("The CSV file is %d rows" % len(csv.split("\n")))

```

When downloading a station's readings, the data will be cached in a Key Value store located in `datastore/cache`. 
You can change the `datastore` folder path by editing the `waqi.store` property in the `abacus.ini` file.


## Performance

The airbacus is currenrtly hosted on an affordable VPS server. 
while we are working on getting a more powerfull server, please be patient with the slow donwload.


## Ongoing work

[ ] Add information about the units used for the species
[ ] Support for output formats: NetCDF, HDF5, Pandas, etc..
[ ] Support for specifying the time period for historical data downwload
[ ] Support for retrieving the real-time data
[ ] Support for updatable download (only download the parts which are not already in cache)
[ ] Add github sponsor information
[ ] Add usage license 




