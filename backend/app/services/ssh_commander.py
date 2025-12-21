import paramiko
import asyncio

def _reboot_sync(ip, user, password, port=22):
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(ip, port=port, username=user, password=password, timeout=5)
        # Mikrotik / Linux reboot command
        stdin, stdout, stderr = ssh.exec_command("/system reboot")
        # For Linux it would be 'sudo reboot' but assuming Mikrotik/RouterOS here
        # If it's a Linux server we might need 'reboot'. 
        # But 'system reboot' is RouterOS specific.
        # Let's try flexible command or just system reboot for now as per Context.
        
        # Read output to ensure command was sent
        stdout.read()
        ssh.close()
        return True, "Reboot command sent"
    except Exception as e:
        return False, str(e)

async def reboot_device(ip: str, user: str, passw: str, port: int = 22):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _reboot_sync(ip, user, passw, port))
