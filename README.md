# monnet-ansible

Monnet to ansible gateway 

## Install

mkdir /opt/monnet-ansible

cd /opt/monnet-ansible

git clone https://github.com/diegargon/monnet-ansible.git

cp files/monnet-ansible.service  /etc/systemd/system

systemctl enable  monnet-ansible.service

systemctl start  monnet-ansible.service
