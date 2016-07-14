Title:  Frequently Asked Questions

[TOC]

General
-------

### What is a VPN?
A Virtual Private Network is a private network on the Internet.  
Here, it is made of our customers and our servers acts like routers.  
That means that everything goes through our servers, and you appear anonymous
on the Internet.  
Because of the strong encryption used, attackers or your ISP cannot log,
filter, or change anything.

### Why should I pay to use it instead of tor?
Although tor may be free (and extremely good for some usage), tor is also very
slow and exit nodes can see and intercept your traffic.  
This means that tor is good if you want full anonymity, but not for
everyday web browsing, or to play an online game. For that, a VPN is perfect.

### Do you propose an affiliate program?
Yes! Share your affiliate link and earn 2 weeks for each referral.  
Invite 24 friends and you get one year of free VPN!

### Can I have a static IP address?
Yes, as each server has its own address. You only have to choose one.

### Can I have a dedicated IP address?
Not at the moment.

### Do you monitor or limit bandwidth usage?
No, every user share each VPN server's connection.  
We always try to have enough bandwidth (at least 20Mbps) available
for everyone.

### Do you censor some websites or protocols?
No and we will never do it.

### Which protocols are supported?
We only support OpenVPN for now.

### Which payment methods are supported?
We support Paypal, Stripe (credit card) and Bitcoin.  
Feel free to ask [the support](/page/help) if you need any other method.

### Is it open-source?
Yes! Our VPN is made with OpenVPN.  
Our servers' config and this website are also open-source and available on our
[GitHub project](https://github.com/CCrypto/ccvpn/).

### Are my data kept secure?
Yes, the VPN traffic is strongly encrypted and we do not keep any data on the
VPN servers.  
The website and database are on a different server, in a
different datacenter.

### Will there be more servers/countries available?
Yes, but we first need money to pay the servers.  
If you would like to have a server somewhere, know a good provider or would
like to host one, please contact us.


Account
-------

### Can I have a trial account?
Yes, we provide 7 days trial accounts.  
You just have to [sign up](/account/signup).

### Can I use my account on multiple machines?
Yes, you can! Up to 10 at the same time!  

### How can I delete my account?
Contact [the support](/page/help).


Technical
---------

### Encryption used
Authentication uses a 4096 bits RSA key. (3072 bits on oldest servers)  
The current recommended key size considered safe until 2030 is 2048 bits.  

VPN trafic encryption is performed with the Blowfish cipher using a random
128 bits key re-generated every 60 minutes, and unique to a VPN connection.

Key Exchange uses a 3072 bits Diffie-Hellman parameters.  
A 2048 bits key is considered safe until 2030.

### Do you support IPv6?
Yes, most of our servers are dual stack - they perfectly support IPv4 and IPv6
at the same time.  
Some are IPv4 only (but we're working with our providers to fix it) and will
block all IPv6 traffic to make sure your IPv6 address is not leaked.

### Do you support PPTP?
No, PPTP is not supported and will not be supported.  
PPTP is considered insecure and should never be used.



Legal
-----

### What do you log?
We only keep VPN connection IP addresses because of the law.  
We do not keep any data concerning your traffic.

### Is it really anonymous?
Depends of your definition of anonymous.  
It is anonymous, because we will not ask you for your name or verify your
identity to be able to use the VPN, and we use anonymous payment methods
like Bitcoin.  
It is anonymous, because no one can find out your identity from the other side
of the VPN.  
However, French authorities can ask us for user data (username, email,
payments, ...)

### Will you log traffic or send user data to authorities?
We won't log your traffic under any condition.  
We may give the little we know about you to authorities
only if required by the law to keep the service running.  
In this case, we'll try to contact you before doing anything if possible.


