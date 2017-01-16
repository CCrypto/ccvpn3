Title: Installation sous GNU/Linux

Avec NetworkManager
-------------------

*ATTENTION*: **Cette méthode nécéssite une version très récente de NetworkManager.
Des versions plus anciennes peuvent ne pas fonctionner ou montrer des problèmes
de sécurité.**  
Elle a été moins testée que la méthode classique et pourrait ne pas fonctionner
sur votre système.
Elle a fonctionné avec Linux Mint 17 ou plus et Arch Linux à jour.
**Dans le doute, utilisez les autres méthodes.**

1. Téléchargez et installez OpenVPN et le plugin NM avec votre gestionnaire de paquets :

    - *Debian*: `sudo apt-get install install openvpn resolvconf network-manager-openvpn network-manager-openvpn-gnome`
    - *Fedora*: `sudo yum install openvpn networkmanager-openvpn`
    - *Arch Linux*: `sudo pacman -S openvpn networkmanager-openvpn`

2. Téléchargez la configuration (.ovpn) dont vous avez besoin dans
    [votre compte](/account/config) et placez la dans `/etc/openvpn/` .  
    ie: `/etc/openvpn/ccrypto.conf`

2. [Téléchargez le fichier ca.crt](https://vpn.ccrypto.org/ca.crt) et placez le aussi dans `/etc/openvpn/` .

4. Créez le profile NetworkManager :

    - Créez une nouvelle connexion. Ça dépend beaucoup de l'environnement.
        - *Mint*: Clic gauche sur l'icone Network dans le Control Panel> Network Connections> Add
    - Choisissez "Import a saved VPN configuration" / "Importer une configuration VPN enregistrée"
    - Sélectionnez le .conf placé dans /etc/openvpn
    - Choisissez "password authentication" / "mot de passe" comme type d'authentification
    - Entrez vos identifiants CCrypto.
    - Choisissez le ca.crt dans /etc/openvpn comme "CA Certificate" / "Certificat du CA" et enregistrez.

5. Votre VPN est maintenant prêt à être utilisé avec NetworkManager.



Avec systemd (Arch, Fedora 16 ou plus, Debian 8 ou plus, ...)
------------

1. Téléchargez et installez OpenVPN avec votre gestionnaire de paquets :

    - Debian: `sudo apt-get install install openvpn`
    - Fedora: `sudo yum install openvpn`
    - Arch Linux: `sudo pacman -S openvpn`

2. Téléchargez la configuration (.ovpn) dont vous avez besoin dans
    [votre compte](/account/config) et placez la dans `/etc/openvpn/` .  
    Renommez le pour avoir un .conf.
    ie: `/etc/openvpn/ccrypto.conf`

3. Démarrez le service OpenVPN :

        sudo systemctl start openvpn@ccrypto

4. *(Facultatif)* Pour qu'OpenVPN puisse se connecter au démarrage,
    créez un fichier texte quelque part avec votre identifiant et votre
    mot de passe, sur deux lignes. Ajoutez ensuite cette ligne à la fin de
    votre fichier .conf :

        auth-user-pass /path/to/the/file.txt

    Et activez le service systemd :

        systemctl enable openvpn@ccrypto

    Pour plus de sécurité, vous pouvez restreindre l'accès à ce fichier :

        sudo chown root:root /path/to/the/file.txt
        sudo chmod 600 /path/to/the/file.txt


Sans systemd (Debian avant 8.0, ...)
---------------

1. Téléchargez et installez OpenVPN avec votre gestionnaire de paquets :

    - Debian: `sudo apt-get install install openvpn resolvconf`
    - Fedora: `sudo yum install openvpn`

2. Téléchargez la configuration (.ovpn) dont vous avez besoin dans
    [votre compte](/account/config) et placez la dans `/etc/openvpn/` .  
    Renommez le pour avoir un .conf.
    ie: `/etc/openvpn/ccrypto.conf`

3. Démarrez le service OpenVPN :

        sudo service openvpn start ccrypto

4. *(Facultatif)* Pour qu'OpenVPN puisse se connecter au démarrage,
    créez un fichier texte quelque part avec votre identifiant et votre
    mot de passe, sur deux lignes. Ajoutez ensuite cette ligne à la fin de
    votre fichier .conf :

        auth-user-pass /path/to/the/file.txt

    Ajoutez le nom du fichier de configuration à la liste AUTOSTART dans `/etc/default/openvpn` (vous pouvez l'ajouter à la fin):

        AUTOSTART="ccrypto"

    Pour plus de sécurité, vous pouvez restreindre l'accès à ce fichier :

        sudo chown root:root /path/to/the/file.txt
        sudo chmod 600 /path/to/the/file.txt



