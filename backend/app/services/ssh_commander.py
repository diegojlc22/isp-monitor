"""
SSH Commander with Retry and Better Error Handling
"""
import paramiko
import asyncio
from typing import Tuple

async def reboot_device(
    ip: str, 
    user: str, 
    password: str, 
    port: int = 22,
    max_retries: int = 3,
    timeout: int = 10
) -> Tuple[bool, str]:
    """
    Reboot device via SSH with retry mechanism
    
    Args:
        ip: Device IP address
        user: SSH username
        password: SSH password
        port: SSH port (default 22)
        max_retries: Maximum number of retry attempts (default 3)
        timeout: Connection timeout in seconds (default 10)
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    
    async def _reboot_attempt(attempt: int) -> Tuple[bool, str]:
        """Single reboot attempt"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Connect with timeout
            loop = asyncio.get_running_loop()
            await loop.run_in_executor(
                None,
                lambda: ssh.connect(
                    ip, 
                    port=port, 
                    username=user, 
                    password=password, 
                    timeout=timeout,
                    banner_timeout=timeout
                )
            )
            
            # Try Mikrotik/RouterOS command first
            stdin, stdout, stderr = ssh.exec_command("/system reboot")
            
            # Read output with timeout
            try:
                output = await asyncio.wait_for(
                    loop.run_in_executor(None, stdout.read),
                    timeout=5
                )
                error = await asyncio.wait_for(
                    loop.run_in_executor(None, stderr.read),
                    timeout=5
                )
                
                # If RouterOS command failed, try Linux reboot
                if error and b"bad command name" in error.lower():
                    stdin, stdout, stderr = ssh.exec_command("sudo reboot")
                    await asyncio.wait_for(
                        loop.run_in_executor(None, stdout.read),
                        timeout=5
                    )
                
            except asyncio.TimeoutError:
                # Timeout is OK - device is rebooting
                pass
            
            ssh.close()
            return True, f"✅ Reboot command sent successfully (attempt {attempt + 1})"
            
        except paramiko.AuthenticationException:
            return False, "❌ Authentication failed - check username/password"
        
        except paramiko.SSHException as e:
            if attempt < max_retries - 1:
                # Retry on SSH errors
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
                return None, str(e)  # Signal retry
            return False, f"❌ SSH error after {attempt + 1} attempts: {str(e)}"
        
        except asyncio.TimeoutError:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                return None, "Timeout"  # Signal retry
            return False, f"❌ Connection timeout after {attempt + 1} attempts"
        
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                return None, str(e)  # Signal retry
            return False, f"❌ Error after {attempt + 1} attempts: {str(e)}"
    
    # Retry loop
    for attempt in range(max_retries):
        success, message = await _reboot_attempt(attempt)
        
        if success is not None:  # Got a definitive result
            return success, message
        
        # None means retry
        print(f"⚠️ Retry {attempt + 1}/{max_retries} for {ip}: {message}")
    
    # Should never reach here, but just in case
    return False, f"❌ Failed after {max_retries} attempts"


async def execute_command(
    ip: str,
    user: str,
    password: str,
    command: str,
    port: int = 22,
    timeout: int = 10
) -> Tuple[bool, str, str]:
    """
    Execute arbitrary SSH command
    
    Returns:
        Tuple of (success: bool, stdout: str, stderr: str)
    """
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        loop = asyncio.get_running_loop()
        await loop.run_in_executor(
            None,
            lambda: ssh.connect(
                ip, 
                port=port, 
                username=user, 
                password=password, 
                timeout=timeout
            )
        )
        
        stdin, stdout, stderr = ssh.exec_command(command)
        
        output = await asyncio.wait_for(
            loop.run_in_executor(None, stdout.read),
            timeout=timeout
        )
        error = await asyncio.wait_for(
            loop.run_in_executor(None, stderr.read),
            timeout=timeout
        )
        
        ssh.close()
        
        return True, output.decode('utf-8', errors='ignore'), error.decode('utf-8', errors='ignore')
        
    except Exception as e:
        return False, "", str(e)
