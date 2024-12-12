# AirBacus - Open Air Quality Data Store

[![CI](https://github.com/aqicn/abacus/actions/workflows/ruff.yaml/badge.svg)](https://github.com/aqicn/abacus/actions/workflows/ruff.yaml)

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

The Python3 script is dependency free, so you do *not* need to install any library to run it.

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

When downloading a station's readings, the data will be cached in a Key-Value store located in `datastore/cache`. 
You can change the `datastore` folder path by editing the `waqi.store` property in the `abacus.ini` file.


## Performance

The AirBacus server implementation is an highly optimized TSDB (time series DB) server, written in Golang, and which can take 1000 concurrent requests without any issues.

However,  the current physical server on which the AirBacus server is running is a low-cost shared VPS, with only two cores (shared with other processes) and 2G of RAM.

While working on getting sponsors to upgrade to a more powerful VPS server, the download speed is limited to one concurrent request. So, please, be patient with the slow downloads.



## Ongoing work

 - [ ] Add information about the units used for the species
 - [ ] Support for output formats: NetCDF, HDF5, Pandas, etc.
 - [ ] Support for specifying the time period for historical data download
 - [ ] Support for retrieving the real-time data
 - [ ] Support for updatable download (only download the parts which are not already in the cache)
 - [ ] Add GitHub sponsor information
 - [ ] Add usage license 




