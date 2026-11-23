# VM setup (VirtualBox + Ubuntu Server + Nginx)

These are the steps used to prepare the virtual machine for the measurements.

## 1. Create the VM
- VirtualBox 7.2.22 on Windows 11 Home
- VM name: `ubuntu-nginx`
- Guest OS: Ubuntu Server 26.04.1 LTS (kernel 7.0.0-44-generic), default installation with OpenSSH server
- 2 vCPU, 2048 MB RAM, 15 GB dynamically allocated VDI disk
- Network: NAT (adapter 1)

## 2. Port forwarding (VirtualBox GUI)
Settings → Network → Adapter 1 (NAT) → Advanced → Port Forwarding:

| Name | Protocol | Host port | Guest port |
|------|----------|-----------|------------|
| http | TCP | 8081 | 80 |
| ssh  | TCP | 2222 | 22 |

(Equivalent command, not used in this study:
`VBoxManage modifyvm ubuntu-nginx --natpf1 "http,tcp,,8081,,80" --natpf1 "ssh,tcp,,2222,,22"`)

## 3. Install Nginx (inside the VM)
```bash
sudo apt update
sudo apt install -y nginx        # installed version: nginx 1.28.3 (Ubuntu)
```
The default Nginx configuration was used (document root `/var/www/html`).

## 4. Copy the built site (from the host, repository root)
```powershell
scp -P 2222 -r dist deaduser@localhost:~/dist
```

## 5. Publish the site (inside the VM)
```bash
sudo rm -rf /var/www/html/*
sudo cp -r /home/deaduser/dist/. /var/www/html/
```

## 6. Check
```bash
nginx -v
systemctl status nginx --no-pager
```
Then open http://localhost:8081 on the host.

## Notes
- Hyper-V was enabled on the host (needed by Docker Desktop / WSL 2). VirtualBox therefore
  ran through the Windows Hypervisor Platform (NEM) instead of VT-x directly. Evidence in
  `VBox.log`: `HM: HMR3Init: Attempting fall back to NEM: VT-x is not available`.
- The guest kernel reports `Hypervisor detected: KVM` because VirtualBox offers a
  KVM-compatible paravirtualization interface; KVM itself is not used.
- Memory samples were taken inside the VM with `scripts/measure_vm_memory.sh` over SSH
  and copied back with `scp -P 2222 deaduser@localhost:~/mem1.txt results/vm_mem1.txt`.
