# Media Node API

## Requirements

* Operating System: Debian 10 or higher
* Python: Version 3.11 or higher

## Installation

Follow these steps to set up the project on your system.

### 0. Install Operating System

Download the [small installation image][1] for Debian and install the OS.

**Note**:
During the [Selecting and Installing Software installation step][2],
**do not install** any desktop environments.

### 1. Clone the Repository

Clone the repository and navigate into its directory:

```bash
git clone https://github.com/evgenii-d/media-node-api.git \
&& cd media-node-api
```

### 2. Make Scripts Executable

Ensure that all setup scripts have executable permissions:

```bash
chmod +x ./scripts/*.sh
```

### 3. Execute Setup Scripts

Run the following scripts in order to configure the system
and its dependencies:

1) setup_system.sh
2) setup_project.sh
3) setup_services.sh

Execute each script using the following command:

```bash
./scripts/<script_name>.sh
```

**Warning**: Running `setup_system.sh` will block SSH access!
Ensure you have console access if needed.

### 4. Reboot the System to Apply Changes

```bash
sudo shutdown -r now
```

[1]: https://www.debian.org/distrib/netinst
[2]: https://www.debian.org/releases/stable/i386/ch06s03#pkgsel
