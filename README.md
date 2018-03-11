# OrangePiZero_OLED_Dht_display
Display information on OLED display connected to Orange Pi Zero


# Installation
```shell
git clone https://github.com/jingl3s/OrangePiZero_OLED_Dht_display.git

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
Description=Sound Interactions
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
  
  
## Meta

Jingl3s

Distribué sous la licence BSD. Voir ``LICENSE`` pour plus d'information.


## Contribution

Fork du projet
  