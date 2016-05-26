if uname -a | grep -i 'Debian';
then
    PACKAGE='deb'
elif uname -a | grep -i 'Ubuntu';
then
    PACKAGE='deb'
elif uname -a | grep -i 'Darwin';
then
    PACKAGE='dmg'
else
    PACKAGE='rpm'
fi

if arch | grep '^i[0-9]86$';
then
    ARCH='x86'
else
    ARCH='x86_64'
fi

(
    if [ $PACKAGE == 'dmg' ]; then
        cd /Users/techteam/Development/ncpa/build
        sudo make build_${PACKAGE}
        sudo /bin/cp *.${PACKAGE} "/Volumes/teamshare/ncpastaging/posix/${PACKAGE}/${ARCH}/"
        sudo make clean
    else
        cd /root/Development/ncpa/build
        make build_${PACKAGE}
        /bin/cp *.${PACKAGE} "/mnt/smbshare/ncpastaging/posix/${PACKAGE}/${ARCH}/"
        make clean
    fi
)

echo "Build successful! Saved in NCPA staging area."