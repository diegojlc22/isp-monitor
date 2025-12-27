
import socket
import logging
import subprocess
import ctypes
import os
import sys

# Configure logger
logger = logging.getLogger("network_diagnostics")
logger.setLevel(logging.INFO)

def is_admin():
    """Check if the script is running with administrative privileges."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def check_port_availability(host: str, port: int) -> bool:
    """
    Check if a port is available (not in use).
    Returns True if AVAILABLE (bind successful), False if IN USE.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((host, port))
            return True # Port is free
        except OSError:
            return False # Port is busy

def check_firewall_rule(rule_name: str, port: int) -> bool:
    """
    Check if a Windows Firewall rule exists for the specified port.
    Returns True if exists, False otherwise.
    Note: Requires reliable parsing of PowerShell output, which can be tricky.
    A simpler check is just to attempt to CREATE it and catch the 'already exists' error 
    or use idempotent commands, but we want to be 'intelligent'.
    """
    try:
        # PowerShell command to find rule by DisplayName and LocalPort
        cmd = f"Get-NetFirewallRule -DisplayName '{rule_name}' -ErrorAction SilentlyContinue"
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True
        )
        # If exit code is 0 and we have output, rule likely exists.
        return result.returncode == 0 and len(result.stdout.strip()) > 0
    except Exception as e:
        logger.error(f"Failed to check firewall rule: {e}")
        return False

def create_firewall_rule(rule_name: str, port: int):
    """
    Creates a Windows Firewall rule to update inbound traffic on the specified port.
    Requires Admin privileges.
    """
    if not is_admin():
        logger.warning(f"⚠️ Cannot create firewall rule '{rule_name}': Admin privileges required.")
        print(f"\n[NETWORK AUTO-FIX] ❌ Failed to create firewall rule for port {port}. Please run the application as Administrator.\n")
        return False

    logger.info(f"Attempting to create firewall rule '{rule_name}' for port {port}...")
    
    # PowerShell command to create the rule
    # New-NetFirewallRule -DisplayName "ISP Monitor Backend" -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow
    cmd = (
        f"New-NetFirewallRule -DisplayName '{rule_name}' "
        f"-Direction Inbound -LocalPort {port} -Protocol TCP -Action Allow"
    )
    
    try:
        result = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Firewall rule '{rule_name}' created successfully.")
            print(f"\n[NETWORK AUTO-FIX] ✅ Windows Firewall rule created for port {port}. Remote access enabled.\n")
            return True
        else:
            logger.error(f"Failed to create firewall rule. Output: {result.stderr}")
            return False
    except Exception as e:
        logger.error(f"Error executing firewall creation command: {e}")
        return False

def run_diagnostics(host: str = "0.0.0.0", port: int = 8000):
    """
    Main entry point for network diagnostics.
    """
    print("----------------------------------------------------------------")
    print("🧠 ISP MONITOR INTELLIGENCE: Running Network Diagnostics...")
    
    # 1. Check Port Availability
    # careful: if we run this INSIDE the backend app, the port might effectively be 'in use' by us soon 
    # or if we are restarting, the old process might still hold it.
    # Actually, uvicorn checks this too. This is more useful for 'pre-flight' checks or external diagnostics.
    # For now, we will focus on the FIREWALL which is the #1 silent killer of connectivity.
    
    # 2. Check Firewall
    rule_name = "ISP Backend Rule"
    if check_firewall_rule(rule_name, port):
        logger.info(f"Firewall rule '{rule_name}' detected. ✅")
        print(f"   [OK] Firewall Rule '{rule_name}' exists.")
    else:
        logger.warning(f"Firewall rule '{rule_name}' NOT detected. Attempting Auto-Fix... 🔧")
        print(f"   [WARN] Firewall Rule '{rule_name}' missig. Attempting Auto-Fix...")
        success = create_firewall_rule(rule_name, port)
        if not success:
             print("   [FAIL] Could not create firewall rule. Backend might not be accessible from mobile.")

    print("----------------------------------------------------------------")

if __name__ == "__main__":
    run_diagnostics()
