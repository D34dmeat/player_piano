McGuire Piano Player
====================

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


Building a Raspberry Pi image
-----------------------------

This is a set of instructions for how the raspberry pi image is built
from scratch

 * Download the raspbian image from
   http://www.raspberrypi.org/downloads/

 * Write image to sdcard

 * Boot pi, and follow config to set hostname and resize image

 * `apt-get update && apt-get install wpa_supplicant isc-dhcp-server`

 * Configure dhcp server, edit /etc/dhcp/dhcpd.conf, put this at the bottom:

    subnet 172.19.22.0 netmask 255.255.255.0 {
      range 172.19.22.2 172.19.22.20;
      option routers 172.19.22.1;
    }

 * Configure networking by editing /etc/network/interfaces:

    auto lo eth0 wlan0

    iface lo inet loopback
    
    iface eth0 inet static
    address 172.19.22.1
    netmask 255.255.255.0
    
    allow-hotplug wlan0
    iface wlan0 inet dhcp
        wpa-ssid "Your SSID"
        wpa-psk "Your Passphrase"

  * Reboot, plug an ethernet cable directly between the pi and a
    computer. This other computer should receive an IP address from
    the pi's DHCP server in the form of 172.19.22.X.

  * SSH into 172.19.22.1 - username:pi password:raspberry

  * This is the mode in which you can debug the pi, regardless of the
    Wifi setting.

  * Get the wifi IP: ifconfig wlan0

  * You should also be able to ssh into the pi from the wifi network.

  

