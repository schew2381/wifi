from requests import Session
import urllib3
import json
import time
from typing import Set
import configparser
from datetime import timedelta, datetime

# Ignore warnings for SSL login
urllib3.disable_warnings()

# Converts bytes to megabits
def megabit(num: int):
    return num / 125000

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
    def start_tracking(self, interval: int, minutes: int, hosts: Set[str]):
        endtime = datetime.utcnow() + timedelta(seconds= minutes * 60)
        i = 1
        while True:
            self.update(hosts) # Update info while checking for server timeout
            for entry in self.tracked:
                tx_rate = self.tracked[entry]['tx_bytes-r']
                rx_rate = self.tracked[entry]['rx_bytes-r']

                print(entry + ":")
                print('tx_bytes-rate:' + str(tx_rate))
                print('In megabits per second:' + str(megabit(tx_rate)))
                print('rx_bytes-r:' + str(rx_rate))
                print('In megabits per second:' + str(megabit(rx_rate)))
                print()
            print("iteration: " + str(i))
            print()
            if datetime.utcnow() > endtime:  # if timed out
                print("The function has run for the elapsed time.")
                break
            i += 1
            time.sleep(interval)

    # Check if timed out of server login
    def update(self, hosts: Set[str]):
        self.base = json.loads(self.session.get("https://192.168.1.1/proxy/network/api/s/default/stat/sta").text)
        if self.base["meta"]["rc"] == "error" and self.base["meta"]["msg"] == "api.err.LoginRequired":
            raise LoggedInException("Not logged in yet, please retry again")
        self.data = self.base["data"]
        self.set_tracking(hosts)


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read('credentials.ini')
    length = input('Program length in minutes: ')
    interval = input('Interval between pings in seconds: ')
    test = Unify({"username": config["login"]["username"], "password": config["login"]["password"],
                  "rememberMe": False})
    test.start_tracking(int(interval), int(length), {config["hosts"]["device1"], config["hosts"]["device2"], config["hosts"]["device3"]})
