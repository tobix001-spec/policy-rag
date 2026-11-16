<#
.SYNOPSIS
  Launch and manage a single-GPU EC2 instance running PolicyRAG (Option 1: docker compose on one box).

.EXAMPLE
  .\deploy\aws\ec2.ps1 launch            # create key pair + firewall + instance (starts billing)
  .\deploy\aws\ec2.ps1 status            # state, IP, setup progress
  .\deploy\aws\ec2.ps1 logs              # follow the first-boot setup log
  .\deploy\aws\ec2.ps1 tunnel            # open the UI at http://localhost:8501 over SSH
  .\deploy\aws\ec2.ps1 stop              # stop paying for the GPU (disk still costs ~$8/month)
  .\deploy\aws\ec2.ps1 start             # start again (new public IP; firewall re-pinned to your IP)
  .\deploy\aws\ec2.ps1 destroy           # terminate instance, delete firewall + key pair

.NOTES
  Requires AWS CLI v2 configured with `aws configure`. Nothing is exposed to the internet: the security
  group allows only SSH from your current IP, and the app is reached through an SSH tunnel.
#>
param(
    [Parameter(Position = 0)]
    [ValidateSet("launch", "status", "logs", "tunnel", "stop", "start", "destroy")]
    [string]$Action = "status",
    [string]$Region = "us-east-1",
    [string]$InstanceType = "g6.xlarge",   # NVIDIA L4 24 GB. g5.xlarge (A10G 24 GB) also works.
    [int]$VolumeGb = 100,
    [string]$Name = "policyrag"
)

$ErrorActionPreference = "Stop"
$KeyName = "$Name-key"
$SgName = "$Name-ssh"
$KeyPath = Join-Path $env:USERPROFILE ".ssh\$KeyName.pem"
$Bootstrap = Join-Path $PSScriptRoot "bootstrap.sh"

function Say($msg, $color = "Cyan") { Write-Host $msg -ForegroundColor $color }

