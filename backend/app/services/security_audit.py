"""
Security Audit Service - Weekly Scanner for Network Vulnerabilities
Checks for default passwords, outdated firmware, and open dangerous ports.
"""

import asyncio
from datetime import datetime
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment, Parameters
from backend.app.services.snmp import _snmp_get
from backend.app.services.notifier import send_notification
from loguru import logger

# Default credentials to check
DEFAULT_CREDENTIALS = [
    ("ubnt", "ubnt"),
    ("admin", "admin"),
    ("admin", ""),
    ("root", "root"),
    ("admin", "password"),
    ("admin", "1234"),
]

async def check_default_password(ip: str, ssh_port: int = 22) -> bool:
    """Try to connect with default credentials"""
    try:
        import paramiko
        for username, password in DEFAULT_CREDENTIALS:
            try:
                client = paramiko.SSHClient()
                client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                client.connect(ip, port=ssh_port, username=username, password=password, timeout=3, look_for_keys=False, allow_agent=False)
                client.close()
                logger.warning(f"[SECURITY] Default credentials found on {ip}: {username}/{password}")
                return True
            except paramiko.AuthenticationException:
                continue
            except Exception:
                continue
        return False
    except Exception as e:
        logger.debug(f"[SECURITY] Could not check SSH on {ip}: {e}")
        return False

async def check_snmp_default_community(ip: str) -> list:
    """Check if device responds to common default SNMP communities"""
    vulnerable_communities = []
    common_communities = ["public", "private", "admin", "community"]
    
    for community in common_communities:
        try:
            result = await _snmp_get(ip, community, ["1.3.6.1.2.1.1.1.0"], timeout=2.0)
            if result:
                vulnerable_communities.append(community)
        except:
            continue
    
    return vulnerable_communities

async def check_open_dangerous_ports(ip: str) -> list:
    """Check for dangerous open ports (Telnet, HTTP admin, etc)"""
    dangerous_ports = {
        23: "Telnet (Insecure)",
        80: "HTTP (Unencrypted Admin)",
        8080: "HTTP Alt (Unencrypted)",
        21: "FTP (Insecure)",
        8728: "Mikrotik API (Unencrypted)"
    }
    
    open_ports = []
    for port, description in dangerous_ports.items():
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(ip, port),
                timeout=2.0
            )
            writer.close()
            await writer.wait_closed()
            open_ports.append(f"Port {port} ({description})")
            logger.warning(f"[SECURITY] {ip} has open port {port}: {description}")
        except:
            continue
    
    return open_ports

async def run_security_audit():
    """Main security audit job - runs weekly"""
    logger.info("[SECURITY AUDIT] Starting weekly security scan...")
    
    vulnerabilities = []
    
    async with AsyncSessionLocal() as session:
        # Get all online equipment
        result = await session.execute(
            select(Equipment.ip, Equipment.name, Equipment.ssh_port, Equipment.brand)
            .where(Equipment.is_online == True)
        )
        devices = result.all()
        
        for ip, name, ssh_port, brand in devices:
            device_issues = []
            
            # 1. Check default SSH passwords
            if await check_default_password(ip, ssh_port or 22):
                device_issues.append("⚠️ Senha padrão detectada (SSH)")
            
            # 2. Check default SNMP communities
            vuln_communities = await check_snmp_default_community(ip)
            if vuln_communities:
                device_issues.append(f"⚠️ SNMP com community padrão: {', '.join(vuln_communities)}")
            
            # 3. Check dangerous open ports
            open_ports = await check_open_dangerous_ports(ip)
            if open_ports:
                device_issues.append(f"⚠️ Portas inseguras abertas: {', '.join(open_ports)}")
            
            if device_issues:
                vulnerabilities.append({
                    "name": name,
                    "ip": ip,
                    "issues": device_issues
                })
    
    # Send report if vulnerabilities found
    if vulnerabilities:
        message = "🔒 *RELATÓRIO DE SEGURANÇA SEMANAL*\n\n"
        message += f"📅 Data: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n"
        message += f"⚠️ Encontrados {len(vulnerabilities)} dispositivos com problemas:\n\n"
        
        for vuln in vulnerabilities[:10]:  # Limit to 10 to avoid huge messages
            message += f"*{vuln['name']}* ({vuln['ip']})\n"
            for issue in vuln['issues']:
                message += f"  • {issue}\n"
            message += "\n"
        
        if len(vulnerabilities) > 10:
            message += f"... e mais {len(vulnerabilities) - 10} dispositivos.\n"
        
        message += "\n🛡️ Recomendação: Altere senhas padrão e desabilite serviços inseguros."
        
        # Get notification config
        async with AsyncSessionLocal() as session:
            params_res = await session.execute(
                select(Parameters).where(Parameters.key.in_([
                    'telegram_token', 'telegram_chat_id', 'telegram_enabled',
                    'whatsapp_enabled', 'whatsapp_target'
                ]))
            )
            config = {p.key: p.value for p in params_res.scalars().all()}
        
        await send_notification(
            message=message,
            telegram_token=config.get('telegram_token'),
            telegram_chat_id=config.get('telegram_chat_id'),
            telegram_enabled=config.get('telegram_enabled', 'true').lower() == 'true',
            whatsapp_enabled=config.get('whatsapp_enabled', 'false').lower() == 'true',
            whatsapp_target=config.get('whatsapp_target')
        )
        
        logger.info(f"[SECURITY AUDIT] Report sent: {len(vulnerabilities)} vulnerable devices")
    else:
        logger.info("[SECURITY AUDIT] No vulnerabilities found!")

async def security_audit_job():
    """Background job that runs security audit weekly"""
    while True:
        try:
            await run_security_audit()
        except Exception as e:
            logger.error(f"[SECURITY AUDIT] Error: {e}")
        
        # Wait 7 days (604800 seconds)
        await asyncio.sleep(604800)

if __name__ == "__main__":
    asyncio.run(run_security_audit())
