# Host Scripts

## "vm_prep.py" Python Script

Created to prep a KVM host and create a new VM.<br/>
The script can accomplish the following tasks:

- Remove a logical volume
- Extend a logical volume
- Create a logical volume
- Format a logical volume
- Mount a file system
- Unmount a file system
- Create a new virtual machine

The main menu prompts the user to select a task.<br/>
Subsequent prompts guide the user through completion of each task.

### Requires:

- Python 3.6.9 or greater
- Change "vg", "mount_point", and "iso_dir" variables

### Usage:

```python3 vm_prep.py```

## "install_ansible.py" Python Script

Script is designed to install ansible and its prerequisites.
The script completes the following tasks:

- Installs: python-pip, python-venv, whois(mkpasswd) via package manager
- Creates an administrator account to run Ansible playbooks from
- Sets the user password and gives sudo access 
- Creates a virtual Python environment in the new user's home directory
- Installs Ansible and it's requirements in the virtual environment
- Disables host key checking 
- Creates directories for playbooks and group vars
- Writes out inventory and vars file templates
- Sets permissions of created files and folders for use by new user
- Tests the ansible installation and verifies any changes made

### Requires:

- Python 3.8 or greater for Ansible compatibility
- Change "ansible_user", and "virt_env" variables

### Usage:

```python3 install_ansible.py```

asdf