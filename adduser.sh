#!/bin/bash
###############################
#add ubuntu user for developer#
###############################

for n in $@
do
    LOGIN=$(echo $n|awk -F "." '{print $1}')
    echo "cmd =useradd -m -s /bin/bash $LOGIN -c $n="
    useradd -m -s /bin/bash $LOGIN -c $n

    echo "cmd =echo $LOGIN:$LOGIN | chpasswd="
    echo $LOGIN:$LOGIN | chpasswd

    echo "cmd =echo -ne $LOGIN\n$LOGIN\n | smbpasswd -a -s $LOGIN="
    echo -ne "$LOGIN\n$LOGIN\n" | smbpasswd -a -s $LOGIN
done
