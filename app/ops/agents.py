from __future__ import annotations

from typing import Any, Dict, List, Tuple


SEVERITY_RANK = {"low": 0, "medium": 1, "high": 2, "critical": 3}


def _num(value: Any):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _text(incident: Dict[str, Any], asset: Dict[str, Any] | None) -> str:
    chunks = [incident.get("title", ""), incident.get("description", "")]
    if asset:
        chunks.extend([asset.get("name", ""), asset.get("asset_type", "")])
    return " ".join(chunks).lower()


class IntakeTriageAgent:
    name = "intake_triage"

    def run(self, incident: Dict[str, Any], asset: Dict[str, Any] | None) -> Dict[str, Any]:
        text = _text(incident, asset)
        measurements = incident.get("measurements", {}) or {}
        missing = []
        if not asset:
            missing.append("activo asociado")
        if not measurements:
            missing.append("mediciones")
        if "temper" in text and not any(k in measurements for k in ("temperature_c", "temp_c", "temperature")):
            missing.append("temperatura medida")
        if any(k in text for k in ("corriente", "amper", "sobrecarga")) and not any(k in measurements for k in ("current_a", "amps", "current")):
            missing.append("corriente medida")
        return {
            "summary": "Ingreso estructurado y listo para triage." if not missing else "Ingreso válido con evidencia técnica pendiente.",
            "missing_evidence": missing,
            "confidence": 0.95 if not missing else 0.74,
            "requires_human_approval": False,
        }


class SafetyAgent:
    name = "safety_guard"

    def run(self, incident: Dict[str, Any], asset: Dict[str, Any] | None) -> Dict[str, Any]:
        text = _text(incident, asset)
        m = incident.get("measurements", {}) or {}
        flags: List[str] = []
        recommended_severity = incident.get("severity", "medium")

        critical_words = ("humo", "fuego", "arco", "chispa", "cable expuesto", "olor a quemado", "explosion")
        if any(w in text for w in critical_words):
            flags.append("Indicador de riesgo eléctrico/térmico inmediato reportado.")
            recommended_severity = "critical"

        temp = _num(m.get("temperature_c", m.get("temp_c", m.get("temperature"))))
        if temp is not None:
            if temp >= 90:
                flags.append(f"Temperatura reportada {temp:.1f} °C: requiere inspección inmediata y criterio de desenergización segura.")
                recommended_severity = "critical"
            elif temp >= 70:
                flags.append(f"Temperatura reportada {temp:.1f} °C: condición térmica anormal que requiere revisión prioritaria.")
                if SEVERITY_RANK.get(recommended_severity, 1) < SEVERITY_RANK["high"]:
                    recommended_severity = "high"

        current = _num(m.get("current_a", m.get("amps", m.get("current"))))
        rated = _num((asset or {}).get("rated_current_a"))
        if current is not None and rated and rated > 0:
            ratio = current / rated
            if ratio >= 1.25:
                flags.append(f"Corriente {current:.1f} A = {ratio:.2f}× la nominal registrada ({rated:.1f} A).")
                recommended_severity = "critical" if ratio >= 1.5 else "high"

        safety_boundary = [
            "No puentear protecciones ni enclavamientos para diagnosticar.",
            "Aplicar bloqueo/etiquetado y verificar ausencia de tensión antes de intervenir potencia.",
            "Toda maniobra de energización o cambio de protección requiere aprobación humana competente.",
        ]
        return {
            "flags": flags,
            "recommended_severity": recommended_severity,
            "safety_boundary": safety_boundary,
            "confidence": 0.94 if flags else 0.82,
            "requires_human_approval": True,
        }


