# Create the cheapest viable Hetzner Cloud server in Germany (Falkenstein fsn1).
# Requires: HCLOUD_TOKEN (Read & Write).
#
# Usage:
#   $env:HCLOUD_TOKEN = "..."
#   .\scripts\hetzner\New-HetznerDeServer.ps1 -SshPublicKeyPath $env:USERPROFILE\.ssh\hetzner-fsn-telegram-shop_ed25519.pub
# Fallback same price: -Location nbg1

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SshPublicKeyPath,

    [string]$Name = "telegram-shop-fsn",
    [string]$Location = "fsn1",
    [string]$ServerType = "cx22",
    [string]$Image = "ubuntu-24.04",
    [switch]$WithIPv4,
    [string]$SshKeyName = "telegram-shop-fsn"
)

$ErrorActionPreference = "Stop"

if (-not $env:HCLOUD_TOKEN) {
    Write-Error "Set HCLOUD_TOKEN (Hetzner Console → Security → API tokens). Do not commit it."
}

if (-not (Test-Path $SshPublicKeyPath)) {
    Write-Error "Public key not found: $SshPublicKeyPath  Run New-HetznerSshKey.ps1 first."
}

$pub = (Get-Content -Raw $SshPublicKeyPath).Trim()
$cloudInitPath = Join-Path $PSScriptRoot "cloud-init.yaml"
if (-not (Test-Path $cloudInitPath)) {
    Write-Error "Missing $cloudInitPath"
}
$userData = Get-Content -Raw $cloudInitPath

function Invoke-Hetzner {
    param([string]$Method, [string]$Path, $Body)
    $uri = "https://api.hetzner.cloud/v1$Path"
    $headers = @{ Authorization = "Bearer $($env:HCLOUD_TOKEN)" }
    if ($null -ne $Body) {
        $json = $Body | ConvertTo-Json -Depth 8 -Compress
        return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers -ContentType "application/json" -Body $json
    }
    return Invoke-RestMethod -Method $Method -Uri $uri -Headers $headers
}

Write-Host "Uploading SSH key $SshKeyName ..."
$existingKeys = Invoke-Hetzner GET "/ssh_keys"
$key = $existingKeys.ssh_keys | Where-Object { $_.name -eq $SshKeyName } | Select-Object -First 1
if (-not $key) {
    $created = Invoke-Hetzner POST "/ssh_keys" @{ name = $SshKeyName; public_key = $pub }
    $key = $created.ssh_key
}

Write-Host "Creating firewall (deny public except optional bootstrap SSH)..."
$fwName = "$Name-fw"
$firewalls = Invoke-Hetzner GET "/firewalls"
$fw = $firewalls.firewalls | Where-Object { $_.name -eq $fwName } | Select-Object -First 1
$fwRules = @(
    @{ direction = "in"; protocol = "icmp"; source_ips = @("0.0.0.0/0", "::/0") },
    @{ direction = "in"; protocol = "udp"; port = "41641"; source_ips = @("0.0.0.0/0", "::/0") }
)
if ($WithIPv4) {
    # Leave 22 open only if you pass -WithIPv4; close it after Tailscale SSH works.
    $fwRules += @{ direction = "in"; protocol = "tcp"; port = "22"; source_ips = @("0.0.0.0/0", "::/0") }
}

if (-not $fw) {
    $fwCreated = Invoke-Hetzner POST "/firewalls" @{
        name  = $fwName
        rules = $fwRules
    }
    $fw = $fwCreated.firewall
}

$publicNet = @{
    enable_ipv6 = $true
    enable_ipv4 = [bool]$WithIPv4
}

Write-Host "Creating server $Name type=$ServerType location=$Location ipv4=$WithIPv4 ..."
$serverBody = @{
    name        = $Name
    server_type = $ServerType
    location    = $Location
    image       = $Image
    ssh_keys    = @($key.id)
    user_data   = $userData
    public_net  = $publicNet
    firewalls   = @(@{ firewall = $fw.id })
    labels      = @{ app = "telegram-shop"; loc = $Location }
}

$resp = Invoke-Hetzner POST "/servers" $serverBody
$server = $resp.server

Write-Host ""
Write-Host "Created server id=$($server.id) status=$($server.status)"
Write-Host "IPv6: $($server.public_net.ipv6.ip)"
if ($server.public_net.ipv4.ip) {
    Write-Host "IPv4: $($server.public_net.ipv4.ip)"
    Write-Host "Bootstrap SSH (close after Tailscale):"
    Write-Host "  ssh -i `"$($SshPublicKeyPath -replace '\.pub$','')`" deploy@$($server.public_net.ipv4.ip)"
} else {
    Write-Host "No IPv4 (cheaper). Use Hetzner Console or IPv6 SSH, then: sudo tailscale up --ssh"
}
Write-Host ""
Write-Host "Next:"
Write-Host "  1. Wait ~2 min for cloud-init"
Write-Host "  2. sudo tailscale up --ssh --hostname=$Name --auth-key=tskey-auth-HOST"
Write-Host "  3. Remove TCP/22 from firewall $fwName"
Write-Host "  4. rsync code to /opt/telegram-shop and docker compose up -d"
Write-Host "See docs/deploy/HETZNER-GERMANY.md"
