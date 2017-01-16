Title: Questions fréquemment posées

[TOC]

Géneral
-------

### Qu'est-ce qu'un VPN ?
Un VPN (Réseau Privé Virtuel) est un réseau virtual permettant de considérer
plusieurs ordinateurs distants comme étant sur le même réseau local.
Ici, c'est utilisé pour faire passer tout le traffic de nos clients
à travers nos serveurs.  
Cela permet de paraître anonyme sur Internet et de chiffrer vos communications
pour qu'un intermédiaire (FAI, attaquant, Wifi public, ...) ne puisse pas
vous espionner ou modifier les données et vous garanti un accès neutre et
sécurisé au réseau.

### Pourquoi payer pour un VPN au lieu d'utiliser Tor ?
Tor a les avantages d'être gratuit et parfaitement anonyme, mais les noeuds
de sortie ne sont pas toujours dignes de confiance et peuvent enregistrer ou
intercepter vos données, et c'est beaucoup plus lent qu'un VPN.  
Un VPN est donc largement plus adapté à une utilisation de tous les jours.

### Avez-vous un programme d'affiliation ?
Oui, vous pouvez partager un lien associé à votre compte, qui vous
fera gagner 2 semaines de VPN pour chaque client l'ayant suivi.  
Inviter 24 personnes vous donne donc 1 an de VPN gratuit !

### Est-ce que le P2P est autorisé ?
Sur certains serveurs. C'est indiqué dans CCVPNGUI et sur la page
de téléchargement de config.

### Puis-je avoir une adresse statique ?
Oui, chaque serveur a une adresse statique. Il suffit d'en choisir un.

### Puis-je avoir une adresse dédiée ?
Non, pas pour le moment.

### Y a-t-il une limite de bande passante ?
Non, tous les utilisateurs partagent équitablement la connexion des serveurs.  
Nous faisons en sorte qu'il y ait toujours un minimum de 20Mbps disponible
pour chaque client.

### Censurez-vous certains sites ou protocoles ?
Non, et nous ne le ferons jamais. Le VPN vous fourni un accès complêtement neutre.

### Avec quels protocoles fonctionne le VPN ?
Notre VPN est fait avec OpenVPN.

### Quelles méthodes de payement sont disponibles ?
Vous pouvez payer par Paypal ou Stripe (carte), ou encore avec des Bitcoins.  
Vous pouvez [nous contacter](/page/help) si vous avez besoin d'un autre moyen
de payement.

### Est-ce Libre ?
Oui ! Notre VPN fonctionne avec OpenVPN, et ce site ansi que les outils que nous
avons développé pour gérer le VPN sont libres et disponibles sur
[GitHub](https://github.com/CCrypto/).

### Est-ce vraiment sécurisé ?
Oui, le VPN utilise différents algorithmes de chiffrement fiables et nous ne
gardons aucune données sensible sur les serveurs du VPN.  
Les comptes clients et historiques de connexions sont uniquement gardés sur des
serveurs séparés.

### Y aura-t-il plus de serveurs ou dans d'autres pays ?
Oui, nous ajoutons des serveurs en fonction de la demande et de nos moyens.  
Si vous voudriez héberger un serveur, recommander un bon hébergeur, ou
seriez simplement intéressé par une certain pays, contactez nous.

Comptes
-------

### Puis-je avoir un compte de test gratuit ?
Oui, pendant 7 jours.
Vous n'avez qu'à [créer un compte](/account/signup) et [nous contacter](/page/help).

### Puis-je utiliser mon compte sur plusieurs machines ?
Oui, vous pouvez utiliser votre compte avec un maximum de 10 connexions
simultannées.  
Vous devrez cependant créer un profile pour chacune des
connexions.

### Comment supprimer mon compte ?
[Contactez nous](/page/help).


Technique
---------

### Chiffrement
L'authentification utilise une clé RSA de 4096 bits. (3072 sur les serveurs plus anciens)  
Les clés de 2048 bits ou plus sont considérées sûres jusqu'à 2030.

Le traffic est chiffré avec Blowfish, en utilisant une clé aléatoire de 128 bits
re-générée toutes les 60 minutes et unique pour chaque connexion au VPN.

L'échange de clés (Diffie-Hellman) utilise un groupe de 3072 bits.  
2048 bits ou plus est considéré suffisant jusqu'en 2030.

### Est-ce que l'IPv6 est supporté ?
Oui, la plupart des serveurs fonctionnent en IPv4 et IPv6 (dual stack).
Quelques-uns ne fonctionnent qu'en IPv4 et bloquent entièrement l'IPv6 pour
éviter de laisser passer votre addresse IPv6.

### Est-ce que le PPTP est supporté ?
Non, le PPTP n'est plus considéré sécurisé et ne doit plus être utilisé.


Légal
-----

### Quelles informations gardez-vous ?
Nous conservons uniquement l'adresses IP et l'heure de chaque connexion,
comme exigé par la loi. Nous n'analysons et n'enregistrons rien concernant
les données passant par le VPN.

### Est-ce réellement anonyme ?
Ça dépend de votre définition d'anonyme.  
C'est anonyme, parce que nous ne vous demandons pas votre nom et ne vérifions pas
votre identité pour vous laisser profiter du VPN, et que nous autorisons des
méthodes de payement anonymes, comme le Bitcoin.  
C'est anonyme, parce que l'on ne peut pas directement associer une connexion à travers le VPN
à votre identité.  
Mais, les autorités françaises peuvent nous demander votre historique de
connexions et les données associées à votre compte. (nom, adresse e-mail, ...)
C'est donc traçable dans les cas extrêmes et ne vous permet pas d'échapper à la loi.

### Donnez vous des informations aux autorités ?
Nous ne vous espionnerons jamais.  
Le peu de données enregistrées peuvent être transmises aux autorités si requis
par la loi.
Dans ce cas, nous essaierons de contacter les clients concernés avant tout,
si possible.


