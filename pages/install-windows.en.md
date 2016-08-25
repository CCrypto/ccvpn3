Title: Install on Windows

With CCVPNGUI
-------------

CCVPNGUI is made for CCrypto VPN and contains everything it needs. Just download and run:  
<https://dl.ccrypto.org/ccvpngui/releases/ccvpngui-1.0.0-1.exe>
[(sig)](https://dl.ccrypto.org/ccvpngui/releases/ccvpngui-1.0.0-1.exe.asc)


It's open-source and based on [LVPNGUI](https://github.com/PacketImpact/lvpngui/).


With OpenVPN GUI
----------------

1. Download OpenVPN for Windows on
    [OpenVPN.net](http://openvpn.net/index.php/open-source/downloads.html)  
    (you need the Windows Installer) and install OpenVPN.

2. In [your account](/account/config), download the config file (.ovpn) you want to use,
    and copy it to `C:\Program Files\OpenVPN\config\`.
    If you downloaded multiple config files as an archive, extract it in that folder.

3. Start `OpenVPN GUI` *as Administrator*. You can find it on your desktop or in the start menu.  
    Once it's started, you should see it in the system tray. Right click it and select Connect.

4. It should now open a OpenVPN log window showing its progress.  
    If an error occured, please see the [self-diagnosis](/page/self-diagnosis) page.  
    If it doesn't solve your problem or you have another question, contact
    our [support](/tickets/)

5. If everything worked, the OpenVPN icon should turn green.  
   Your are now connected and can enjoy your secure connection.


Save username and password
--------------------------

You can make OpenVPN remember your username and password, so you don't need
to type them everytime you want to use the VPN.  

This can be done by creating a text file named "ccrypto_creds.txt" containing
your username on the first line and your password on the second
(see example below).  
Move it to `C:\Program Files\OpenVPN\config\`, next to the .ovpn file you
copied there before.  

It should look like this:

    JackSparrow
    s0mep4ssw0rd

Then, open the .ovpn file with a text editor (Notepad, Notepad++, ...)
and add this line at the end of the file:

    auth-user-pass ccrypto_creds.txt

Now, if you restart OpenVPN, it should not ask you for your password anymore.


