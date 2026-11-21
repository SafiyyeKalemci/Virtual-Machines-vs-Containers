$vbox = "C:\Program Files\Oracle\VirtualBox\VBoxManage.exe"
$vm = "ubuntu-nginx"
$url = "http://localhost:8081/"
1..3 | ForEach-Object {
    $sw = [Diagnostics.Stopwatch]::StartNew()
    & $vbox startvm $vm --type headless | Out-Null
    while ($true) {
        try {
            $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 2
            if ($r.StatusCode -eq 200) { break }
        } catch { }
        Start-Sleep -Milliseconds 200
    }
    $sw.Stop()
    "run $_ : $([math]::Round($sw.Elapsed.TotalSeconds,1)) s"
    & $vbox controlvm $vm acpipowershutdown
    while (-not (& $vbox showvminfo $vm --machinereadable | Select-String 'VMState="poweroff"')) { Start-Sleep -Seconds 2 }
    Start-Sleep -Seconds 30
}