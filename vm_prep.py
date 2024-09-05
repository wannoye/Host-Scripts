#!/usr/bin/python3
import subprocess, re
vg = "vms"
mount_point = "/mnt/"
iso_dir = "/mnt/Star-Lord/Ego/"
first_run = True

input_num = "\nEnter the corresponding number: "
ctrlc = "\n(\"Ctrl + C\" returns to main menu)\n"
invalid = "\n  Invalid entry, try again."
unconfirmed = "\n  Unconfirmed change, returning to main menu."
returning = "\n\n  Returning to main menu."

tasks = [
    ["Remove a logical volume", "remove_volume()"],
    ["Extend a logical volume", "extend_volume()"],
    ["Create a logical volume", "create_volume()"],
    ["Format a logical volume", "format_volume()"],
    ["Mount a file system", "mount_fs()"],
    ["Unmount a file system", "unmount_fs()"],
    ["Create a new virtual machine", "create_vm()"],
    ["Quit (or \"Ctrl + C\")", "exit()"]]

def collect_vg_data():
    global vg_free, vg_size, free_megs
    vgs = subprocess.check_output("vgs " + vg + " | awk '{print$1, $6, $7}' | column -t", shell=True)
    vgs = vgs.decode('utf-8').strip().split()
    vg_free = vgs[-1].lower().strip(('<'))
    vg_size = vgs[-2].lower().strip(('<'))
    if "t" in vg_free: free_megs = float(vg_free.strip(('t'))) * 1000000
    elif "g" in vg_free: free_megs = float(vg_free.strip(('g'))) * 1000
    elif "m" in vg_free: free_megs = float(vg_free.strip(('m')))
    else: free_megs = 0
    print(f"\nInfo for the \"{vg}\" VG:\n\n  Size: {vg_size}\n  Free: {vg_free}", sep="")

def collect_lv_data():
    global volumes
    lvs = subprocess.check_output("lvs " + vg + " | awk '{print$1, $2, $4}' | column -t", shell=True)
    lvs = lvs.decode('utf-8').strip()
    lvs = lvs.split("\n")[1:]
    volumes = [[] for v in range(len(lvs))]
    key = 0
    for volume in lvs:
        volume = volume.split(vg)
        volumes[key].extend((str(key + 1) + ".", volume[0].strip(), volume[1].strip()))
        key += 1
    print(f"\nLogical volumes in the \"{vg}\" VG:\n")
    col_width = max(len(string) for row in volumes for string in row) + 2
    for volume in volumes: print("  " + "".join(string.ljust(col_width) for string in volume[1:]))

def collect_fs_data():
    try:
        global filesystems, tasks
        mounts = subprocess.check_output("cat /proc/mounts | grep '" + mount_point + "' | grep -v 'Star-Lord'", shell=True)
        mounts = mounts.decode('utf-8').split("\n")[0:-1]
        filesystems = [[] for f in range(len(mounts))]
        key = 0
        for fs in mounts:
            fs = fs.split()[1:3]
            fs[0] = fs[0].split("/")[:4]
            filesystems[key].extend((str(key + 1) + ".", fs[0][2], fs[1]))
            key += 1
        print(f"\nFilesystems mounted at \"{mount_point}\":\n")
        col_width = max(len(string) for row in filesystems for string in row) + 2
        for filesystem in filesystems: print("  " + "".join(string.ljust(col_width) for string in filesystem[1:]))
        if not any("unmount_fs()" in task for task in tasks):
            unmount_task = ["Unmount a file system", "unmount_fs()"]
            tasks.insert(5, unmount_task)
    except:
        tasks = [task for task in tasks if task[1] != "unmount_fs()"]

def collect_isos_data():
    try:
        ls_isos = subprocess.check_output("ls " + iso_dir + "*.iso", shell=True, stderr=subprocess.PIPE)
        ls_isos = ls_isos.decode('utf-8').strip().split()
        isos = [[] for e in range(len(ls_isos))]
        key = 0
        for iso in ls_isos:
            iso = iso.split(iso_dir)
            isos[key].extend((str(key + 1) + ".", iso[1]))
            key += 1
        return isos
    except:
        print("\n  No ISO files found.")
        print(returning)
        main_prompt()

