Systemd setup
--------------

See https://wiki.archlinux.org/index.php/Systemd/User#Automatic_start-up_of_systemd_user_instances


Make sure user systemd is operational:

    systemctl --user status

Edit the piano.service file and fix the absolute paths to match your directory structure.

Link the systemd service file:

    mkdir -p ~/.config/systemd/user
    ln -s conf/systemd/piano.service ~/config/systemd/user/

Enable the service:

    systemctl --user enable piano

As root, allow the user to start processes on system boot:

    loginctl enable-linger YOURUSER

Reboot, and the service should automatically start