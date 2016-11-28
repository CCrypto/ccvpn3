Title: NO-P2P Servers

See also: our [Privacy Policy](/page/privacy).

Because of its high number of simultaneous connections and high bandwidth usage,
and the amount of legal issues sometimes linked,
we have to restrict the use of the BitTorrent protocol on specific servers.  
Our servers marked as **NO-P2P** are more expensive to maintain
and and cost more in bandwidth than in other countries,
so we ask our clients to not use the BitTorrent protocol
on these servers.


### Enforcement

As monitoring all connections would be a big privacy violation towards our clients and cost much more,
we chose to only intercept connection made to a specific set of known BitTorrent trackers
as listed at the end of this page.  
Rules are then applied to the intercepted content and if a match if found,
the client is disconnected and banned from the server.  
Intercepted data is never logged or stored, only the username and the date of detection are stored.

If you think this has happened by mistake, please contact our support.

Trackers targeted:

    94.23.183.33
    62.138.0.158
    163.172.157.35
    151.80.120.112/30
    109.121.134.121
    87.98.148.74
    192.99.81.115

The exact rules used are still under development and will be published once stable.

