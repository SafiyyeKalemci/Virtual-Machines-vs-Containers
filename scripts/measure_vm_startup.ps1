$vbox = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$vm = "ubuntu-nginx"
$url = "http://localhost:8081/"
1..10 | ForEach-Object {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $vbox startvm $vm --type headless | Out-Null
    if ($LASTEXITCODE -ne 0) { "run $_ : GECERSIZ (startvm hata verdi)"; return }
    while ($true) {
        try {
            $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { break }
        } catch { }
        Start-Sleep -Milliseconds 200
    }
    $sw.Stop()
    "run $_ : $([math]::Round($sw.Elapsed.TotalSeconds,1)) s"
    "$_,$([math]::Round($sw.Elapsed.TotalSeconds,1)),started $(Get-Date -Format 'HH:mm')" | Add-Content results\vm_startup.csv
    & $vbox controlvm $vm acpipowerbutton
    $t = 0
    while (-not (& $vbox showvminfo $vm --machinereadable | Select-String 'VMState="poweroff"') -and $t -lt 300) { Start-Sleep -Seconds 2; $t += 2 }
    Start-Sleep -Seconds 30
}