#!/usr/bin/python3

from subprocess import run, PIPE
from sys import exit
from venv import create
from random import choice
from string import ascii_letters, digits
from os import chmod, makedirs, path, uname

ansible_user = 'ansible'
virt_env = 'ansible_venv'

def python_prep():
    try:
        print("\nCollecting OS Info!\n")
        with open('/etc/os-release') as release:
            os_info = release.read()
        if 'Ubuntu' in os_info:
            print("Installing Packages:", "python-pip,", "python-venv,", "whois(mkpasswd)!\n")
            apt_install = 'apt install -y python3-pip python3-env whois'
            install = run(apt_install, shell=True, check=True, stdout=PIPE, stderr=PIPE)
        elif 'AlmaLinux' in os_info:
            print(f"Installing Package:", "python-pip,", "mkpasswd!\n")
            dnf_install = 'dnf install -y python3-pip mkpasswd'
            install = run(dnf_install, shell=True, stdout=PIPE, stderr=PIPE)
        else: 
            print(f"Operating System Not Compatible!\n")
            raise
    except:
        print("Something Went Wrong Installing Packages!\n\nExiting...\n")
        exit()

def create_user():
    try:
        with open('/etc/passwd', 'r') as passwd:
            users = passwd.read()
        if ansible_user not in users:
            salt = ''.join(choice(ascii_letters + digits) for i in range(8))
            print(f"Creating '{ansible_user}' User!\n\nSet a ", end='')
            pswd = run(['mkpasswd', '-m', 'SHA-512', '-S', salt], stdout=PIPE, stderr=PIPE)
            if not pswd.returncode:
                adduser = run(['useradd', '-m', '-s', '/bin/bash', ansible_user, '-p', pswd.stdout.decode('utf-8').strip()])
                if not adduser.returncode: print(f"\nUser '{ansible_user}' Created!\n")
                else: raise
            else: raise
            print(f"Setting Permissions for '{ansible_user}'!\n")
            global sudoer_file
            sudoer_file = f'/etc/sudoers.d/{ansible_user}'
            permissions = f"## '{ansible_user}' User Permissions\n{ansible_user}	ALL=(ALL)       NOPASSWD: ALL"
            if path.exists(sudoer_file):
                with open(sudoer_file, 'r') as sudoer:
                    lines = sudoer.readlines()
                if any(line.strip() == permissions for line in lines):
                    print(f"Permissions for '{ansible_user}' Already Set!\n")
                else: 
                    with open(sudoer_file, 'w') as sudoer:
                        sudoer.write(permissions)
            elif not path.exists(sudoer_file):
                with open(sudoer_file, 'w') as sudoer:
                    sudoer.write(permissions)
            else: 
                print(f"Something Went Wrong Setting Permissions for '{ansible_user}'!")
                raise
            chmod(sudoer_file, 0o440)
        else:
            print(f"User {ansible_user} Already Exists!\n")
    except: 
        print(f"Something Went Wrong Creating User {ansible_user}!\n\nExiting...\n")
        exit()

def create_venv():
    try:
        print(f"Creating '{virt_env}' Virtual Environment!\n")
        create(f'/home/{ansible_user}/{virt_env}', with_pip=True)
        print("Installing Ansible Packages!\n")
        pip_install = f'/home/{ansible_user}/{virt_env}/bin/python3 -m pip install ansible ansible.navigator'
        run(pip_install, shell=True, check=True, stdout=PIPE, stderr=PIPE)
    except:
        print("Something Went Wrong Creating the Virtual Environment or Installing Packages!\n\nExiting...\n")
        exit()