class DiagnosticAgent:
    name = "diagnostic_assistant"

    def run(self, incident: Dict[str, Any], asset: Dict[str, Any] | None) -> Dict[str, Any]:
        text = _text(incident, asset)
        hypotheses: List[Dict[str, Any]] = []

        if "contactor" in text or "calent" in text:
            hypotheses.extend([
                {"hypothesis": "Resistencia de contacto elevada por apriete deficiente, superficie degradada o contacto fatigado.", "check": "Comparar temperatura entre fases, caída de tensión por polo y torque de terminales con equipo desenergizado."},
                {"hypothesis": "Sobrecarga o desbalance de corriente aguas abajo.", "check": "Medir corrientes RMS por fase y compararlas con placa y ajuste de protección."},
            ])
        if "compres" in text:
            hypotheses.extend([
                {"hypothesis": "Condición mecánica/operativa elevando demanda del motor.", "check": "Correlacionar corriente, presión, temperatura y estado de válvula/descarga."},
                {"hypothesis": "Secuencia de arranque o transición defectuosa.", "check": "Revisar temporización, enclavamientos y estados de contactores/relés sin forzar maniobras."},
            ])
        if "banco" in text or "capacitor" in text or "kvar" in text:
            hypotheses.extend([
                {"hypothesis": "Etapa de compensación no conectando o contactor de capacitor degradado.", "check": "Verificar corriente por etapa, estado de fusibles/contactores y secuencia del regulador."},
                {"hypothesis": "Compensación no adecuada a la condición real de carga o presencia de armónicos.", "check": "Registrar FP, THD y perfil de carga antes de modificar etapas o añadir reactancias."},
            ])
        if "winche" in text or "guinche" in text or "izaje" in text:
            hypotheses.extend([
                {"hypothesis": "Falla de enclavamiento, freno o lógica de inversión.", "check": "Probar continuidad de mando y secuencia de enclavamientos con potencia aislada antes de prueba funcional controlada."},
            ])
        if not hypotheses:
            hypotheses = [
                {"hypothesis": "La evidencia disponible no permite aislar una causa única.", "check": "Capturar placa, corriente por fase, tensión, temperatura y estado de protecciones antes de reemplazar componentes."}
            ]

        return {
            "hypotheses": hypotheses[:5],
            "diagnosis_is_not_final": True,
            "confidence": 0.78 if len(hypotheses) > 1 else 0.62,
            "requires_human_approval": True,
        }


class WorkPlanningAgent:
    name = "work_planner"

    def run(self, incident: Dict[str, Any], asset: Dict[str, Any] | None, safety: Dict[str, Any], diagnosis: Dict[str, Any]) -> Dict[str, Any]:
        steps = [
            "Confirmar identificación del activo, placa y condición reportada.",
            "Registrar estado inicial y mediciones sin alterar ajustes.",
            "Aplicar aislamiento seguro antes de inspección física de potencia.",
        ]
        for item in diagnosis.get("hypotheses", [])[:3]:
            steps.append(item["check"])
        steps.extend([
            "Documentar hallazgo con mediciones y evidencia fotográfica.",
            "Emitir decisión técnica: corregir, reemplazar, observar o escalar.",
            "Solo energizar para prueba funcional con autorización y condiciones de seguridad verificadas.",
        ])
        priority = safety.get("recommended_severity", incident.get("severity", "medium"))
        return {
            "title": f"Inspección y diagnóstico — {incident.get('title', 'incidente')}",
            "priority": priority,
            "steps": steps,
            "safety_notes": safety.get("safety_boundary", []),
            "requires_human_approval": True,
            "confidence": 0.9,
        }


class SupervisorAgent:
    name = "supervisor"

    def run(self, incident: Dict[str, Any], triage: Dict[str, Any], safety: Dict[str, Any], diagnosis: Dict[str, Any], plan: Dict[str, Any]) -> Dict[str, Any]:
        severity = safety.get("recommended_severity", incident.get("severity", "medium"))
        missing = triage.get("missing_evidence", [])
        confidence = min(
            float(triage.get("confidence", 0.5)),
            float(safety.get("confidence", 0.5)),
            float(diagnosis.get("confidence", 0.5)),
            float(plan.get("confidence", 0.5)),
        )
        status = "awaiting_evidence" if missing else "triaged"
        return {
            "severity": severity,
            "incident_status": status,
            "decision": "Generar orden de trabajo para revisión humana.",
            "missing_evidence": missing,
            "confidence_floor": round(confidence, 2),
            "requires_human_approval": True,
            "release_gate": "No ejecutar cambios de protección, cableado o energización de prueba sin aprobación humana.",
        }


def run_agent_stack(incident: Dict[str, Any], asset: Dict[str, Any] | None) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    triage = IntakeTriageAgent().run(incident, asset)
    safety = SafetyAgent().run(incident, asset)
    diagnosis = DiagnosticAgent().run(incident, asset)
    plan = WorkPlanningAgent().run(incident, asset, safety, diagnosis)
    supervisor = SupervisorAgent().run(incident, triage, safety, diagnosis, plan)
    bundle = {
        "triage": triage,
        "safety": safety,
        "diagnosis": diagnosis,
        "work_plan": plan,
        "supervisor": supervisor,
    }
    runs = [
        {"agent_name": IntakeTriageAgent.name, "output": triage},
        {"agent_name": SafetyAgent.name, "output": safety},
        {"agent_name": DiagnosticAgent.name, "output": diagnosis},
        {"agent_name": WorkPlanningAgent.name, "output": plan},
        {"agent_name": SupervisorAgent.name, "output": supervisor},
    ]
    return bundle, runs
