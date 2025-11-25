#!/bin/bash
# Script to install Ansible on Jenkins container
# Run this script on the Jenkins machine (inside the container or on the host)

echo "=========================================="
echo "Installing Ansible on Jenkins Machine"
echo "=========================================="

# Check if running as root or with sudo
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root or with sudo"
    exit 1
fi

# Update package lists
echo "Updating package lists..."
apt-get update

# Install required dependencies
echo "Installing dependencies..."
apt-get install -y python3 python3-pip python3-dev libffi-dev libssl-dev

# Install Ansible using pip
echo "Installing Ansible..."
pip3 install ansible

# Verify installation
echo ""
echo "=========================================="
echo "Verifying Ansible installation..."
echo "=========================================="
ansible --version

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Ansible installed successfully!"
    echo ""

    # Verify Python can import ansible
    echo "Verifying Python Ansible module..."
    python3 -c "import ansible; print('✅ Ansible Python module version:', ansible.__version__)" || {
        echo "❌ Ansible Python module import failed"
        exit 1
    }

    echo ""
    echo "✅ All checks passed - Ansible is now available system-wide and can be used by Jenkins"
else
    echo ""
    echo "❌ Ansible installation failed"
    exit 1
fi
