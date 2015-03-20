Packet à Installer pour faire marcher ZT 

mkdir "ZT_Folder" (exemple "ZT") 

passer en superuser

apt-get update
apt-get install git
apt-get install python3.2
apt-get install rabbitmq-server
apt-get install redis-server
apt-get install curl
curl -sL https://deb.nodesource.com/setup | bash
apt-get install nodejs
sudo apt-get install libqt4-dev

revenir en user normal et aller dans ZT_Folder

git clone https://github.com/b0hoja/Zatfits.git

Aller sur le repertoire de ZatFits

git checkout inscr

envs/mhenv/bin/python envs/mhenv/bin/pip install python-qt 

verifier le #bang dans Zatfits/servers/makehuman/makehuman.py


aller dans Zatfits/zatfits/

modifier le  path de Zatfits dans le ./startup.sh 
(nano startup.sh)

/sbin/ifconfig pour récupérer l'IP 

lancer le serveur : ./startup.sh 

(CTRL + C pour quitter, et relancer une seconde fois lors du premier lancement)

Modifier le path du serveur MH dans l'interface Admin du site (celui ci-dessus)

dans un navigateur web : http://adressIP:5999

login : zatfits@zatfits.com	
pwd : zatfits@zatfits.com

aller dans http://192.168.235.143:5999/admin/servermanager/servertype/
changer le path des scripts : /home/zatfits/RepZatfits/Zatfits/servers/makehuman/makehuman.py

aller dans http://192.168.235.143:5999/admin/servermanager/server/ 
selectionner 2 serveurs et lancez les

vous pouvez tester le model making et le fitting

Lancement d'un docker ZTControler
sudo docker run -ti -v /home/zatfits/ZT2/Zatfits/zatfits/user_models/:/home/ZT/Zatfits/zatfits/user_models -p 8999:8999 -name zt8999 zatfits sh /home/ZT/start.sh 8999


kill server : docker rm -f zt8999 