def query_osinfo_data():
    try:
        os_name = ""
        osinfo = ""
        while not os_name.isalnum():
            os_name = input(f"{ctrlc}\nEnter an OS to query the os-info database: ")
            if not os_name.isalnum(): print(invalid)
            else: 
                try:
                    osinfo = subprocess.check_output("osinfo-query --fields=short-id,name os | grep -i " + os_name, shell=True, stderr=subprocess.PIPE)
                    osinfo = osinfo[:-1].decode('utf-8').split('\n')
                except:
                    if not osinfo:
                        print("\n  No OS found by that search term, try again.")
                        os_name = ""
        key = 0
        osids = [[] for o in range(len(osinfo))]
        for os in osinfo:
            os = os.split("|")
            osids[key].extend((str(key + 1) + ".", os[0].strip(), os[1].strip()))
            key += 1
        return osids    
    except KeyboardInterrupt:
        print(returning)
        main_prompt()

def remove_volume():
    try:
        vol_choice = 0
        while vol_choice not in range(1, len(volumes) + 1):
            print("\nSelect a volume to remove:\n")
            for volume in volumes: print(f"{volume[0].center(5)}{volume[1]}")
            vol_choice = input(f"{ctrlc}{input_num}")
            if vol_choice.isdigit(): vol_choice = int(vol_choice)
            if vol_choice not in range(1, len(volumes) + 1): print(invalid)
        volume = volumes[vol_choice - 1][1]
        confirm = ""
        while confirm not in ("yes", "no"):
            confirm = input(f"\nRemove the \"{volume}\" logical volume? (Yes/No): ")
            confirm = confirm.lower()
            if confirm == "yes":
                print(f"\n  Deactivating and removing the \"{volume}\" logical volume:")
                lvchange = subprocess.run(["lvchange", "-an", "/dev/" + vg + "/" + volume])
                lvremove = subprocess.run(["lvremove", "-f", "/dev/" + vg + "/" + volume])
            elif confirm == "no": print(unconfirmed)
            else: print(invalid)
    except KeyboardInterrupt:
        print(returning)
    main_prompt()

def valid_space():
    valid = re.compile('\d+\.?\d*[gm]')
    valid_g = re.compile('\d+\.?\d*g')
    valid_m = re.compile('\d+\.?\d*m')
    space = ""
    megs = 0.0
    while not valid.fullmatch(space):
        print(f"\n  Available space: {vg_free}")
        space = input(f"{ctrlc}\nEnter the space to add (Examples: 512m -or- 2.5g): ")
        space = space.lower()   
        if valid_g.fullmatch(space): megs = float(space.strip(('g'))) * 1000
        elif valid_m.fullmatch(space): megs = float(space.strip(('m')))
        else: print(invalid)
        if megs > free_megs:
            print(f"\n  Insufficient space in \"{vg}\" volume group, try again.")
            space = ""
            megs = 0.0
    return space

def extend_volume():
    try:
        vol_choice = 0
        while vol_choice not in range(1, len(volumes) + 1):
            print("\nSelect a volume to extend:\n")
            for volume in volumes: print(f"{volume[0].center(5)}{volume[1]}")
            vol_choice = input(f"{ctrlc}{input_num}")
            if vol_choice.isdigit(): vol_choice = int(vol_choice)
            if vol_choice not in range(1, len(volumes) + 1): print(invalid)
        volume = volumes[vol_choice - 1][1]
        add = valid_space()    
        confirm = ""   
        while confirm not in ("yes", "no"):
            confirm = input(f"\nAdd \"{add}\" to logical volume \"{volume}\"? (Yes/No): ")
            confirm = confirm.lower()
            if confirm == "yes":
                print(f"\n  Extending volume \"{volume}\" by \"{add}\":")
                lvextend = subprocess.run(["lvextend", "-L", "+" + add, "/dev/" + vg + "/" + volume])
            elif confirm == "no": print(unconfirmed)
            else: print(invalid)
    except KeyboardInterrupt:
        print(returning)
    main_prompt()