function Invoke-Aws {
    # Runs the AWS CLI with the chosen region and decides success by exit code. Windows PowerShell 5.1
    # turns any native stderr line into a terminating error under 'Stop', so relax it locally.
    $ErrorActionPreference = "Continue"
    $out = & aws.exe @args --region $Region 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { throw "aws $($args -join ' ') failed:`n$($out -join "`n")" }
    return (($out | Where-Object { $_ -notmatch '^(WARNING|NOTE):' }) -join "`n").Trim()
}

function Get-MyIp { (Invoke-RestMethod -Uri "https://checkip.amazonaws.com" -TimeoutSec 10).Trim() }

function Get-InstanceId {
    $id = Invoke-Aws ec2 describe-instances `
        --filters "Name=tag:Name,Values=$Name" "Name=instance-state-name,Values=pending,running,stopping,stopped" `
        --query "Reservations[].Instances[].InstanceId | [0]" --output text
    if ($id -eq "None" -or -not $id) { return $null }
    return $id
}

function Get-SgId {
    $id = Invoke-Aws ec2 describe-security-groups --filters "Name=group-name,Values=$SgName" `
        --query "SecurityGroups[0].GroupId" --output text
    if ($id -eq "None" -or -not $id) { return $null }
    return $id
}

function Set-SshRule($sgId) {
    # Replace any existing SSH rule with one for the current IP only (home IPs change).
    $ip = Get-MyIp
    $existing = Invoke-Aws ec2 describe-security-groups --group-ids $sgId `
        --query "SecurityGroups[0].IpPermissions[?FromPort==``22``].IpRanges[].CidrIp" --output text
    foreach ($cidr in ($existing -split "\s+" | Where-Object { $_ -and $_ -ne "None" })) {
        if ($cidr -ne "$ip/32") {
            $null = Invoke-Aws ec2 revoke-security-group-ingress --group-id $sgId --protocol tcp --port 22 --cidr $cidr
        }
    }
    if ($existing -notmatch [regex]::Escape("$ip/32")) {
        $null = Invoke-Aws ec2 authorize-security-group-ingress --group-id $sgId --protocol tcp --port 22 --cidr "$ip/32"
    }
    Say "Firewall: SSH allowed only from $ip/32"
}

function Get-PublicIp($id) {
    Invoke-Aws ec2 describe-instances --instance-ids $id --query "Reservations[0].Instances[0].PublicIpAddress" --output text
}

function Invoke-Ssh([string]$ip, [string[]]$opts = @(), [string]$cmd = "") {
    # ssh syntax: options, then user@host, then the remote command
    $sshArgs = @("-i", $KeyPath, "-o", "StrictHostKeyChecking=accept-new", "-o", "ServerAliveInterval=30") + $opts + @("ubuntu@$ip")
    if ($cmd) { $sshArgs += $cmd }
    & ssh @sshArgs
}

# ------------------------------------------------------------------------------------------- preflight
if (-not (Get-Command aws.exe -CommandType Application -ErrorAction SilentlyContinue)) {
    throw "AWS CLI not found. Install it (winget install Amazon.AWSCLI), open a new terminal, run 'aws configure'."
}
$account = Invoke-Aws sts get-caller-identity --query Account --output text
Say "AWS account $account, region $Region" "DarkGray"

switch ($Action) {

    "launch" {
        if (Get-InstanceId) { throw "An instance tagged '$Name' already exists. Use 'status', 'start' or 'destroy'." }

        # GPU quota: new accounts often have 0 vCPUs for G instances; xlarge needs 4.
        try {
            $quota = [double](Invoke-Aws service-quotas get-service-quota --service-code ec2 --quota-code L-DB2E81BA `
                    --query "Quota.Value" --output text)
            if ($quota -lt 4) {
                Say "Your 'Running On-Demand G and VT instances' quota is $quota vCPUs; $InstanceType needs 4." "Yellow"
                Say "Request an increase (approval can take hours to a day):" "Yellow"
                Say "  aws service-quotas request-service-quota-increase --service-code ec2 --quota-code L-DB2E81BA --desired-value 4 --region $Region" "Yellow"
                throw "GPU quota too low."
            }
        } catch {
            if ($_.Exception.Message -eq "GPU quota too low.") { throw }
            Say "Could not read the GPU quota (continuing): $($_.Exception.Message.Split("`n")[0])" "DarkYellow"
        }

        # Key pair (private key saved under ~/.ssh, readable only by you, as OpenSSH requires)
        $haveKey = Invoke-Aws ec2 describe-key-pairs --filters "Name=key-name,Values=$KeyName" --query "length(KeyPairs)" --output text
        if ($haveKey -eq "0") {
            New-Item -ItemType Directory -Force (Split-Path $KeyPath) | Out-Null
            $material = Invoke-Aws ec2 create-key-pair --key-name $KeyName --key-type ed25519 --query KeyMaterial --output text
            [IO.File]::WriteAllText($KeyPath, ($material -replace "`r`n", "`n") + "`n")
            & icacls $KeyPath /inheritance:r /grant:r "$($env:USERNAME):(R)" | Out-Null
            Say "Created key pair $KeyName -> $KeyPath"
        } elseif (-not (Test-Path $KeyPath)) {
            throw "Key pair $KeyName exists in AWS but $KeyPath is missing. Delete it in the EC2 console or run 'destroy'."
        }

        # Security group in the default VPC
        $sgId = Get-SgId
        if (-not $sgId) {
            $vpc = Invoke-Aws ec2 describe-vpcs --filters "Name=isDefault,Values=true" --query "Vpcs[0].VpcId" --output text
            if ($vpc -eq "None") { throw "No default VPC in $Region. Create one (aws ec2 create-default-vpc) or pick another region." }
            $sgId = Invoke-Aws ec2 create-security-group --group-name $SgName --vpc-id $vpc `
                --description "PolicyRAG: SSH from owner IP only" --query GroupId --output text
            Say "Created security group $sgId"
        }
        Set-SshRule $sgId

        # Newest AWS Deep Learning Base GPU AMI (Ubuntu): NVIDIA driver preinstalled
        $amiId = $null
        foreach ($ubuntu in @("22.04", "24.04")) {
            $ami = Invoke-Aws ec2 describe-images --owners amazon `
                --filters "Name=name,Values=Deep Learning Base OSS Nvidia Driver GPU AMI (Ubuntu $ubuntu)*" "Name=state,Values=available" `
                --query "sort_by(Images, &CreationDate)[-1].[ImageId,RootDeviceName,Name]" --output text
            if ($ami -and $ami -ne "None") { $amiId, $rootDev, $amiName = $ami -split "\t"; break }
        }
        if (-not $amiId) { throw "Deep Learning Base GPU AMI not found in $Region." }
        Say "AMI: $amiName ($amiId)"

        # user data must have LF line endings or bash on the instance fails with '\r' errors
        $userData = Join-Path $env:TEMP "policyrag-bootstrap.sh"
        [IO.File]::WriteAllText($userData, ([IO.File]::ReadAllText($Bootstrap) -replace "`r`n", "`n"),
            (New-Object Text.UTF8Encoding $false))

        # JSON goes through a file: Windows PowerShell 5.1 mangles quotes in native-command arguments
        $bdm = Join-Path $env:TEMP "policyrag-bdm.json"
        "[{`"DeviceName`":`"$rootDev`",`"Ebs`":{`"VolumeSize`":$VolumeGb,`"VolumeType`":`"gp3`",`"DeleteOnTermination`":true,`"Encrypted`":true}}]" |
            Set-Content -Encoding ascii $bdm

        Say "Launching $InstanceType (billing starts now)..." "Yellow"
        $id = Invoke-Aws ec2 run-instances --image-id $amiId --instance-type $InstanceType --key-name $KeyName `
            --security-group-ids $sgId --block-device-mappings "file://$bdm" --user-data "file://$userData" `
            --metadata-options "HttpTokens=required,HttpEndpoint=enabled" `
            --tag-specifications "ResourceType=instance,Tags=[{Key=Name,Value=$Name}]" "ResourceType=volume,Tags=[{Key=Name,Value=$Name}]" `
            --query "Instances[0].InstanceId" --output text
        Say "Instance $id; waiting for it to run..."
        $null = Invoke-Aws ec2 wait instance-running --instance-ids $id
        $ip = Get-PublicIp $id
        Say "`nRunning at $ip. First-boot setup now takes ~10-20 min (models, image build, index)." "Green"
        Say "  Watch setup:  .\deploy\aws\ec2.ps1 logs"
        Say "  Check:        .\deploy\aws\ec2.ps1 status"
        Say "  Use the app:  .\deploy\aws\ec2.ps1 tunnel   then open http://localhost:8501"
        Say "  STOP PAYING:  .\deploy\aws\ec2.ps1 stop" "Yellow"
    }

    "status" {
        $id = Get-InstanceId
        if (-not $id) { Say "No '$Name' instance (nothing is billing for compute)."; break }
        $state = Invoke-Aws ec2 describe-instances --instance-ids $id --query "Reservations[0].Instances[0].[State.Name,InstanceType,LaunchTime]" --output text
        Say "Instance $id : $state"
        if ($state -like "running*") {
            $ip = Get-PublicIp $id
            Say "Public IP: $ip"
            Say "Setup status:"
            Invoke-Ssh $ip @("-o", "ConnectTimeout=10") "cat /var/log/policyrag-status 2>/dev/null || echo 'not started yet'"
        }
    }

    "logs" {
        $id = Get-InstanceId
        if (-not $id) { throw "No '$Name' instance." }
        Invoke-Ssh (Get-PublicIp $id) @("-t") "tail -n 50 -f /var/log/policyrag-bootstrap.log"
    }

    "tunnel" {
        $id = Get-InstanceId
        if (-not $id) { throw "No '$Name' instance." }
        $ip = Get-PublicIp $id
        Say "Tunnel open while this window stays open (Ctrl+C to close):" "Green"
        Say "  UI   http://localhost:8501"
        Say "  API  http://localhost:8000/docs"
        Invoke-Ssh $ip @("-N", "-L", "8501:127.0.0.1:8501", "-L", "8000:127.0.0.1:8000")
    }

    "stop" {
        $id = Get-InstanceId
        if (-not $id) { throw "No '$Name' instance." }
        $null = Invoke-Aws ec2 stop-instances --instance-ids $id
        $null = Invoke-Aws ec2 wait instance-stopped --instance-ids $id
        Say "Stopped. GPU billing has ended; the $VolumeGb GB disk still costs about `$8/month until 'destroy'." "Green"
    }

    "start" {
        $id = Get-InstanceId
        if (-not $id) { throw "No '$Name' instance. Use 'launch'." }
        Set-SshRule (Get-SgId)
        $null = Invoke-Aws ec2 start-instances --instance-ids $id
        $null = Invoke-Aws ec2 wait instance-running --instance-ids $id
        Say "Running at $(Get-PublicIp $id). Containers restart automatically in ~1-2 min; then run 'tunnel'." "Green"
    }

    "destroy" {
        $confirm = Read-Host "Terminate the '$Name' instance and delete its disk, firewall and key pair? Type 'destroy'"
        if ($confirm -ne "destroy") { Say "Cancelled."; break }
        $id = Get-InstanceId
        if ($id) {
            $null = Invoke-Aws ec2 terminate-instances --instance-ids $id
            Say "Terminating $id..."
            $null = Invoke-Aws ec2 wait instance-terminated --instance-ids $id
        }
        $sgId = Get-SgId
        if ($sgId) { $null = Invoke-Aws ec2 delete-security-group --group-id $sgId; Say "Deleted security group $sgId" }
        $null = Invoke-Aws ec2 delete-key-pair --key-name $KeyName
        if (Test-Path $KeyPath) { Remove-Item $KeyPath -Force }
        Say "Everything removed. Nothing left billing." "Green"
    }
}
