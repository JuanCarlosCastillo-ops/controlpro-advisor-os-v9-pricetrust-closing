from __future__ import annotations
from datetime import datetime, timezone
from math import sqrt
from typing import Any, Dict, List

from .models import ComponentRequirement, EngineeringPack, ProjectIntake
from .pricing import decide_prices, generate_rfq_message, summarize_market, load_canonical_components, load_starter_profiles, priceguard_methodology
from .cad import single_line_cad_svg, control_ladder_cad_svg, panel_layout_cad_svg, terminal_schedule, wire_schedule, drawio_xml
from app.integrations.config import integration_status

VERSION = "14.0-mathtrust-pro"
PRODUCT = "ControlPro Advisor OS V14 MathTrust Pro"


def example_intake() -> Dict[str, Any]:
    return ProjectIntake().model_dump()


def _round(value: float, digits: int = 2) -> float:
    return round(float(value), digits)


def _estimate_flc(i: ProjectIntake) -> float:
    if i.full_load_amps and i.full_load_amps > 0:
        return float(i.full_load_amps)
    watts = i.motor_power_hp * 746
    if i.phases == 3:
        return watts / (sqrt(3) * i.voltage * i.efficiency * i.power_factor)
    return watts / (i.voltage * i.efficiency * i.power_factor)


def _conductor_size_awg(current: float, distance_m: float) -> str:
    thresholds = [
        (15, "#14 AWG Cu"), (20, "#12 AWG Cu"), (30, "#10 AWG Cu"),
        (45, "#8 AWG Cu"), (65, "#6 AWG Cu"), (85, "#4 AWG Cu"),
        (115, "#2 AWG Cu"), (150, "1/0 AWG Cu"), (200, "3/0 AWG Cu"),
    ]
    adjusted = current * (1.08 if distance_m > 30 else 1.0) * (1.12 if distance_m > 75 else 1.0)
    for limit, size in thresholds:
        if adjusted <= limit:
            return size
    return "Requiere cálculo dedicado de conductor"


def _breaker_size(current: float) -> int:
    standard = [15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90, 100, 110, 125, 150, 175, 200, 225, 250, 300, 350, 400, 500, 600, 700, 800, 1000, 1200]
    target = max(15, current * 1.75)
    return next((std for std in standard if std >= target), standard[-1])


def _overload_setting(current: float, service_factor: float) -> float:
    multiplier = 1.25 if service_factor >= 1.15 else 1.15
    return round(current * multiplier, 1)


def _voltage_drop_percent(current: float, voltage: float, distance_m: float, phases: int) -> float:
    route_factor = 1.732 if phases == 3 else 2.0
    proxy_resistance_per_m = 0.00082
    vd = route_factor * current * distance_m * proxy_resistance_per_m
    return max(0.1, round((vd / voltage) * 100, 2))



def _machine_type(i: ProjectIntake) -> str:
    text = f"{i.application} {i.load_type} {i.project_name} {i.user_notes}".lower()
    if any(w in text for w in ["guinche", "winche", "hoist", "izaje", "elevador", "polipasto"]):
        return "hoist"
    if any(w in text for w in ["compresor", "compressor", "aire comprimido"]):
        return "compressor"
    if any(w in text for w in ["bomba", "pump", "sumergible", "centrífuga", "centrifuga"]):
        return "pump"
    if any(w in text for w in ["banda", "transportadora", "conveyor", "cinta"]):
        return "conveyor"
    if any(w in text for w in ["ventilador", "fan", "extractor"]):
        return "fan"
    return "general_motor"


def _machine_context(i: ProjectIntake) -> Dict[str, Any]:
    mt = _machine_type(i)
    contexts = {
        "hoist": {
            "label": "Guinche / izaje",
            "safety_gate": "Seguridad de izaje",
            "safety_fix": "Confirmar freno, finales de carrera, paro de emergencia, enclavamientos y prueba sin carga/con carga supervisada.",
            "checks": ["freno", "finales de carrera", "E-Stop", "enclavamientos", "prueba con carga"],
            "vfd_note": "En izaje exige coordinación de freno, rampas, finales, E-Stop y validación de carga suspendida.",
            "terminal_labels": {"cmd1": "SUBIR", "cmd2": "BAJAR", "di1": "FWD/UP", "di2": "REV/DOWN", "limit": "LS-UP/LS-DN", "aux": "BRK"},
            "risks": [
                ("Movimiento simultáneo subir/bajar", "Alta", "Enclavamiento lógico, permisos VFD y prueba funcional."),
                ("Sobre-recorrido de carga", "Alta", "Finales superior/inferior y prueba supervisada."),
                ("Freno mal seleccionado o secuenciado", "Alta", "Confirmar placa del freno y lógica de liberación."),
            ],
            "field_steps": [
                ("Freno", "Placa/tensión/corriente del freno y lógica de liberación.", "El guinche no se trata como motor común."),
                ("Finales de carrera", "Ubicación mecánica, accionamiento y redundancia si aplica.", "Evita sobre-recorrido y riesgo de carga."),
            ],
            "checklists": {
                "taller": ["Continuidad", "Torque/ajuste", "E-Stop", "Finales", "Freno", "Rampas VFD", "Prueba sin carga", "Rotulado"],
                "campo": ["Bloqueo/etiquetado", "Verificación tensión", "Sentido de giro", "Freno", "Finales", "Prueba con carga supervisada", "Firma de entrega"],
                "fallas_comunes": ["No arranca: revisar E-Stop/permisivos/VFD", "Freno no libera: verificar tensión/rectificador/secuencia", "Se pasa de carrera: revisar finales y parámetros", "Alarma VFD: leer código antes de resetear"],
            },
        },
        "compressor": {
            "label": "Compresor de aire",
            "safety_gate": "Seguridad de compresor",
            "safety_fix": "Confirmar presostato, unloader/descarga, válvula de alivio, ventilación, temperatura y protección por sobrecarga.",
            "checks": ["presostato", "unloader", "válvula de alivio", "ventilación", "temperatura", "duty cycle"],
            "vfd_note": "En compresores el VFD se justifica por rampa, control de presión, menor golpe mecánico y diagnóstico; validar compatibilidad con unloader/presostato.",
            "terminal_labels": {"cmd1": "MARCHA", "cmd2": "PARO/AUTO", "di1": "RUN", "di2": "RESET/AUTO", "limit": "PRESOSTATO/TERM", "aux": "RUN"},
            "risks": [
                ("Arranques frecuentes y calentamiento", "Alta", "Validar ciclos/hora, ventilación, protección térmica y rampa."),
                ("Control de presión incompleto", "Alta", "Confirmar presostato, válvula de alivio y lógica de paro por presión."),
                ("Descarga/unloader no considerada", "Media", "Verificar sistema de descarga antes de seleccionar arranque."),
            ],
            "field_steps": [
                ("Sistema de presión", "Presostato, válvula de alivio, tanque, drenajes y setpoints.", "Evita sobrepresión y arranques erráticos."),
                ("Descarga/unloader", "Confirmar si el compresor arranca cargado o descargado.", "Define torque, rampa y tipo de arranque."),
            ],
            "checklists": {
                "taller": ["Continuidad", "Torque/ajuste", "E-Stop", "Presostato", "Señal RUN/FAULT", "Ventilación VFD", "Rotulado"],
                "campo": ["Bloqueo/etiquetado", "Tensión real", "Sentido de giro", "Presión de corte/arranque", "Temperatura", "Prueba de paro por falla", "Firma de entrega"],
                "fallas_comunes": ["No arranca: revisar presostato/E-Stop/VFD", "Dispara térmico: revisar carga, ventilación y rampa", "No alcanza presión: revisar mecánica/fugas", "Cicla muy rápido: revisar tanque/presostato/unloader"],
            },
        },
        "pump": {
            "label": "Bomba",
            "safety_gate": "Protección hidráulica",
            "safety_fix": "Confirmar protección contra trabajo en seco, nivel/presión, válvulas, cebado y golpe de ariete.",
            "checks": ["nivel", "presión", "trabajo en seco", "válvulas", "cebad/flujo"],
            "vfd_note": "En bombas el VFD se justifica por control de presión/caudal, ahorro y arranque suave; validar caudal mínimo y curva.",
            "terminal_labels": {"cmd1": "MARCHA", "cmd2": "AUTO/MAN", "di1": "RUN", "di2": "AUTO", "limit": "NIVEL/PRES", "aux": "RUN"},
            "risks": [
                ("Trabajo en seco", "Alta", "Agregar sensor de nivel/flujo o protección dedicada."),
                ("Cavitación o bajo caudal", "Media", "Verificar curva de bomba, válvulas y condiciones de succión."),
                ("Golpe de ariete", "Media", "Usar rampa/valvulado adecuado y pruebas de presión."),
            ],
            "field_steps": [("Hidráulica", "Nivel, presión, válvulas, succión/descarga y sentido de giro.", "La protección eléctrica no corrige fallas hidráulicas.")],
            "checklists": {
                "taller": ["Continuidad", "Torque/ajuste", "E-Stop", "Entradas nivel/presión", "Señal RUN/FAULT", "Rotulado"],
                "campo": ["Bloqueo/etiquetado", "Tensión real", "Sentido de giro", "Nivel/flujo", "Presión", "Prueba automática/manual", "Firma de entrega"],
                "fallas_comunes": ["No arranca: revisar nivel/presión/E-Stop", "Trabaja en seco: bloquear y revisar sensor", "Cavita: revisar succión", "Dispara protección: revisar carga/obstrucción"],
            },
        },
        "conveyor": {
            "label": "Banda transportadora",
            "safety_gate": "Seguridad de banda",
            "safety_fix": "Confirmar guardas, cable de paro, sensores de desalineación/atasco y señalización.",
            "checks": ["guardas", "pull-cord", "desalineación", "atasco", "E-Stop"],
            "vfd_note": "En bandas el VFD se justifica por rampa, velocidad y menor estrés; validar guardas y paros de emergencia distribuidos.",
            "terminal_labels": {"cmd1": "MARCHA", "cmd2": "PARO", "di1": "RUN", "di2": "STOP", "limit": "PULLCORD/SENS", "aux": "RUN"},
            "risks": [("Atrapamiento", "Alta", "Guardas y cable de paro accesible."), ("Desalineación/atasco", "Media", "Sensores y prueba de paro."), ("Arranque inesperado", "Alta", "Alarma previa y enclavamientos.")],
            "field_steps": [("Seguridad mecánica", "Guardas, pull-cord, puntos de atrapamiento y señalización.", "El control debe proteger al operador." )],
            "checklists": {"taller": ["Continuidad", "E-Stop/pull-cord", "RUN/FAULT", "Rotulado"], "campo": ["Bloqueo/etiquetado", "Guardas", "Alarma previa", "Prueba pull-cord", "Firma"], "fallas_comunes": ["No arranca: revisar pull-cord/E-Stop", "Se detiene: revisar desalineación/atasco", "Falla VFD: leer código"]},
        },
        "general_motor": {
            "label": "Motor industrial general",
            "safety_gate": "Seguridad de motor",
            "safety_fix": "Confirmar paro, sobrecarga, fase, ambiente y procedimiento de prueba.",
            "checks": ["sobrecarga", "fase", "E-Stop", "ambiente", "rotulado"],
            "vfd_note": "En motor general el VFD se justifica por rampa, diagnóstico o control de velocidad; si no, DOL/soft pueden ser suficientes.",
            "terminal_labels": {"cmd1": "MARCHA", "cmd2": "PARO", "di1": "RUN", "di2": "RESET", "limit": "PERMISIVO", "aux": "RUN"},
            "risks": [("Protección mal ajustada", "Alta", "Confirmar FLA de placa y clase de protección."), ("Pérdida de fase", "Media", "Relé monitor de fase en trifásicos críticos."), ("Ambiente severo", "Media", "Gabinete y ventilación según sitio.")],
            "field_steps": [],
            "checklists": {"taller": ["Continuidad", "Torque/ajuste", "E-Stop", "RUN/FAULT", "Rotulado"], "campo": ["Bloqueo/etiquetado", "Tensión real", "Giro", "Corriente en carga", "Firma"], "fallas_comunes": ["No arranca: revisar E-Stop/control", "Dispara térmico: medir corriente", "Gira al revés: corregir fases con procedimiento seguro"]},
        },
    }
    ctx = contexts.get(mt, contexts["general_motor"])
    return {"type": mt, **ctx}