def create_volume():
    try:
        name = ""
        while not name.isalnum() or any(name in vol for vol in volumes):
            name = input(f"{ctrlc}\nEnter a name for the new logical volume: ")
            if any(name in vol for vol in volumes): print(f"\n  Volume \"{name}\" already exists.")
            elif not name.isalnum(): print(invalid)
        size = valid_space()
        confirm = ""
        while confirm not in ("yes", "no"):
            confirm = input(f"\nCreate logical volume named \"{name}\" with size \"{size}\"? (Yes/No): ")
            confirm = confirm.lower()
            if confirm == "yes":
                print(f"\n  Creating new volume \"{name}\" with size \"{size}\":")
                lvcreate = subprocess.run(["lvcreate", "-L", size, "-n", name, vg])
            elif confirm == "no": print(unconfirmed)
            else: print(invalid)
    except KeyboardInterrupt:
        print(returning)
    main_prompt()

def format_volume():
    try:
        vol_choice = 0
        while vol_choice not in range(1, len(volumes) + 1):
            print("\nSelect a volume to format:\n")
            for volume in volumes: print(f"{volume[0].center(5)}{volume[1]}")
            vol_choice = input(f"{ctrlc}{input_num}")
            if vol_choice.isdigit(): vol_choice = int(vol_choice)
            if vol_choice not in range(1, len(volumes) + 1): print(invalid)
        volume = volumes[vol_choice - 1][1]
        fs_types = [
            ["1.", "exfat"],
            ["2.", "ext2"],
            ["3.", "ext3"],
            ["4.", "ext4"],
            ["5.", "ntfs"],
            ["6.", "xfs"]]
        fs_choice = 0
        while fs_choice not in range(1, len(fs_types) + 1):
            print("\nSelect a filesystem type:\n")
            for fs in fs_types: print(f"{fs[0].center(5)}{fs[1]}")
            fs_choice = input(f"{ctrlc}{input_num}")
            if fs_choice.isdigit(): fs_choice = int(fs_choice)
            if fs_choice not in range(1, len(fs_types) + 1): print(invalid)
        filesystem = fs_types[fs_choice - 1][1]
        confirm = ""
        while confirm not in ("yes", "no"):
            confirm = input(f"\nFormat the \"{volume}\" logical volume as an \"{filesystem}\" filesystem? (Yes/No): ")
            confirm = confirm.lower()
            if confirm == "yes":
                print(f"\n  Formatting the \"{volume}\" logical volume as an \"{filesystem}\" filesystem:")
                mkfs = subprocess.run(["mkfs." + filesystem, "/dev/" + vg + "/" + volume], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if mkfs.stderr:
                    for line in mkfs.stderr.decode('utf-8').rstrip("\n").split("\n"): print(f"  {line}")
                if mkfs.stdout:
                    for line in mkfs.stdout.decode('utf-8').rstrip("\n").split("\n"): print(f"  {line}")
            elif confirm == "no": print(unconfirmed)
            else: print(invalid)
    except KeyboardInterrupt:
        print(returning)
    main_prompt()

def mount_fs():
    try:
        vol_choice = 0
        while vol_choice not in range(1, len(volumes) + 1):
            print("\nSelect a volume to mount:\n")
            for volume in volumes: print(f"{volume[0].center(5)}{volume[1]}")
            vol_choice = input(f"{ctrlc}{input_num}")
            if vol_choice.isdigit(): vol_choice = int(vol_choice)
            if vol_choice not in range(1, len(volumes) + 1): print(invalid)
        volume = volumes[vol_choice - 1][1]
        confirm = ""
        while confirm not in ("yes", "no"):
            confirm = input(f"\nMount \"/dev/{vg}/{volume}\" to \"{mount_point}{volume}\"? (Yes/No): ")
            confirm = confirm.lower()
            if confirm == "yes":
                print(f"\n  Mounting \"/dev/{vg}/{volume}\" to \"{mount_point}{volume}\":")
                mkdir = subprocess.run(["mkdir", "-p", mount_point + volume])
                mount = subprocess.run(["mount", "/dev/" + vg + "/" + volume, mount_point + volume])
                if not mount.returncode:
                    print(f"  Filesystem successfully mounted to \"{mount_point}{volume}\"." )
                    print("  Add an entry in \"/etc/fstab\" as needed.")
            elif confirm == "no": print(unconfirmed)
            else: print(invalid)
    except KeyboardInterrupt:
        print(returning)
    main_prompt()

def unmount_fs():
    try:
        vol_choice = 0
        while vol_choice not in range(1, len(filesystems) + 1):
            print("\nSelect a filesystem to unmount:\n")
            for filesystem in filesystems: print(f"{filesystem[0].center(5)}{filesystem[1]}")
            vol_choice = input(f"{ctrlc}{input_num}")
            if vol_choice.isdigit(): vol_choice = int(vol_choice)
            if vol_choice not in range(1, len(filesystems) + 1): print(invalid)
        volume = filesystems[vol_choice - 1][1]
        confirm = ""
        while confirm not in ("yes", "no"):
            confirm = input(f"\nUnmount filesystem at \"{mount_point}{volume}\"? (Yes/No): ")
            confirm = confirm.lower()
            if confirm == "yes":
                print(f"\n  Unmount filesystem at \"{mount_point}{volume}\" and removing the directory.")
                umount = subprocess.run(["umount",  mount_point + volume])
                rmdir = subprocess.run(["rmdir", mount_point + volume])
                if not umount.returncode and not rmdir.returncode:
                     print(f"  Filesystem successfully unmounted and directory removed.")
            elif confirm == "no": print(unconfirmed)
            else: print(invalid)
    except KeyboardInterrupt:
        print(returning)
    main_prompt()

def vm_name():
    try:
        name = ""
        while not name.isalnum():
            name = input(f"{ctrlc}\nEnter an name for the VM: ")
            if not name.isalnum(): print(invalid)
        return name
    except KeyboardInterrupt:
        print(returning)
        main_prompt()

def vm_ostype():
    try:
        os_types = [
            ["1.", "Linux"],
            ["2.", 'Windows'],
            ["3.", 'Freebsd'],
            ["4.", 'Other']]
        ostype_choice = 0
        while ostype_choice not in range(1, len(os_types) + 1):
            print("\nSelect an OS type for the VM:\n")
            for os_type in os_types: print(f"{os_type[0].center(5)}{os_type[1]}")
            ostype_choice = input(f"{ctrlc}{input_num}")
            if ostype_choice.isdigit(): ostype_choice = int(ostype_choice)
            if ostype_choice not in range(1, len(os_types) + 1): print(invalid)
        ostype = os_types[ostype_choice - 1][1].lower()
        return ostype
    except KeyboardInterrupt:
        print(returning)
        main_prompt()

def vm_osid():
    try:
        osids = query_osinfo_data()
        osid_choice = 0
        while osid_choice not in range(1, len(osids) + 1):
            print("\nSelect an OS for the VM:\n")
            for os in osids: print(f"{os[0].center(5)}{os[2]}")
            osid_choice = input(f"{ctrlc}{input_num}")
            if osid_choice.isdigit(): osid_choice = int(osid_choice)
            if osid_choice not in range(1, len(osids) + 1): print(invalid)
        osid = osids[osid_choice - 1][1].lower()
        return osid
    except KeyboardInterrupt:
        print(returning)
        main_prompt()

def vm_vcpu():
    try:
        vcpu = 0
        while vcpu not in range(1,5):
            vcpu = input(f"{ctrlc}\nHow many vCPU cores would you like to allocate? (1-4): ")
            if vcpu.isdigit(): vcpu = int(vcpu)
            if vcpu not in range(1,5): print(invalid)
        return vcpu
    except KeyboardInterrupt:
        print(returning)
        main_prompt()

def vm_ram():
    try:
        ram = 1
        while not ram % 128 == 0 or ram == 0:
            ram = input(f"{ctrlc}\nHow much ram would you like to allocate? (Mb, increments of 128): ")
            if ram.isdigit(): ram = int(ram)
            else: ram = 1
            if not ram % 128 == 0 or ram == 0: print(invalid)
        return ram
    except KeyboardInterrupt:
        print(returning)
        main_prompt()

def vm_volume():
    try:
        vol_choice = 0
        while vol_choice not in range(1, len(volumes) + 1):
            print("\nSelect a volume for the VM:\n")
            for volume in volumes: print(f"{volume[0].center(5)}{volume[1]}")
            vol_choice = input(f"{ctrlc}{input_num}")
            if vol_choice.isdigit(): vol_choice = int(vol_choice)
            if vol_choice not in range(1, len(volumes) + 1): print(invalid)
        volume = volumes[vol_choice - 1][1]
        return volume
    except KeyboardInterrupt:
        print(returning)
        main_prompt()

def vm_iso():
    try:
        isos = collect_isos_data()
        iso_choice = 0
        while iso_choice not in range(1, len(isos) + 1):
            print("\nSelect an ISO file for the VM:\n")
            for iso in isos: print(f"{iso[0].center(5)}{iso[1]}")
            iso_choice = input(f"{ctrlc}{input_num}")
            if iso_choice.isdigit(): iso_choice = int(iso_choice)
            if iso_choice not in range(1, len(isos) + 1): print(invalid)
        iso = isos[iso_choice - 1][1]
        return iso
    except KeyboardInterrupt:
        print(returning)
        main_prompt()

def install_vm(name, ostype, osid, vcpu, ram, volume, iso):
    pass
    try:
        confirm = ""
        while confirm not in ("yes", "no"):
            print("\nVM paramaters:\n"
                f"\n  Name: {name}",
                f"\n  OS Type: {ostype}",
                f"\n  Operating System: {osid}",
                f"\n  vCPU Cores: {vcpu}",
                f"\n  Memory (in MB): {ram}",
                f"\n  Volume: {volume}",
                f"\n  ISO File: {iso}")
            confirm = input("\nCreate a VM with these details? (Yes/No): ")
            confirm = confirm.lower()
            if confirm == "yes":
                install_cmd = [
                "timeout", "5",
                "virt-install",
                "--virt-type=kvm",
                "--hvm",
                f"--name={name}",
                f"--os-type={ostype}",
                f"--os-variant={osid}",
                f"--vcpus={vcpu}",
                f"--ram={ram}",
                f"--disk=/dev/{vg}/{volume},bus=virtio",
                "--graphics=vnc",
                "--graphics=spice",
                f"--cdrom={iso_dir}{iso}",
                "--network=bridge=br0,model=virtio,virtualport_type=openvswitch"]
                print(f"\n  Creating \"{name}\" VM.\n")
                virt_install = subprocess.run(install_cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
                if virt_install.stderr:
                    for line in virt_install.stderr.decode('utf-8').rstrip("\n").split("\n"): print(f"  {line}")
                print("\n  Launch Virtual Machine Manager to find the VM and complete the installation.")
                quit = input("\nType \"Q\" to quit, any other key returns to main menu: ")
                quit = quit.lower()
                if quit == "q": exit()
            elif confirm == "no": 
                print(unconfirmed)
            else: print(invalid)
    except KeyboardInterrupt:
        print(returning)
    main_prompt()

def create_vm():
    name = vm_name()
    ostype = vm_ostype()
    osid = vm_osid()
    vcpu = vm_vcpu()
    ram = vm_ram()
    volume = vm_volume()
    iso = vm_iso()
    install_vm(name, ostype, osid, vcpu, ram, volume, iso)

def main_prompt():
    try:
        global first_run, tasks
        task = 0
        while task not in range(1, len(tasks) + 1):
            if first_run:
                print("\n  Starting VM prep script...")
                first_run = False
            collect_vg_data()
            collect_lv_data()
            collect_fs_data()
            print("\nSelect a task:\n")
            key = 1
            for t in tasks:
                num = str(key) + "."
                print(f"{num.center(5)}{t[0]}")
                key += 1
            task = input(input_num)
            if task.isdigit(): task = int(task)
            if task not in range(1, len(tasks) + 1): print(invalid)
        eval(tasks[task - 1][1])
    except KeyboardInterrupt:
        print("\n")
        exit()

if __name__ == "__main__":
    main_prompt()
