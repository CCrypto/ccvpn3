Title: Self Diagnosis


Windows
-------

*Before anything, make sure you have started OpenVPN as Administrator and that your
config files exist in `C:\Program Files\OpenVPN\config\`.*

### netsh.exe error

If you find lines like those in your OpenVPN log:

    NETSH: C:\Windows\system32\netsh.exe interface ipv6 set address Local Area Network
    ERROR: netsh command failed: returned error code 1

This error is really frequent on Windows and seem to happen because of
a OpenVPN problem with netsh.exe and IPv6.  
To fix it, rename your network connection to avoid spaces,
for example "Local Area Network" to "lan".

  - [Rename a network connection](http://windows.microsoft.com/en-au/windows-vista/rename-a-network-connection)


### Multiple TAP-Windows adapters

    Error: When using --tun-ipv6, if you have more than one TAP-Windows adapter, you must also specify --dev-node
    Exiting due to fatal error

That one can happen when you have multiple TAP-Windows adapters, most of the
time because of another software using TAP.

To fix it, open a command prompt (Shift+Right click) in your OpenVPN directory
(where openvpn.exe is), and run:

    openvpn.exe --show-adapters

This will list your TAP adapters.  
Then, open your ccrypto.ovpn configuration file with notepad and add this on a
new line:

    dev-node [name]

Replace [name] by your TAP adapter name.


### Still doesn't work

If you still cannot use the VPN, please go to the [Support page](/page/help)
and we'll do our best to help you.  
Please also send us your OpenVPN logs.


GNU/Linux
---------

### I have a ".ovpn" file but I need a ".conf"!
You just have to change the extension by renamming the file.  
.conf is more commonly used on GNU/Linux, but it's the same as the .ovpn file.


### I'm unable to use your VPN with Network-Manager.
First, check that you have properly created the profile (tutorial to come).  
If it's the case, before anything else, let's make sure that OpenVPN itself is working with the following command:  
`sudo openvpn --config ccrypto.conf`  
(make sure to replace "ccrypto.conf" by the actual name of your configuration file)

### I'm connected but cannot ping google.com
Try to `ping 8.8.8.8`: if it works then your computer doesn't use the right DNS server.
Add `nameserver 10.99.0.20` at the beginning of /etc/resolv.conf **once the connection is made**.
Else, continue reading.


### It still doesn't work!
Using the `ip route` command, make sure you have, alongside with other lines, the following:  

    0.0.0.0/1 via 10.99.2.1 dev tun0  
    10.99.0.0/24 via 10.99.2.1 dev tun0  
    10.99.2.0/24 dev tun0  proto kernel  scope link  src 10.99.2.18  
    128.0.0.0/1 via 10.99.2.1 dev tun0  
    199.115.114.65 via 192.168.1.1 dev wlan0  

These values might (and for some, will) change a little depending on your configuration (for example: wlan0 → eth0, 192.168.1.1 → 192.168.42.23, etc.).  
If you don't have every one of these lines, kill OpenVPN and fire it again or add the routes by hand using `ip route add`.
If you don't know how to do it, it would be best to come ask on IRC (we will need the output of both `ip addr` and `ip route`,
please paste them into https://paste.cubox.me and just give us the link to the paste).


### I've tried everything but nothing seems to work! T_T
Ok… I guess now you can come [ask us on IRC](/chat) (but remember to stay a while, we're not payed professionnal, we might not be around at a given time but we will answer later on).

