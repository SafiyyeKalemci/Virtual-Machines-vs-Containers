"run,seconds" | Set-Content results\docker_startup.csv
1..10 | ForEach-Object {
    docker stop portfolio | Out-Null
    Start-Sleep -Seconds 5
    $sw = [Diagnostics.Stopwatch]::StartNew()
    docker start portfolio | Out-Null
    while ($true) {
        try {
            $r = Invoke-WebRequest -Uri "http://localhost:8080/" -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { break }
        } catch { }
        Start-Sleep -Milliseconds 50
    }
    $sw.Stop()
    "run $_ : $([math]::Round($sw.Elapsed.TotalSeconds,2)) s"
    "$_,$([math]::Round($sw.Elapsed.TotalSeconds,2))" | Add-Content results\docker_startup.csv
    Start-Sleep -Seconds 5
}