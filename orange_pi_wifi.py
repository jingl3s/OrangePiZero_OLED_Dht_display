

import logging
import subprocess
from urllib.error import URLError
import urllib.request


_logger = None

def orange_pi_network() -> bool:
    '''
    Detect si access point est la

Si oui verification si internet est disponible

Si non alors redemarrage networking ou test pour redemarrer seulement la carte wifi

    '''
    reseau_dispo = False
    # Reseau local dispo
    if _is_network_avail():
        reseau_dispo = True
    else:
        _enable_network()
        reseau_dispo = _is_network_avail()

    return reseau_dispo


def _enable_network():

    if verify_url('http://192.168.254.1'):
        _restart_network()
    else:
        enable_wifi(True)
        if verify_wifi_status():
            if verify_url('http://192.168.254.1'):
                _restart_network()


def _is_network_avail() -> bool:
    reseau_dispo = False
    # Reseau local dispo
    if verify_url('http://192.168.254.1'):
        # Internet dispo
        if verify_url('http://www.domoticz.com'):
            reseau_dispo = True
    return reseau_dispo


def enable_wifi(state: bool):
    if state:
        state_txt = "on"
    else:
        state_txt = "off"
    cmd = ["nmcli", "radio", "wifi", state_txt]

    _execute_cmd(cmd)


def _restart_network():
    cmd = ["sudo", "systemctl", "restart", "networking"]
    _execute_cmd(cmd)


def verify_wifi_status()->bool:
    cmd = ["ip", "a", "show", "wlan0"]
    try:
        output = subprocess.check_output(cmd)

        print(output)
    except subprocess.CalledProcessError as e: 
        print("Exception {}".format(e))
    return True
        


def verify_url(url: str) -> bool:
    last_comm_success = False
    if True:
        if True:
            try:
                with urllib.request.urlopen(url) as response:
                    # html = response.read()
                    if response.status != 200:
                        _logger.error('com error')
                    else:
                        last_comm_success = True

            except URLError as e:
                _logger.debug("Exception URLError {}".format(e))
            except ConnectionRefusedError as e:
                _logger.debug(
                    "Exception ConnectionRefusedError {}".format(e))
    return last_comm_success


def _execute_cmd(cmd):
    try:
        with subprocess.Popen(cmd) as proc:
            proc.communicate()
    except:
        # Ignore error to permit continue process and cases debug on non
        # android
        pass


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    _logger = logging.getLogger()
    exec_net = orange_pi_network()
    _logger.info("Exec network: {}".format(exec_net))
