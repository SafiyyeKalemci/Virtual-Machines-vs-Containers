#!/usr/bin/env bash
# measure_vm_memory.sh - samples memory and CPU use inside the Ubuntu VM
# while a k6 load test runs on the host.
#
# In the VM (over SSH):  bash measure_vm_memory.sh 1      -> mem1.txt
# On the host:           k6 run -e TARGET=http://localhost:8081 scripts/load_test.js
#
# 10 samples, one about every 5 s (vmstat 1 2 takes ~1 s, then sleep 4).
# Columns: time, used memory in MiB ("used" column of free -m, page cache
# excluded, whole VM), CPU busy % (100 - idle from vmstat).
# Note: the SSH session itself adds a small amount of memory and CPU use.

rep=${1:-1}
for i in $(seq 1 10); do
  echo "$(date +%T) $(free -m | awk '/Mem:/ {print $3}') $(vmstat 1 2 | tail -1 | awk '{print 100-$15}')"
  sleep 4
done > "mem${rep}.txt"
