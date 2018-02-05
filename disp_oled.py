'''
@author: zorbac

Copyright 2014 zorbac at free.fr
This code is free software; you can redistribute it and/or modify it
under the terms of the BSD license (see the file
COPYING.txt included with the distribution).
'''
from PIL import ImageFont
from datetime import datetime
from math import log
import os
import platform
import psutil
from random import randint
import socket
import time


try:
    from pyA20.gpio import gpio as GPIO  # @UnresolvedImport
    from pyA20.gpio import port  # @UnresolvedImport
    MODE = "PYA20"
except ImportError:
    MODE = "RPI"
    try:
        import RPi.GPIO as GPIO

    except ImportError:
        import GPIOEmu as GPIO

from luma.core.render import canvas  # @NoMove @UnresolvedImport
# from demo_opts import get_device

global width
width = 128
global height
height = 64

global col1
col1 = 4

global number_line_per_page
number_line_per_page = 4


def do_nothing(obj):
    pass


def make_font(name, size):
    font_path = os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'fonts', name))
    return ImageFont.truetype(font_path, size)


global font10

byteunits = ('B', 'KB', 'MB', 'GB', 'TB', 'PB', 'EB', 'ZB', 'YB')


def filesizeformat(value):
    exponent = int(log(value, 1024))
    return "%.1f %s" % (float(value) / pow(1024, exponent), byteunits[exponent])


def bytes2human(n):
    """
    >>> bytes2human(10000)
    '9K'
    >>> bytes2human(100001221)
    '95M'
    """
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 << (i + 1) * 10
    for s in reversed(symbols):
        if n >= prefix[s]:
            value = int(float(n) / prefix[s])
            return '%s%s' % (value, s)
    return "%sB" % n


def cpu_usage():
    # load average, uptime
    av1, av2, av3 = os.getloadavg()
    return "LOAD: %.1f %.1f %.1f" \
        % (av1, av2, av3)


def cpu_temperature():
    tempC = ((int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1000))
    return "CPU TEMP: %sc" \
        % (str(tempC))


def mem_usage():
    usage = psutil.virtual_memory()
    return "MEM FREE: %s/%s" \
        % (bytes2human(usage.available), bytes2human(usage.total))


def disk_usage(p_dir):
    usage = psutil.disk_usage(p_dir)
    return "DSK FREE: %s/%s" \
        % (bytes2human(usage.total - usage.used), bytes2human(usage.total))


def network(iface):
    stat = psutil.net_io_counters(pernic=True)[iface]
    return "NET: %s: Tx%s, Rx%s" % \
           (iface, bytes2human(stat.bytes_sent), bytes2human(stat.bytes_recv))


def lan_ip():
    #f = os.popen('ifconfig eth0 | grep "inet\ addr" | cut -c 21-33')
    f = os.popen("ip route get 1 | awk '{print $NF;exit}'")
    ip = str(f.read())
    # strip out trailing chars for cleaner output
    return "IP: %s" % ip.rstrip('\r\n').rstrip(' ')


def platform_info():
    return "%s %s" % (platform.system(), platform.release())


def uptime():
    # La commande n'est pas disponible avec le meme nom sur toutes les
    # plateformes
    if 'boot_time' in dir(psutil):
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time()  # @UndefinedVariable
                                                         )
    else:
        uptime = datetime.now() - datetime.fromtimestamp(psutil.get_boot_time())
    return "Uptime %s" % str(uptime).split('.')[0]


def date():
    return str(datetime.now().strftime(
        '%a %b %d %H:%M:%S'))


def get_dht(dht_sensor):
    temp, hum = dht_sensor.get_valeurs()
    return '{:0.1f}°  {:0.1f}%'.format(
        temp, hum)


def stats_page(device):
    global dht11
    global dht22
    global page_lines
    global current_line

    with canvas(device) as draw:
        draw.rectangle((0, 0, 127, height - 1), outline="white", fill="black")
        if looper == 0:
            draw.text((col1, line_pixel[0]), 'WELCOME TO OPi ZERO',
                      font=font10, fill=255)
            draw.text((col1, line_pixel[3]),
                      'Starting up...', font=font10, fill=255)
        elif looper > 0:

            for ligne_en_cours in range(number_line_per_page):

                if current_line < len(page_lines):
                    if page_lines[current_line][1] is not None:
                        draw.text((col1, line_pixel[ligne_en_cours]), page_lines[current_line][0](
                            page_lines[current_line][1]),  font=font10, fill=255)
                    else:
                        draw.text((col1, line_pixel[ligne_en_cours]),
                                  page_lines[current_line][0](),  font=font10, fill=255)
                else:
                    draw.text((col1, line_pixel[ligne_en_cours]),
                              '',  font=font10, fill=255)
                current_line = (current_line + 1)
            if current_line >= len(page_lines):
                current_line = 0


def get_oled_device():
    from luma.core.interface.serial import i2c  # @UnresolvedImport
    from luma.oled.device import ssd1306  # @UnresolvedImport

    # Activation du reset pour avoir l'affichage fonctionnel
    # initialize GPIO
    pin = port.PA6
    GPIO.init()
    GPIO.setcfg(pin, GPIO.OUTPUT)
    # send initial high, low, high
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.02)
    GPIO.output(pin, GPIO.LOW)
    time.sleep(0.02)
    GPIO.output(pin, GPIO.HIGH)
    time.sleep(0.02)

    # rev.1 users set port=0
    serial = i2c(port=0, address=0x3D)
