from requests import Session
import urllib3
import json
import time
from typing import Set
import configparser
import flask

# Ignore warnings for SSL login
urllib3.disable_warnings()


# Class to handle log in failures
class LoggedInException(Exception):

    def __init__(self, *args, **kwargs):
        super(LoggedInException, self).__init__(*args, **kwargs)


# Unify class to hold server data
class Unify:

    # Enters server and logs in
    def __init__(self, data):
        self.session = Session()
        self.site = self.session.post("https://192.168.1.1/api/auth/login",
                                      data, verify=False)
        # self.site = self.session.post("https://192.168.1.1/api/auth/login", verify=False)
        self.site = self.session.post("https://192.168.1.1/api/auth/login", verify=False)
        self.base = json.loads(self.session.get("https://192.168.1.1/proxy/network/api/s/default/stat/sta").text)

        if self.base["meta"]["rc"] == "error" and self.base["meta"]["msg"] == "api.err.LoginRequired":
            raise LoggedInException("Not logged in yet, please retry again")

        self.data = self.base["data"]

        self.tracked = {}

    # Finds items to be tracked
    def set_tracking(self, hosts: Set[str]):
        for entry in self.data:
            if "hostname" in entry and entry["hostname"] in hosts:
                self.tracked[entry["hostname"]] = entry

    # Begins tracking items and checks if server timed-out
    def start_tracking(self, interval: int):
        while True:
            self.logged_out() # Check for server timeout
            for entry in self.tracked:
                print(entry + ":" + str(self.tracked[entry]['rx_bytes']))
                print('tx_bytes-r:' + str(self.tracked[entry]['tx_bytes-r']))
                print('rx_bytes-r:' + str(self.tracked[entry]['rx_bytes-r']))
                print()

            time.sleep(interval)

    # Check if timed out of server login
    def logged_out(self):
        if self.base["meta"]["rc"] == "error" and self.base["meta"]["msg"] == "api.err.LoginRequired":
            raise LoggedInException("Not logged in yet, please retry again")


config = configparser.ConfigParser()
config.read('credentials.ini')
test = Unify({"username": config["login"]["username"], "password": config["login"]["password"],
              "rememberMe": False})
test.set_tracking({config["hosts"]["device1"], config["hosts"]["device2"], config["hosts"]["device3"]})
test.start_tracking(1)
