CCrypto VPN 
===========

CCVPN is the software we use at CCrypto to provide our VPN.
You can see it live at https://vpn.ccrypto.org/

It handles user management, support tickets, billing and is used as a backend
for VPN authentication.  
It communicates with an external service, lambdacore, that manages VPN servers
and sessions.

**Disclaimer: this is a specialized solution that requires proprietary software to function.
This repo is a way for us to share our work freely as we don't believe keeping it secret will do any good;
feel free to base your own work on it but don't except it to be of an use as-is.**

CCrypto's commercial support *does not* include this and will not help you set it up.
Feel free to contact us about ccvpn, but with no guarantee.  
[PacketImpact](https://packetimpact.net/) however may provide you commercial support
and more services about ccvpn and lambdacore.


Getting Started
---------------

```bash
    pip install --user git+git://github.com/PacketImpact/lcoreapi.git
    git clone https://github.com/CCrypto/ccvpn3.git
    cd ccvpn3/

    ./manage.py createsuperuser
    ./manage.py runserver

```

CRON
----

For bitcoin payments, you will need to run a script regularly to check for
verified transaction. Another to delete old cancelled payments.
And another to send expiration emails.

    */5 * * * * /home/vpn/ccvpn3/manage.py check_btc_payments
    0 0 * * * /home/vpn/ccvpn3/manage.py expire_payments
    0 */6 * * * /home/vpn/ccvpn3/manage.py expire_notify

