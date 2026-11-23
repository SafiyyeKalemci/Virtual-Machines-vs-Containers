# Virtual Machines vs. Containers – SEN421 Course Project

SEN421 Cloud Architecture and Services, Fall 2026 – Topic 2 (Part A)
Istanbul Aydın University – Safiyye Kalemci

## Overview
This project runs the same application in a virtual machine (VirtualBox, Ubuntu Server)
and in a Docker container, and compares image/disk size, startup time, memory use, and
requests per second. The application is my portfolio website (React + Vite, static files),
served by Nginx in both environments. A monthly cloud cost estimate (AWS EC2 vs. AWS Fargate)
is also included.

Application source: https://github.com/SafiyyeKalemci/Portfolio-Website

## Test Environment
| Item | Value |
|------|-------|
| Host | Intel Core i5-12500H (12 cores, 16 threads), 15.8 GB RAM, Windows 11 Home (build 26300) |
| VM | VirtualBox 7.2.22 (running through Hyper-V / NEM), Ubuntu Server 26.04.1 LTS, kernel 7.0.0-44-generic, 2 vCPU, 2048 MB RAM, 15 GB disk, Nginx 1.28.3 |
| Container | Docker Desktop 4.81.0 (Engine 29.6.1, WSL 2 backend: WSL 2.7.10.0, kernel 6.18.33.2-2), image `nginx:alpine` (Nginx 1.31.8), limits `--cpus=2 --memory=2g` |
| Load test | k6 v2.4.0, run on the same host |
| Site build | Vite 7.3.1, `--base=/`, `dist/` ≈ 5.6 MB |

## Repository Structure
- `docker/` – Dockerfile (default Nginx configuration of `nginx:alpine`)
- `vm/` – VM setup steps (`setup_vm.md`)
- `scripts/` – load test, startup and memory measurement scripts, figure script
- `results/` – raw results (k6 JSON, startup CSV, memory logs) and `aws/` cost estimates
- `figures/` – architecture diagram and result figures (PDF and PNG)
- `screenshots/` – evidence of the deployments

`dist/` (the built site) is not committed; build it as shown below.

## How to Reproduce
1. **Build the site** (in the Portfolio-Website repository), then copy `dist/` to the root of this repository:
   ```powershell
   npm ci
   npm run build -- --base=/
   ```
2. **Container** (repository root):
   ```powershell
   docker build -t portfolio-nginx -f docker/Dockerfile .
   docker run -d --name portfolio -p 8080:80 --cpus=2 --memory=2g portfolio-nginx
   ```
3. **VM**: follow [`vm/setup_vm.md`](vm/setup_vm.md). The site is served on port 8081.
4. **Throughput** – one warm-up run, then three recorded runs, 60 s apart
   (load: 10 s ramp to 50 virtual users, 30 s at 50; each iteration requests the page, CSS and JS):
   ```powershell
   k6 run -e TARGET=http://localhost:8081 scripts/load_test.js   # warm-up
   foreach ($i in 1..3) { k6 run -e TARGET=http://localhost:8081 --summary-export="results/vm_run$i.json" scripts/load_test.js; Start-Sleep -Seconds 60 }
   ```
   Use port 8080 and `docker_run$i.json` for the container. Docker Desktop was closed during the VM tests.
5. **Startup time** (start command until the first HTTP 200):
   ```powershell
   powershell -ExecutionPolicy Bypass -File scripts\measure_vm_startup.ps1
   powershell -ExecutionPolicy Bypass -File scripts\measure_docker_startup.ps1
   ```
   VM: power-on of a stopped VM. Docker: `docker start` of an existing container while Docker Desktop is already running.
6. **Memory under load** – run the sampler and a k6 test at the same time (three repetitions):
   - VM (inside the VM over SSH): `bash measure_vm_memory.sh 1`, then copy `mem1.txt` to `results/vm_mem1.txt`
   - Docker: `powershell -ExecutionPolicy Bypass -File scripts\measure_docker_memory.ps1 -Rep 1`
7. **Size**:
   ```powershell
   docker images portfolio-nginx
   docker image inspect portfolio-nginx --format "{{.Size}}"
   docker exec portfolio sh -c "du -xsm / 2>/dev/null"
   ```
   In the VM: `df -h /`; on the host: size of the `.vdi` file.
8. **Figures**:
   ```powershell
   pip install matplotlib
   python scripts/make_figures.py
   ```

## Main Results (mean ± SD of 3 runs unless noted)
| Metric | Docker | VM |
|--------|--------|----|
| Throughput (req/s) | 2110.8 ± 94.0 | 546.9 ± 22.6 |
| Median response time (ms) | 22.3 ± 1.0 | 78.6 ± 1.9 |
| p95 response time (ms) | 81.6 ± 3.9 | 321.7 ± 15.6 |
| Startup time, median (s) | 0.19 (n = 10) | 41.5 (n = 9) |
| Memory under load (MiB) | 17.6 ± 0.1 (container cgroup) | 410.7 ± 0.6 (whole VM) |
| Filesystem size | 70 MiB | 5.0 GiB |

## Cost
No cloud resources were created; all experiments ran locally (actual cost: 0 USD).
Monthly estimates from the AWS Pricing Calculator (Europe (Milan)) are in `results/aws/`.
