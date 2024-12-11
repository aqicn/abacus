# AirBacus - Open Air Quality Data Store

AirBacus is an open air quality data store. You can use this repo to download
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

The script needs the `requests` and `sseclient` library for downloading the
data.

```bash
pip install requests sseclient
```

## Downloading the station historical data

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