def _data_quality(i: ProjectIntake) -> Dict[str, Any]:
    """Score de entrada: no premia llenar por llenar; premia datos verificables.

    En trabajos de miles de dólares, el sistema debe decir cuándo puede cotizar,
    cuándo solo puede producir borrador, y cuándo debe bloquear salida de construcción.
    """
    checks: List[Dict[str, Any]] = []

    def add(name: str, ok: bool, impact: str, fix: str, weight: int):
        checks.append({"check": name, "ok": ok, "impact": impact, "fix": fix, "weight": weight})

    ctx = _machine_context(i)
    is_hoist = ctx["type"] == "hoist"
    safety_ok = True
    if is_hoist:
        safety_ok = i.needs_brake and i.needs_limit_switches and i.needs_estop
    elif ctx["type"] in {"compressor", "pump", "conveyor"}:
        safety_ok = i.needs_estop and ((i.phases != 3) or i.needs_phase_monitor)
    add("Corriente de placa / FLA", bool(i.full_load_amps and i.full_load_amps > 0), "Crítica", "Subir foto de placa o confirmar FLA medido antes de enviar precio cerrado.", 16)
    add("Datos eléctricos base", i.voltage > 0 and i.phases in {1, 3} and i.frequency_hz in {50, 60}, "Crítica", "Confirmar tensión real, fases y frecuencia.", 12)
    add("Potencia y aplicación", i.motor_power_hp > 0 and bool(i.application), "Crítica", "Indicar máquina, potencia y uso real.", 10)
    add("Evidencia fotográfica", i.field_photos_count >= 3 or (i.nameplate_photo_confirmed and i.panel_photo_confirmed and i.site_photo_confirmed), "Alta", "Cargar placa, tablero actual/ruta y ambiente de instalación.", 12)
    add(ctx["safety_gate"], safety_ok, "Crítica", ctx["safety_fix"], 16)
    add("Protección ante falla de fase", (i.phases != 3) or i.needs_phase_monitor, "Alta", "En motores trifásicos de trabajo crítico usar monitor de fase/secuencia.", 8)
    add("Distancia y ambiente", i.cable_run_m >= 0 and bool(i.environment), "Alta", "Medir ruta real, temperatura, polvo/humedad y canalización.", 10)
    add("Ubicación comercial", bool(i.location_city and i.location_province and i.country), "Media", "Indicar ciudad/provincia para proveedores, logística y vigencia.", 6)
    add("Alcance y margen", bool(i.installation_scope) and i.margin_percent >= 12 and i.contingency_percent >= 3, "Media", "Definir si incluye tablero, instalación, pruebas, transporte y margen mínimo.", 6)
    add("Cortocircuito disponible", bool(i.short_circuit_available_ka and i.short_circuit_available_ka > 0), "Alta", "Si no se conoce, marcar SCCR/kAIC como pendiente y no liberar construcción.", 4)

    total_weight = sum(c["weight"] for c in checks)
    earned = sum(c["weight"] for c in checks if c["ok"])
    score = round((earned / max(1, total_weight)) * 100, 1)
    critical_missing = [c for c in checks if not c["ok"] and c["impact"] == "Crítica"]
    high_missing = [c for c in checks if not c["ok"] and c["impact"] == "Alta"]

    if critical_missing:
        status = "bloqueado para construcción; solo borrador de cotización"
    elif high_missing:
        status = "cotización revisable; exige RFQ/verificación antes de oferta cerrada"
    else:
        status = "apto para cotización piloto con revisión profesional"

    return {
        "score_percent": score,
        "status": status,
        "critical_missing": critical_missing,
        "high_missing": high_missing,
        "checks": checks,
        "rule": "Todo dato no confirmado aparece como supuesto o compuerta. La app no convierte desconocidos en certeza.",
    }


def _starter_by_id(alternatives: List[Dict[str, Any]], starter_id: str) -> Dict[str, Any]:
    for profile in alternatives:
        if profile.get("id") == starter_id:
            return profile.copy()
    fallback = {
        "id": starter_id,
        "name": starter_id.replace("_", " ").title(),
        "fit": "Arquitectura seleccionada por reglas internas de seguridad y coherencia.",
        "how_it_works": "Pendiente de descripción específica.",
        "better_when": "Pendiente de validación del caso.",
        "price_impact": "Impacto de precio dependiente del BOM final.",
        "initial_cost": "Variable",
        "control_quality": 70,
        "safety_depth": 70,
        "complexity": 60,
        "risk": "Requiere revisión humana.",
        "sell_when": "Cuando la arquitectura coincide con el riesgo y el presupuesto.",
    }
    return fallback


