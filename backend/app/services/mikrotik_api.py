from librouteros import connect
import asyncio

async def get_mikrotik_live_traffic(ip: str, user: str, password: str, interface: str, port: int = 8728):
    """
    Connects to Mikrotik API and gets live interface traffic.
    Returns (rx_mbps, tx_mbps) or None.
    Uses /interface/monitor-traffic which returns CURRENT bits-per-second.
    """
    def _fetch():
        try:
            # Connect
            api = connect(username=user, password=password, host=ip, port=port, timeout=5)
            
            # Request traffic for interface
            # cmd uses named arguments as keyword args in librouteros
            # /interface/monitor-traffic interface=<name> once
            items = list(api(cmd='/interface/monitor-traffic', interface=interface, once=True))
            
            api.close()
            
            if items:
                # Items is a list of dicts. We want first one.
                stats = items[0]
                # 'rx-bits-per-second' is Download (In)
                # 'tx-bits-per-second' is Upload (Out)
                rx_bps = int(stats.get('rx-bits-per-second', 0))
                tx_bps = int(stats.get('tx-bits-per-second', 0))
                
                # Convert to Mbps
                rx_mbps = rx_bps / 1_000_000
                tx_mbps = tx_bps / 1_000_000
                
                return (round(rx_mbps, 2), round(tx_mbps, 2))
            
            return None
        except Exception as e:
            print(f"[ERROR] Mikrotik API ({ip}): {e}")
            return None

    try:
        # librouteros block IO, so run in thread
        return await asyncio.to_thread(_fetch)
    except:
        return None
