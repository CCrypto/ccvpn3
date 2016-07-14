Title: Auto-Diagnostic


Windows
-------

*Tout d'abord, assurez vous d'avoir bien démarré OpenVPN en tant qu'administrateur
et que votre fichier de configuration est correctement placé dans
`C:\Program Files\OpenVPN\config\`.*

### netsh.exe

Si vous trouvez ces lignes dans votre historique OpenVPN:

    NETSH: C:\Windows\system32\netsh.exe interface ipv6 set address Connexion au réseau local
    ERROR: netsh command failed: returned error code 1

Cette erreur est fréquente sous windows et semble arriver à cause d'un problème
d'OpenVPN avec netsh.exe et l'IPv6.
Pour le résoudre, renommez votre connection réseau pour éviter les espaces.
Par exemple « Connexion au réseau local » en « lan ».

  - [(fr) Renommer une connexion réseau](http://windows.microsoft.com/fr-xf/windows-vista/rename-a-network-connection)


### Multiples interfaces TAP

    Error: When using --tun-ipv6, if you have more than one TAP-Windows adapter, you must also specify --dev-node
    Exiting due to fatal error

Cette erreur pourra apparaitre si vous avec de multiples interfaces TAP,
la plupart du temps à cause d'un autre logiciel utilisant TAP.
Pour le résoudre, ouvrez un interpréteur de commandes (Shift + Clic droit)
dans votre répertoire OpenVPN (là où openvpn.exe se situe) et lancez :

    openvpn.exe --show-adapters

Cela va lister vos interfaces TAP.
Puis, ouvrez votre fichier de configuration ccrypto.ovpn avec un éditeur de texte
et ajoutez ceci sur une nouvelle ligne :

    dev-node [nom]

Remplacez [nom] par le nom de votre interface TAP.


### Ça ne fonctionne toujours pas ?

Si vous ne pouvez toujours pas utiliser le VPN, n'hésitez pas à
[nous contacter](/page/help).
Joignez les logs d'OpenVPN à votre message, pour nous aider à trouver
le problème au plus vite.


GNU/Linux
---------

### J'ai un fichier ".ovpn" mais il me faut un ".conf" !
Il vous suffit de changer l'extension en renommant le fichier.

### Il m'est impossible d'utiliser votre VPN avec Network-Manager.
Tout d'abord, vérifiez que vous avez correctement créé le profil (tutoriel à venir).
Si c'est bien le cas, avant toute chose, vérifiez qu'OpenVPN lui-même est opérationnel en utilisant cette commande :
`sudo openvpn --config ccrypto.conf`
(assurez-vous de remplacer "ccrypto.conf" par le nom de votre fichier de configuration)

### Je suis connecté mais je ne peux pas ping google.com
Essayez de `ping 8.8.8.8`, si ça marche, votre ordinateur n'utilise pas le serveur DNS. Ajoutez `nameserver 10.99.0.20` au début de /etc/resolv.con **une fois la connexion établie**. Sinon, lisez la suite.

### Ça ne marche toujours pas !
En utilisant la commande `ip route`, vérifiez que vous avez, entre autre choses, les lignes suivantes :

    0.0.0.0/1 via 10.99.2.1 dev tun0
    10.99.0.0/24 via 10.99.2.1 dev tun0
    10.99.2.0/24 dev tun0  proto kernel  scope link  src 10.99.2.18
    128.0.0.0/1 via 10.99.2.1 dev tun0
    199.115.114.65 via 192.168.1.1 dev wlan0

Ces valeurs peuvent (et pour certaines, vont) changer suivant votre configuration (par exemple : wlan0 → eth0, 192.168.1.1 → 192.168.42.23, etc.)  
Si vous n'avez pas toutes ces lignes, relancez OpenVPN ou ajouter les routes à la main en utilisant `ip route add`.
Si vous ne savez pas comment faire, ce serait mieux de venir nous demander sur IRC
(nous allons avoir besoin des sorties des commandes `ip addr` et `ip route`,
veuillez utiliser https://paste.cubox.me et nous envoyer uniquement le lien vers le paste).

### J'ai tout essayé mais rien ne semble fonctionner ! T_T
Ok… Je pense que vous pouvez venir [nous demander sur IRC](/chat) (mais souvenez-vous que nous ne sommes pas des professionnels payés, nous ne sommes pas toujours présent mais nous finirons toujours par répondre si vous ne partez pas trop vite).

