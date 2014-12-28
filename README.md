McGuire Piano Player
====================

Building a Raspberry Pi image
-----------------------------

This is a set of instructions for how the raspberry pi image is built
from scratch:

 * Download and install arch linux arm : http://archlinuxarm.org/platforms/armv6/raspberry-pi

 * Plug ethernet into pi and power on. For debugging purposes, you may
   wish to use this on a wifi connected laptop that also has an
   ethernet port:
   https://gist.github.com/EnigmaCurry/ac5946fa11a761b7b93f

   This will allow the laptop to connect to the pi share internet
   access to the pi.

 * Test ssh works:  ssh root@172.19.22.101 (assuming IP address used
   in the script above, password is 'root')
 
 * Set the locale to en_US.UTF-8. Uncomment en_US.UTF-8 from
   /etc/locale.gen and run 'locale-gen'.

 * run: localectl set-locale LANG=en_US.UTF-8

 * Set the hostname:

    hostnamectl set-hostname piano

 * The wired connection will work automatically, but you will need to
   setup the wifi connection on a per-installation basis.

   pacman -S netctl
   systemctl enable netctl
   systemctl start netctl

 * Create a new file /etc/netctl/wifi, change ESSID and Key:

      Description='A simple WPA encrypted wireless connection'
      Interface=wlan0
      Connection=wireless
      Security=wpa
      IP=dhcp
      ESSID='YOUR ESSID HERE'

      # Prepend hexadecimal keys with \"
      # If your key starts with ", write it as '""<key>"'
      # See also: the section on special quoting rules in netctl.profile(5)
      Key='YOUR WPA KEY HERE'
      # Uncomment this if your ssid is hidden
      #Hidden=yes

         
    systemctl start netctl@wifi.service
    systemctl enable netctl@wifi.service

   Wifi should have started, note the IP for wlan0 with ifconfig.

 * Unplug ethernet, reboot, and ensure the wifi came up automatically.
 TODO: This isn't actually happening, 'netctl wifi start' works after
 bootup, but not during? 

 * Update the OS : `pacman -Syu`

 * Create app user:

   useradd piano
   passwd piano              # pw: piano
   mkdir -p /home/piano
   chown piano:piano /home/piano
   gpasswd -a piano audio


Setup app on raspberry pi
-------------------------

 * Install system dependencies (as root):
  
    pacman -S git python python-virtualenv base-devel alsa-lib alsa-utils

 * Download and install midish (as root):

    curl http://www.midish.org/midish-1.0.6.tar.gz -o midish-1.0.6.tar.gz
    tar xfv midish-1.0.6.tar.gz
    cd midish-1.0.6
    ./configure
    make
    make install

 * Connect midi device, and note which port it's on:

    aconnect -l

   (should be client 20: 'USB-2.0-MIDI')

 * Create a new file: /etc/midishrc (replace 20 with the correct port number):

    dnew 0 "20:0" wo
    dnew 1 "20:1" ro

 * Install app (as app user: piano)

    cd ~
    git clone git@bitbucket.org:enigmacurry/player_piano.git
    virtualenv --python=python3.4 player_piano/env
    source player_piano/env/bin/activate
    pip install -e player_piano

 * Start Pyro4 nameserver:

    pyro4-ns &

 * TODO: daemonize midi service. For now, start midi service manually:

     python midi.py

 * TODO: daemonize flask service


Midi links
------------------

Creative Commons:
 * http://www.piano-midi.de/

Unknown license:
 * http://www.pianola.co.nz/rollscans/zip_download.html
 * http://www.trachtman.org/ragtime/ - needs commercial license.
 * http://bushgrafts.com/jazz/midi.htm - these are real nice.


Debugging midi output
---------------------

USB midi device can be seen by:

    aconnect -o
    client 20: 'USB2.0-MIDI' [type=kernel]
        0 'USB2.0-MIDI MIDI 1'
        1 'USB2.0-MIDI MIDI 2'

20:0 is the output, 20:1 is the input.

Play a midi file to the midi output port:

    aplaymidi -p 20:0 test.mid
