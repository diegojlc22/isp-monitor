"""
Security Audit Service - Weekly Scanner for Network Vulnerabilities
Checks for default passwords, outdated firmware, and open dangerous ports.
"""

import asyncio
from datetime import datetime
from sqlalchemy import select
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment, Parameters, Insight
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
        # Get all online priority equipment
        result = await session.execute(
            select(Equipment.id, Equipment.ip, Equipment.name, Equipment.ssh_port, Equipment.brand)
            .where(Equipment.is_online == True, Equipment.is_priority == True)  # Only priority equipment
        )
        devices = result.all()
        
        for eq_id, ip, name, ssh_port, brand in devices:
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
                # Salvar no banco como Insight
                session.add(Insight(
                    insight_type='security',
                    severity='warning',
                    equipment_id=eq_id,
                    title=f"Vulnerabilidades em {name}",
                    message=" \n".join(device_issues),
                    recommendation="Recomendamos alterar senhas padrões e fechar portas não utilizadas."
                ))
        
        await session.commit()
    
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
                    'whatsapp_enabled', 'whatsapp_target', 'whatsapp_target_group'
                ]))
            )
            config = {p.key: p.value for p in params_res.scalars().all()}
        
        await send_notification(
            message=message,
            telegram_token=config.get('telegram_token'),
            telegram_chat_id=config.get('telegram_chat_id'),
            telegram_enabled=config.get('telegram_enabled', 'true').lower() == 'true',
            whatsapp_enabled=config.get('whatsapp_enabled', 'false').lower() == 'true',
            whatsapp_target=config.get('whatsapp_target'),
            whatsapp_target_group=config.get('whatsapp_target_group')
        )
        
        logger.info(f"[SECURITY AUDIT] Report sent: {len(vulnerabilities)} vulnerable devices")
    else:
        logger.info("[SECURITY AUDIT] No vulnerabilities found!")

async def security_audit_job():
    """Background job that runs security audit at configured interval"""
    while True:
        try:
            # Check last run
            now = datetime.now()
            should_run = False
            
            async with AsyncSessionLocal() as session:
                res = await session.execute(
                    select(Parameters).where(Parameters.key == "security_audit_last_run")
                )
                last_run_param = res.scalar_one_or_none()
                
                res_days = await session.execute(
                    select(Parameters).where(Parameters.key == "security_audit_days")
                )
                days_param = res_days.scalar_one_or_none()
                days = int(days_param.value) if days_param else 7

                if not last_run_param:
                    should_run = True
                else:
                    last_run = datetime.fromisoformat(last_run_param.value)
                    if (now - last_run).total_seconds() >= days * 86400:
                        should_run = True

            if should_run:
                await run_security_audit()
                async with AsyncSessionLocal() as session:
                    # Update last run
                    res = await session.execute(
                        select(Parameters).where(Parameters.key == "security_audit_last_run")
                    )
                    param = res.scalar_one_or_none()
                    if not param:
                        session.add(Parameters(key="security_audit_last_run", value=now.isoformat()))
                    else:
                        param.value = now.isoformat()
                    await session.commit()
            else:
                logger.info("[SECURITY] Audit skipped (already ran recently).")

        except Exception as e:
            logger.error(f"[SECURITY AUDIT] Error: {e}")
        
        await asyncio.sleep(3600)  # Check every hour

if __name__ == "__main__":
    asyncio.run(run_security_audit())