#     device = ssd1306(serial, rotate=1)
    device = ssd1306(serial)

    # Activer la ligne suivante permet de bloquer l'affichage sur le dernier text lors de l'arret du programme
    #     device.cleanup = do_nothing
    return device


def get_my_device():
    try:
        dev = get_oled_device()
    except:
        dev = get_emul_device()
    return dev


def get_emul_device():
    from luma.emulator.device import pygame  # @UnresolvedImport
    device = pygame(mode="1")
    # Activer la ligne suivante permet de bloquer l'affichage sur le dernier text lors de l'arret du programme
#     device.cleanup = do_nothing
    return device


def get_push_button(p_dict_pin):
    disp = list()
    for pin, pin_info in p_dict_pin.items():
        disp.append("{} {}".format(pin, pin_info["last_state"]))
    return "INT: " + ",".join(disp)


class DHTFake(object):
    def __init__(self):
        pass

    def get_valeurs(self):
        self.valeurs = (randint(-200, 300) / 10.0, randint(100, 950) / 10.0)
        return self.valeurs


def create_dht():
    global dht11
    global dht22
    try:
        from dht.dht_interface import DHTInterface
        dht11 = DHTInterface(0, 11)
        dht22 = DHTInterface(1, 22)
    except:
        dht11 = DHTFake()
        dht22 = DHTFake()


def call_shutdown(pin_info):

    if pin_info["count"] == 3:
        print("Extinction demandé {}".format(pin_info["count"]))
        pin_info["count"] = 0
    else:
        print("Passage")


def io_setup(p_list_pin):
    # Activation du reset pour avoir l'affichage fonctionnel

    # initialize GPIO
    dict_pin = dict()

    if MODE == "PYA20":
        GPIO.init()
    elif MODE == "RPI":
        GPIO.setmode(GPIO.BCM)

    for pin in p_list_pin:

        if MODE == "PYA20":
            if pin == 15:
                pa_pin = port.PA15
            elif pin == 16:
                pa_pin = port.PA16
            else:
                raise ValueError("Pin number is not expected {}".format(pin))

            GPIO.setcfg(pa_pin, GPIO.INPUT)
            GPIO.pullup(pa_pin, GPIO.PULLUP)
        elif MODE == "RPI":
            pa_pin = pin
            GPIO.setup(pin, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        else:
            raise ValueError("Pin number is not expected {}".format(pin))

        dict_pin[pin] = dict()
        dict_pin[pin]["pin"] = pa_pin

        current_state = GPIO.input(pin)
        dict_pin[pin]["last_state"] = current_state
        dict_pin[pin]["change"] = False
        dict_pin[pin]["count"] = 0

    return dict_pin


def io_verif_status(p_dict_pin):
    # Activation du reset pour avoir l'affichage fonctionnel

    for pin_info in p_dict_pin.values():
        current = GPIO.input(pin_info["pin"])

        if current and pin_info["last_state"] != current:
            print("Changement detecte")
            pin_info["change"] = True
            pin_info["count"] += 1
            if pin_info["fonction"] is not None:
                pin_info["fonction"](pin_info)
        else:
            pin_info["change"] = False

        pin_info["last_state"] = current


def main():
    global looper
    global line_pixel
    global page_lines
    global current_line
    global number_line_per_page
    global font10
    
    temps_attente = 2
    looper = 0

# breakpoint
#     import sys;sys.path.append(r'/opt/eclipse/plugins/org.python.pydev_6.0.0.201709191431/pysrc')
#     import pydevd;pydevd.settrace('192.168.254.199')

    # Function available from Luma.demo demo_opts.py
#     device = get_device()
    device = get_my_device()
    create_dht()

    # Identify of embedded platform
    p_list_pin = list()
#     hostname = socket.gethostname()
    hostname = "localhost"
    if hostname in "localhost":
        p_list_pin.append(15)
        p_list_pin.append(16)
        dict_pin = io_setup(p_list_pin)
        dict_pin[15]["fonction"] = call_shutdown
        dict_pin[16]["fonction"] = None
    else:
        dict_pin = dict()

    current_line = 0

    page_lines = list()
    page_lines.append((platform_info, None))
    page_lines.append((lan_ip, None))
    page_lines.append((uptime, None))
    page_lines.append((date, None))

    page_lines.append((cpu_usage, None))
    page_lines.append((cpu_temperature, None))
    page_lines.append((mem_usage, None))
    page_lines.append((disk_usage, '/'))

    page_lines.append((get_dht, dht11))
    page_lines.append((get_dht, dht22))
    page_lines.append((get_push_button, dict_pin))

    line_pixel = list()
    hauteur_ligne = int(height / number_line_per_page) - 1

    for cpt in range(number_line_per_page):
        line_pixel.append(cpt * hauteur_ligne + 2)

    font10 = make_font("ProggyTiny.ttf", 16)

    while True:
        io_verif_status(dict_pin)
        stats_page(device)
        if looper == 0:
            time.sleep(temps_attente * 2)
            looper = 1
        else:
            time.sleep(temps_attente)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
