import json
import sys
import urllib.error
import urllib.parse
import urllib.request
import configparser
import datetime
import time
import dbm
import csv
import os
import io

from .fetch import SSEClient, Fetch


class Configuration:
    def __init__(self, filename="airbacus.ini"):
        self.config = configparser.ConfigParser()
        self.config.read(filename)

        if self.server().find("your-airbacus-server-endpoint") >= 0:
            print("Please configure the airbacus server endpoint in %s" % filename)
            exit(-1)
        if self.token().find("dummy") >= 0:
            print("Please configure the waqi token in %s" % filename)
            exit(-1)

    def server(self):
        return self.config.get("airbacus", "server")

    def cache(self):
        path = self.config.get("airbacus", "store") + "/.cache/"
        os.makedirs(path, exist_ok=True)
        return path

    def token(self):
        return self.config.get("waqi", "token")


class Store:
    def __init__(self):
        self.config = Configuration()

    def fetchSSE(self, url, title=""):
        client = SSEClient(
            self.config.server() + url,
            headers={
                "X-Waqi-Token": self.config.token(),
                "X-AirBacus-Client": "py/1.0.0",
            },
        )
        samples = []
        for e in client.events():
            m = json.loads(e.data)
            if e.event == "error":
                print("\nOh no!", e.data)
            elif m == "done":
                break
            elif m != "started":
                st = ""
                for x in m:
                    try:
                        t = x[0]
                        st = datetime.datetime.fromtimestamp(
                            t, tz=datetime.timezone.utc
                        ).strftime("%b %d, %Y")
                        v = x[1]
                        samples.append((t, v))
                    except Exception as e:
                        print("\nSorry, something went wrong: ", e)
                        exit(-1)
                sys.stdout.write("\x1b[2K\r")
                print(title, ":", st, ": ", len(samples), end="")
                sys.stdout.flush()
        sys.stdout.write("\x1b[2K\r")
        return samples

    def fetchJSON(self, url):
        r = Fetch(
            self.config.server() + url,
            headers={
                "X-Waqi-Token": self.config.token(),
                "X-AirBacus-Client": "py/1.0.0",
            },
        )
        if r.status_code == 0:
            print("Sorry, failed to fetch %s: %s" % (url, r.text))
            return None

        if r.status_code != 200:
            print("Sorry, failed to fetch %s: http error %d" % (url, r.status_code))
            return None

        json = r.json()
        if json is None:
            snippet = r.text[:50]
            print("Sorry, failed to fetch %s: invalid JSON (%s...)" % (url, snippet))
            return None

        return json["data"]

    def allStations(self):
        url = "/api/stations"
        stations = self.fetchJSON(url)
        if stations is None:
            return []
        return list(map(lambda x: Station(self, x), stations))


class Station:
    def __init__(self, repo, station):
        self.model = station
        self.repo = repo

    def name(self):
        return self.model["name"]

    def geo(self):
        return self.model["geo"]

    def id(self):
        return self.model["feed"] + ":" + self.model["station"]

    def download(self):
        if self.model["species"] is None:
            print(
                "%s:%s This station has no active measurement"
                % (self.model["feed"], self.model["name"])
            )
            return None

        db = dbm.open(self.repo.config.cache() + "/datastore.dbm", "c")

        readings = dict()

        species = self.model["species"]
        for specie in species:
            title = "%s:%s (%s)" % (self.model["feed"], self.model["name"], specie)
            key = self.model["feed"] + ":" + self.model["station"] + ":" + specie
            if key in db:
                x = json.loads(db[key])
                samples = x["samples"]
                print("%s is already downloaded (%d samples)" % (title, len(samples)))

            else:
                args = {
                    "station": self.model["station"],
                    "feed": self.model["feed"],
                    "specie": specie,
                    "from": "2020-01-01",
                }
                url = "/api/station/historic?" + urllib.parse.urlencode(args)
                samples = self.repo.fetchSSE(url, title)
                print("%s downloaded %d samples" % (title, len(samples)))

                db[key] = json.dumps(
                    {"samples": samples, "fetched": time.time(), "version": 1}
                )

            for x in samples:
                t = x[0]
                if t not in readings:
                    readings[t] = dict()
                readings[t][specie] = x[1]

        return StationReadings(self, species, readings)


class StationReadings:
    def __init__(self, station: Station, species, readings):
        self.readings = readings
        self.station = station
        self.species = species

    def csv(self):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["time"] + self.species)
        for t in sorted(self.readings.keys()):
            st = datetime.datetime.fromtimestamp(t, tz=datetime.timezone.utc).strftime(
                "%Y-%m-%dT%H:%M:%SZ"
            )
            writer.writerow(
                [st]
                + [
                    self.readings[t][x] if x in self.readings[t] else None
                    for x in self.species
                ]
            )
        return output.getvalue()
