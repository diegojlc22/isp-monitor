Write-Host "=== DIAGNOSTICO DE FIREWALL E SNMP ===" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar status do Firewall
Write-Host "[1] Status do Firewall do Windows:" -ForegroundColor Yellow
$firewallProfiles = Get-NetFirewallProfile
foreach ($profile in $firewallProfiles) {
    Write-Host "  - $($profile.Name): $($profile.Enabled)" -ForegroundColor $(if ($profile.Enabled) { "Red" } else { "Green" })
}
Write-Host ""

# 2. Verificar regras SNMP
Write-Host "[2] Regras de Firewall relacionadas a SNMP:" -ForegroundColor Yellow
$snmpRules = Get-NetFirewallRule | Where-Object { $_.DisplayName -like "*SNMP*" }
if ($snmpRules) {
    foreach ($rule in $snmpRules) {
        Write-Host "  - $($rule.DisplayName): $($rule.Enabled) ($($rule.Direction))" -ForegroundColor Cyan
    }
} else {
    Write-Host "  Nenhuma regra SNMP encontrada (isso e normal)" -ForegroundColor Green
}
Write-Host ""

# 3. Testar conectividade basica
Write-Host "[3] Testando conectividade com o radio:" -ForegroundColor Yellow
$targetIP = "192.168.47.35"
Write-Host "  - Ping para $targetIP..." -NoNewline
$pingResult = Test-Connection -ComputerName $targetIP -Count 2 -Quiet
if ($pingResult) {
    Write-Host " OK" -ForegroundColor Green
} else {
    Write-Host " FALHOU" -ForegroundColor Red
}
Write-Host ""

# 4. Verificar portas UDP abertas (limitado no Windows)
Write-Host "[4] Verificando se porta UDP 161 esta acessivel:" -ForegroundColor Yellow
Write-Host "  (Nota: Windows nao tem teste nativo de UDP, usando workaround)" -ForegroundColor Gray

# Tentar criar socket UDP temporario
try {
    $udpClient = New-Object System.Net.Sockets.UdpClient
    $udpClient.Client.ReceiveTimeout = 1000
    $udpClient.Connect($targetIP, 161)
    Write-Host "  - Socket UDP criado com sucesso" -ForegroundColor Green
    $udpClient.Close()
} catch {
    Write-Host "  - Erro ao criar socket UDP: $($_.Exception.Message)" -ForegroundColor Red
}
Write-Host ""

# 5. Verificar se servico SNMP local esta instalado (nao necessario, mas informativo)
Write-Host "[5] Servico SNMP local (Windows):" -ForegroundColor Yellow
$snmpService = Get-Service -Name "SNMP" -ErrorAction SilentlyContinue
if ($snmpService) {
    Write-Host "  - Status: $($snmpService.Status)" -ForegroundColor Cyan
    Write-Host "  (Nota: Nao e necessario para cliente SNMP)" -ForegroundColor Gray
} else {
    Write-Host "  - Nao instalado (OK, nao e necessario)" -ForegroundColor Green
}
Write-Host ""

# 6. Recomendacoes
Write-Host "=== RECOMENDACOES ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Se o ping funciona mas SNMP nao:" -ForegroundColor Yellow
Write-Host "  1. Verifique o radio Ubiquiti em http://$targetIP" -ForegroundColor White
Write-Host "     - Services > SNMP > Enable" -ForegroundColor White
Write-Host "     - Community: publicRadionet" -ForegroundColor White
Write-Host "     - Allowed IPs: adicione o IP deste servidor ou deixe vazio" -ForegroundColor White
Write-Host ""
Write-Host "  2. Se o Firewall estiver ativo, crie regra de saida:" -ForegroundColor White
Write-Host "     New-NetFirewallRule -DisplayName 'SNMP Client' -Direction Outbound -Protocol UDP -RemotePort 161 -Action Allow" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Teste com snmpwalk (se tiver instalado):" -ForegroundColor White
Write-Host "     snmpwalk -v2c -c publicRadionet $targetIP" -ForegroundColor Gray
Write-Host ""
