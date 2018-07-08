.emula# OrangePiZero_OLED_Dht_display
Display information on OLED display connected to Orange Pi Zero


# Installation
Recurse submodule is used to get the git dependencies as per dht directory

```shell
git clone https://github.com/jingl3s/OrangePiZero_OLED_Dht_display.git --recurse-submodules

```

Or if you have already cloned:

```shell
git submodule update --init --recursive
```

* Setup the informations needed
  * Edit the disp_oled.py
    * width, height, and number_line_per_page of oled screen
    * get_oled_device() if reset pin
    * create_dht() for your dht sensor
    * dict_pin in case of push button connected
    * page_lines settings of information displayed
    * WAIT_TIME time waiting between each page displayed
    
* Service lancé au démarrage<br> 

```shell
sudo nano /lib/systemd/system/opi_oled_dht.service
```

```ini
[Unit]
Description=Orange Pi Display server
After=multi-user.target
[Service]
Type=idle
ExecStart=/usr/bin/python3 /home/__TBD__/OrangePiZero_OLED_Dht_display/disp_oled.py
[Install]
WantedBy=multi-user.target
``` 

__TBD__ is defined path on your installation

```shell
sudo chmod 644 /lib/systemd/system/opi_oled_dht.service
sudo systemctl daemon-reload
sudo systemctl enable opi_oled_dht.service
```



# Links
- GPIO
  - RaspberryPi https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/
  - OrangePi (not used) https://github.com/rm-hull/OPi.GPIO
  
- GIT submodule
  - https://stackoverflow.com/questions/7597748/linking-a-single-file-from-another-git-repository
  git submodule add <URL> <local_link_name>
  
- ETC configuration 
  - https://github.com/laneboysrc/rc-headless-transmitter/blob/master/configurator/orangepizero/INSTALL.md
  
# Licence

This code is free software; you can redistribute it and/or modify it
under the terms of the BSD license (see the file
COPYING.txt included with the distribution).
  
## Meta

Jingl3s

Distribué sous la licence BSD. Voir ``LICENSE`` pour plus d'information.


## Contribution

Fork du projet
  