#!/usr/bin/env sh
# Performs basic bootstrapping required to connect to a host via Ansible:
# - Installs, enables and starts sshd
# - Installs python3 (python2 on CentOS 7)

# Number of times to attempt execution of a command before failing.
MAX_TRIES=3
TRY_WAIT=5

try () {
    # Try a command a certain number of times
    # Parameters: $1 - command
    #             $2 - number of tries
    #             $3 - time to wait between tries
    COUNT=0
    while [ $COUNT -lt $MAX_TRIES ]; do
        if $1; then
            return
        else
            COUNT=$((COUNT+1))
            sleep "$3"
        fi
    done
    echo "Failed to execute command $1"
    exit 1
}

enable_systemd () {
    systemctl enable --now "$1"
}

init_pacman () {
    # The default arch image comes with pacman unconfigured. For the purposes of
    # bootstrapping, we first enable a temporary server, before then initializing
    # pacmans keyring and installing rankmirrors to generate a mirrorlist.
    # shellcheck disable=SC2016
    sed -i 's!#Server = http://mirror.rackspace.com/archlinux/$repo/os/$arch!Server = http://mirror.rackspace.com/archlinux/$repo/os/$arch!' /etc/pacman.d/mirrorlist
    pacman-key --init
    pacman-key --populate archlinux
    # Running -Sy is not reccomended, so we need to upgrade all packages instead. Fingers crossed...
    try "pacman -Syu pacman-contrib --noconfirm" "$MAX_TRIES" "$TRY_WAIT"
    # Run mirrorlist and replace the original mirrorlist with the generated one
    cp /etc/pacman.d/mirrorlist /etc/pacman.d/mirrorlist.bak
    sed -i 's/^#Server/Server/' /etc/pacman.d/mirrorlist.bak
    rankmirrors -n 10 /etc/pacman.d/mirrorlist.bak > /etc/pacman.d/mirrorlist
    rm /etc/pacman.d/mirrorlist.bak
}

# Debian
if command -v apt; then
    try "apt update" "$MAX_TRIES" "$TRY_WAIT"
    try "apt install -y openssh-server python3" "$MAX_TRIES" "$TRY_WAIT"
    enable_systemd ssh
# Fedora and EL >=8
# We check dnf first, as CentOS8 comes with both dnf and yum.
# This way, we always install python3 on hosts that support it
elif command -v dnf; then
    try "dnf install -y openssh-server python3" "$MAX_TRIES" "$TRY_WAIT"
    enable_systemd sshd
# EL <=7
elif command -v yum; then
    try "yum install -y openssh-server python" "$MAX_TRIES" "$TRY_WAIT"
    enable_systemd sshd
# Archlinux
elif command -v pacman; then
    init_pacman
    try "pacman -S openssh python --noconfirm" "$MAX_TRIES" "$TRY_WAIT"
    enable_systemd sshd
# Suse
elif command -v zypper; then
    try "zypper install -y openssh python3" "$MAX_TRIES" "$TRY_WAIT"
    enable_systemd sshd
# Alpine
elif command -v apk; then
    try "apk update" "$MAX_TRIES" "$TRY_WAIT"
    try "apk add openssh-server openssh-client python3" "$MAX_TRIES" "$TRY_WAIT"
    rc-update add sshd
    rc-service sshd start
fi
