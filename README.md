# Virtual Machines vs. Containers – SEN421 Course Project

SEN421 Cloud Architecture and Services, Fall 2026 – Topic 2
Istanbul Aydın University – [Your Name]

## Overview
This project compares running the same application in a virtual machine
(VirtualBox, Ubuntu Server) and in a Docker container. The application is my
portfolio website (React + Vite), served by Nginx in both environments.
Measured: image size, startup time, memory use, and requests per second.

Application source: https://github.com/SafiyyeKalemci/Portfolio-Website

## Test Environment
- Host: [CPU, RAM], Windows 11 Home
- VM: VirtualBox [version], Ubuntu Server [version], [x] vCPU, [x] GB RAM
- Container: Docker Desktop [version] (WSL2 backend)
- Load test: k6 [version]

## Repository Structure
- `docker/` – Dockerfile and Nginx configuration
- `vm/` – setup commands for the VM
- `scripts/` – measurement scripts
- `results/` – raw results (CSV) and charts

## How to Reproduce
[To be added]
