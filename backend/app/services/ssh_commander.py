"""
SSH Commander with Connection Pooling and Optimizations
"""
import paramiko
import asyncio
import logging
from typing import Tuple, Dict, List
from collections import defaultdict
import time

logger = logging.getLogger(__name__)

class SSHConnectionPool:
    def __init__(self, max_connections_per_host: int = 5, pool_ttl: int = 300):
        self.max_conn = max_connections_per_host
        self.ttl = pool_ttl # Seconds to keep connection alive
        # Structure: host -> List[{'client': SSHClient, 'created': timestamp, 'lock': Lock}]
        # But sharing paramiko client across threads requires care. 
        # Since we use run_in_executor, we treat client as exclusive to a task while in use.
        self._pool: Dict[str, List[paramiko.SSHClient]] = defaultdict(list)
        self._lock = asyncio.Lock()
    
    async def get_connection(self, ip: str, user: str, password: str, port: int, timeout: int) -> paramiko.SSHClient:
        async with self._lock:
            # Try to get valid existing connection
            while self._pool[ip]:
                client = self._pool[ip].pop()
                if self._is_alive(client):
                    return client
                else:
                    client.close()
        
        # Create new connection (outside lock to allow concurrency)
        return await self._create_connection(ip, user, password, port, timeout)

    async def release_connection(self, ip: str, client: paramiko.SSHClient):
        if not self._is_alive(client):
            client.close()
            return

        async with self._lock:
            if len(self._pool[ip]) < self.max_conn:
                self._pool[ip].append(client)
            else:
                client.close()

    def _is_alive(self, client: paramiko.SSHClient) -> bool:
        try:
            transport = client.get_transport()
            return transport and transport.is_active()
        except:
            return False

    async def _create_connection(self, ip, user, password, port, timeout) -> paramiko.SSHClient:
        def connect():
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                ip, 
                port=port, 
                username=user, 
                password=password, 
                timeout=timeout,
                banner_timeout=timeout
            )
            return ssh
        
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, connect)

    async def close_all(self):
        async with self._lock:
            for ip in self._pool:
                for client in self._pool[ip]:
                    client.close()
                self._pool[ip].clear()

# Global Pool
ssh_pool = SSHConnectionPool()

async def reboot_device(
    ip: str, 
    user: str, 
    password: str, 
    port: int = 22,
    max_retries: int = 3,
    timeout: int = 10
) -> Tuple[bool, str]:
    
    for attempt in range(max_retries):
        client = None
        try:
            client = await ssh_pool.get_connection(ip, user, password, port, timeout)
            
            loop = asyncio.get_running_loop()
            
            # --- Command Execution ---
            # Try RouterOS reboot first
            stdin, stdout, stderr = client.exec_command("/system reboot")
            
            # Non-blocking read needed? paramiko exec_command returns file-like objects.
            # Reading them is blocking.
            
            # Helper to read output safely
            async def read_stream(stream):
                return await loop.run_in_executor(None, stream.read)

            try:
                out = await asyncio.wait_for(read_stream(stdout), timeout=5)
                err = await asyncio.wait_for(read_stream(stderr), timeout=5)
                
                if err and b"bad command name" in err.lower():
                     # Fallback to Linux
                     stdin, stdout, stderr = client.exec_command("sudo reboot")
            except asyncio.TimeoutError:
                # Timeout is often expected on reboot
                pass
            
            # Return to pool? No, connection is likely dead after reboot.
            client.close()
            return True, f"[OK] Reboot command sent (attempt {attempt+1})"

        except Exception as e:
            if client:
                client.close() # Don't return broken client to pool
            
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
                continue
            return False, f"[ERROR] Failed to reboot: {e}"

    return False, "Max retries exceeded"

async def execute_command(
    ip: str,
    user: str,
    password: str,
    command: str,
    port: int = 22,
    timeout: int = 10
) -> Tuple[bool, str, str]:
    
    client = None
    try:
        client = await ssh_pool.get_connection(ip, user, password, port, timeout)
        
        loop = asyncio.get_running_loop()
        # Blocking exec
        stdin, stdout, stderr = client.exec_command(command)
        
        async def read_stream(stream):
            return await loop.run_in_executor(None, stream.read)
            
        out_bytes = await asyncio.wait_for(read_stream(stdout), timeout=timeout)
        err_bytes = await asyncio.wait_for(read_stream(stderr), timeout=timeout)
        
        await ssh_pool.release_connection(ip, client)
        
        return True, out_bytes.decode('utf-8', errors='ignore'), err_bytes.decode('utf-8', errors='ignore')

    except Exception as e:
        if client:
            client.close()
        return False, "", str(e)
