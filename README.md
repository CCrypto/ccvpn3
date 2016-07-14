CCrypto VPN 
===========

CCVPN is the software we use at CCrypto to provide our VPN.
You can see it live at https://vpn.ccrypto.org/

It handles user management, support tickets, billing and is used as a backend
for VPN authentication.  
It communicates with an external service, lambdacore, that manages VPN servers
and sessions.

CCrypto's commercial support *does not* include this product and will not help you set it up.
Feel free to contact us about ccvpn, but with no guarantee.  
[PacketImpact](https://packetimpact.net/) however may provide you commercial support
and more services about ccvpn and lambdacore.


Getting Started
---------------

```bash
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

