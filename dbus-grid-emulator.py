#!/usr/bin/env python

# import normal packages
import platform
import logging
import sys
import os
import sys
import sqlite3
if sys.version_info.major == 2:
    import gobject
else:
    from gi.repository import GLib as gobject
import sys
import time
import configparser # for config/ini file

# our own packages from victron
sys.path.insert(1, os.path.join(os.path.dirname(__file__), '/opt/victronenergy/dbus-systemcalc-py/ext/velib_python'))
from vedbus import VeDbusService
from datetime import datetime

class DbusTeslaAPIService:
  def __init__(self):
    config = self._getConfig()
    deviceinstance = int(config['DEFAULT']['Deviceinstance'])
    customname = config['DEFAULT']['CustomName']
    productname='Grid Emulator'
    connection='Grid Emulator'

    #formatting
    _kwh = lambda p, v: (str(round(v, 2)) + 'kWh')
    _state = lambda p, v: (str(v))
    _mode = lambda p, v: (str(v))
    _a = lambda p, v: (str(round(v, 1)) + 'A')
    _w = lambda p, v: (str(round(v, 1)) + 'W')
    _v = lambda p, v: (str(round(v, 1)) + 'V')

    self._dbusservicegrid = VeDbusService("{}.http_{:02d}".format('com.victronenergy.grid', deviceinstance))

    logging.debug("%s /DeviceInstance = %d" % ('com.victronenergy.grid', deviceinstance))

    self._runningSeconds = 0
    self._startDate = datetime.now()
    self._lastCheck = datetime(2023, 12, 8)
    self._running = False
    self._carData = {}

    self.add_standard_paths(self._dbusservicegrid, "Grid", "Grid", connection, deviceinstance, config, {
            '/Ac/Energy/Forward': {'initial': 0, 'textformat': _kwh},
            '/Ac/Energy/Reverse': {'initial': 0, 'textformat': _kwh},
            '/Ac/Energy/Power': {'initial': 0, 'textformat': _w},
            '/Ac/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L1/Current': {'initial': 0, 'textformat': _a},
            '/Ac/L1/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L1/Voltage': {'initial': 0, 'textformat': _v},
            '/Ac/L2/Current': {'initial': 0, 'textformat': _a},
            '/Ac/L2/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L2/Voltage': {'initial': 0, 'textformat': _v},
            '/Ac/L3/Current': {'initial': 0, 'textformat': _a},
            '/Ac/L3/Power': {'initial': 0, 'textformat': _w},
            '/Ac/L3/Voltage': {'initial': 0, 'textformat': _v},
          })

    # last update
    self._lastUpdate = 0

    # add _update function 'timer'
    gobject.timeout_add(500, self._update) # pause 250ms before the next request

    # add _signOfLife 'timer' to get feedback in log every 5minutes
    gobject.timeout_add(self._getSignOfLifeInterval()*60*1000, self._signOfLife)

  def add_standard_paths(self, dbusservice, productname, customname, connection, deviceinstance, config, paths):
      # Create the management objects, as specified in the ccgx dbus-api document
      dbusservice.add_path('/Mgmt/ProcessName', __file__)
      dbusservice.add_path('/Mgmt/ProcessVersion', 'Unknown version, and running on Python ' + platform.python_version())
      dbusservice.add_path('/Mgmt/Connection', connection)

      # Create the mandatory objects
      dbusservice.add_path('/DeviceInstance', deviceinstance)
      dbusservice.add_path('/ProductId', 0xFFFF) # id assigned by Victron Support from SDM630v2.py
      dbusservice.add_path('/ProductName', productname)
      dbusservice.add_path('/CustomName', customname)
      dbusservice.add_path('/Connected', 1)
      dbusservice.add_path('/Latency', None)
      dbusservice.add_path('/FirmwareVersion', "1.0")
      dbusservice.add_path('/HardwareVersion', 0)
      dbusservice.add_path('/Position', int(config['DEFAULT']['Position']))
      dbusservice.add_path('/Serial', "0000000000")
      dbusservice.add_path('/UpdateIndex', 0)

      # add path values to dbus
      for path, settings in paths.items():
        dbusservice.add_path(
          path, settings['initial'], gettextcallback=settings['textformat'], writeable=True, onchangecallback=self._handlechangedvalue)

  def _getConfig(self):
    config = configparser.ConfigParser()
    config.read("%s/config.ini" % (os.path.dirname(os.path.realpath(__file__))))
    return config;

  def _getSignOfLifeInterval(self):
    config = self._getConfig()
    value = config['DEFAULT']['SignOfLifeLog']

    if not value:
        value = 0

    return int(value)

  def _getTeslaAPISerial(self):
    vin = 0
    if not vin:
        vin = 0
    return str(vin)

  def _signOfLife(self):
    logging.info("--- Start: sign of life ---")
    logging.info("Last _update() call: %s" % (self._lastUpdate))
    logging.info("Last '/Ac/Power': %s" % (self._dbusservicegrid['/Ac/Power']))
    logging.info("--- End: sign of life ---")
    return True

  def _update(self):
    try:
       config = self._getConfig()
      
       voltage = 120
       current = 12

       power = 10000
       totalin = 10000
       totalout = 0

       self._dbusservice['/Ac/Power'] =  power # positive: consumption, negative: feed into grid
       self._dbusservice['/Ac/L1/Voltage'] = 230
       self._dbusservice['/Ac/L2/Voltage'] = 230
       #self._dbusservice['/Ac/L3/Voltage'] = 230
       self._dbusservice['/Ac/L1/Current'] = round(power/2 / 230 ,2)
       self._dbusservice['/Ac/L2/Current'] = round(power/2 / 230 ,2)
       #self._dbusservice['/Ac/L3/Current'] = round(power/3 / 230 ,2)
       self._dbusservice['/Ac/L1/Power'] = round(power/2, 2)
       self._dbusservice['/Ac/L2/Power'] = round(power/2, 2)
       #self._dbusservice['/Ac/L3/Power'] = round(power/3, 2)

       self._dbusservice['/Ac/Energy/Forward'] = totalin
       self._dbusservice['/Ac/Energy/Reverse'] = totalout

      #  if power > 0: 
      #    self._dbusservicegrid['/Ac/Power'] = power
      #    self._dbusservicegrid['/Ac/Energy/Forward'] = "1.00kWh"
      #    if voltage > 120:
      #      self._dbusservicegrid['/Ac/L1/Voltage'] = 120
      #      self._dbusservicegrid['/Ac/L1/Current'] = int(current) / 2
      #      self._dbusservicegrid['/Ac/L1/Power'] = int(power) / 2
      #      self._dbusservicegrid['/Ac/L2/Voltage'] = 120
      #      self._dbusservicegrid['/Ac/L2/Current'] = int(current) / 2
      #      self._dbusservicegrid['/Ac/L2/Power'] = int(power) / 2
      #    else:
      #      self._dbusservicegrid['/Ac/L1/Voltage'] = 120
      #      self._dbusservicegrid['/Ac/L1/Current'] = current
      #      self._dbusservicegrid['/Ac/L1/Power'] = power
      #      self._dbusservicegrid['/Ac/L2/Voltage'] = 0
      #      self._dbusservicegrid['/Ac/L2/Current'] = 0
      #      self._dbusservicegrid['/Ac/L2/Power'] = 0
      #  else:
      #      self._dbusservicegrid['/Ac/L1/Voltage'] = 0
      #      self._dbusservicegrid['/Ac/L1/Current'] = 0
      #      self._dbusservicegrid['/Ac/L1/Power'] = 0
      #      self._dbusservicegrid['/Ac/L2/Voltage'] = 0
      #      self._dbusservicegrid['/Ac/L2/Current'] = 0
      #      self._dbusservicegrid['/Ac/L2/Power'] = 0

       #logging
       logging.debug("Grid Consumption (/Ac/Power): %s" % (self._dbusservicegrid['/Ac/Power']))
       logging.debug("---");

       # increment UpdateIndex - to show that new data is available
       index = self._dbusservicegrid['/UpdateIndex'] + 1  # increment index
       if index > 255:   # maximum value of the index
         index = 0       # overflow from 255 to 0
       self._dbusservicegrid['/UpdateIndex'] = index

       #update lastupdate vars
       self._lastUpdate = time.time()
    except Exception as e:
       self._dbusservicegrid['/Status'] = 10
       logging.critical('Error at %s', '_update', exc_info=e)

    # return true, otherwise add_timeout will be removed from GObject - see docs http://library.isr.ist.utl.pt/docs/pygtk2reference/gobject-functions.html#function-gobject--timeout-add
    return True

  def _handlechangedvalue(self, path, value):
    logging.debug("someone else updated %s to %s" % (path, value))
    return True # accept the change



def main():
  #configure logging
  logging.basicConfig(      format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S',
                            level=logging.INFO,
                            handlers=[
                                logging.FileHandler("%s/current.log" % (os.path.dirname(os.path.realpath(__file__)))),
                                logging.StreamHandler()
                            ])

  try:
      logging.info("Start");

      from dbus.mainloop.glib import DBusGMainLoop
      # Have a mainloop, so we can send/receive asynchronous calls to and from dbus
      DBusGMainLoop(set_as_default=True)

      #start our main-service
      pvac_output = DbusTeslaAPIService()

      logging.info('Connected to dbus, and switching over to gobject.MainLoop() (= event based)')
      mainloop = gobject.MainLoop()
      mainloop.run()
  except Exception as e:
    logging.critical('Error at %s', 'main', exc_info=e)
if __name__ == "__main__":
  main()