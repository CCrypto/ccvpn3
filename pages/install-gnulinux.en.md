Title: Install on GNU/Linux

With NetworkManager
-------------------

*WARNING*: **This method requires a very recent NetworkManager.
Older versions will not work or may be insecure.**  
It has not been tested as much as the classic one and may not work on your system.
It is known to work with an up to date Arch Linux and Linux Mint 17 or later.  
**If you are not sure about it, choose the other methods**

1. Download and install OpenVPN and the NetworkManager plugin with your package manager.

    - *Debian*: `sudo apt-get install install openvpn resolvconf network-manager-openvpn network-manager-openvpn-gnome`
    - *Fedora*: `sudo yum install openvpn networkmanager-openvpn`
    - *Arch Linux*: `sudo pacman -S openvpn networkmanager-openvpn`

2. Download the .ovpn file you need in [your account](/account/config) and put
    it in `/etc/openvpn/` .  
    ie: `/etc/openvpn/ccrypto.conf`

3. [Download the ca.crt file](https://vpn.ccrypto.org/ca.crt) and put it in `/etc/openvpn/` aswell.

4. Create the NetworkManager profile:

    - Create a new OpenVPN connection. This highly depends on your environment:
        - *Mint*: Left click on the Network icon in the Control Panel> Network Connections> Add
    - Select "Import a saved VPN configuration"
    - Select your ccrypto-\*.conf config file from the /etc/openvpn/ directory
    - Select "password authentication" as the authentication type
    - Enter your CCrypto username and password.
    - Select the ca.crt you saved into /etc/openvpn as the CA Certificate and click "Save".

5. Your VPN is now ready to use with NetworkManager.



With systemd (Arch, Fedora 16 or later, Debian 8 or later, ...)
------------

1. Download and install OpenVPN with your package manager.

    - Debian: `sudo apt-get install install openvpn`
    - Fedora: `sudo yum install openvpn`
    - Arch Linux: `sudo pacman -S openvpn`

2. Download the .ovpn file you need in [your account](/account/config) and put
    it in `/etc/openvpn/` .  
    ie: `/etc/openvpn/ccrypto.conf`

3. Start the OpenVPN service:

        sudo systemctl start openvpn@ccrypto

4. *(Optional)* To make OpenVPN start at boot,
    create a text file anywhere and write your username and
    password inside, on two lines.  
    Then, add at the end of your ccrypto.conf file:

        auth-user-pass /path/to/the/file.txt

    And enable the systemd service :

        systemctl enable openvpn@ccrypto

    For additional security, you can make sure only root is be able to access this file:

        sudo chown root:root /path/to/the/file.txt
        sudo chmod 600 /path/to/the/file.txt



Without systemd (Debian before 8.0, ...)
---------------

1. Download and install OpenVPN with your package manager.

    - Debian: `sudo apt-get install install openvpn resolvconf`
    - Fedora: `sudo yum install openvpn`

2. Download the .ovpn file you need in [your account](/account/config) and put
    it in `/etc/openvpn/` .  
    ie: `/etc/openvpn/ccrypto.conf`

3. Start the OpenVPN service:

        sudo service openvpn start ccrypto

4. *(Optional)* To make OpenVPN start at boot,
    create a text file anywhere and write your username and
    password inside, on two lines.  
    Then, add at the end of your ccrypto.conf file:

        auth-user-pass /path/to/the/file.txt

    And add the configuration file name to the AUTOSTART list in `/etc/default/openvpn` (you can add it at the end):

        AUTOSTART="ccrypto"

    For additional security, you can make sure only root is be able to access this file:

        sudo chown root:root /path/to/the/file.txt
        sudo chmod 600 /path/to/the/file.txt



