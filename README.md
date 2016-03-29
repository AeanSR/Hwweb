##How to deploy and run the project !
==============================
###### Author: Andrew Lee
###### Contact: [lichundian@gmail.com](mailto:lichundian@gmail.com)
==========================
## Requirements
1. [mongodb](http://www.mongodb.org/)
 - download and install the mongdb
 - write a conf file, the content is below:
>\#mongodb.conf:
port=27017
logpath=/var/log/mongodb.log
logappend=true
dbpath=/var/data/mongodb
fork=true

 - start the mongo server
> $mkdir -p /var/data/mongodb
$sudo mongod -f mongod.conf

 - add the mongod service into the system
> $sudo vim /etc/rc.d/rc.local
add $MONGO_HOME/bin/mongod -f $MONGO_HOME/mongod.conf

 - when your computer crashes(MongoDB crashes, e.g. via kill), you cann't start the mongod service normally. Then you should repair it.
> $sudo mongod --repair -f mongod.conf

2. pip (pip is python package manager, you should install python 2.7 firstly)
 - install pip through the command below
> curl -O [https://bootstrap.pypa.io/get-pip.py](https://bootstrap.pypa.io/get-pip.py)
python get-pip.py
3. tornado, motor
 - install the 3-party python requirements
> $pip install 'tornado==4.0.1'
$pip install 'motor==0.3.2'
$pip install 'sockjs-tornado==1.0.2'

## Hwweb(Homework web system) deployment
1. import the data to mongodb
> $cd data_script
$./dataImport
2. modify the port running on the localhost(optional)
 - the default port is **8888**, you can change it in the **index.py**
3. run the web system
> $ screen python index.py
4. use **[ngrok](https://ngrok.com/)** to publish your app on the public network
 - Download ngrok and install it.
 - To use a solid domain, you need sign up the ngrok.com and get the right to bind your domain with your localhost port.
 - You can register a free domain, such as tk domain.
 - Assuming you have gotten a domain (eg: http://www.ucas-2014.tk) and got a token(eg:iuhnCIczc1NcieEXCs3Q) belonging to you when signing up on the https://ngrok.com . You run your app on localhost through 8888 port. You can bind your local app with the public domain through the commands below:
> $ngrok -authtoken iuhnCIczc1NcieEXCs3Q
$screen ngrok -hostname ucas-2014.tk 8888
