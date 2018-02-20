import random
import logging
import string
import os
import inspect
from shutit_module import ShutItModule

class shutit_btrfs_dedupe(ShutItModule):


	def build(self, shutit):
		shutit.run_script('''#!/bin/bash
MODULE_NAME=shutit_btrfs_dedupe
rm -rf $( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )/vagrant_run/*
if [[ $(command -v VBoxManage) != '' ]]
then
	while true
	do
		VBoxManage list runningvms | grep ${MODULE_NAME} | awk '{print $1}' | xargs -IXXX VBoxManage controlvm 'XXX' poweroff && VBoxManage list vms | grep shutit_btrfs_dedupe | awk '{print $1}'  | xargs -IXXX VBoxManage unregistervm 'XXX' --delete
		# The xargs removes whitespace
		if [[ $(VBoxManage list vms | grep ${MODULE_NAME} | wc -l | xargs) -eq '0' ]]
		then
			break
		else
			ps -ef | grep virtualbox | grep ${MODULE_NAME} | awk '{print $2}' | xargs kill
			sleep 10
		fi
	done
fi
if [[ $(command -v virsh) ]] && [[ $(kvm-ok 2>&1 | command grep 'can be used') != '' ]]
then
	virsh list | grep ${MODULE_NAME} | awk '{print $1}' | xargs -n1 virsh destroy
fi
''')
		vagrant_image = shutit.cfg[self.module_id]['vagrant_image']
		vagrant_provider = shutit.cfg[self.module_id]['vagrant_provider']
		gui = shutit.cfg[self.module_id]['gui']
		memory = shutit.cfg[self.module_id]['memory']
		shutit.build['vagrant_run_dir'] = os.path.dirname(os.path.abspath(inspect.getsourcefile(lambda:0))) + '/vagrant_run'
		shutit.build['module_name'] = 'shutit_btrfs_dedupe_' + ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(6))
		shutit.build['this_vagrant_run_dir'] = shutit.build['vagrant_run_dir'] + '/' + shutit.build['module_name']
		shutit.send(' command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])
		shutit.send('command rm -rf ' + shutit.build['this_vagrant_run_dir'] + ' && command mkdir -p ' + shutit.build['this_vagrant_run_dir'] + ' && command cd ' + shutit.build['this_vagrant_run_dir'])
		if shutit.send_and_get_output('vagrant plugin list | grep landrush') == '':
			shutit.send('vagrant plugin install landrush')
		shutit.send('vagrant init ' + vagrant_image)
		shutit.send_file(shutit.build['this_vagrant_run_dir'] + '/Vagrantfile','''Vagrant.configure("2") do |config|
  config.landrush.enabled = true
  config.vm.provider "virtualbox" do |vb|
    vb.gui = ''' + gui + '''
    vb.memory = "''' + memory + '''"
  end

  config.vm.define "btrfsdedupe1" do |btrfsdedupe1|
    btrfsdedupe1.vm.box = ''' + '"' + vagrant_image + '"' + '''
    btrfsdedupe1.vm.hostname = "btrfsdedupe1.vagrant.test"
    config.vm.provider :virtualbox do |vb|
      vb.name = "shutit_btrfs_dedupe_1"
    end
  end
end''')
		try:
			pw = file('secret').read().strip()
		except IOError:
			pw = ''
		if pw == '':
			shutit.log("""You can get round this manual step by creating a 'secret' with your password: 'touch secret && chmod 700 secret'""",level=logging.CRITICAL)
			pw = shutit.get_env_pass()
			import time
			time.sleep(10)

		try:
			shutit.multisend('vagrant up --provider ' + shutit.cfg['shutit-library.virtualization.virtualization.virtualization']['virt_method'] + " btrfsdedupe1",{'assword for':pw,'assword:':pw},timeout=99999)
		except NameError:
			shutit.multisend('vagrant up btrfsdedupe1',{'assword for':pw,'assword:':pw},timeout=99999)
		if shutit.send_and_get_output("""vagrant status 2> /dev/null | grep -w ^btrfsdedupe1 | awk '{print $2}'""") != 'running':
			shutit.pause_point("machine: btrfsdedupe1 appears not to have come up cleanly")


		# machines is a dict of dicts containing information about each machine for you to use.
		machines = {}
		machines.update({'btrfsdedupe1':{'fqdn':'btrfsdedupe1.vagrant.test'}})
		ip = shutit.send_and_get_output('''vagrant landrush ls 2> /dev/null | grep -w ^''' + machines['btrfsdedupe1']['fqdn'] + ''' | awk '{print $2}' ''')
		machines.get('btrfsdedupe1').update({'ip':ip})



		for machine in sorted(machines.keys()):
			shutit.login(command='vagrant ssh ' + machine,check_sudo=False)
			shutit.login(command='sudo su -',password='vagrant',check_sudo=False)
			shutit.run_script(r'''#!/bin/sh
# See https://raw.githubusercontent.com/ianmiell/vagrant-swapfile/master/vagrant-swapfile.sh
fallocate -l ''' + shutit.cfg[self.module_id]['swapsize'] + r''' /swapfile
ls -lh /swapfile
chown root:root /swapfile
chmod 0600 /swapfile
ls -lh /swapfile
mkswap /swapfile
swapon /swapfile
swapon -s
grep -i --color swap /proc/meminfo
echo "
/swapfile none            swap    sw              0       0" >> /etc/fstab''')
			shutit.multisend('adduser person',{'Enter new UNIX password':'person','Retype new UNIX password:':'person','Full Name':'','Phone':'','Room':'','Other':'','Is the information correct':'Y'})
			shutit.logout()
			shutit.logout()
		shutit.login(command='vagrant ssh ' + sorted(machines.keys())[0],check_sudo=False)
		shutit.login(command='sudo su -',password='vagrant',check_sudo=False)
		shutit.install('git')
		shutit.install('make')
		shutit.install('libsqlite3x-devel')
		shutit.install('gcc')
		shutit.install('glib2-devel')
		shutit.install('libatomic')
		shutit.send('git clone https://github.com/markfasheh/duperemove')
		shutit.send('cd duperemove')
		shutit.send('make')
		shutit.send('mkdir -p /root/dupefiles/test')
		shutit.send('cd /root/dupefiles')
		shutit.send('''for i in {1..10000000}; do echo 'this is a line' >> test/1; done''')
		for f in range(2,10):
			shutit.send('''cat test/1 > test/''' + str(f))
		shutit.send('BEFORE=$(df -k /)')
		shutit.send('../duperemove/duperemove -r test -d --hashfile=/root/.dupehashes')
		shutit.send('AFTER=$(df -k /)')
		shutit.send('echo $BEFORE && echo $AFTER')
		shutit.pause_point('')
		shutit.logout()
		shutit.logout()

		shutit.log('''********************************************************************************

# Vagrantfile created in: ''' + shutit.build['vagrant_run_dir'] + '''
# Run:

cd ''' + shutit.build['vagrant_run_dir'] + ''' && vagrant status && vagrant landrush ls

# to get information about your machines' setup.

********************************************************************************''',add_final_message=True,level=logging.DEBUG)


		return True


	def get_config(self, shutit):
		shutit.get_config(self.module_id,'vagrant_image',default='bings/centos-7-btrfs')
		shutit.get_config(self.module_id,'vagrant_provider',default='virtualbox')
		shutit.get_config(self.module_id,'gui',default='false')
		shutit.get_config(self.module_id,'memory',default='2048')
		shutit.get_config(self.module_id,'swapsize',default='2G')
		return True

	def test(self, shutit):
		return True

	def finalize(self, shutit):
		return True

	def is_installed(self, shutit):
		return False

	def start(self, shutit):
		return True

	def stop(self, shutit):
		return True

def module():
	return shutit_btrfs_dedupe(
		'shutit.shutit_btrfs_dedupe.shutit_btrfs_dedupe', 937013422.0001,
		description='',
		maintainer='',
		delivery_methods=['bash'],
		depends=['shutit.tk.setup','shutit-library.virtualization.virtualization.virtualization','tk.shutit.vagrant.vagrant.vagrant']
	)
