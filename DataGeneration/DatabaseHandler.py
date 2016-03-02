import sqlite3 as sql
import pandas as pd
from DataGeneration.MapLocation import MapLocation


class DatabaseHandler:

    def __init__(self, db_file_name='db.sqlite3', full=True):
        if full:
            self.conn = sql.connect(db_file_name)
            self.initialize_db()

    def initialize_db(self):
        self._add_addresses_table()
        self._add_stops_table()
        self._add_routes_table()
        self.conn.commit()

    def _add_addresses_table(self):
        c = self.conn.cursor()
        c.execute("""
                  CREATE TABLE IF NOT EXISTS addresses
                  (id INTEGER PRIMARY KEY,
                  latitude real NOT NULL,
                  longitude real NOT NULL)
                  """)
        c.close()

    def _add_stops_table(self):
        c = self.conn.cursor()
        c.execute("""
                  CREATE TABLE IF NOT EXISTS stops
                  (id INTEGER PRIMARY KEY,
                  latitude real NOT NULL,
                  longitude real NOT NULL)
                  """)
        c.close()

    def _add_routes_table(self):
        c = self.conn.cursor()
        c.execute("""
                  CREATE TABLE IF NOT EXISTS routes
                  (id INTEGER PRIMARY KEY,
                  address_id INTEGER NOT NULL,
                  stop_id INTEGER NOT NULL,
                  distance INTEGER NOT NULL,
                  time INTEGER NOT NULL,
                  FOREIGN KEY(address_id) REFERENCES addresses(id),
                  FOREIGN KEY(stop_id) REFERENCES stops(id))
                  """)
        c.close()

    def add_addresses_from_file(self, file_name):
        df = pd.read_csv(file_name)
        df.to_sql('addresses', self.conn, if_exists='append', index=False)

    def add_stops_from_file(self, file_name):
        df = pd.read_csv(file_name)
        df.to_sql('stops', self.conn, if_exists='append', index=False)

    def add_address(self, location):
        if not hasattr(location, 'latitude'):
            raise TypeError('location must have latitude property')
        if not hasattr(location, 'longitude'):
            raise TypeError('location must have longitude property')
        c = self.conn.cursor()
        if location.id != 0:
            c.execute("INSERT INTO addresses (id, latitude, longitude) "
                      "VALUES (?, ?, ?)",
                      (location.id, location.latitude, location.longitude))
        else:
            c.execute("INSERT INTO addresses (latitude, longitude) "
                      "VALUES (?, ?)", (location.latitude, location.longitude))
        self.conn.commit()
        c.close()

    def add_stop(self, location):
        if not hasattr(location, 'latitude'):
            raise TypeError('location must have latitude property')
        if not hasattr(location, 'longitude'):
            raise TypeError('location must have longitude property')
        c = self.conn.cursor()
        if location.id != 0:
            c.execute("INSERT INTO stops (id, latitude, longitude) "
                      "VALUES (?, ?, ?)",
                      (location.id, location.latitude, location.longitude))
        else:
            c.execute("INSERT INTO stops (latitude, longitude) "
                      "VALUES (?, ?)",
                      (location.latitude, location.longitude))
        self.conn.commit()
        c.close()

    def add_route(self, address, stop, distance, time):
        c = self.conn.cursor()
        c.execute("INSERT INTO routes "
                  "(address_id, stop_id, distance, time) "
                  "VALUES (?, ?, ?, ?)",
                  (address, stop, distance, time))
        self.conn.commit()
        c.close()

    # Information Retrieval
    def get_address_generator(self, verbose=False):
        c = self.conn.cursor()
        c.execute("SELECT "
                  "addresses.latitude, addresses.longitude, addresses.id "
                  "FROM addresses LEFT JOIN routes "
                  "ON routes.address_id = addresses.id "
                  "WHERE routes.id IS NULL")
        if verbose:
            print("fetching all addresses without routes...")
        rows = c.fetchall()
        c.close()
        if verbose:
            print("fetched {} addresses".format(len(rows)))
        for row in rows:
            yield MapLocation(latitude=row[0], longitude=row[1], id=row[2])

    def get_all_stops(self):
        c = self.conn.cursor()
        c.execute("SELECT * from stops")
        rows = c.fetchall()
        c.close()
        return [MapLocation(latitude=row[1], longitude=row[2], id=row[0])
                for row in rows]

    def output_routes(self, file_path):
        return self.routes_dataframe().to_csv(file_path)

    def routes_dataframe(self):
        return pd.read_sql_query(
            "SELECT "
            "addresses.latitude AS address_latitude,"
            "addresses.longitude AS address_longitude,"
            "stops.latitude AS stop_latitude,"
            "stops.longitude AS stop_longitude,"
            "routes.distance AS distance,"
            "routes.time AS time "
            "FROM routes "
            "LEFT JOIN addresses ON routes.address_id = addresses.id "
            "LEFT JOIN stops ON routes.stop_id = stops.id",
            self.conn)