def ansillary_setup():
    try:
        global inventory, vars_file, ansible_cfg
        print(f"Disabling Host Key Checking!\n")
        disable_hkc = "host_key_checking = False"
        ansible_cfg = f'/home/{ansible_user}/{virt_env}/ansible.cfg'
        with open(ansible_cfg, 'a') as cfg:
            cfg.write(f'{disable_hkc}\n')
        print("Creating the 'playbooks/group_vars' Directory!\n")
        makedirs(f'/home/{ansible_user}/playbooks/group_vars', exist_ok=True)
        print("Creating the 'playbooks/inventory' File!\n")
        inventory = f'/home/{ansible_user}/playbooks/inventory'
        hostname = uname().nodename
        with open(inventory, 'w') as inv:
            inv.write(f'[hosts]\n{hostname}\n\n[containers]\n\n[vms]')
        print("Creating the 'group_vars/all.yml' File!\n")
        group_vars = [
            "ansible_user: 'user'",
            "ansible_become_pass: 'pass'",
            "new_user: 'user'",
            "user_pass: 'pass'",
            "cifs_user: 'user'",
            "cifs_pass: 'pass'",
            "cifs_server: 'ip'",
            "cifs_share:",
            "  - 'share_1'",
            "  - 'share_2'",
            "  - 'share_3'"
        ]
        vars_file = f'/home/{ansible_user}/playbooks/group_vars/all.yml'
        with open(vars_file, 'w') as vars:
            for var in group_vars:
                vars.write(var + '\n')
        print(f"Changing Ownership of Created Files to '{ansible_user}:{ansible_user}!\n")
        chown = f'chown -R {ansible_user}:{ansible_user} /home/{ansible_user}/{virt_env} /home/{ansible_user}/playbooks'
        run(chown, shell=True, check=True, stdout=PIPE, stderr=PIPE)
        print("Changing Privilege of Created Files to '770'!\n")
        chmod = f'chmod 770 /home/{ansible_user}/{virt_env} /home/{ansible_user}/playbooks'
        run(chmod, shell=True, check=True, stdout=PIPE, stderr=PIPE)
    except:
        print("Something Went Wrong During Ansilary Setup!\n\nExiting...\n")
        exit()

def test_setup():
    try:
        print("Activating the Virtual Environment & Pinging the Localhost!\n")
        activate = f'source /home/{ansible_user}/{virt_env}/bin/activate'
        ping = f"{activate} && ansible -m ping localhost"
        ping_status = run(ping, shell=True, executable="/bin/bash")
        if not ping_status.returncode:
            print("\nAnsible Ping Module Test Succeeded!\n")
        else:
            print("Ansible Ping Module Test Failed!\n")
            raise
        print(f"File Permissions for '/home/{ansible_user}' Contents:\n")
        file_permissions = run(['ls', '-lah', f'/home/{ansible_user}'])
        if file_permissions.returncode:
            print(f"Something Went Wrong Listing the Contents of '/home/{ansible_user}'")
            raise
        print(f"\n'{ansible_user}' User Permissions, Contents of '{sudoer_file}':\n")
        with open(sudoer_file, 'r') as sudoer:
            for line in sudoer:
                print(line.strip())
        print(f"\nContents of {ansible_cfg}:\n")
        with open(ansible_cfg, 'r') as cfg:
            for line in cfg:
                print(line.strip())
        print(f"\n'group_vars/all.yml' File Contents:\n")
        with open(vars_file, 'r') as vars:
            for line in vars:
                print(line.strip())
        print("\nInventory File Contents:\n")
        with open(inventory, 'r') as inv:
            for line in inv:
                print(line.strip())

        encrypt_cmd = f'ansible-vault encrypt {vars_file}'
        print("\nAnsible Setup is Now Complete!\n")
        print(f"Once Variables are Added, Encrypt the 'group_vars/all.yml' File with:\n\n{encrypt_cmd}\n")
        print(f"The Virtual Environment can be Activated by Issuing the Command:\n\n{activate}\n")
    except:
        print("Something Went Wrong During Setup Verification!\n\nExiting...\n")
        exit()

if __name__ == "__main__":
    python_prep()
    create_user()
    create_venv()
    ansillary_setup()
    test_setup()