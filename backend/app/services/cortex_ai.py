import asyncio
import math
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import select, func, or_, text, case
from backend.app.database import AsyncSessionLocal
from backend.app.models import Equipment, TrafficLog, Alert, Parameters, SignalLog
from loguru import logger

# --- CORTEX AI ENGINE v3.0 ---
# "Human-in-the-Loop & Adaptive Radio Physics"

class CortexAI:
    def __init__(self):
        self.insights: List[Dict[str, Any]] = []
        self.last_run = None
        self.is_running = False
        
        # Configuração Base
        self.config = {
            "enabled": True,
            "modules": {
                "security": True,
                "capacity": True,
                "performance": True,
                "radio_health": True,
                "energy": True
            },
            "thresholds": {
                "z_score_sensitivity": 3.0, 
                "predictive_window_minutes": 60,
                "default_bad_rssi": -74,
                "min_ccq_critical": 80
            }
        }

    async def get_config(self):
        """Carrega configurações do banco de dados para ajuste fino."""
        async with AsyncSessionLocal() as session:
            # 1. Carregar Estado Global
            res = await session.execute(select(Parameters).where(Parameters.key == 'cortex_enabled'))
            param = res.scalar_one_or_none()
            if param:
                self.config["enabled"] = (param.value.lower() == 'true')

            # 2. Carregar Threshold Global de Sinal
            res = await session.execute(select(Parameters).where(Parameters.key == 'cortex_signal_threshold'))
            param = res.scalar_one_or_none()
            if param:
                try:
                    self.config["thresholds"]["default_bad_rssi"] = int(param.value)
                except: pass

            return self.config

    async def toggle_cortex(self, enabled: bool):
        async with AsyncSessionLocal() as session:
            stmt = select(Parameters).where(Parameters.key == 'cortex_enabled')
            res = await session.execute(stmt)
            param = res.scalar_one_or_none()
            
            val_str = 'true' if enabled else 'false'
            if param:
                param.value = val_str
            else:
                session.add(Parameters(key='cortex_enabled', value=val_str))
            
            await session.commit()
            self.config["enabled"] = enabled
            return {"status": "success", "enabled": enabled}

    async def update_signal_settings(self, threshold: int):
        async with AsyncSessionLocal() as session:
            stmt = select(Parameters).where(Parameters.key == 'cortex_signal_threshold')
            res = await session.execute(stmt)
            param = res.scalar_one_or_none()
            
            if param:
                param.value = str(threshold)
            else:
                session.add(Parameters(key='cortex_signal_threshold', value=str(threshold)))
            
            await session.commit()
            self.config["thresholds"]["default_bad_rssi"] = threshold
            return {"status": "success", "threshold": threshold}

    async def get_pending_signals(self):
        """
        Retorna rádios que estão com sinal pior que o threshold global 
        e que ainda NÃO foram marcados como 'normais' (não possuem accepted_rssi).
        """
        threshold = self.config["thresholds"]["default_bad_rssi"]
        pending = []
        
        async with AsyncSessionLocal() as session:
            # Buscando equipamentos do tipo rádio/station com sinal pior (maior numericament se negativo, ex: -75 < -70)
            # Na verdade RSSI é negativo, então "pior que -70" significa valores como -71, -75, etc.
            # SQL: signal_dbm <= threshold (ex: -75 <= -70)
            stmt = select(Equipment).where(
                Equipment.equipment_type == 'station',
                Equipment.signal_dbm.isnot(None),
                Equipment.signal_dbm <= threshold
            )
            res = await session.execute(stmt)
            equipments = res.scalars().all()
            
            for eq in equipments:
                overrides = eq.ai_overrides or {}
                # Se já aceitou este sinal ou um pior, não é mais pendente
                if 'accepted_rssi' in overrides:
                    if eq.signal_dbm >= overrides['accepted_rssi']:
                        continue
                
                pending.append({
                    "id": eq.id,
                    "name": eq.name,
                    "signal": eq.signal_dbm,
                    "threshold": threshold,
                    "brand": eq.brand
                })
        
        return pending

    async def teach_cortex(self, equipment_id: int, parameter: str, value: Any):
        """
        Sistema Human-in-the-Loop: Ensina a IA a aceitar padrões específicos por equipamento.
        Exemplo: cortex.teach_cortex(10, 'accepted_rssi', -78)
        """
        async with AsyncSessionLocal() as session:
            eq = await session.get(Equipment, equipment_id)
            if not eq:
                return {"error": "Equipamento não encontrado"}
            
            # Inicializa se estiver nulo
            if eq.ai_overrides is None:
                eq.ai_overrides = {}
            
            # Garante que é um dicionário e atualiza
            current_overrides = dict(eq.ai_overrides)
            current_overrides[parameter] = value
            eq.ai_overrides = current_overrides
            
            logger.info(f"[CORTEX LEARN] 🎓 Aprendizado aplicado ao ID {equipment_id}: {parameter} = {value}")
            await session.commit()
            return {"status": "learned", "equipment": eq.name, parameter: value}

    async def run_analysis(self):
        await self.get_config()
        
        if not self.config["enabled"]:
            return []

        logger.info("[CORTEX] 🧠 Iniciando Análise Cognitiva v3.0 (Adaptive Engine)...")
        self.is_running = True
        self.insights = [] 

        try:
            async with AsyncSessionLocal() as session:
                # 1. Performance (Flapping & Topologia)
                if self.config["modules"]["performance"]:
                    res = await self._analyze_performance_topology(session)
                    self.insights.extend(res)
                
                # 2. Capacidade Preditiva
                if self.config["modules"]["capacity"]:
                    res = await self._analyze_capacity_predictive(session)
                    self.insights.extend(res)
                
                # 3. Segurança e Anomalias
                if self.config["modules"]["security"]:
                    res = await self._analyze_security_anomaly(session)
                    self.insights.extend(res)

                # 4. Saúde de Rádio (RF Adaptive) - NOVO v3.0
                if self.config["modules"]["radio_health"]:
                    res = await self._analyze_radio_health(session)
                    self.insights.extend(res)

                # 5. Saúde de Energia (Proativo) - NOVO v3.1
                if self.config["modules"].get("energy"):
                    res = await self._analyze_energy_health(session)
                    self.insights.extend(res)

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

    # --- MÓDULO 4: SAÚDE DE RÁDIO ADAPTATIVA (v3.0) ---
    async def _analyze_radio_health(self, session):
        """
        Analisa a saúde física do link RF usando Baselines Históricos e Overrides Humanos.
        Evita falsos positivos em áreas remotas.
        """
        insights = []
        now = datetime.utcnow()
        window_15m = now - timedelta(minutes=15)
        window_7d = now - timedelta(days=7)

        # 1. Coleta de dados com Média Histórica (Baseline)
        baseline_cte = select(
            SignalLog.equipment_id,
            func.avg(SignalLog.rssi).label("avg_rssi_7d"),
            func.avg(SignalLog.ccq).label("avg_ccq_7d")
        ).where(SignalLog.timestamp >= window_7d)\
         .group_by(SignalLog.equipment_id).cte("baseline_rf")

        current_data_stmt = select(
            Equipment.id,
            Equipment.name,
            Equipment.ai_overrides,
            func.avg(SignalLog.rssi).label("curr_rssi"),
            func.avg(SignalLog.ccq).label("curr_ccq"),
            baseline_cte.c.avg_rssi_7d,
            baseline_cte.c.avg_ccq_7d
        ).join(SignalLog, Equipment.id == SignalLog.equipment_id)\
         .outerjoin(baseline_cte, Equipment.id == baseline_cte.c.equipment_id)\
         .where(SignalLog.timestamp >= window_15m)\
         .group_by(Equipment.id, Equipment.name, Equipment.ai_overrides, baseline_cte.c.avg_rssi_7d, baseline_cte.c.avg_ccq_7d)

        res = await session.execute(current_data_stmt)
        radios = res.all()

        for eq_id, name, overrides, curr_rssi, curr_ccq, base_rssi, base_ccq in radios:
            curr_rssi = curr_rssi or 0
            curr_ccq = curr_ccq or 0
            base_rssi = base_rssi or curr_rssi
            overrides = overrides or {}
            limit_rssi = overrides.get('accepted_rssi', self.config["thresholds"]["default_bad_rssi"])
            
            # 1. Degradação Crítica
            if curr_rssi < limit_rssi and (curr_rssi < (base_rssi - 3)):
                insights.append({
                    "type": "performance", "severity": "critical",
                    "title": f"Degradação de Sinal: {name}",
                    "description": f"Sinal atual ({int(curr_rssi)}dBm) está abaixo do aceitável e degradou em relação à média histórica ({int(base_rssi)}dBm).",
                    "recommendation": "Verificar se há novas obstruções (árvores/construções) ou se o rádio desalinou.",
                    "equipment_name": name,
                    "equipment_id": eq_id,
                    "learning_key": "accepted_rssi",
                    "learning_value": int(curr_rssi),
                    "timestamp": datetime.now()
                })
                continue

            # 2. Interferência / Ruído
            if curr_rssi > -70 and curr_ccq < self.config["thresholds"]["min_ccq_critical"]:
                insights.append({
                    "type": "performance", "severity": "warning",
                    "title": f"Interferência em {name}",
                    "description": f"O sinal está excelente ({int(curr_rssi)}dBm), mas a qualidade (CCQ) caiu para {int(curr_ccq)}%.",
                    "recommendation": "Troque a frequência do rádio ou verifique ruído externo próximo à torre.",
                    "equipment_name": name,
                    "equipment_id": eq_id,
                    "timestamp": datetime.now()
                })

            # 3. Sinal Baixo / Obstrução
            elif curr_rssi <= limit_rssi and curr_ccq < self.config["thresholds"]["min_ccq_critical"]:
                 insights.append({
                    "type": "performance", "severity": "warning",
                    "title": f"Link Precário: {name}",
                    "description": f"Sinal e Qualidade estão baixos simultaneamente (RSSI: {int(curr_rssi)} / CCQ: {int(curr_ccq)}%).",
                    "recommendation": "Considere trocar o equipamento por um de maior ganho ou verificar visada.",
                    "equipment_name": name,
                    "equipment_id": eq_id,
                    "timestamp": datetime.now()
                })

        return insights

        return insights

    # --- MÓDULOS LEGACY RE-ATUALIZADOS (v2.0 adaptados) ---

    async def _analyze_performance_topology(self, session):
        insights = []
        one_hour_ago = datetime.utcnow() - timedelta(hours=1)
        stmt = select(
            Alert.device_name, 
            Equipment.id,
            Equipment.parent_id,
            func.count(Alert.id).label("count")
        ).join(Equipment, Alert.device_name == Equipment.name)\
         .where(Alert.timestamp >= one_hour_ago)\
         .where(or_(Alert.message.ilike("%offline%"), Alert.message.ilike("%restabelecida%")))\
         .group_by(Equipment.id, Alert.device_name, Equipment.parent_id)
        
        res = await session.execute(stmt)
        flappers = res.all()
        for name, eq_id, parent_id, count in flappers:
            if count >= 3:
                severity = "critical" if count > 10 else "warning"
                insights.append({
                    "type": "performance", "severity": severity,
                    "title": f"Instabilidade Crônica: {name}",
                    "description": f"Detectados {count} eventos de queda/retorno na última hora.",
                    "recommendation": "Verifique nobreak/fontes.",
                    "timestamp": datetime.now(),
                    "equipment_name": name,
                    "equipment_id": eq_id
                })
        return insights

    async def _analyze_capacity_predictive(self, session):
        insights = []
        window = datetime.utcnow() - timedelta(hours=1)
        stmt = select(Equipment.id, Equipment.name, Equipment.max_traffic_in, TrafficLog.in_mbps, TrafficLog.timestamp)\
         .join(TrafficLog, Equipment.id == TrafficLog.equipment_id)\
         .where(TrafficLog.timestamp >= window)\
         .order_by(TrafficLog.timestamp.asc())
        res = await session.execute(stmt)
        data_points = res.all()
        
        equipment_data = {}
        for eq_id, name, max_in, val, ts in data_points:
            if name not in equipment_data: equipment_data[name] = {"id": eq_id, "max": max_in, "values": []}
            equipment_data[name]["values"].append(val or 0.0)

        for name, data in equipment_data.items():
            values = data["values"]
            limit = data["max"] or 0
            if limit == 0 or len(values) < 10: continue
            avg_usage = sum(values) / len(values)
            if avg_usage > (limit * 0.90):
                insights.append({
                    "type": "capacity", "severity": "critical", 
                    "title": f"Saturação Iminente: {name}", 
                    "description": f"Link operando em {int((avg_usage/limit)*100)}% da capacidade.", 
                    "recommendation": "Upgrade urgente.", 
                    "equipment_name": name, 
                    "equipment_id": data["id"],
                    "timestamp": datetime.now()
                })
            else:
                growth = values[-1] - values[0]
                if growth > (limit * 0.20):
                    rate = growth / 60 
                    if rate > 0:
                        time_to_saturation = (limit - values[-1]) / rate
                        if 0 < time_to_saturation < 120:
                            insights.append({
                                "type": "capacity", "severity": "warning", 
                                "title": f"Tendência de Esgotamento: {name}", 
                                "description": f"Previsão de saturação em ~{int(time_to_saturation)} minutos.", 
                                "recommendation": "Balanceamento preventivo.", 
                                "equipment_name": name, 
                                "equipment_id": data["id"],
                                "timestamp": datetime.now()
                            })
        return insights

    async def _analyze_security_anomaly(self, session):
        insights = []
        stmt = select(Equipment.id, Equipment.name, Equipment.equipment_type, Equipment.is_panel, Equipment.ai_overrides, func.avg(TrafficLog.out_mbps), func.stddev(TrafficLog.out_mbps), func.max(TrafficLog.out_mbps), func.avg(TrafficLog.in_mbps))\
         .join(TrafficLog, Equipment.id == TrafficLog.equipment_id)\
         .where(TrafficLog.timestamp >= datetime.utcnow() - timedelta(hours=24))\
         .group_by(Equipment.id, Equipment.name, Equipment.equipment_type, Equipment.is_panel, Equipment.ai_overrides)
        try:
            res = await session.execute(stmt)
            stats = res.all()
        except Exception: return []

        for eq_id, name, eq_type, is_panel, overrides, avg_up, std_up, peak_up, avg_down in stats:
            avg_up, std_up, peak_up, avg_down = avg_up or 0, std_up or 1, peak_up or 0, avg_down or 0
            overrides = overrides or {}
            
            # Se já ensinamos a IA a ignorar anomalias de tráfego aqui
            if overrides.get('bypass_traffic_anomaly'):
                continue

            eq_type_lower = (eq_type or "station").lower()
            is_infra = eq_type_lower in ['transmitter', 'ap', 'radio', 'switch', 'router'] or is_panel
            
            if std_up > 0:
                # Se for infra, tolerância é muito maior (10x em vez de 3x)
                sensitivity = 10.0 if is_infra else self.config["thresholds"]["z_score_sensitivity"]
                z = (peak_up - avg_up) / std_up
                if z > sensitivity and peak_up > 20:
                    insights.append({
                        "type": "security", "severity": "info", 
                        "title": f"Comportamento Fora do Padrão: {name}", 
                        "description": f"Pico de Upload {round(z, 1)}x acima do normal.", 
                        "timestamp": datetime.now(), 
                        "recommendation": "Monitore se persistir.", 
                        "equipment_name": name,
                        "equipment_id": eq_id,
                        "learning_key": "bypass_traffic_anomaly"
                    })

            if not is_infra and peak_up > 40 and avg_down < 10: 
                insights.append({
                    "type": "security", "severity": "warning", 
                    "title": f"Anomalia de Tráfego: {name}", 
                    "description": f"O equipamento apresenta fluxo assimétrico: Saída (TX) em {int(peak_up)}Mbps e Entrada (RX) próxima a zero. Isso pode indicar um ataque DoS ou Vírus se esta for a interface WAN, ou um download intenso se for a interface LAN.", 
                    "recommendation": "Verificar se o tráfego é legítimo. Se for uma estação (CPE), ignore se estiver monitorando a porta Ethernet.", 
                    "timestamp": datetime.now(), 
                    "equipment_name": name,
                    "equipment_id": eq_id,
                    "learning_key": "bypass_traffic_anomaly"
                })

        return insights

    # --- MÓDULO 5: SAÚDE DE ENERGIA E PREDITIVA (v3.1) ---
    async def _analyze_energy_health(self, session):
        """
        Analisa a estabilidade de energia (Voltagem) e prevê queda de bateria.
        Utiliza a nova base de dados calibrada.
        """
        insights = []
        now = datetime.utcnow()
        window_1h = now - timedelta(hours=1)
        
        # 1. Coleta dados de energia e thresholds
        stmt = select(
            Equipment.id,
            Equipment.name,
            Equipment.voltage,
            Equipment.min_voltage_threshold,
            func.avg(TrafficLog.voltage).label("avg_volt_1h")
        ).join(TrafficLog, Equipment.id == TrafficLog.equipment_id)\
         .where(TrafficLog.timestamp >= window_1h)\
         .where(Equipment.voltage != None)\
         .group_by(Equipment.id, Equipment.name, Equipment.voltage, Equipment.min_voltage_threshold)
        
        try:
            res = await session.execute(stmt)
            data = res.all()
            
            for eq_id, name, last_v, threshold, avg_v in data:
                if not last_v or not avg_v or not threshold: continue
                
                # Regra Proativa: Se a voltagem caiu significativamente em relação à média (descarga)
                # E está chegando na zona de perigo (threshold + margem de 1V)
                safety_margin = 1.0
                if last_v < (avg_v - 0.15) and last_v < (threshold + safety_margin):
                    insights.append({
                        "type": "performance", "severity": "warning",
                        "title": f"Tendência de Queda de Energia: {name}",
                        "description": f"O equipamento apresenta queda proativa de voltagem ({last_v}V), operando abaixo da média recente ({round(avg_v, 2)}V). Possível operação em bateria.",
                        "recommendation": "Verificar status da rede AC e autonomia das baterias.",
                        "equipment_name": name,
                        "equipment_id": eq_id,
                        "timestamp": datetime.now()
                    })
                
                # Regra Crítica: Bateria quase no fim (abaixo do threshold + 0.3V)
                elif last_v < (threshold + 0.3):
                    insights.append({
                        "type": "performance", "severity": "critical",
                        "title": f"Energia Crítica: {name}",
                        "description": f"Baterias em nível crítico ({last_v}V), muito próximas ao limite de desligamento ({threshold}V).",
                        "recommendation": "Ação imediata necessária (Gerador ou substituição de baterias).",
                        "equipment_name": name,
                        "equipment_id": eq_id,
                        "timestamp": datetime.now()
                    })

        except Exception as e:
            logger.error(f"[CORTEX] Erro no módulo de energia: {e}")
        
        return insights

cortex_engine = CortexAI()
