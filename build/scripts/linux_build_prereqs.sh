if uname -a | grep -i 'Debian';
then
	apt-get install debian-builder rpm gcc git wget openssl libssl-dev libffi-dev zlib1g-dev alien -y
elif uname -a | grep -i 'Darwin';
then
	echo "must be installed manually"
elif uname -a | grep -i 'el5';
then
	yum install epel-release -y
	yum install gcc zlib zlib-devel openssl openssl-devel rpm-build wget buildsys-macros -y
elif  uname -a | grep -i 'el6';
then
	yum install epel-release -y
	yum install gcc zlib zlib-devel openssl openssl-devel rpm-build wget -y
elif  uname -a | grep -i 'el7';
then
	yum install epel-release -y
	yum install gcc zlib zlib-devel openssl openssl-devel rpm-build wget -y
else
	echo "Could not determine your OS type... you need to install the following dependencies:"
	echo ""
	echo "gcc"
	echo "zlib, zlib-devel"
	echo "openssl, openssl-devel"
	echo "libffi-devel"
	echo "rpm-build"
	echo "wget"
	echo "git"
	echo ""
	echo "If you're running a debian distro you must also install debian-builder"
	echo ""
fi