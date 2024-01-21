import sqlite3
from datetime import datetime
import time

class GridDataStore:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = sqlite3.connect(self.db_path)
        self.create_table()

    def create_table(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE com.victronenergy.grid (
                    'Source'	TEXT NOT NULL UNIQUE,
                    'Updated'	INTEGER,
                    '/Ac/Energy/Forward'	INTEGER DEFAULT 0,
                    '/Ac/Energy/Reverse'	INTEGER DEFAULT 0,
                    '/Ac/Energy/Power'	INTEGER DEFAULT 0,
                    '/Ac/Power'	INTEGER DEFAULT 0,
                    '/Ac/L1/Current'	INTEGER DEFAULT 0,
                    '/Ac/L1/Power'	INTEGER DEFAULT 0,
                    '/Ac/L1/Voltage'	INTEGER DEFAULT 0,
                    '/Ac/L2/Current'	INTEGER DEFAULT 0,
                    '/Ac/L2/Power'	INTEGER DEFAULT 0,
                    '/Ac/L2/Voltage'	INTEGER DEFAULT 0,
                    '/Ac/L3/Current'	INTEGER DEFAULT 0,
                    '/Ac/L3/Power'	INTEGER DEFAULT 0,
                    '/Ac/L3/Voltage'	INTEGER DEFAULT 0,
                    PRIMARY KEY('Source')
                )
            ''')

    def insert_data(self, source, updated, energy_forward, energy_reverse, energy_power, power, 
                    l1_current, l1_power, l1_voltage, 
                    l2_current, l2_power, l2_voltage, 
                    l3_current, l3_power, l3_voltage):
        with self.conn:
            self.conn.execute('''
                INSERT INTO "com.victronenergy.grid" (
                    'Source', 'Updated', '/Ac/Energy/Forward', '/Ac/Energy/Reverse', '/Ac/Energy/Power',
                    '/Ac/Power', '/Ac/L1/Current', '/Ac/L1/Power', '/Ac/L1/Voltage',
                    '/Ac/L2/Current', '/Ac/L2/Power', '/Ac/L2/Voltage',
                    '/Ac/L3/Current', '/Ac/L3/Power', '/Ac/L3/Voltage'
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(Source) DO UPDATE SET
                    'Updated' = excluded.Updated,
                    '/Ac/Energy/Forward' = excluded.'/Ac/Energy/Forward',
                    '/Ac/Energy/Reverse' = excluded.'/Ac/Energy/Reverse',
                    '/Ac/Energy/Power' = excluded.'/Ac/Energy/Power',
                    '/Ac/Power' = excluded.'/Ac/Power',
                    '/Ac/L1/Current' = excluded.'/Ac/L1/Current',
                    '/Ac/L1/Power' = excluded.'/Ac/L1/Power',
                    '/Ac/L1/Voltage' = excluded.'/Ac/L1/Voltage',
                    '/Ac/L2/Current' = excluded.'/Ac/L2/Current',
                    '/Ac/L2/Power' = excluded.'/Ac/L2/Power',
                    '/Ac/L2/Voltage' = excluded.'/Ac/L2/Voltage',
                    '/Ac/L3/Current' = excluded.'/Ac/L3/Current',
                    '/Ac/L3/Power' = excluded.'/Ac/L3/Power',
                    '/Ac/L3/Voltage' = excluded.'/Ac/L3/Voltage'
            ''', (source, int(time.time()), energy_forward, energy_reverse, energy_power, 
                  power, l1_current, l1_power, l1_voltage, 
                  l2_current, l2_power, l2_voltage, 
                  l3_current, l3_power, l3_voltage))

    def retrieve_data(self, source):
        cursor = self.conn.cursor()
        cursor.execute('SELECT * FROM com.victronenergy.grid WHERE source = ?', (source,))
        return cursor.fetchall()

    def close(self):
        self.conn.close()