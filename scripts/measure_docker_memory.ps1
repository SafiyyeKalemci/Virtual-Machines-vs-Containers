# measure_docker_memory.ps1 - samples the memory and CPU use of the "portfolio"
# container while a k6 load test runs in a second terminal.
#
# Terminal 1:  powershell -ExecutionPolicy Bypass -File scripts\measure_docker_memory.ps1 -Rep 1
# Terminal 2:  k6 run -e TARGET=http://localhost:8080 scripts/load_test.js
#
# 10 samples, about every 3 s (docker stats --no-stream itself takes ~1-2 s).
# Memory = the container's own cgroup usage as reported by docker stats.
# Output lines: "HH:mm:ss <used> / <limit> <cpu%>"  ->  results\docker_mem<Rep>.txt

param([int]$Rep = 1)

1..10 | ForEach-Object {
    $m = docker stats portfolio --no-stream --format "{{.MemUsage}} {{.CPUPerc}}"
    "$(Get-Date -Format HH:mm:ss) $m"
    Start-Sleep -Seconds 3
} | Tee-Object -FilePath "results\docker_mem$Rep.txt"