def _select_architecture(i: ProjectIntake, alternatives: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Selecciona arquitectura antes de armar BOM.

    Regla crítica V14: la solución recomendada, el BOM y la propuesta al cliente
    deben hablar el mismo idioma. Si el caso es izaje, estrella-triángulo no se
    recomienda por defecto porque puede requerir torque y control fino.
    """
    text = f"{i.budget_profile} {i.user_notes} {i.application} {i.load_type} {i.preferred_quality}".lower()
    hoist = _is_hoist(i)
    explicit_star = any(w in text for w in ["estrella", "triangulo", "triángulo", "star-delta", "star delta"])
    explicit_soft = any(w in text for w in ["soft", "suave", "arrancador suave"])
    explicit_vfd = any(w in text for w in ["variador", "vfd", "frecuencia", "premium", "inteligente"])
    explicit_plc = any(w in text for w in ["plc", "hmi", "scada"])
    economical = any(w in text for w in ["econ", "barato", "mínimo", "minimo"])

    reason: List[str] = []
    warnings: List[str] = []

    if hoist:
        reason.append("Aplicación de izaje detectada: carga suspendida, inversión, freno y finales de carrera elevan el riesgo.")
        if explicit_star:
            warnings.append("Estrella-triángulo no queda como recomendación principal para este guinche salvo validación explícita: motor de 6 terminales, carga liviana al arranque y torque suficiente.")
        if explicit_soft and not explicit_vfd:
            arch = "soft_starter"
            reason.append("Se pidió arranque suave; se trata como opción intermedia, pero no reemplaza control de freno ni seguridad de izaje.")
        elif economical and i.starts_per_hour < 12 and not explicit_vfd:
            arch = "dol_reversing"
            reason.append("Perfil económico y baja frecuencia: inversión con contactores puede ser cotizable, manteniendo freno/enclavamientos/finales.")
        else:
            arch = "vfd_smart"
            reason.append("Para guinche profesional/premium o muchas maniobras, VFD + control inteligente alinea mejor control, rampa, diagnóstico y protección mecánica.")
    else:
        if explicit_plc:
            arch = "plc_hmi_control"
            reason.append("Se pidió PLC/HMI o trazabilidad avanzada.")
        elif explicit_vfd or i.starts_per_hour >= 30:
            arch = "vfd_smart"
            reason.append(_machine_context(i)["vfd_note"])
        elif explicit_soft or i.starts_per_hour >= 15:
            arch = "soft_starter"
            reason.append(f"{_machine_context(i)['label']}: arranques moderados; soft starter reduce corriente/golpe sin control de velocidad.")
        elif explicit_star:
            arch = "star_delta"
            reason.append("Estrella-triángulo solo si el motor/carga lo permiten y se confirma cableado de 6 terminales.")
        elif i.needs_reversing:
            arch = "dol_reversing"
            reason.append("Se requiere inversión de giro con costo controlado.")
        else:
            arch = "dol_basic"
            reason.append("Caso simple sin inversión ni requerimientos de control avanzado.")

    profile = _starter_by_id(alternatives, arch)
    profile.update({
        "architecture_id": arch,
        "architecture_reason": " ".join(reason),
        "architecture_warnings": warnings,
        "why": "Seleccionada por coherencia arquitectura-BOM, seguridad de aplicación, presión de cotización y valor comercial defendible.",
    })
    return profile


def _build_requirements(i: ProjectIntake, calc: Dict[str, Any], architecture: Dict[str, Any]) -> List[ComponentRequirement]:
    arch = architecture.get("architecture_id") or architecture.get("id") or "dol_basic"
    req: List[ComponentRequirement] = []

    def add(component_id: str, category: str, item: str, qty: float, spec: str, must_have: bool = True, checks=None, risk: str = "", unit: str = "u"):
        req.append(ComponentRequirement(component_id=component_id, category=category, item=item, qty=qty, unit=unit, spec=spec, must_have=must_have, critical_checks=checks or [], risk_note=risk))

    # Protección y seguridad comunes
    add("mccb_main", "Fuerza", "MCCB principal", 1, f"3P, {calc['breaker_size_a']} A preliminar, tensión {int(i.voltage)} V, SCCR/kAIC por verificar", checks=["corriente", "tensión", "SCCR", "curva"], risk="No seleccionar sin verificar cortocircuito disponible.")

    # Componentes dependientes de arquitectura: aquí se evita mezclar VFD con estrella-triángulo.
    if arch == "vfd_smart" or arch == "plc_hmi_control":
        add("contactor_fwd", "Fuerza", "Contactor de línea / seguridad para VFD", 1, f"AC-3, corriente >= {calc['full_load_current_a']} A, bobina {int(i.control_voltage)} V; no usado para invertir fases", checks=["AC-3", "bobina", "coordinación con VFD"], risk="En VFD la inversión no se hace con dos contactores; se controla por entradas/lógica del variador.")
        ctx = _machine_context(i)
        add("vfd", "Fuerza", "Variador de frecuencia", 1, f"Para {i.motor_power_hp:g} HP, {int(i.voltage)} V, heavy duty, parametrización según {ctx['label']}", checks=["corriente", "rampas", "protecciones", "parámetros", "diagnóstico"], risk=ctx["vfd_note"] + " Requiere comisionamiento.")
        add("line_reactor", "Fuerza", "Reactor de línea", 1, f"3%, {int(i.voltage)} V, corriente compatible con {calc['full_load_current_a']} A", must_have=False, checks=["corriente", "tensión", "temperatura"], risk="Mejora robustez de variador/red; validar necesidad según instalación.")
        if i.needs_brake or _is_hoist(i):
            add("braking_resistor", "Fuerza", "Resistencia de frenado", 1, "Dimensionar por ciclo de carga, energía de frenado y especificación del VFD", must_have=False, checks=["ohmios", "watts", "ciclo", "ventilación"], risk="No usar genérica sin cálculo térmico y validación del fabricante.")
        if arch == "plc_hmi_control":
            add("plc_basic", "Control", "PLC básico", 1, "Entradas/salidas suficientes para mando, finales, freno, fallas y reserva", must_have=False, checks=["IO", "tensión", "programación", "backup"], risk="Sube ingeniería, pero mejora diagnóstico y expansión.")
    elif arch == "soft_starter":
        add("overload_relay", "Fuerza", "Relé de sobrecarga", 1, f"Rango que cubra ajuste {calc['overload_setting_a']} A", checks=["rango", "clase", "compatibilidad"], risk="Ajuste incorrecto puede disparar falso o no proteger.")
        add("contactor_fwd", "Fuerza", "Contactor principal", 1, f"AC-3, corriente >= {calc['full_load_current_a']} A, bobina {int(i.control_voltage)} V", checks=["AC-3", "bobina", "corriente"])
        add("soft_starter", "Fuerza", "Soft starter", 1, f"Para {i.motor_power_hp:g} HP, {int(i.voltage)} V, corriente >= {calc['full_load_current_a']} A", checks=["corriente", "bypass", "torque", "rampa"], risk="Validar torque de arranque y compatibilidad con freno.")
        add("bypass_contactor", "Fuerza", "Contactor bypass", 1, f"AC-3, corriente >= {calc['full_load_current_a']} A, bobina {int(i.control_voltage)} V", must_have=False, checks=["AC-3", "bobina", "coordinación"], risk="Puede requerirse para reducir pérdidas/temperatura en soft starter.")
    elif arch == "star_delta":
        add("overload_relay", "Fuerza", "Relé de sobrecarga", 1, f"Rango que cubra ajuste {calc['overload_setting_a']} A", checks=["rango", "clase", "compatibilidad"], risk="Ajuste incorrecto puede disparar falso o no proteger.")
        add("main_contactor", "Fuerza", "Contactor principal estrella-triángulo", 1, f"AC-3, corriente >= {calc['full_load_current_a']} A, bobina {int(i.control_voltage)} V", checks=["AC-3", "bobina", "corriente"] )
        add("star_contactor", "Fuerza", "Contactor estrella", 1, "Compatible con esquema estrella-triángulo y temporizador", checks=["coordinación", "enclavamiento"] )
        add("delta_contactor", "Fuerza", "Contactor triángulo", 1, "Compatible con esquema estrella-triángulo y temporizador", checks=["coordinación", "enclavamiento"] )
        add("star_delta_timer", "Control", "Temporizador estrella-triángulo", 1, "Rango ajustable y contactos para conmutación segura", checks=["tiempo", "contactos", "tensión control"], risk="No usar si el motor no tiene 6 terminales accesibles o la carga requiere alto torque inicial.")
    elif arch == "dol_reversing":
        add("overload_relay", "Fuerza", "Relé de sobrecarga", 1, f"Rango que cubra ajuste {calc['overload_setting_a']} A", checks=["rango", "clase", "compatibilidad"], risk="Ajuste incorrecto puede disparar falso o no proteger.")
        add("contactor_fwd", "Fuerza", "Contactor subir", 1, f"AC-3, corriente >= {calc['full_load_current_a']} A, bobina {int(i.control_voltage)} V", checks=["AC-3", "bobina", "corriente"], risk="Verificar compatibilidad con enclavamiento.")
        add("contactor_rev", "Fuerza", "Contactor bajar", 1, f"AC-3, corriente >= {calc['full_load_current_a']} A, bobina {int(i.control_voltage)} V", checks=["AC-3", "bobina", "corriente"], risk="Verificar compatibilidad con enclavamiento.")
        add("mechanical_interlock", "Seguridad", "Enclavamiento mecánico", 1, "Compatible con ambos contactores de inversión", checks=["compatibilidad física", "bloqueo real"], risk="Obligatorio para evitar inversión simultánea.")
    else:
        add("overload_relay", "Fuerza", "Relé de sobrecarga", 1, f"Rango que cubra ajuste {calc['overload_setting_a']} A", checks=["rango", "clase", "compatibilidad"], risk="Ajuste incorrecto puede disparar falso o no proteger.")
        add("contactor_fwd", "Fuerza", "Contactor principal", 1, f"AC-3, corriente >= {calc['full_load_current_a']} A, bobina {int(i.control_voltage)} V", checks=["AC-3", "bobina", "corriente"])

    if i.needs_phase_monitor:
        add("phase_monitor", "Seguridad", "Relé monitor de fase", 1, f"Para red {int(i.voltage)} V trifásica; falla y secuencia de fase", checks=["tensión", "secuencia", "ajustes"], risk=f"Recomendado para proteger { _machine_context(i)['label'].lower() } ante pérdida de fase.")
    add("control_transformer", "Control", "Transformador de control", 1, f"{int(i.voltage)} V a {int(i.control_voltage)} V, {calc['control_transformer_va']} VA preliminar", checks=["VA", "fusibles", "aislamiento"])
    add("cabinet", "Tablero", "Gabinete industrial", 1, "NEMA/IP según polvo, humedad y temperatura; tamaño con 25% de reserva", checks=["grado IP/NEMA", "espacio", "ventilación"])
    if i.needs_estop:
        add("estop", "Seguridad", "Paro de emergencia", 1, "Hongo 22mm, contacto NC, rotulado y accesible", checks=["contacto NC", "acción positiva", "ubicación"])
    _ctx = _machine_context(i)
    if _ctx["type"] == "hoist":
        _push_spec = "Subir, bajar, stop, pilotos y rotulación"
    elif _ctx["type"] == "compressor":
        _push_spec = "Marcha/paro, reset, modo auto/manual y pilotos presión/falla"
    elif _ctx["type"] == "pump":
        _push_spec = "Manual/auto, marcha/paro, pilotos nivel/presión/falla"
    elif _ctx["type"] == "conveyor":
        _push_spec = "Marcha/paro, prealarma, E-Stop/pull-cord y pilotos"
    else:
        _push_spec = "Marcha, paro, reset, pilotos marcha/falla y rotulación"
    add("pushbuttons", "Control", "Botonera de mando", 1, _push_spec, checks=["IP", "contactos", "rotulado"])
    if i.needs_limit_switches:
        add("limit_switches", "Seguridad", "Finales de carrera", 2, "Superior e inferior, robustos, IP adecuado", checks=["mecánica", "IP", "cableado"], risk="Clave para evitar sobre-recorrido.")
    if i.needs_brake:
        add("brake_rectifier", "Control", "Control/rectificador de freno", 1, "Según placa del freno; validar tensión y corriente", checks=["tensión freno", "corriente", "secuencia lógica"], risk="No comprar sin confirmar placa del freno.")

    add("label_package", "Taller", "Etiquetado premium", 1, "Marcadores de cables, borneras, componentes y láminas de tablero", must_have=False, checks=["legibilidad", "durabilidad", "numeración"], risk="Ahorra horas de mantenimiento y da presentación profesional.")
    add("terminal_blocks", "Cableado", "Borneras, puentes y marcadores", 1, "Paquete industrial para control/fuerza con rotulación", checks=["sección", "corriente", "marcado"])
    add("wiring_pack", "Cableado", "Consumibles de cableado de tablero", 1, "Canaleta, punteras, etiquetas, cable control, amarras", checks=["orden", "calibre", "colores"])
    power_cable_m = max(1, round(i.cable_run_m * 1.18, 1))
    add("power_cable", "Cableado", "Conductor de fuerza", power_cable_m, f"{calc['conductor_preliminary']} preliminar, longitud con reserva incluida", checks=["calibre", "temperatura", "caída de tensión", "canalización"], unit="m")
    return req

def _alternatives(i: ProjectIntake) -> List[Dict[str, Any]]:
    profiles = load_starter_profiles()
    if profiles:
        return profiles
    return [
        {"name": "DOL + contactores de inversión", "fit": "Rápido y robusto para trabajos simples", "initial_cost": "Bajo", "control_quality": 52, "safety_depth": 68, "complexity": 38, "risk": "Mayor golpe mecánico; menor diagnóstico", "sell_when": "Cliente prioriza costo.", "how_it_works": "Conecta motor directo a red con contactores enclavados.", "better_when": "Uso simple y bajo presupuesto.", "price_impact": "Baja costo inicial pero puede subir desgaste."},
        {"name": "Soft starter + protección reforzada", "fit": "Arranque más suave sin control fino", "initial_cost": "Medio", "control_quality": 70, "safety_depth": 76, "complexity": 58, "risk": "No da control de velocidad", "sell_when": "Se quiere bajar estrés de arranque.", "how_it_works": "Reduce tensión/corriente durante arranque.", "better_when": "Red débil o arranques moderados.", "price_impact": "Costo medio con menor estrés mecánico."},
        {"name": "Variador + control inteligente", "fit": "Premium para control, rampas y diagnóstico", "initial_cost": "Alto", "control_quality": 94, "safety_depth": 88, "complexity": 76, "risk": "Requiere parametrización", "sell_when": "Guinche crítico o uso frecuente.", "how_it_works": "Controla frecuencia/tensión del motor.", "better_when": "Se quiere control y confiabilidad superior.", "price_impact": "Más caro al inicio, pero reduce paradas y reclamos."},
    ]

def _recommended(i: ProjectIntake, alternatives: List[Dict[str, Any]], architecture: Dict[str, Any]) -> Dict[str, Any]:
    rec = _starter_by_id(alternatives, architecture.get("architecture_id") or architecture.get("id") or "dol_basic")
    ctx = _machine_context(i)
    if (architecture.get("architecture_id") or architecture.get("id")) == "vfd_smart":
        rec["how_it_works"] = f"Controla frecuencia/tensión del motor, limita corriente, permite rampas, alarmas y diagnóstico. {ctx['vfd_note']}"
        rec["price_impact"] = "Mayor costo inicial por variador, protección, parametrización y pruebas. Se justifica cuando reduce paradas, estrés mecánico, reclamos o tiempo de diagnóstico."
        rec["better_when"] = f"{ctx['label']}: cuando se requiere arranque controlado, diagnóstico, rampa o propuesta de alta confiabilidad."
    rec.update({
        "architecture_id": architecture.get("architecture_id") or architecture.get("id"),
        "architecture_reason": architecture.get("architecture_reason", ""),
        "architecture_warnings": architecture.get("architecture_warnings", []),
        "why": architecture.get("why", "Seleccionada por coherencia entre solución, BOM y riesgo técnico."),
    })
    return rec

def _agents() -> List[Dict[str, Any]]:
    return [
        {"name": "Arquitecto de datos", "mission": "Limpia entrada, detecta faltantes y baja confianza si hay datos flojos.", "output": "Ficha técnica revisable"},
        {"name": "Ingeniero de fuerza", "mission": "Define rama de potencia, protecciones y componentes críticos.", "output": "Unifilar + requerimientos"},
        {"name": "Diseñador de control", "mission": "Arma lógica con enclavamientos, finales, paro y freno.", "output": "Ladder conceptual"},
        {"name": "Normalizador de materiales", "mission": "Convierte pedidos ambiguos en componentes canónicos comprables.", "output": "BOM inteligente"},
        {"name": "Comprador técnico", "mission": "Compara proveedor, marca, stock, entrega, precio y riesgo.", "output": "Decisiones de precio"},
        {"name": "Agente RFQ", "mission": "Genera mensaje listo para pedir precios reales y confirmar stock.", "output": "Solicitud a proveedores"},
        {"name": "Comercial Shark", "mission": "Calcula margen, riesgo, precio piso/recomendado/premium.", "output": "Cotización defendible"},
        {"name": "Revisor brutal", "mission": "Bloquea certezas falsas y exige validación humana antes de construir.", "output": "Compuertas de seguridad"},
    ]


def _single_line_svg(i: ProjectIntake, calc: Dict[str, Any]) -> str:
    return f"""
    <svg viewBox='0 0 1000 520' xmlns='http://www.w3.org/2000/svg' role='img'>
      <rect width='1000' height='520' fill='#071019'/>
      <defs><filter id='g'><feGaussianBlur stdDeviation='2.2' result='b'/><feMerge><feMergeNode in='b'/><feMergeNode in='SourceGraphic'/></feMerge></filter></defs>
      <text x='28' y='42' fill='#55c8ff' font-size='26' font-family='Inter, Arial' font-weight='700'>DIAGRAMA UNIFILAR · {int(i.voltage)} V · {i.phases}F · CONCEPTUAL</text>
      <g stroke='#bfe6ff' stroke-width='3' fill='none' filter='url(#g)'>
        <line x1='500' y1='60' x2='500' y2='110'/><circle cx='500' cy='125' r='15'/><line x1='500' y1='140' x2='500' y2='185'/>
        <rect x='438' y='185' width='124' height='52' rx='8'/><line x1='500' y1='237' x2='500' y2='288'/>
        <rect x='442' y='288' width='116' height='52' rx='8'/><line x1='500' y1='340' x2='500' y2='385'/>
        <line x1='280' y1='385' x2='720' y2='385'/>
        <line x1='340' y1='385' x2='340' y2='440'/><circle cx='340' cy='468' r='30'/>
        <line x1='650' y1='385' x2='650' y2='430'/><path d='M625 430 h50 M625 450 h50 M625 470 h50'/>
      </g>
      <g fill='#dff5ff' font-family='Inter, Arial' font-size='18'>
        <text x='560' y='130'>Seccionador / MCCB</text><text x='560' y='154'>{calc['breaker_size_a']} A preliminar · kAIC/SCCR por verificar</text>
        <text x='575' y='220'>Protección motor / sobrecarga</text><text x='575' y='244'>Ajuste preliminar: {calc['overload_setting_a']} A</text>
        <text x='575' y='323'>Control: {int(i.control_voltage)} V</text>
        <text x='205' y='472'>M</text><text x='375' y='458'>{i.motor_power_hp:g} HP · {calc['full_load_current_a']} A</text><text x='375' y='484'>{i.application}</text>
        <text x='700' y='452'>Transformador control</text><text x='700' y='480'>{int(i.voltage)}V → {int(i.control_voltage)}V</text>
      </g>
    </svg>
    """.strip()


def _control_svg(i: ProjectIntake) -> str:
    down = "BAJAR" if i.needs_reversing else "MARCHA"
    return f"""
    <svg viewBox='0 0 1000 520' xmlns='http://www.w3.org/2000/svg' role='img'>
      <rect width='1000' height='520' fill='#071019'/>
      <text x='28' y='42' fill='#55c8ff' font-size='26' font-family='Inter, Arial' font-weight='700'>DIAGRAMA DE CONTROL · LADDER CONCEPTUAL</text>
      <g stroke='#d7efff' stroke-width='3' fill='none'>
        <line x1='80' y1='85' x2='80' y2='470'/><line x1='920' y1='85' x2='920' y2='470'/>
        <line x1='80' y1='130' x2='920' y2='130'/><line x1='80' y1='215' x2='920' y2='215'/><line x1='80' y1='300' x2='920' y2='300'/><line x1='80' y1='385' x2='920' y2='385'/>
        <path d='M170 108 v44 M195 108 v44 M280 108 v44 M305 108 v44 M410 108 v44 M435 108 v44'/><circle cx='825' cy='130' r='34'/>
        <path d='M170 193 v44 M195 193 v44 M320 193 v44 M345 193 v44 M505 193 v44 M530 193 v44'/><circle cx='825' cy='215' r='34'/>
        <path d='M170 278 v44 M195 278 v44 M320 278 v44 M345 278 v44 M505 278 v44 M530 278 v44'/><circle cx='825' cy='300' r='34'/>
        <path d='M170 363 v44 M195 363 v44 M390 363 v44 M415 363 v44'/><circle cx='825' cy='385' r='34'/>
      </g>
      <g fill='#dff5ff' font-family='Inter, Arial' font-size='17'>
        <text x='62' y='75'>L1</text><text x='905' y='75'>L2</text>
        <text x='160' y='100'>STOP</text><text x='260' y='100'>E-STOP</text><text x='390' y='100'>SUBIR</text><text x='807' y='136'>CR1</text>
        <text x='160' y='185'>CR1</text><text x='300' y='185'>LÍMITE SUP.</text><text x='485' y='185'>ENCL. BAJAR</text><text x='801' y='221'>KM1</text>
        <text x='160' y='270'>CR2</text><text x='300' y='270'>LÍMITE INF.</text><text x='485' y='270'>ENCL. SUBIR</text><text x='801' y='306'>{down}</text>
        <text x='160' y='355'>KM1/KM2</text><text x='375' y='355'>FRENO OK</text><text x='805' y='391'>BRK</text>
      </g>
    </svg>
    """.strip()


def _panel_svg() -> str:
    return """
    <svg viewBox='0 0 1000 520' xmlns='http://www.w3.org/2000/svg' role='img'>
      <rect width='1000' height='520' fill='#071019'/>
      <text x='28' y='42' fill='#55c8ff' font-size='26' font-family='Inter, Arial' font-weight='700'>VISTA 3D CONCEPTUAL · TABLERO + MOTOR</text>
      <g transform='translate(185 82) skewY(-4)'>
        <rect x='0' y='0' width='300' height='365' rx='20' fill='#17212d' stroke='#77ccff' stroke-width='3'/>
        <rect x='32' y='42' width='94' height='74' rx='10' fill='#e8eef5'/><rect x='160' y='42' width='94' height='74' rx='10' fill='#e8eef5'/>
        <rect x='32' y='148' width='222' height='86' rx='10' fill='#0e1821' stroke='#426b86'/>
        <rect x='50' y='166' width='38' height='52' rx='4' fill='#f4f8fb'/><rect x='105' y='166' width='38' height='52' rx='4' fill='#f4f8fb'/><rect x='160' y='166' width='38' height='52' rx='4' fill='#f4f8fb'/>
        <rect x='32' y='270' width='222' height='55' rx='8' fill='#0c131b' stroke='#426b86'/><line x1='48' y1='336' x2='245' y2='336' stroke='#ffa533' stroke-width='5'/>
      </g>
      <g transform='translate(565 132)'>
        <ellipse cx='120' cy='120' rx='150' ry='58' fill='#071019' stroke='#16354a'/>
        <rect x='35' y='55' width='245' height='112' rx='38' fill='#155174' stroke='#8ecaff' stroke-width='3'/>
        <rect x='278' y='96' width='112' height='30' fill='#aeb8c2'/><circle cx='398' cy='111' r='22' fill='#d5dce3'/>
        <path d='M60 55 v112 M82 55 v112 M104 55 v112 M126 55 v112 M148 55 v112 M170 55 v112 M192 55 v112 M214 55 v112 M236 55 v112' stroke='#071019' stroke-width='3'/>
        <text x='45' y='235' fill='#dff5ff' font-family='Inter, Arial' font-size='22'>Motor TEFC · modelo conceptual</text>
      </g>
    </svg>
    """.strip()


def _build_budget(i: ProjectIntake, material_cost: float, market_summary: Dict[str, Any]) -> Dict[str, Any]:
    panel_labor = 180.0 * i.labor_days_panel
    field_labor = 220.0 * i.labor_days_field
    engineering = 450.0 + max(0, i.motor_power_hp - 10) * 8
    transport = 120.0 if i.location_province.lower() not in {"guayas", "pichincha"} else 70.0
    subtotal = material_cost + panel_labor + field_labor + engineering + transport
    contingency = subtotal * i.contingency_percent / 100
    margin = (subtotal + contingency) * i.margin_percent / 100
    recommended = subtotal + contingency + margin
    floor = subtotal + contingency + ((subtotal + contingency) * 0.12)
    premium = recommended * 1.22
    fitlock_blocked = int(market_summary.get("fitlock_blocked_count", 0) or 0)
    mathtrust = market_summary.get("mathtrust", {}) or {}
    commercial_blocked = bool(fitlock_blocked or market_summary.get("red_count", 0) or float(market_summary.get("mathtrust_score_percent", 0) or 0) < 72)
    return {
        "materials": round(material_cost, 2),
        "panel_labor": round(panel_labor, 2),
        "field_labor": round(field_labor, 2),
        "engineering": round(engineering, 2),
        "transport_logistics": round(transport, 2),
        "contingency": round(contingency, 2),
        "margin": round(margin, 2),
        "floor_price": round(floor, 2),
        "recommended_sell_price": round(recommended, 2),
        "premium_price": round(premium, 2),
        "price_confidence": "bloqueada por FitLock/MathTrust" if commercial_blocked else ("alta" if market_summary.get("priceguard_score_percent", 0) >= 82 and market_summary.get("red_count", 0) == 0 else ("media-alta" if market_summary.get("priceguard_score_percent", 0) >= 70 and market_summary.get("red_count", 0) <= 2 else "media/baja")),
        "priceguard_status": f"PriceGuard {market_summary.get('priceguard_score_percent', 0)}% · MathTrust {market_summary.get('mathtrust_score_percent',0)}% · FitLock bloqueados {market_summary.get('fitlock_blocked_count',0)} · verde {market_summary.get('green_count',0)} · amarillo {market_summary.get('yellow_count',0)} · rojo {market_summary.get('red_count',0)}",
        "commercial_blocked": commercial_blocked,
        "commercial_release_status": "BLOQUEADA: solo pre-cotización interna" if commercial_blocked else "Lista para propuesta revisable",
        "range_label": "Rango preliminar no confirmado" if commercial_blocked else "Precio recomendado revisable",
        "mathtrust_score_percent": market_summary.get("mathtrust_score_percent", 0),
        "mathtrust_verdict": market_summary.get("mathtrust_verdict", ""),
        "commercial_note": "Pre-cotización bloqueada por FitLock/MathTrust: no enviar como oferta cerrada; solicitar RFQ técnico y confirmar componentes compatibles." if commercial_blocked else "Cotización defendible con semáforo PriceGuard. Precio final cerrado solo con proveedor confirmado, stock y vigencia.",
    }


def _risks(i: ProjectIntake) -> List[Dict[str, Any]]:
    ctx = _machine_context(i)
    base = [
        {"risk": "Cotización con precio no confirmado", "severity": "Alta", "mitigation": "Separar precio estimado, referencial y confirmado; enviar RFQ cuando confianza sea baja."},
        {"risk": "SCCR no coordinado", "severity": "Media", "mitigation": "Verificar corriente de cortocircuito disponible y ratings de todos los componentes."},
        {"risk": "Ambiente severo", "severity": "Media", "mitigation": f"Seleccionar gabinete y componentes según ambiente declarado: {i.environment}."},
    ]
    specific = [{"risk": r, "severity": sev, "mitigation": mit} for r, sev, mit in ctx["risks"]]
    return base[:1] + specific + base[1:]



def _is_hoist(i: ProjectIntake) -> bool:
    return _machine_type(i) == "hoist"


def _consistency_audit(i: ProjectIntake, calc: Dict[str, Any], architecture: Dict[str, Any], requirements: List[ComponentRequirement]) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, status: str, severity: str, detail: str, action: str):
        checks.append({"name": name, "status": status, "severity": severity, "detail": detail, "action": action})

    estimated = _estimate_flc(ProjectIntake(**{**i.model_dump(), "full_load_amps": None}))
    provided = i.full_load_amps or 0
    if provided > 0:
        deviation = abs(provided - estimated) / max(estimated, 0.1) * 100
        status = "ok" if deviation <= 35 else "revisar"
        severity = "media" if deviation <= 35 else "alta"
        add("Coherencia FLA vs potencia", status, severity, f"FLA placa {provided:.1f} A vs estimado {estimated:.1f} A; desviación {deviation:.1f}%.", "Si supera 35%, revisar placa, conexión, tensión y unidades HP/kW.")
    else:
        add("Coherencia FLA vs potencia", "pendiente", "alta", f"Sin FLA; estimado {estimated:.1f} A usado solo como referencia.", "Confirmar corriente de placa antes de cerrar protección/material.")

    ctx = _machine_context(i)
    if _is_hoist(i):
        add(ctx["safety_gate"], "ok" if (i.needs_brake and i.needs_limit_switches and i.needs_estop) else "bloquear", "crítica", "Aplicación de carga suspendida detectada.", ctx["safety_fix"])
    else:
        add(ctx["safety_gate"], "ok" if i.needs_estop else "revisar", "media", f"Contexto detectado: {ctx['label']}.", ctx["safety_fix"])

    if calc["voltage_drop_percent"] > 3:
        add("Caída de tensión", "revisar", "media", f"Caída estimada {calc['voltage_drop_percent']}%.", "Revisar calibre, canalización y longitud real.")
    else:
        add("Caída de tensión", "ok", "baja", f"Caída estimada {calc['voltage_drop_percent']}%.", "Mantener verificación con tabla/código local.")

    if i.short_circuit_available_ka and i.short_circuit_available_ka > 0:
        add("SCCR/kAIC", "dato disponible", "alta", f"Corto disponible declarado: {i.short_circuit_available_ka} kA.", "Seleccionar interruptor/tablero con capacidad superior y coordinación.")
    else:
        add("SCCR/kAIC", "pendiente", "alta", "No se declaró corriente de cortocircuito disponible.", "Cotizar con advertencia; no liberar fabricación hasta verificar kAIC/SCCR.")

    arch = architecture.get("architecture_id") or architecture.get("id") or "desconocida"
    component_ids = {r.component_id for r in requirements}
    vfd_set = {"vfd", "line_reactor", "braking_resistor"}
    star_set = {"main_contactor", "star_contactor", "delta_contactor", "star_delta_timer"}
    if arch == "vfd_smart" and not {"vfd"}.issubset(component_ids):
        add("Coherencia arquitectura-BOM", "bloquear", "crítica", "La arquitectura recomendada es VFD pero el BOM no contiene variador.", "Regenerar BOM desde arquitectura o bloquear propuesta.")
    elif arch == "star_delta" and (component_ids & vfd_set):
        add("Coherencia arquitectura-BOM", "bloquear", "crítica", "La arquitectura estrella-triángulo contiene componentes de VFD.", "Eliminar VFD/reactor/resistencia o cambiar recomendación a VFD.")
    elif arch == "vfd_smart" and (component_ids & star_set):
        add("Coherencia arquitectura-BOM", "bloquear", "crítica", "La arquitectura VFD contiene componentes estrella-triángulo.", "Eliminar contactores estrella-triángulo o cambiar arquitectura.")
    elif arch == "dol_reversing" and (component_ids & (vfd_set | star_set)):
        add("Coherencia arquitectura-BOM", "bloquear", "crítica", "La arquitectura de inversión por contactores tiene componentes de otra arquitectura.", "Separar alternativas y cotizar solo la arquitectura seleccionada.")
    else:
        add("Coherencia arquitectura-BOM", "ok", "alta", f"Arquitectura {arch} coincide con el BOM generado.", "Mantener regla: una arquitectura recomendada = un BOM principal coherente.")

    if _is_hoist(i) and arch == "star_delta":
        add("Regla especial guinche/izaje", "revisar", "alta", "Se seleccionó estrella-triángulo en aplicación de izaje.", "Solo aceptar si motor/carga lo permiten y responsable humano confirma torque, seis terminales y secuencia de freno.")
    elif _is_hoist(i):
        add("Regla especial guinche/izaje", "ok", "alta", f"Arquitectura {arch} evita recomendar estrella-triángulo por defecto en carga suspendida.", "Validar freno, finales, E-Stop, rampas y pruebas antes de construir.")

    blockers = [c for c in checks if c["status"] in {"bloquear"} or (c["severity"] == "crítica" and c["status"] in {"pendiente", "revisar"})]
    score = max(0, round(100 - len(blockers) * 14 - sum(1 for c in checks if c["status"] == "revisar") * 6, 1))
    return {"score_percent": score, "checks": checks, "blockers": blockers}


def _assumption_ledger(i: ProjectIntake, calc: Dict[str, Any], market_summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    assumptions = []
    def add(topic: str, assumption: str, confidence: str, verification: str):
        assumptions.append({"topic": topic, "assumption": assumption, "confidence": confidence, "verification": verification})
    if not i.short_circuit_available_ka:
        add("SCCR/kAIC", "No se conoce corriente de cortocircuito; el breaker se trata como preliminar.", "baja", "Solicitar dato de transformador/red o medir/calcular antes de construir.")
    if not i.full_load_amps:
        add("Corriente de motor", f"Se estima FLC = {calc['full_load_current_a']} A desde HP, tensión, fp y eficiencia.", "media-baja", "Confirmar placa real.")
    add("Precio de materiales", f"Cobertura catálogo {market_summary['coverage_percent']}%; PriceGuard {market_summary.get('priceguard_score_percent',0)}%; FitLock bloqueados {market_summary.get('fitlock_blocked_count',0)}; verdes {market_summary.get('green_count',0)}, amarillos {market_summary.get('yellow_count',0)}, rojos {market_summary.get('red_count',0)}; RFQ requerido en {market_summary['needs_rfq_count']} ítems.", "según fuente", "Confirmar stock/vigencia y compatibilidad técnica; el precio 100% cerrado solo existe con proveedor confirmado y componente que calza.")
    add("Mano de obra", f"Se asumen {i.labor_days_panel} días tablero y {i.labor_days_field} días campo.", "media", "Ajustar con visita técnica y alcance final.")
    add("Alcance", i.installation_scope, "media", "Definir exclusiones: obra civil, canalización extra, parada de producción, permisos.")
    if _is_hoist(i):
        add("Izaje", "Se trata como equipo crítico por carga suspendida; se exige revisión superior.", "alta", "Probar sin carga, con carga supervisada y firmar checklist.")
    return assumptions


def _release_gates(i: ProjectIntake, quality: Dict[str, Any], consistency: Dict[str, Any], market_summary: Dict[str, Any]) -> Dict[str, Any]:
    gates = []
    def gate(name: str, passed: bool, consequence: str, required_action: str):
        gates.append({"name": name, "passed": passed, "consequence": consequence, "required_action": required_action})
    gate("Datos críticos", not quality["critical_missing"], "Sin datos críticos no se puede construir ni cerrar precio técnico.", "Completar placa, tensión/fases, aplicación y seguridad.")
    gate("Coherencia técnica", len(consistency["blockers"]) == 0, "Bloqueadores elevan revisión humana y bajan confianza.", "Resolver auditoría de coherencia.")
    fitlock_ok = market_summary.get("fitlock_blocked_count", 0) == 0
    gate("FitLock / dimensionamiento", fitlock_ok, "Componentes que no calzan con HP/FLA/tensión bloquean precio y BOM fuerte.", "Enviar RFQ técnico y seleccionar breaker/VFD/reactor/cable compatibles.")
    gate("Mercado/precio", market_summary.get("needs_rfq_count", 99) <= 3 and market_summary.get("priceguard_score_percent", 0) >= 70 and fitlock_ok, "Ítems en rojo, FitLock o PriceGuard bajo obligan a RFQ antes de precio cerrado.", "Confirmar proveedores/stock, compatibilidad y corregir outliers de precio.")
    gate("SCCR/kAIC", bool(i.short_circuit_available_ka and i.short_circuit_available_ka > 0), "No liberar fabricación sin capacidad interruptiva verificada.", "Solicitar corto disponible o criterio de protección.")
    ctx = _machine_context(i)
    if _is_hoist(i):
        passed_ctx = i.needs_brake and i.needs_limit_switches and i.needs_estop
        consequence = "Carga suspendida sin seguridad completa es bloqueo crítico."
    else:
        passed_ctx = i.needs_estop and ((i.phases != 3) or i.needs_phase_monitor)
        consequence = f"{ctx['label']} sin protecciones mínimas aumenta riesgo de falla y reclamo."
    gate(ctx["safety_gate"], passed_ctx, consequence, ctx["safety_fix"])
    quote_ready = all(g["passed"] for g in gates[:4])
    construction_ready = all(g["passed"] for g in gates)
    return {
        "quote_ready": quote_ready,
        "construction_ready": construction_ready,
        "gates": gates,
        "verdict": "Lista para cotización piloto" if quote_ready else "No enviar oferta cerrada sin completar compuertas",
        "construction_verdict": "No liberada para construcción automática" if not construction_ready else "Construcción puede pasar a revisión formal humana",
    }


def _quote_readiness(quality: Dict[str, Any], consistency: Dict[str, Any], market_summary: Dict[str, Any], release: Dict[str, Any]) -> Dict[str, Any]:
    mathtrust = float(market_summary.get("mathtrust_score_percent", market_summary.get("priceguard_score_percent", 0)) or 0)
    score = round(quality["score_percent"] * 0.22 + consistency["score_percent"] * 0.22 + float(market_summary["coverage_percent"]) * 0.10 + float(market_summary.get("priceguard_score_percent", 0)) * 0.16 + mathtrust * 0.18 + (100 if release["quote_ready"] else 45) * 0.12, 1)
    if score >= 92 and release["quote_ready"]:
        status = "Alta: lista para propuesta piloto revisable"
    elif score >= 78:
        status = "Media: propuesta con RFQ/advertencias"
    else:
        status = "Baja: solo borrador interno"
    return {
        "score_percent": score,
        "status": status,
        "seller_message": "Ahorra tiempo porque arma el expediente; el humano valida. Si MathTrust/FitLock bloquea, la salida es pre-cotización interna, no oferta cerrada.",
        "do_not_send_if": [g["name"] for g in release["gates"] if not g["passed"] and g["name"] in {"Datos críticos", "Mercado/precio", "Coherencia técnica", "FitLock / dimensionamiento"}],
    }


def _field_verification_plan(i: ProjectIntake) -> List[Dict[str, Any]]:
    base = [
        {"step": "Placa y alimentación", "what": "Foto de placa, tensión entre fases, tierra, frecuencia y FLA.", "why": "Evita comprar bobina/protección equivocada."},
        {"step": "Ruta física", "what": "Medir distancia real, canalización, temperatura y polvo/humedad.", "why": "Ajusta conductor, gabinete y reserva."},
        {"step": "Tablero existente", "what": "Fotos internas, espacio, entradas inferiores/superiores, borneras y cableado.", "why": "Reduce sorpresas y horas de montaje."},
        {"step": "Proveedor", "what": "Confirmar precio, stock, marca, garantía y entrega.", "why": "Convierte precio referencial en precio confirmado."},
    ]
    ctx = _machine_context(i)
    base += [{"step": step, "what": what, "why": why} for step, what, why in ctx.get("field_steps", [])]
    return base


def _qa_scorecard(quality: Dict[str, Any], consistency: Dict[str, Any], release: Dict[str, Any], quote: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "data_score": quality["score_percent"],
        "consistency_score": consistency["score_percent"],
        "quote_score": quote["score_percent"],
        "release_gate_passed": release["quote_ready"],
        "construction_gate_passed": release["construction_ready"],
        "principle": "Métricas altas no eliminan aprobación humana; reducen corrección y tiempo perdido.",
    }




def _engineer_review_board(i: ProjectIntake, release: Dict[str, Any], market_summary: Dict[str, Any], quote: Dict[str, Any]) -> Dict[str, Any]:
    """Simula la mesa de revisión y marca qué pidió cada perfil y cómo se resolvió.

    No representa usuarios reales; es una lista de chequeo de producto basada en perfiles típicos.
    """
    construction = "Satisfecho para piloto" if not release["construction_ready"] else "Satisfecho para revisión formal"
    rfq_ok = market_summary["needs_rfq_count"] <= 3
    personas = [
        {"perfil": "Ingeniero junior", "lo_que_exigia": "Guía paso a paso, ejemplos y bloqueo si faltan datos.", "respuesta_v10": "Flujo guiado, modo rápido, semáforo de precisión y compuertas de salida.", "estado": "feliz para piloto"},
        {"perfil": "Técnico tablerista", "lo_que_exigia": "BOM aterrizado, categorías, chequeos críticos y materiales editables.", "respuesta_v10": "BOM normalizado por categoría, tabla cotizable, CSV/XLSX y notas de riesgo por componente.", "estado": "feliz para piloto"},
        {"perfil": "Mantenimiento industrial", "lo_que_exigia": "Plan de pruebas, fallas comunes y entrega sin improvisación.", "respuesta_v10": "Checklist de taller/campo, plan de verificación y diagnóstico de fallas típicas.", "estado": "feliz para piloto"},
        {"perfil": "Diseñador eléctrico", "lo_que_exigia": "Trazabilidad, supuestos, auditoría, compuertas y documentos formales.", "respuesta_v10": "Libro de supuestos, auditoría de coherencia, export PDF, Markdown y bloqueo SCCR/kAIC.", "estado": construction},
        {"perfil": "Cotizador/compras", "lo_que_exigia": "Precios por confianza, proveedores, RFQ y exportación a Excel.", "respuesta_v10": "Market engine, price confidence, RFQ, CSV/XLSX BOM y fuente/vigencia por línea.", "estado": "feliz para piloto" if rfq_ok else "feliz con advertencia RFQ"},
        {"perfil": "Seguridad/supervisor", "lo_que_exigia": "No liberar construcción si hay riesgo crítico.", "respuesta_v10": "Construction gate separado de quote gate; aprobación humana obligatoria.", "estado": "feliz: no promete construcción automática"},
    ]
    return {
        "veredicto": "La V14 MathTrust Pro está lista para prueba piloto cerrada con ingenieros: arquitectura, BOM, CAD/taller, RFQ, PDF y propuesta obedecen la misma solución principal.",
        "quote_score": quote["score_percent"],
        "personas": personas,
        "regla_de_venta": "Vender ahorro de tiempo y expediente técnico-comercial trazable, no certificación automática.",
        "pendiente_realista": "Conectar credenciales reales de proveedores/marketplaces para pasar de precio referencial a precio confirmado masivo.",
    }


def _guided_flow(i: ProjectIntake, quality: Dict[str, Any], market_summary: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "modo_rapido": [
            "1. Elige tipo de máquina y potencia.",
            "2. Confirma tensión/fases/FLA o sube placa.",
            "3. Define seguridad: paro, finales, freno, monitor de fase.",
            "4. Genera solución y revisa semáforo.",
            "5. Confirma precios de baja confianza con RFQ.",
            "6. Exporta propuesta y BOM.",
        ],
        "modo_expediente": [
            "Completa fotos, ambiente, distancia, SCCR/kAIC, alcance y logística.",
            "Revisa auditoría de coherencia y libro de supuestos.",
            "Cierra precios confirmados y bloqueadores antes de ofertar fuerte.",
        ],
        "next_best_actions": [c["fix"] for c in (quality.get("critical_missing") or quality.get("high_missing") or [])][:5] or ["Enviar RFQ a proveedores y guardar precios confirmados."],
        "market_status": f"{market_summary['items_with_price']}/{market_summary['total_items']} materiales tienen precio; PriceGuard {market_summary.get('priceguard_score_percent',0)}%; verdes {market_summary.get('green_count',0)}, amarillos {market_summary.get('yellow_count',0)}, rojos {market_summary.get('red_count',0)}; {market_summary['needs_rfq_count']} requieren RFQ.",
    }


def _output_quality_contract(release: Dict[str, Any], quote: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "promesa": "Con pocos datos produce el 80-90% del expediente para revisión, cotización y negociación.",
        "no_promete": "No certifica construcción ni energización sin responsable humano, campo y normativa local.",
        "reglas_no_basura": [
            "Separar dato confirmado, supuesto y pendiente.",
            "No ocultar baja confianza de precio.",
            "Bloquear construcción si faltan seguridad, SCCR/kAIC o coherencia crítica.",
            "FitLock: bloquear propuesta fuerte si breaker, VFD, reactor, cable o protecciones no calzan con HP/FLA/tensión.",
            "Mostrar acciones concretas para cerrar cada pendiente.",
            "Entregar archivos exportables y trazables.",
        ],
        "quote_gate": quote["status"],
        "construction_gate": release["construction_verdict"],
    }


def _machine_checklists(i: ProjectIntake) -> Dict[str, List[str]]:
    ctx = _machine_context(i)
    return {
        "datos_minimos": ["Foto de placa", "Tensión/fases medidas", "FLA o corriente medida", "Distancia real", "Ambiente", "Ubicación de entrega", "kAIC/SCCR si se libera construcción"] + ctx["checks"][:3],
        "cotizacion": ["Confirmar ítems de baja confianza", "Enviar RFQ", "Revisar stock", "Definir vigencia", "Aplicar margen", "Adjuntar exclusiones", "Marcar supuestos"],
        "taller": ctx["checklists"]["taller"],
        "campo": ctx["checklists"]["campo"],
        "fallas_comunes": ctx["checklists"]["fallas_comunes"],
    }

def generate_engineering_pack(payload: Dict[str, Any] | ProjectIntake) -> EngineeringPack:
    i = payload if isinstance(payload, ProjectIntake) else ProjectIntake(**payload)
    flc = _estimate_flc(i)
    calculations = {
        "full_load_current_a": _round(flc, 2),
        "breaker_size_a": _breaker_size(flc),
        "overload_setting_a": _overload_setting(flc, i.service_factor),
        "conductor_preliminary": _conductor_size_awg(flc, i.cable_run_m),
        "voltage_drop_percent": _voltage_drop_percent(flc, i.voltage, i.cable_run_m, i.phases),
        "control_transformer_va": 1000 if i.control_voltage <= 120 else 1500,
        "starting_current_estimate": f"{round(flc * 6, 1)} A aprox. en arranque directo",
        "short_circuit_available_ka": i.short_circuit_available_ka or "pendiente",
        "calculation_basis": "FLA de placa si existe; si no, estimación desde HP, V, fp y eficiencia.",
        "notice": "Cálculos preliminares para cotización. Para construcción se requiere placa real, tablas/códigos aplicables, temperatura, canalización, coordinación y verificación de campo.",
    }
    quality = _data_quality(i)
    alternatives = _alternatives(i)
    architecture = _select_architecture(i, alternatives)
    requirements = _build_requirements(i, calculations, architecture)
    decisions = decide_prices(requirements, i)
    market_summary = summarize_market(decisions)
    consistency = _consistency_audit(i, calculations, architecture, requirements)
    release = _release_gates(i, quality, consistency, market_summary)
    quote = _quote_readiness(quality, consistency, market_summary, release)
    assumptions = _assumption_ledger(i, calculations, market_summary)
    recommended = _recommended(i, alternatives, architecture)
    budget = _build_budget(i, float(market_summary["materials_cost"]), market_summary)
    rfq_message = generate_rfq_message(requirements, decisions, i)
    completeness = min(99.5, round((quality["score_percent"] * 0.30) + (consistency["score_percent"] * 0.24) + (float(market_summary["coverage_percent"]) * 0.24) + (quote["score_percent"] * 0.22), 1))
    correction_load = "Mínima" if completeness >= 92 and release["quote_ready"] else "Media" if completeness >= 78 else "Alta"
    construction_release = bool(release["construction_ready"])
    validation_status = "Apto para prueba piloto comercial revisable" if release["quote_ready"] else "Borrador interno: completar compuertas antes de enviar"
    review_board = _engineer_review_board(i, release, market_summary, quote)
    guided_flow = _guided_flow(i, quality, market_summary)
    output_contract = _output_quality_contract(release, quote)

    pack = EngineeringPack(
        meta={"product": PRODUCT, "version": VERSION, "generated_at": datetime.now(timezone.utc).isoformat(), "language": "es", "release_type": "pilot release con MarketPilot + FitLock"},
        intake=i.model_dump(),
        executive_verdict={
            "headline": "Cotización industrial inteligente: menos datos, más expediente, cero certezas falsas.",
            "verdict": "El sistema guía la entrada, genera solución, cálculos, BOM normalizado, precios por confianza, RFQ, presupuesto, riesgos, compuertas de calidad, exportables y acciones pendientes para que el ingeniero revise en vez de reconstruir.",
            "business_pain": "Reduce horas perdidas en cotizaciones de miles de dólares que quizá no se ganen.",
            "release_gate": release["verdict"],
        },
        data_quality=quality,
        agents=_agents(),
        calculations=calculations,
        requirements=[r.model_dump() for r in requirements],
        alternatives=alternatives,
        recommended_option=recommended,
        market={
            "summary": market_summary,
            "price_decisions": [d.model_dump() for d in decisions],
            "supplier_count": len(market_summary["suppliers_used"]),
            "method": "PriceGuard 14 + MathTrust + FitLock Pro: validación matemática por compatibilidad técnica, mediana/IQR, dispersión, profundidad de catálogo, fuente/stock/vigencia y RFQ. Sin componente compatible no existe precio cerrable.",
            "price_truth_rule": "precio estimado ≠ precio confirmado; todo valor muestra semáforo, fuente, vigencia, stock, banda y acción requerida.",
            "priceguard_methodology": priceguard_methodology(),
            "architecture_lock": architecture,
        },
        budget=budget,
        risks=_risks(i),
        checklists=_machine_checklists(i),
        diagrams={
            "single_line_svg": single_line_cad_svg(i, calculations, architecture),
            "control_ladder_svg": control_ladder_cad_svg(i, architecture),
            "panel_preview_svg": panel_layout_cad_svg(i, [r.model_dump() for r in requirements], architecture),
            "single_line_legacy_svg": single_line_cad_svg(i, calculations, architecture),
            "control_ladder_legacy_svg": control_ladder_cad_svg(i, architecture),
            "panel_preview_legacy_svg": panel_layout_cad_svg(i, [r.model_dump() for r in requirements], architecture),
        },
        statistics={
            "engineering_completeness_percent": completeness,
            "market_coverage_percent": market_summary["coverage_percent"],
            "quote_confidence": budget["price_confidence"],
            "reviewer_correction_load": correction_load,
            "time_saved_estimate": "2–6 horas por cotización compleja",
            "estimated_manual_quote_hours": "4–8 h",
            "estimated_controlpro_quote_hours": "35–75 min",
            "commercial_savings_message": "Ahorra horas de búsqueda, normalización de BOM, armado de RFQ, presupuesto y documento para cliente.",
            "deliverables_ready": 15,
            "rfq_required_items": market_summary["needs_rfq_count"],
            "priceguard_score_percent": market_summary.get("priceguard_score_percent", 0),
            "priceguard_green": market_summary.get("green_count", 0),
            "priceguard_yellow": market_summary.get("yellow_count", 0),
            "priceguard_red": market_summary.get("red_count", 0),
            "priceguard_verdict": market_summary.get("priceguard_verdict", "Revisable"),
            "mathtrust_score_percent": market_summary.get("mathtrust_score_percent", 0),
            "mathtrust_verdict": market_summary.get("mathtrust_verdict", ""),
            "mathtrust_model": market_summary.get("mathtrust", {}),
            "locked_price_count": market_summary.get("locked_price_count", 0),
            "referential_price_count": market_summary.get("referential_price_count", 0),
            "blocked_price_count": market_summary.get("blocked_price_count", 0),
            "candidate_offer_audit": market_summary.get("candidate_offer_audit", {}),
            "price_outliers": market_summary.get("outlier_count", 0),
            "auto_corrected_prices": market_summary.get("auto_corrected_count", 0),
            "execution_days_estimate": "2–4 días con materiales disponibles",
            "quote_readiness_score": quote["score_percent"],
        },
        deliverables=[
            {"name": "Propuesta para cliente", "description": "Resumen comercial con precio piso/recomendado/premium, alcance, vigencia y exclusiones."},
            {"name": "BOM cotizable", "description": "Materiales normalizados con proveedor, precio, confianza, stock, semáforo PriceGuard y decisión."},
            {"name": "Reporte PriceGuard", "description": "Semáforos verde/amarillo/rojo, bandas de mercado, outliers, autocorrecciones y acciones RFQ."},
            {"name": "Mensaje RFQ", "description": "Texto listo para WhatsApp/correo a proveedores."},
            {"name": "Diagrama unifilar", "description": "SVG conceptual para revisión técnica."},
            {"name": "Diagrama de control", "description": "Ladder conceptual con enclavamientos y seguridad."},
            {"name": "Vista 3D conceptual", "description": "Explicación visual del tablero y motor."},
            {"name": "Semáforo de precisión", "description": "Calidad de datos, coherencia, mercado y compuertas."},
            {"name": "Libro de supuestos", "description": "Qué se asumió, confianza y cómo verificar."},
            {"name": "Checklist de cotización", "description": "Pasos para no enviar precio flojo."},
            {"name": "Checklist de pruebas", "description": "Taller, campo, seguridad y firma."},
            {"name": "Registro de riesgos", "description": "Riesgos técnicos/comerciales con mitigación."},
            {"name": "Expediente Markdown", "description": "Archivo exportable para editar o convertir a PDF."},
            {"name": "Reporte PDF", "description": "Resumen formal para revisión y presentación."},
            {"name": "BOM CSV/XLSX", "description": "Lista de materiales editable para compras y seguimiento."},
        ],
        rfq={"message": rfq_message, "channels_ready": ["WhatsApp manual", "Correo", "WhatsApp Cloud API con credenciales", "SMTP con credenciales"], "note": "La versión piloto genera RFQ listo. El envío automático requiere credenciales reales y aprobación del usuario."},
        crm={"quote_status": "Borrador técnico-comercial" if not release["quote_ready"] else "Listo para propuesta piloto revisable", "next_action": "Confirmar ítems RFQ y enviar propuesta" if release["quote_ready"] else "Completar compuertas antes de enviar", "win_loss_learning": ["Registrar si se gana o pierde", "Guardar precio competidor si existe", "Actualizar base interna"]},
        validation={
            "status": validation_status,
            "human_approval_required": True,
            "construction_release": construction_release,
            "gates": [f"{'OK' if g['passed'] else 'PENDIENTE'} · {g['name']}: {g['required_action']}" for g in release["gates"]],
        },
        assumption_ledger=assumptions,
        consistency_audit=consistency,
        release_gates=release,
        quote_readiness=quote,
        field_verification_plan=_field_verification_plan(i),
        qa_scorecard=_qa_scorecard(quality, consistency, release, quote),
        machine_context=_machine_context(i),
        client_layer={"visible_first": ["registro_piloto", "datos_minimos", "resultado", "presupuesto", "entregables"], "hidden_by_default": ["api_activation", "env_template", "admin_internal"], "principle": "El cliente ve lo necesario; el ingeniero profundiza por capas."},
        lead_capture={"enabled": True, "mode": "piloto", "fields": ["nombre", "correo", "teléfono", "empresa", "rol"], "storage": "runtime/localStorage; conectar CRM/DB en producción"},
        review_board=review_board,
        guided_flow=guided_flow,
        output_quality_contract=output_contract,
        cad_outputs={
            "level": "CAD-like piloto / Draw.io editable",
            "single_line_sheet": "E-001",
            "control_ladder_sheet": "E-002",
            "panel_layout_sheet": "E-003",
            "terminal_schedule": terminal_schedule(i, architecture),
            "wire_schedule": wire_schedule(i, calculations, architecture),
            "drawio_available": True,
            "upgrade_rule": "Antes de fabricar, convertir a CAD final con marcas/modelos reales, numeración congelada, revisión de SCCR/kAIC y firma responsable.",
        },
        api_activation=integration_status(),
        priceguard={"methodology": priceguard_methodology(), "summary": market_summary, "anti_garbage_rule": "Si un precio sale fuera de banda, sin stock, vencido o de fuente débil, se marca amarillo/rojo y no se permite precio cerrado sin RFQ.", "catalog_scope": market_summary.get("catalog_scope"), "confidence_policy": market_summary.get("confidence_policy"), "candidate_offer_audit": market_summary.get("candidate_offer_audit")},
        starter_intelligence={"profiles": alternatives, "recommended": recommended, "architecture_lock": architecture, "didactic_rule": "Cada arranque explica cómo funciona, cuándo conviene, cómo impacta precio/riesgo y por qué el BOM debe coincidir con la arquitectura seleccionada."},
        premium_document_contract={"pdf": "portada + resumen ejecutivo + semáforos + supuestos + presupuesto + BOM + anexos + firmas", "spreadsheet": "BOM editable con semáforo y fuente", "cad": "SVG/Draw.io CAD-like para revisión y formalización"},
        human_review_notice="ControlPro reduce tiempo, ordena el expediente y baja la carga de corrección; no reemplaza normativa local, verificación de campo, proveedor confirmado ni aprobación humana antes de fabricar o energizar.",
    )
    return pack


def export_pack_markdown(payload: Dict[str, Any] | ProjectIntake) -> str:
    pack = generate_engineering_pack(payload).model_dump()
    lines: List[str] = []
    lines.append(f"# {pack['meta']['product']} — Expediente técnico-comercial")
    lines.append("")
    lines.append(f"**Proyecto:** {pack['intake']['project_name']}")
    lines.append(f"**Cliente:** {pack['intake']['client_name']}")
    lines.append(f"**Ubicación:** {pack['intake']['location_city']}, {pack['intake']['location_province']}, {pack['intake']['country']}")
    lines.append(f"**Generado:** {pack['meta']['generated_at']}")
    lines.append("")
    lines.append("## Veredicto ejecutivo")
    lines.append(pack['executive_verdict']['verdict'])
    lines.append("")
    lines.append("## Calidad de datos")
    lines.append(f"Estado: **{pack['data_quality']['status']}** · Score: **{pack['data_quality']['score_percent']}%**")
    for c in pack['data_quality']['checks']:
        lines.append(f"- {'OK' if c['ok'] else 'FALTA'} · **{c['check']}** · impacto {c['impact']} · {c['fix']}")
    lines.append("")
    lines.append("## Semáforo de precisión")
    lines.append(f"Preparación cotización: **{pack['quote_readiness']['status']}** · Score: **{pack['quote_readiness']['score_percent']}%**")
    lines.append(f"Liberación construcción: **{pack['release_gates']['construction_verdict']}**")
    lines.append("")
    lines.append("## Auditoría de coherencia")
    for c in pack['consistency_audit']['checks']:
        lines.append(f"- **{c['name']}** · {c['status']} · {c['detail']} · Acción: {c['action']}")
    lines.append("")
    lines.append("## Libro de supuestos")
    for a in pack['assumption_ledger']:
        lines.append(f"- **{a['topic']}** · {a['assumption']} · Confianza: {a['confidence']} · Verificación: {a['verification']}")
    lines.append("")
    lines.append("## Cálculos preliminares")
    for k, v in pack['calculations'].items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("## Solución recomendada")
    lines.append(f"**{pack['recommended_option']['name']}** — {pack['recommended_option']['fit']}")
    lines.append(pack['recommended_option']['why'])
    if pack.get("starter_intelligence", {}).get("architecture_lock"):
        arch = pack["starter_intelligence"]["architecture_lock"]
        lines.append(f"FitLock Pro: **{arch.get('architecture_id', arch.get('id',''))}** · {arch.get('architecture_reason','')}")
        for w in arch.get('architecture_warnings', []):
            lines.append(f"- Advertencia arquitectura: {w}")
    lines.append("")
    lines.append("## BOM cotizable")
    for row in pack['market']['price_decisions']:
        offer = row['selected_offer']
        if offer:
            lines.append(f"- **{row['component_id']}** · Cant. {row['qty']} · {offer['brand']} {offer['model']} · {offer['supplier_name']} · ${row['unit_cost']} · confianza {row['confidence_label']} · {row['decision_note']}")
        else:
            lines.append(f"- **{row['component_id']}** · Cant. {row['qty']} · ${row['unit_cost']} estimado · requiere RFQ")
    lines.append("")
    lines.append("## Presupuesto")
    for k, v in pack['budget'].items():
        lines.append(f"- **{k}:** {v}")
    lines.append("")
    lines.append("## RFQ listo para enviar")
    lines.append("```text")
    lines.append(pack['rfq']['message'])
    lines.append("```")
    lines.append("")
    lines.append("## Salidas CAD-like / taller")
    lines.append("- E-001 Unifilar CAD-like SVG")
    lines.append("- E-002 Ladder CAD-like SVG")
    lines.append("- E-003 Layout de tablero CAD-like SVG")
    lines.append("- Draw.io editable para formalización")
    lines.append("- Lista de borneras y lista de cables exportables")
    lines.append("")
    lines.append("### Lista preliminar de borneras")
    for row in pack.get("cad_outputs", {}).get("terminal_schedule", []):
        lines.append(f"- **{row['terminal']}** · {row['wire']} · {row['from']} → {row['to']} · {row['function']}")
    lines.append("")
    lines.append("### Lista preliminar de cables")
    for row in pack.get("cad_outputs", {}).get("wire_schedule", []):
        lines.append(f"- **{row['cable']}** · {row['from']} → {row['to']} · {row['conductors']} · {row['size']} · {row['length_m']} m")
    lines.append("")
    lines.append("## Riesgos")
    for r in pack['risks']:
        lines.append(f"- **{r['risk']}** ({r['severity']}): {r['mitigation']}")
    lines.append("")
    lines.append("## Mesa simulada de ingenieros")
    lines.append(pack["review_board"]["veredicto"])
    for p in pack["review_board"]["personas"]:
        lines.append(f"- **{p['perfil']}**: {p['estado']} · {p.get('respuesta_v13', 'Resuelto')}")
    lines.append("")
    lines.append("## Próximas acciones guiadas")
    for n in pack["guided_flow"]["next_best_actions"]:
        lines.append(f"- {n}")
    lines.append("")
    lines.append("## Aviso")
    lines.append(pack['human_review_notice'])
    return "\n".join(lines)


def export_client_proposal(payload: Dict[str, Any] | ProjectIntake) -> str:
    pack = generate_engineering_pack(payload).model_dump()
    b = pack['budget']
    blocked = bool(b.get('commercial_blocked') or not pack.get('release_gates', {}).get('quote_ready'))
    lines = [
        "# Propuesta técnica-comercial" if not blocked else "# PRE-COTIZACIÓN INTERNA — NO ENVIAR COMO OFERTA CERRADA",
        "",
        f"**Proyecto:** {pack['intake']['project_name']}",
        f"**Cliente:** {pack['intake']['client_name']}",
        f"**Ubicación:** {pack['intake']['location_city']}, {pack['intake']['location_province']}",
        "",
    ]
    if blocked:
        lines += [
            "## Estado comercial",
            "**Bloqueada por MathTrust/FitLock.** Esta salida sirve para revisión interna y solicitud de RFQ, no para enviarse como oferta cerrada al cliente.",
            f"- MathTrust: {pack['market']['summary'].get('mathtrust_score_percent', 0)}% · {pack['market']['summary'].get('mathtrust_verdict', '')}",
            f"- PriceGuard: {pack['market']['summary'].get('priceguard_score_percent', 0)}% · {pack['market']['summary'].get('priceguard_verdict', '')}",
            f"- FitLock bloqueados: {pack['market']['summary'].get('fitlock_blocked_count', 0)}",
            f"- RFQ requeridos: {pack['market']['summary'].get('needs_rfq_count', 0)}",
            "",
        ]
    lines += [
        "## Alcance propuesto",
        "Diseño, selección preliminar de componentes, armado de expediente técnico, lista de materiales, presupuesto, checklist de pruebas y recomendaciones de instalación para sistema de control industrial.",
        "",
        "## Solución recomendada",
        f"{pack['recommended_option']['name']}: {pack['recommended_option']['fit']}.",
        f"Criterio de arquitectura: {pack.get('starter_intelligence', {}).get('architecture_lock', {}).get('architecture_reason', '')}",
        "",
    ]
    if blocked:
        lines += [
            "## Rango preliminar no confirmado",
            f"- Orden de magnitud piso: ${b['floor_price']:,.2f}",
            f"- Orden de magnitud medio: ${b['recommended_sell_price']:,.2f}",
            f"- Orden de magnitud alto: ${b['premium_price']:,.2f}",
            "",
            "**Advertencia:** estos valores NO son precio cerrado. Los componentes críticos deben confirmarse por proveedor con modelo, corriente/HP, tensión, stock, vigencia y compatibilidad técnica.",
            "",
            "## Ítems que bloquean oferta cerrada",
        ]
        for d in pack['market']['price_decisions']:
            if d.get('semaphore_color') == 'rojo' or any('FitLock' in str(x) for x in d.get('anomaly_flags', [])):
                lines.append(f"- **{d['component_id']}**: {d.get('action_required','Enviar RFQ')}")
        lines += ["", "## Próxima acción", "Enviar RFQ técnico, actualizar precios confirmados y regenerar propuesta."]
    else:
        lines += [
            "## Valores comerciales",
            f"- Precio piso técnico: ${b['floor_price']:,.2f}",
            f"- Precio recomendado: ${b['recommended_sell_price']:,.2f}",
            f"- Opción premium: ${b['premium_price']:,.2f}",
        ]
    lines += [
        "",
        "## Vigencia y condiciones",
        "Precio sujeto a confirmación de stock, proveedor, placa real de motor/freno, condiciones de campo y aprobación técnica final.",
        "",
        "## Nota de seguridad",
        pack['human_review_notice'],
    ]
    return "\n".join(lines)
