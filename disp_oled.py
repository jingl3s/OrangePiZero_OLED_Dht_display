'''
@author: jingl3s

Copyright 2014 jingl3s
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
import subprocess
from collections import OrderedDict

try:
    import orange_pi_wifi
except:
    pass

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
col1 = 3

global number_line_per_page
number_line_per_page = 4

#Screen rotation
g_rotate_val = 0

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


def get_opi_wifi():
    global count_wifi
    global opi_next_time
    if opi_next_time < time.time(): 
        opi_next_time = time.time() + 15*60
        count_wifi += True == orange_pi_wifi.orange_pi_network()
    return "Wifi actif coubt {}".format(count_wifi)

def cpu_usage():
    # load average, uptime
    av1, av2, av3 = os.getloadavg()
    return "LOAD: %.1f %.1f %.1f" \
        % (av1, av2, av3)


def cpu_temperature():
    tempC = ((int(open('/sys/class/thermal/thermal_zone0/temp').read()) / 1000))
#     return "CPU TEMP: %sc" % (str(tempC))
    return "CPU TEMP: {0:0.1f} C".format(tempC)

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
    sensor = dht_sensor.get_sensor()
    return 'DHT{}: {:5.1f}°  {:4.1f}%'.format(sensor,
        temp, hum)


def stats_page():
    '''
    Format the text to display and return the list of string to display
    '''
    global page_lines
    global current_line

    list_text = list()
    # First start display a dedicated message
    if looper == 0:
        list_text.append('WELCOME TO OPi ZERO')
        list_text.append('')
        list_text.append('Starting up...')
    elif looper > 0:
        # Format the displayed information per pages by calling each function returning text to display
        for _ in range(number_line_per_page):
            
            text_to_add = ''
            if current_line < len(page_lines):
                if not page_lines[current_line][0] is None:
                    if page_lines[current_line][1] is not None:
                        text_to_add = page_lines[current_line][0](
                            page_lines[current_line][1])
                    else:
                        text_to_add = page_lines[current_line][0]()
            list_text.append(text_to_add)
            current_line = (current_line + 1) % len(page_lines)
    return list_text


def disp_text(device, p_list_text):
    '''
    Display the content of list to the device 
    :param device: Luma device
    :param p_list_text: List of text with a string per line to display
    '''
    with canvas(device) as draw:
#         draw.rectangle((0, 0, 127, height - 1), outline="white", fill="black")

        for line, text in enumerate(p_list_text):
            draw.text((col1, line_pixel[line]), text,
                      font=font10, fill=255)



def get_oled_device(rotate_val):
    '''
    Intialize my dedicated reset of device to start properly on I2C
    
    :param rotate_val: The rotate vale expected by the device 0,1,2,3
    :return device: Luma device
    '''
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

    # rotate=2 180°
    device = ssd1306(serial, rotate=rotate_val)

    # Activer la ligne suivante permet de bloquer l'affichage sur le dernier text lors de l'arret du programme
    #     device.cleanup = do_nothing
    return device


def get_my_device(rotate=False):
    '''
    Try getting physical device otherwize return the emulated one
    :param rotate:True to enable rotation screen since last call of this function False stay as default
    :return device as luma
    '''
    global g_rotate_val
    if rotate:
        if g_rotate_val == 0:
            g_rotate_val = 2
        else:
            g_rotate_val = 0
    else:
        g_rotate_val = 0
    
    try:
        dev = get_oled_device(g_rotate_val)
    except:
        dev = get_emul_device(g_rotate_val)
    return dev


def get_emul_device(rotate_val):
    '''
    Create a luma emulator device
    :param rotate_val: The rotate vale expected by the device 0,1,2,3
    :return device as luma
    '''
    from luma.emulator.device import pygame  # @UnresolvedImport
    device = pygame(mode="1", rotate=rotate_val)
#     from luma.emulator.device import capture
#     device = capture(mode="1", rotate=rotate_val)
    
    # Activer la ligne suivante permet de bloquer l'affichage sur le dernier text lors de l'arret du programme
#     device.cleanup = do_nothing
    return device


def get_push_button(p_dict_pin):
    disp = list()
    for pin, pin_info in p_dict_pin.items():
        disp.append("{} {}".format(pin, pin_info["last_state"]))
    return "Push But: " + ",".join(disp)


class DHTFake(object):
    def __init__(self, sensor):
        self._sensor = sensor

    def get_valeurs(self):
        self.valeurs = (randint(-200, 300) / 10.0, randint(100, 950) / 10.0)
        return self.valeurs
    
    def get_sensor(self):
        return self._sensor


def create_dht():
    global dht11
    global dht22
    try:
        from dht.dht_interface import DHTInterface
        dht11 = DHTInterface(0, 11)
        dht22 = DHTInterface(1, 22)
        print("DHT reel")
    except:
        dht11 = DHTFake(11)
        dht22 = DHTFake(22)
        print("DHT fake")

def menu(lmenu, device=None, sous_menu=False, gpio_pins=None):
    '''
    Display a menu to the user and add a dedicated character in order to identify the current activated menu
    
    The device is used as parameter to display the menu content
    
    
    :param lmenu: List of menu to display
    :param device: Luma device for display
    :param sous_menu: If True, the sub menu to confirm is not displayed otherwise always disabled
    :param gpio_pins: dictionary of GPIO pins to use 
    '''

    # Copy the menu as modified to display the prompt
    smenu = lmenu[:]
    sel = 0
    eval_ret = None
    
    # Wait at least a selection in menu is confirmed
    while sel < len(lmenu) and eval_ret is None:
        
        # Add the user prompt to identify menu position
        smenu[sel] = '>' + smenu[sel]
        
        disp_text(device, smenu)
        
        # attente de saisi utilisateur car menu demande
        val_lu = action_utilisateur(gpio_pins)
        
        # Goes next position in the menu
        if val_lu == True:
            sel = (sel + 1) % len(smenu)
        # Activate selection of menu
        elif val_lu == False:
            
#             print('Menu selectionne : {}'.format(smenu[sel][1:]))
            
            # Ajout d'une demamde de confirmation pour valider la selection'
            if not sous_menu:
                confirm = list()
                confirm.append('annuler')
                confirm.append('confirmer')

                eval_ret1 = menu(confirm, device, True, gpio_pins=gpio_pins)
            
                # modification ret seulement si confirme
                if eval_ret1 == 1:
                    eval_ret = sel
            else:
                eval_ret = sel
        # Restore default menu as copy
        smenu = lmenu[:]
    return eval_ret


def action_push_button(pin_info, pins_complete):
    '''
    Function called when the GPIO change the current state in order to process something
    
    It will display a menu to user as the gpio button are use to go across the menu and validate with only two buttons
    :param pin_info: The current dictionary information of key pressed
    :param pins_complete: All the dictionary of gpio configured
    '''
    global device
    if pin_info["count"] == 2:

        dmenu = OrderedDict()
        dmenu['Eteindre'] = ['sudo', 'halt']
        dmenu['Test'] = 'print(\'test\')'
        dmenu['Tourner'] = ''
        dmenu['Quitter menu'] = '0'
        
        lmenu = list(dmenu.keys())
        
        pin_info["count"] = 0
        pin_info["change"] = False

        index = menu(lmenu, device, gpio_pins=pins_complete)
        if index == lmenu.index('Eteindre'):
            # Shutdown screen before
            device.cleanup()
            #Execution commande
            print("Command to execute: {}".format(dmenu[lmenu[index]]))
            subprocess.call(dmenu[lmenu[index]])
        if index == lmenu.index('Tourner'):
            device = get_my_device(rotate=True)
        if index == lmenu.index('Test'):
            # For information other idea to evaluate python command
            eval_ret = eval(dmenu[lmenu[index]])  # @UnusedVariable
            
        pin_info["change"] = False
        pin_info["count"] = 0


def action_utilisateur(gpio_pin):
    '''
    Wait until a gpio changes in order to return the status change
    Infinite loop as user action request

    :param gpio_pin:
    :return: True if first gpio key is pressed and False otherwise
    '''
    retour = None
    cle_inter = list(gpio_pin.keys())

    while retour is None:
        io_verif_status(gpio_pin, desative_fonction=True)
        for index, gpio_key in enumerate(cle_inter):
            if gpio_pin[gpio_key]["change"]:
                retour = not (index)
        time.sleep(0.05)
    return retour


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


def io_verif_status(p_dict_pin, desative_fonction=False):
    '''
    Detect the button press and call the associated function if any
    :param p_dict_pin:
    :param desative_fonction:
    '''
    # Activation du reset pour avoir l'affichage fonctionnel
    action_released = False
    for pin_info in p_dict_pin.values():
        last_state = pin_info["last_state"]
        current = GPIO.input(pin_info["pin"])

        pin_info["last_state"] = current
        
        if not current and last_state != current:
            pin_info["change"] = True
            pin_info["count"] += 1
            if not desative_fonction:
                if pin_info["fonction"] is not None:
                    pin_info["fonction"](pin_info, p_dict_pin)
                    action_released = True
        else:
            pin_info["change"] = False
    
    return action_released



def main():
    global looper
    global line_pixel
    global page_lines
    global current_line
    global number_line_per_page
    global font10
    global dht11
    global dht22
    global device

    WAIT_TIME = 30
    WAIT_TIME = 1
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
        dict_pin[15]["fonction"] = action_push_button
        dict_pin[16]["fonction"] = None
    else:
        dict_pin = dict()

    current_line = 0

    page_lines = list()
    page_lines.append((lan_ip, None))
    page_lines.append((uptime, None))
    page_lines.append((None, None))
    page_lines.append((None, None))

#     page_lines.append((platform_info, None))
#     page_lines.append((date, None))
#     page_lines.append((cpu_usage, None))
#     page_lines.append((mem_usage, None))
#     page_lines.append((disk_usage, '/'))

    page_lines.append((cpu_temperature, None))
    page_lines.append((get_dht, dht11))
    page_lines.append((get_dht, dht22))
#    page_lines.append((get_push_button, dict_pin))
    global count_wifi
    global opi_next_time
    count_wifi = 0
    opi_next_time=0
    page_lines.append((get_opi_wifi, None))

    line_pixel = list()
    hauteur_ligne = int(height / number_line_per_page) - 1

    for cpt in range(number_line_per_page):
        line_pixel.append(cpt * hauteur_ligne + 2)

#     font10 = make_font("ProggyTiny.ttf", 16)
    font10 = make_font("enhanced_dot_digital-7.ttf", 10)
    
    

    next_time = time.time()

    while True:
        action_performed = io_verif_status(dict_pin)
        
        # Hide screen to save power
        if not dict_pin[16]["last_state"]:
            device.hide()
        else:
            # Display screen and update content
            device.show()
        
        # Mise a jour du contenu de l'affichage seulement si le bouton le permet
        if next_time < time.time() or action_performed: 
            if dict_pin[16]["last_state"]:
                list_text = stats_page()
                disp_text(device, list_text)
                # Premier affichage dure plus longtemps
                if looper == 0:
                    next_time = time.time() + WAIT_TIME * 2
                    looper = 1
                else:
                    next_time = time.time() + WAIT_TIME
        # Attendre la boucle      
        time.sleep(0.1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
