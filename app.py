

import airbacus

airbacusStore = airbacus.Store()

stations = airbacusStore.allStations()
print("There are %d stations" % len(stations))

# Download the first one
for station in stations:
    print(
        "The station %s is named %s and is located %s"
        % (station.id(), station.name(), station.geo())
    )

    readings = station.download()
    if readings is None:
        continue

    csv = readings.csv()
    print("The CSV file is %d rows" % len(csv.split("\n")))
