#!/bin/bash
# Get the new hostname from the first argument
new_hostname="$1"

# Check for root privileges
if [ "$EUID" -ne 0 ]; then
    echo "This script must be run with root privileges." >&2
    exit 1
fi

# Check if a new hostname was provided
if [ -z "$new_hostname" ]; then
    echo "New hostname is not provided." >&2
    exit 1
fi

# Set the new hostname
hostnamectl set-hostname "$new_hostname"

# Update /etc/hosts [Debian-based Systems]
sed -i "s/^127\.0\.1\.1.*/127.0.1.1 $new_hostname/g" /etc/hosts

echo "Hostname changed successfully. Rebooting in 5 seconds..."
sleep 5 && shutdown -r now
