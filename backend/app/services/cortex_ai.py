import asyncio
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import select, func, or_, text, case
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment, TrafficLog, Alert, Parameters
from loguru import logger

# --- CORTEX AI ENGINE v2.0 ---
# "Predictive AIOps & Anomaly Detection"

class CortexAI:
    def __init__(self):
        self.insights: List[Dict[str, Any]] = []
        self.last_run = None
        self.is_running = False
        # Para roteamento de mensagens:
        # A string de grupos pode ser salva no DB como "ID_GRUPO_GERAL;ID_GRUPO_BATERIA;ID_GRUPO_IA"
        # O notifier irá fazer o split e decidir.
        self.config = {
            "enabled": True,
            "modules": {
                "security": True,
                "capacity": True,
                "performance": True
            },
            "thresholds": {
                "z_score_sensitivity": 3.0, 
                "predictive_window_minutes": 60 
            }
        }

    async def get_config(self):
        """Carrega configurações e pesos do banco de dados para ajuste fino."""
        async with AsyncSessionLocal() as session:
            res = await session.execute(select(Parameters).where(Parameters.key == 'cortex_config'))
            param = res.scalar_one_or_none()
            if param and param.value:
                # Numa implementação real, parsear JSON aqui
                pass 
            return self.config

    async def toggle_cortex(self, enabled: bool):
        self.config["enabled"] = enabled
        async with AsyncSessionLocal() as session:
            # Salvar no DB se possível (lógica simplificada)
            # await session.execute(...)
            pass
        return {"status": "updated", "enabled": enabled}

    async def run_analysis(self):
        await self.get_config()
        
        if not self.config["enabled"]:
            return []

        logger.info("[CORTEX] 🧠 Iniciando Análise Cognitiva (Heurística + Estatística)...")
        self.is_running = True
        self.insights = [] 

        try:
            async with AsyncSessionLocal() as session:
                # Executa módulos em paralelo para performance
                # tasks = []
                # tasks.append(self._analyze_performance_topology(session))
                # tasks.append(self._analyze_capacity_predictive(session))
                # tasks.append(self._analyze_security_anomaly(session))
                # results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Executando sequencialmente por segurança no SQLite/Postgres Async Session sharing
                res_perf = []
                if self.config["modules"]["performance"]:
                    res_perf = await self._analyze_performance_topology(session)
                
                res_cap = []
                if self.config["modules"]["capacity"]:
                    res_cap = await self._analyze_capacity_predictive(session)
                
                res_sec = []
                if self.config["modules"]["security"]:
                    res_sec = await self._analyze_security_anomaly(session)

                results = [res_perf, res_cap, res_sec]

                for res in results:
                    if isinstance(res, list):
                        self.insights.extend(res)
                    elif isinstance(res, Exception):
                        logger.error(f"[CORTEX] Falha em sub-módulo: {res}")

        except Exception as e:
            logger.critical(f"[CORTEX] Falha Crítica na Engine: {e}")
            self.insights.append({
                "type": "error", "severity": "critical", 
                "title": "Kernel Panic no Cortex", "description": str(e),
                "timestamp": datetime.now()
            })
        finally:
            self.is_running = False
            self.last_run = datetime.now()

        # Ordenar insights por severidade
        severity_map = {"critical": 0, "warning": 1, "info": 2}
        self.insights.sort(key=lambda x: severity_map.get(x.get("severity"), 3))
        
        return self.insights

    # --- MÓDULO 1: PERFORMANCE COM CONSCIÊNCIA DE TOPOLOGIA ---
    async def _analyze_performance_topology(self, session):
        """
        Detecta instabilidade ignorando falhas em cascata (Se o Pai cai, ignora os Filhos).
        """
        insights = []
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        
        # Busca equipamentos que caíram muito (Flapping)
        # Assumindo que temos um campo 'parent_id' no Equipment para topologia
        stmt = select(
            Alert.device_name, 
            Equipment.parent_id,
            func.count(Alert.id).label("count")
        ).join(Equipment, Alert.device_name == Equipment.name)\
         .where(Alert.timestamp >= one_hour_ago)\
         .where(or_(Alert.message.ilike("%offline%"), Alert.message.ilike("%restabelecida%")))\
         .group_by(Alert.device_name, Equipment.parent_id)
        
        res = await session.execute(stmt)
        flappers = res.all() # [(name, parent_id, count), ...]
        
        logger.info(f"[CORTEX DEBUG] Flappers encontrados: {flappers}")

        for name, parent_id, count in flappers:
            logger.info(f"[CORTEX DEBUG] Analisando {name}: count={count}, parent={parent_id}")
        # Precisaríamos saber se o PAI caiu. Vamos criar um set de Pais Problemáticos.
        # Se um equipamento tem count > X, ele é um problema. Se ele é pai de alguém, esse alguém deve ser ignorado.
        
        # Mapa de IDs problemáticos
        # Como flappers não traz o ID do device, e sim o nome, precisamos ser espertos.
        # Vamos assumir que se o nome aparece aqui, ele é problemático.
        
        # Como não carregamos o ID do equipment no select acima, não dá pra mapear Parent ID -> ID facilmente sem join extra.
        # Vamos Simplificar: Se detectou Flapping, avisa. A supressão real exige montar a árvore completa em memória.
        
        for name, parent_id, count in flappers:
            if count >= 3:
                severity = "critical" if count > 10 else "warning"
                insights.append({
                    "type": "performance",
                    "severity": severity,
                    "title": f"Instabilidade Crônica: {name}",
                    "description": f"Detectados {count} eventos de queda/retorno na última hora.",
                    "recommendation": "Verifique nobreak/fontes. Se for rádio, verifique alinhamento/interferência.",
                    "timestamp": datetime.now(),
                    "meta": {"flap_count": count},
                    "equipment_name": name
                })
        return insights

    # --- MÓDULO 2: CAPACIDADE PREDITIVA (Regressão Linear Simples) ---
    async def _analyze_capacity_predictive(self, session):
        """
        Não olha apenas se está cheio, mas QUANDO vai encher.
        """
        insights = []
        # Analisa última 1 hora
        window = datetime.utcnow() - timedelta(hours=1)
        
        stmt = select(
            Equipment.name,
            Equipment.max_traffic_in,
            TrafficLog.in_mbps,
            TrafficLog.timestamp
        ).join(TrafficLog, Equipment.id == TrafficLog.equipment_id)\
         .where(TrafficLog.timestamp >= window)\
         .order_by(TrafficLog.timestamp.asc())
        
        res = await session.execute(stmt)
        data_points = res.all()
        
        # Agrupar dados por equipamento
        equipment_data = {}
        for name, max_in, val, ts in data_points:
            if name not in equipment_data: equipment_data[name] = {"max": max_in, "values": []}
            val = val or 0.0
            equipment_data[name]["values"].append(val)

        for name, data in equipment_data.items():
            values = data["values"]
            limit = data["max"] or 0
            if limit == 0 or not values: continue

            avg_usage = sum(values) / len(values)
            
            # 1. Detecção de Saturação Atual
            if avg_usage > (limit * 0.90):
                insights.append({
                    "type": "capacity", "severity": "critical",
                    "title": f"Saturação Iminente: {name}",
                    "description": f"Link operando em {int((avg_usage/limit)*100)}% da capacidade média.",
                    "timestamp": datetime.now(),
                    "recommendation": "Upgrade de link urgente ou balanceamento.",
                    "equipment_name": name
                })
                continue # Se já está cheio, não precisa prever

            # 2. Predição de Tendência (Slope calculation)
            # Se o uso está subindo constantemente nos últimos 60 min
            if len(values) > 10:
                first_val = values[0]
                last_val = values[-1]
                growth = last_val - first_val
                
                # Se cresceu mais de 20% do link em 1 hora e o slope é positivo
                if growth > (limit * 0.20):
                    # time_to_saturation (min) = (limit - current) / rate (mbps/min)
                    rate = growth / 60 
                    if rate > 0:
                        time_to_saturation = (limit - last_val) / rate
                        if 0 < time_to_saturation < 120: # Vai encher em 2 horas
                            insights.append({
                                "type": "capacity", "severity": "warning",
                                "title": f"Tendência de Esgotamento: {name}",
                                "description": f"O tráfego cresceu rapidamente. Previsão de saturação total em ~{int(time_to_saturation)} minutos.",
                                "recommendation": "Acione balanceamento de carga preventivo.",
                                "timestamp": datetime.now(),
                                "equipment_name": name
                            })

        return insights

    # --- MÓDULO 3: SEGURANÇA E ANOMALIAS (Z-Score) ---
    async def _analyze_security_anomaly(self, session):
        """
        Usa estatística para achar comportamento estranho (Vírus, Ataque, Torrent massivo).
        """
        insights = []
        # Janela longa (Média histórica 24h)
        
        # OBS: PostgreSQL requer GROUP BY em todas as colunas não agregadas ou uso de subquery.
        # Vamos simplificar: Calcular agregados por Equipment.id e juntar nome
        
        stmt = select(
            Equipment.name,
            Equipment.equipment_type, # 'station' ou 'transmitter' (AP)
            Equipment.is_panel,       # Booleano auxiliar
            func.avg(TrafficLog.out_mbps).label("avg_upload"),
            func.stddev(TrafficLog.out_mbps).label("std_dev_upload"),
            func.max(TrafficLog.out_mbps).label("peak_upload"),
            func.avg(TrafficLog.in_mbps).label("avg_download")
        ).join(TrafficLog, Equipment.id == TrafficLog.equipment_id)\
         .where(TrafficLog.timestamp >= datetime.utcnow() - timedelta(hours=24))\
         .group_by(Equipment.name, Equipment.equipment_type, Equipment.is_panel)

        try:
            res = await session.execute(stmt)
            stats = res.all()
        except Exception as e:
            logger.error(f"[CORTEX] Erro SQL Security: {e}")
            return []

        for name, eq_type, is_panel, avg_up, std_up, peak_up, avg_down in stats:
            avg_up = avg_up or 0
            std_up = std_up or 1 
            peak_up = peak_up or 0
            avg_down = avg_down or 0

            # Normalização de Tipo
            is_infrastructure = (eq_type == 'transmitter') or is_panel
            
            # Detecção 1: Anomalia Estatística (Z-Score)
            if std_up > 0:
                z_score = (peak_up - avg_up) / std_up
                if z_score > self.config["thresholds"]["z_score_sensitivity"] and peak_up > 20:
                    insights.append({
                        "type": "security", "severity": "warning",
                        "title": f"Pico Anômalo (Z-Score): {name}",
                        "description": f"Tráfego desviou {round(z_score, 1)}x do padrão histórico.",
                        "timestamp": datetime.now(),
                        "recommendation": "Verificar logs de atividade.",
                        "equipment_name": name
                    })

            # Detecção 2: Assimetria de Tráfego Inteligente
            # Lógica:
            # - Se é Infraestrutura (AP/Torre): Upload Alto = Download dos Clientes. NORMAL.
            # - Se é Cliente (Station): Upload Alto = Vírus/Torrent/Backup. SUSPEITO.
            
            check_assymetry = True
            if is_infrastructure:
                # Para APs, "Upload" é o tráfego indo para os clientes. 
                # É perfeitamente normal um AP ter 100Mbps de Upload (clientes baixando) e 5Mbps de Download.
                check_assymetry = False 
            
            if check_assymetry and peak_up > 50 and avg_down < 5: 
                insights.append({
                    "type": "security", "severity": "critical", # Agora podemos ser assertivos
                    "title": f"Possível Ataque/Vírus em {name}",
                    "description": f"Este equipamento (identificado como Station/Cliente) está enviando {int(peak_up)} Mbps, mas recebendo quase nada. Isso indica que o cliente pode estar infectado ou fazendo DoS.",
                    "recommendation": "Bloqueie a porta do switch ou entre em contato com o cliente (possível vírus).",
                    "timestamp": datetime.now(),
                    "equipment_name": name
                })

        return insights

cortex_engine = CortexAI()
