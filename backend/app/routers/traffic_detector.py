"""
Endpoint para auto-detectar interface com tráfego
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import asyncio
import time

router = APIRouter()

class DetectTrafficRequest(BaseModel):
    ip: str
    community: str = "publicRadionet"
    port: int = 161

@router.post("/detect-traffic-interface")
async def detect_traffic_interface(request: DetectTrafficRequest):
    """
    Auto-detecta qual interface tem tráfego real.
    Testa todas as interfaces e retorna a que tem mais tráfego.
    """
    from backend.app.services.snmp import get_snmp_interfaces, get_snmp_interface_traffic
    
    try:
        # 1. Listar interfaces
        interfaces = await get_snmp_interfaces(request.ip, request.community, request.port)
        if not interfaces:
            raise HTTPException(
                status_code=404, 
                detail="Nenhuma interface encontrada via SNMP. Verifique a community e se o SNMP está habilitado."
            )
        
        # 2. Testar tráfego em cada interface (paralelo para ser mais rápido)
        async def test_interface(iface):
            idx = iface['index']
            name = iface['name']
            
            try:
                # Primeira leitura
                traffic1 = await get_snmp_interface_traffic(request.ip, request.community, request.port, idx)
                if not traffic1:
                    return None
                
                in_bytes1, out_bytes1 = traffic1
                time1 = time.time()
                
                # Aguardar 3 segundos (mais rápido que 5s)
                await asyncio.sleep(3)
                
                # Segunda leitura
                traffic2 = await get_snmp_interface_traffic(request.ip, request.community, request.port, idx)
                if not traffic2:
                    return None
                
                in_bytes2, out_bytes2 = traffic2
                time2 = time.time()
                
                # Calcular Mbps
                dt = time2 - time1
                delta_in = max(0, in_bytes2 - in_bytes1)
                delta_out = max(0, out_bytes2 - out_bytes1)
                
                mbps_in = round((delta_in * 8) / (dt * 1_000_000), 2)
                mbps_out = round((delta_out * 8) / (dt * 1_000_000), 2)
                total_mbps = mbps_in + mbps_out
                
                if total_mbps > 0:
                    return {
                        'index': idx,
                        'name': name,
                        'in_mbps': mbps_in,
                        'out_mbps': mbps_out,
                        'total_mbps': total_mbps
                    }
                return None
                
            except Exception as e:
                return None
        
        # Testar todas as interfaces em paralelo (com limite de concorrência)
        sem = asyncio.Semaphore(10)  # Máximo 10 interfaces simultâneas
        
        async def test_with_semaphore(iface):
            async with sem:
                return await test_interface(iface)
        
        tasks = [test_with_semaphore(iface) for iface in interfaces]
        results = await asyncio.gather(*tasks)
        
        # Filtrar resultados válidos
        valid_results = [r for r in results if r is not None]
        
        if not valid_results:
            return {
                "success": False,
                "message": "Nenhuma interface com tráfego detectada no momento",
                "total_interfaces": len(interfaces),
                "interfaces_tested": len(interfaces),
                "suggestion": "Verifique se há tráfego real passando pelo equipamento"
            }
        
        # Ordenar por tráfego total (maior primeiro)
        valid_results.sort(key=lambda x: x['total_mbps'], reverse=True)
        
        # Retornar a melhor interface
        best = valid_results[0]
        
        return {
            "success": True,
            "recommended_interface": best['index'],
            "interface_name": best['name'],
            "traffic_in": best['in_mbps'],
            "traffic_out": best['out_mbps'],
            "total_traffic": best['total_mbps'],
            "all_interfaces_with_traffic": valid_results,
            "total_interfaces": len(interfaces),
            "interfaces_with_traffic": len(valid_results),
            "message": f"Interface {best['index']} ({best['name']}) detectada com {best['total_mbps']} Mbps total"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro na detecção: {str(e)}")
