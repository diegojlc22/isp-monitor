import asyncio
import networkx as nx
from backend.app.models import Equipment, NetworkLink, Tower
from backend.app.database import AsyncSessionLocal
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from loguru import logger
from backend.app.services.wireless_snmp import get_snmp_value, get_snmp_walk_first, detect_equipment_name
import math

class TopologyBuilder:
    def __init__(self):
        self.db = AsyncSessionLocal()
        self.graph = nx.Graph()

    async def build(self):
        """
        Reconstrói a topologia da rede baseada em LLDP/CDP/MAC Table.
        """
        logger.info("[TOPOLOGY] Iniciando descoberta de topologia...")
        try:
            # 1. Carregar todos os equipamentos
            result = await self.db.execute(select(Equipment).options(selectinload(Equipment.tower)))
            equipments = result.scalars().all()
            
            if not equipments:
                logger.warning("[TOPOLOGY] Nenhum equipamento para analisar.")
                return

            # Map IP/MAC -> Equipment ID
            eq_map = {e.ip: e for e in equipments if e.ip}
            mac_map = {e.mac_address: e for e in equipments if e.mac_address} # Se tiver MAC cadastrado, ótimo

            # 2. Descobrir vizinhos (Crawler)
            new_links = []
            
            for eq in equipments:
                if not eq.ip or not eq.is_online:
                    continue
                    
                logger.debug(f"[TOPOLOGY] Analisando vizinhos de {eq.name} ({eq.ip})")
                
                # Tentar extrair vizinhos via SNMP LLDP
                neighbors = await self.get_lldp_neighbors(eq)
                
                if neighbors:
                    logger.info(f"[TOPOLOGY] {eq.name} vê: {neighbors}")
                    
                    for neigh_key in neighbors:
                        # neigh_key pode ser IP ou MAC
                        target_eq = None
                        
                        # Tentar achar por IP
                        if neigh_key in eq_map:
                            target_eq = eq_map[neigh_key]
                        # Tentar achar por MAC (TODO: converter string format)
                        # elif neigh_key in mac_map: target_eq = mac_map[neigh_key]
                        
                        if target_eq and target_eq.id != eq.id:
                            # Link encontrado!
                            # Adicionar a lista (evitar duplicatas A->B e B->A)
                            link = tuple(sorted((eq.id, target_eq.id)))
                            new_links.append(link)
                            
            # 3. Atualizar Banco de Dados (Links)
            # Remove links antigos automaticos (se tiver flag, por enquanto deleta tudo wifi)
            # Para não destruir links manuais, talvez devêssemos ter um tipo "auto".
            
            if new_links:
                unique_links = set(new_links)
                logger.success(f"[TOPOLOGY] Encontrados {len(unique_links)} links ativos.")
                
                # Exemplo simples: Criar links lógicos se não existirem
                for src_id, dst_id in unique_links:
                    await self.ensure_link(src_id, dst_id)
            else:
                logger.info("[TOPOLOGY] Nenhum link LLDP encontrado.")

        except Exception as e:
            logger.error(f"[TOPOLOGY] Erro fatal: {e}")
            import traceback
            traceback.print_exc()
        finally:
            await self.db.close()

    async def get_lldp_neighbors(self, eq: Equipment):
        """
        Busca vizinhos via SNMP (LLDP-MIB ou Mikrotik MNDP).
        Retorna lista de IPs dos vizinhos.
        """
        neighbors_data = []
        try:
            from backend.app.services.wireless_snmp import get_neighbors_data
            
            raw_data = await get_neighbors_data(eq.ip, eq.brand, eq.snmp_community, eq.snmp_port)
            neighbors_data = [n['ip'] for n in raw_data if n.get('ip')]
            
        except Exception as e:
            logger.warning(f"Erro lendo vizinhos de {eq.ip}: {e}")
            
        return neighbors_data

    async def ensure_link(self, eq_id_1, eq_id_2):
        try:
            # Buscar equipamentos para verificar suas torres
            stmt = select(Equipment).where(Equipment.id.in_([eq_id_1, eq_id_2]))
            result = await self.db.execute(stmt)
            eqs = result.scalars().all()
            
            if len(eqs) < 2: return
            
            # Identificar quem é quem (para garantir acesso correto via índices se necessário, mas aqui só precisamos dos objetos)
            e1 = eqs[0]
            e2 = eqs[1]
            
            # Se estão na mesma torre ou algum não tem torre, ignorar
            if not e1.tower_id or not e2.tower_id: return
            if e1.tower_id == e2.tower_id: return
            
            t1_id = e1.tower_id
            t2_id = e2.tower_id
            
            # Verificar se já existe link (em qualquer direção)
            stmt_link = select(NetworkLink).where(
                ((NetworkLink.source_tower_id == t1_id) & (NetworkLink.target_tower_id == t2_id)) |
                ((NetworkLink.source_tower_id == t2_id) & (NetworkLink.target_tower_id == t1_id))
            )
            existing = await self.db.execute(stmt_link)
            if existing.scalar():
                return # Já existe
                
            # Criar novo Link
            logger.success(f"[TOPOLOGY] DETECTADO NOVO LINK: Torre {t1_id} <-> Torre {t2_id} (Via {e1.name} e {e2.name})")
            new_link = NetworkLink(source_tower_id=t1_id, target_tower_id=t2_id, type="wireless")
            self.db.add(new_link)
            await self.db.commit()
            
        except Exception as e:
            logger.error(f"Erro criando link automático: {e}")

async def run_topology_discovery():
    builder = TopologyBuilder()
    await builder.build()
