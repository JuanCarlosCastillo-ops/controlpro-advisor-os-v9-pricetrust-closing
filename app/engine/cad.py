from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any, Dict, List
from xml.sax.saxutils import escape as xml_escape

from .models import ProjectIntake


def _e(value: Any) -> str:
    return escape(str(value), quote=True)


def _arch_id(architecture: Dict[str, Any] | str | None = None) -> str:
    if isinstance(architecture, dict):
        return str(architecture.get("architecture_id") or architecture.get("id") or "dol_basic")
    if isinstance(architecture, str) and architecture.strip():
        return architecture.strip()
    return "dol_basic"



def _machine_type(i: ProjectIntake) -> str:
    text = f"{i.application} {i.load_type} {i.project_name} {i.user_notes}".lower()
    if any(w in text for w in ["guinche", "winche", "hoist", "izaje", "polipasto"]):
        return "hoist"
    if any(w in text for w in ["compresor", "compressor", "aire comprimido"]):
        return "compressor"
    if any(w in text for w in ["bomba", "pump", "centrífuga", "centrifuga"]):
        return "pump"
    if any(w in text for w in ["banda", "transportadora", "conveyor", "cinta"]):
        return "conveyor"
    return "general_motor"


def _labels(i: ProjectIntake) -> Dict[str, str]:
    mt = _machine_type(i)
    if mt == "hoist":
        return {"cmd1":"SUBIR", "cmd2":"BAJAR", "di1":"FWD/UP", "di2":"REV/DOWN", "permissive":"LS-UP/LS-DN", "aux":"BRK", "aux_desc":"Liberación freno", "cable_aux":"Freno", "note":"finales/freno/carga suspendida"}
    if mt == "compressor":
        return {"cmd1":"MARCHA", "cmd2":"AUTO/RESET", "di1":"RUN", "di2":"AUTO/RESET", "permissive":"PRESOSTATO/TERM", "aux":"RUN", "aux_desc":"Permisivo marcha", "cable_aux":"Presostato/termistor", "note":"presostato/unloader/temperatura"}
    if mt == "pump":
        return {"cmd1":"MARCHA", "cmd2":"AUTO/MAN", "di1":"RUN", "di2":"AUTO", "permissive":"NIVEL/PRES", "aux":"RUN", "aux_desc":"Permisivo bomba", "cable_aux":"Nivel/presión", "note":"nivel/presión/trabajo en seco"}
    if mt == "conveyor":
        return {"cmd1":"MARCHA", "cmd2":"PARO", "di1":"RUN", "di2":"STOP", "permissive":"PULLCORD/SENS", "aux":"RUN", "aux_desc":"Permisivo banda", "cable_aux":"Pull-cord/sensores", "note":"guardas/paros distribuidos"}
    return {"cmd1":"MARCHA", "cmd2":"RESET", "di1":"RUN", "di2":"RESET", "permissive":"PERMISIVO", "aux":"RUN", "aux_desc":"Permisivo motor", "cable_aux":"Permisivo", "note":"protección motor"}

def revision_block(title: str, project: str, rev: str = "A") -> str:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""
    <g class='title-block' font-family='Inter, Arial'>
      <rect x='686' y='650' width='466' height='126' fill='#0a1622' stroke='#9edcff' stroke-width='1.3'/>
      <line x1='686' y1='682' x2='1152' y2='682' stroke='#9edcff' stroke-width='1'/>
      <line x1='686' y1='714' x2='1152' y2='714' stroke='#9edcff' stroke-width='1'/>
      <line x1='894' y1='650' x2='894' y2='776' stroke='#9edcff' stroke-width='1'/>
      <line x1='1016' y1='714' x2='1016' y2='776' stroke='#9edcff' stroke-width='1'/>
      <text x='700' y='672' fill='#55c8ff' font-size='17' font-weight='800'>CONTROLPRO ADVISOR OS V12</text>
      <text x='700' y='704' fill='#e6f7ff' font-size='14'>PLANO: {_e(title)}</text>
      <text x='700' y='736' fill='#e6f7ff' font-size='13'>PROYECTO: {_e(project)[:50]}</text>
      <text x='700' y='760' fill='#b8d6e8' font-size='12'>USO: COTIZACIÓN / REVISIÓN · NO LIBERA CONSTRUCCIÓN SIN APROBACIÓN</text>
      <text x='907' y='736' fill='#e6f7ff' font-size='12'>REV: {rev}</text>
      <text x='907' y='760' fill='#e6f7ff' font-size='12'>FECHA: {date}</text>
      <text x='1028' y='736' fill='#e6f7ff' font-size='12'>ESCALA: NTS</text>
      <text x='1028' y='760' fill='#e6f7ff' font-size='12'>FORMATO: SVG/CAD-LIKE</text>
    </g>
    """


def cad_grid() -> str:
    return """
    <defs>
      <pattern id='gridMinor' width='20' height='20' patternUnits='userSpaceOnUse'>
        <path d='M 20 0 L 0 0 0 20' fill='none' stroke='#133146' stroke-width='0.55'/>
      </pattern>
      <pattern id='gridMajor' width='100' height='100' patternUnits='userSpaceOnUse'>
        <rect width='100' height='100' fill='url(#gridMinor)'/>
        <path d='M 100 0 L 0 0 0 100' fill='none' stroke='#1c4c66' stroke-width='1'/>
      </pattern>
      <style>
        .wire{stroke:#d9f2ff;stroke-width:2.4;fill:none;stroke-linecap:round;stroke-linejoin:round}
        .bus{stroke:#ffffff;stroke-width:4;fill:none;stroke-linecap:round;stroke-linejoin:round}
        .device{fill:#091421;stroke:#9edcff;stroke-width:2}
        .device2{fill:#0e2232;stroke:#55c8ff;stroke-width:2}
        .device3{fill:#14243a;stroke:#ffb33a;stroke-width:2}
        .txt{fill:#e6f7ff;font-family:Inter,Arial;font-size:15px}
        .small{fill:#a8c7da;font-family:Inter,Arial;font-size:12px}
        .blue{fill:#55c8ff;font-family:Inter,Arial;font-size:16px;font-weight:800}
        .warn{fill:#ffcf8a;font-family:Inter,Arial;font-size:12px}
      </style>
    </defs>
    <rect width='1200' height='800' fill='#061019'/>
    <rect width='1200' height='800' fill='url(#gridMajor)' opacity='0.64'/>
    """


def single_line_cad_svg(i: ProjectIntake, calc: Dict[str, Any], architecture: Dict[str, Any] | str | None = None) -> str:
    arch = _arch_id(architecture)
    flc = calc.get("full_load_current_a", "--")
    breaker = calc.get("breaker_size_a", "--")
    overload = calc.get("overload_setting_a", "--")
    conductor = calc.get("conductor_preliminary", "--")
    kaic = f"{i.short_circuit_available_ka} kA" if i.short_circuit_available_ka else "PENDIENTE"

    if arch in {"vfd_smart", "plc_hmi_control"}:
        power_chain = f"""
    <rect x='500' y='250' width='200' height='56' class='device'/>
    <text x='525' y='273' class='txt'>FM-01 · Monitor fase</text>
    <text x='525' y='293' class='small'>Pérdida / secuencia / subtensión</text>
    <line x1='600' y1='306' x2='600' y2='350' class='bus'/>
    <rect x='478' y='350' width='244' height='64' class='device2'/>
    <text x='502' y='374' class='txt'>K1 · Contactor línea / seguridad</text>
    <text x='502' y='396' class='small'>No invierte fases · habilita alimentación del VFD</text>
    <line x1='600' y1='414' x2='600' y2='462' class='bus'/>
    <rect x='472' y='462' width='256' height='78' class='device3'/>
    <text x='510' y='490' class='txt'>VFD-01 · Variador</text>
    <text x='510' y='512' class='small'>{_e(i.motor_power_hp)} HP · {int(i.voltage)} V · HD · rampas/freno</text>
    <line x1='728' y1='500' x2='880' y2='500' class='wire'/>
    <rect x='880' y='466' width='190' height='68' class='device'/>
    <text x='905' y='491' class='txt'>BR-01 · Resistencia</text>
    <text x='905' y='512' class='small'>RFQ por ciclo de frenado</text>
    <line x1='600' y1='540' x2='600' y2='606' class='bus'/>
        """
        legend = """
    <text x='96' y='184' class='txt'>QF-01: Interruptor principal</text>
    <text x='96' y='210' class='txt'>K1: Contactor línea / seguridad</text>
    <text x='96' y='236' class='txt'>VFD-01: Rampas, inversión y diagnóstico</text>
    <text x='96' y='262' class='txt'>BR-01: Resistencia frenado (RFQ)</text>
    <text x='96' y='288' class='warn'>Pendiente crítico: SCCR/kAIC real</text>
        """
        title = "E-001 Unifilar VFD"
    elif arch == "star_delta":
        power_chain = f"""
    <rect x='500' y='250' width='200' height='56' class='device'/><text x='525' y='273' class='txt'>KM-L · Contactor línea</text><text x='525' y='293' class='small'>Estrella-triángulo preliminar</text>
    <line x1='600' y1='306' x2='600' y2='350' class='bus'/>
    <rect x='445' y='350' width='310' height='78' class='device2'/><text x='482' y='380' class='txt'>KM-Y / KM-Δ + Temporizador</text><text x='482' y='402' class='small'>Solo motor 6 terminales y carga apta</text>
    <line x1='600' y1='428' x2='600' y2='478' class='bus'/>
    <rect x='500' y='478' width='200' height='56' class='device'/><text x='525' y='501' class='txt'>OL-01 · Sobrecarga</text><text x='525' y='521' class='small'>Ajuste preliminar: {overload} A</text>
    <line x1='600' y1='534' x2='600' y2='606' class='bus'/>
        """
        legend = """
    <text x='96' y='184' class='txt'>KM-L: Principal</text><text x='96' y='210' class='txt'>KM-Y: Estrella</text><text x='96' y='236' class='txt'>KM-Δ: Triángulo</text><text x='96' y='262' class='txt'>TSD: temporizador</text><text x='96' y='288' class='warn'>Validar seis terminales y torque</text>
        """
        title = "E-001 Unifilar estrella-triángulo"
    else:
        inv_text = "KM1/KM2 · Inversión enclavada" if arch == "dol_reversing" else "KM1 · Contactor principal"
        inv_note = "enclavamiento mecánico" if arch == "dol_reversing" else "arranque directo"
        power_chain = f"""
    <rect x='500' y='250' width='200' height='56' class='device'/><text x='525' y='273' class='txt'>FM-01 · Monitor fase</text><text x='525' y='293' class='small'>Pérdida / secuencia / subtensión</text>
    <line x1='600' y1='306' x2='600' y2='358' class='bus'/>
    <rect x='472' y='358' width='256' height='70' class='device2'/><text x='495' y='382' class='txt'>{inv_text}</text><text x='495' y='404' class='small'>AC-3 · bobina {int(i.control_voltage)} V · {inv_note}</text>
    <line x1='600' y1='428' x2='600' y2='478' class='bus'/>
    <rect x='500' y='478' width='200' height='56' class='device'/><text x='525' y='501' class='txt'>OL-01 · Sobrecarga</text><text x='525' y='521' class='small'>Ajuste preliminar: {overload} A</text>
    <line x1='600' y1='534' x2='600' y2='606' class='bus'/>
        """
        legend = """
    <text x='96' y='184' class='txt'>QF-01: Interruptor principal</text><text x='96' y='210' class='txt'>KM1/KM2: contactores si aplica</text><text x='96' y='236' class='txt'>OL-01: Sobrecarga motor</text><text x='96' y='262' class='txt'>TB: Borneras cableadas</text><text x='96' y='288' class='warn'>Pendiente crítico: SCCR/kAIC real</text>
        """
        title = "E-001 Unifilar contactorizado"

    return f"""
<svg viewBox='0 0 1200 800' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='Diagrama unifilar CAD-like'>
  {cad_grid()}
  <text x='42' y='44' class='blue' font-size='24'>E-001 · DIAGRAMA UNIFILAR PRELIMINAR · {_e(arch)}</text>
  <text x='42' y='70' class='small'>Proyecto: {_e(i.project_name)} · Aplicación: {_e(i.application)} · Ubicación: {_e(i.location_city)}, {_e(i.location_province)}</text>
  <g id='feeder'>
    <line x1='600' y1='95' x2='600' y2='145' class='bus'/>
    <rect x='500' y='145' width='200' height='56' class='device2'/>
    <text x='525' y='168' class='txt'>QF-01 · MCCB 3P</text>
    <text x='525' y='188' class='small'>{breaker} A · {int(i.voltage)} V · kAIC: {kaic}</text>
    <line x1='600' y1='201' x2='600' y2='250' class='bus'/>
    {power_chain}
    <circle cx='600' cy='640' r='36' fill='#0e2232' stroke='#9edcff' stroke-width='2.4'/>
    <text x='586' y='649' fill='#e6f7ff' font-family='Inter,Arial' font-size='28' font-weight='800'>M</text>
    <text x='653' y='628' class='txt'>MTR-01 · {_e(i.motor_power_hp)} HP</text>
    <text x='653' y='649' class='small'>FLA {flc} A · {int(i.voltage)} V · {i.phases}F · {int(i.frequency_hz)} Hz</text>
    <text x='653' y='670' class='small'>Cable preliminar: {_e(conductor)} · recorrido {i.cable_run_m:g} m</text>
  </g>
  <g id='control-power'>
    <line x1='600' y1='332' x2='880' y2='332' class='wire'/>
    <rect x='880' y='292' width='198' height='80' class='device'/>
    <text x='902' y='320' class='txt'>T1 · Transformador control</text>
    <text x='902' y='342' class='small'>{int(i.voltage)} V → {int(i.control_voltage)} V · fusible prim/sec</text>
    <line x1='979' y1='372' x2='979' y2='420' class='wire'/>
    <rect x='900' y='420' width='158' height='52' class='device2'/><text x='923' y='452' class='txt'>TB-CONTROL</text>
  </g>
  <g id='terminales'><rect x='72' y='126' width='292' height='176' class='device'/><text x='96' y='154' class='blue'>Leyenda / tags</text>{legend}</g>
  {revision_block(title, i.project_name)}
</svg>
""".strip()


def control_ladder_cad_svg(i: ProjectIntake, architecture: Dict[str, Any] | str | None = None) -> str:
    arch = _arch_id(architecture)
    lab = _labels(i)
    if arch in {"vfd_smart", "plc_hmi_control"}:
        detail = f"Lógica VFD por contexto: {lab['note']}. Comandos a DI, falla por relé y permisos de seguridad. No usa KM1/KM2 para invertir fases."
        rung_labels = [
            ("R1", "S0 STOP NC", "S-ESTOP NC", "RESET", "CR"),
            ("R2", "CR NO", f"S1 {lab['cmd1']}", f"{lab['permissive']} OK", f"VFD-DI1 {lab['di1']}"),
            ("R3", "CR NO", f"S2 {lab['cmd2']}", "PERM OK", f"VFD-DI2 {lab['di2']}"),
            ("R4", "VFD RUN", "FM OK", lab['aux_desc'], lab['aux']),
            ("R5", "VFD FAULT", "FM FAIL", "OL/THERM", "ALM"),
            ("R6", "CR NO", "VFD READY", "RUN FB", "PIL"),
        ]
        terminal_note = f"W201 CR → VFD-DI1 {lab['di1']}; W301 CR → VFD-DI2 {lab['di2']}; W401 VFD-RUN → {lab['aux']}; W601 {lab['permissive']} → DI3/DI4."
    else:
        detail = "Lógica contactorizada: usar enclavamiento eléctrico/mecánico según arquitectura."
        cmd1, cmd2 = lab['cmd1'], lab['cmd2']
        rung_labels = [
            ("R1", "S0 STOP NC", "S-ESTOP NC", "RESET", "CR"),
            ("R2", "CR NO", f"S1 {cmd1}", "PERM OK", "KM1"),
            ("R3", "CR NO", f"S2 {cmd2}", "PERM OK", "KM2"),
            ("R4", "KM1/KM2 NO", "OL NC", "FM OK", lab['aux']),
            ("R5", "OL TRIP", "FM FAIL", "AUX", "ALM"),
            ("R6", "CR NO", "KM1 NO", "KM2 NO", "PIL"),
        ]
        terminal_note = "W201 CR → KM1; W301 CR → KM2 si aplica; W401 permiso de marcha → salida auxiliar."
    yvals = [150, 235, 320, 405, 490, 575]
    rows = []
    for y, labels in zip(yvals, rung_labels):
        r, a, b, c, coil = labels
        rows.append(f"""
    <line x1='90' y1='{y}' x2='1110' y2='{y}' class='wire'/>
    <text x='105' y='{y-8}' class='small'>{_e(r)}</text>
    <text x='160' y='{y-34}' class='txt'>{_e(a)}</text><text x='330' y='{y-34}' class='txt'>{_e(b)}</text><text x='520' y='{y-34}' class='txt'>{_e(c)}</text>
    <circle cx='1000' cy='{y}' r='30' fill='none' stroke='#e6f7ff' stroke-width='2.5'/><text x='943' y='{y+6}' class='txt'>{_e(coil)}</text>
        """)
    return f"""
<svg viewBox='0 0 1200 800' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='Diagrama ladder CAD-like'>
  {cad_grid()}
  <text x='42' y='44' class='blue' font-size='24'>E-002 · CONTROL / LADDER PRELIMINAR · {_e(arch)}</text>
  <text x='42' y='70' class='small'>Control: {int(i.control_voltage)} V · {detail}</text>
  <line x1='90' y1='116' x2='90' y2='600' class='bus'/><line x1='1110' y1='116' x2='1110' y2='600' class='bus'/>
  <text x='74' y='104' class='txt'>L+</text><text x='1094' y='104' class='txt'>L-</text>
  {''.join(rows)}
  <g id='terminal-tags' font-family='Inter,Arial'>
    <rect x='74' y='625' width='730' height='96' class='device'/>
    <text x='96' y='654' class='blue'>Numeración preliminar de cables · {_e(arch)} · {_e(_machine_type(i))}</text>
    <text x='96' y='681' class='small'>{_e(terminal_note)}</text>
    <text x='96' y='704' class='warn'>Revisión de taller: confirmar borneras, colores, calibre de control, parámetros VFD/relés y protecciones específicas de la máquina.</text>
  </g>
  {revision_block('E-002 Control ladder', i.project_name)}
</svg>
""".strip()


def panel_layout_cad_svg(i: ProjectIntake, requirements: List[Dict[str, Any]] | None = None, architecture: Dict[str, Any] | str | None = None) -> str:
    arch = _arch_id(architecture)
    if arch in {"vfd_smart", "plc_hmi_control"}:
        middle_title = "RIEL MEDIO · VFD / REACTOR / FRENADO"
        middle_devices = """
    <rect x='52' y='270' width='112' height='90' class='device2'/><text x='77' y='319' class='small'>K1</text>
    <rect x='194' y='250' width='156' height='130' class='device3'/><text x='235' y='318' class='small'>VFD-01</text>
    <rect x='382' y='270' width='118' height='90' class='device'/><text x='403' y='319' class='small'>LR/BR</text>
        """
    elif arch == "star_delta":
        middle_title = "RIEL MEDIO · ESTRELLA-TRIÁNGULO"
        middle_devices = """
    <rect x='52' y='270' width='96' height='90' class='device2'/><text x='78' y='319' class='small'>KM-L</text>
    <rect x='180' y='270' width='96' height='90' class='device2'/><text x='208' y='319' class='small'>KM-Y</text>
    <rect x='308' y='270' width='96' height='90' class='device2'/><text x='335' y='319' class='small'>KM-Δ</text>
    <rect x='436' y='270' width='70' height='90' class='device'/><text x='450' y='319' class='small'>TSD</text>
        """
    else:
        middle_title = "RIEL MEDIO · CONTACTORES / SOBRECARGA"
        middle_devices = """
    <rect x='72' y='270' width='126' height='90' class='device2'/><text x='105' y='319' class='small'>KM1</text>
    <rect x='218' y='270' width='70' height='90' class='device'/><text x='235' y='319' class='small'>INT</text>
    <rect x='306' y='270' width='126' height='90' class='device2'/><text x='339' y='319' class='small'>KM2</text>
    <rect x='452' y='270' width='64' height='90' class='device'/><text x='466' y='319' class='small'>OL</text>
        """
    return f"""
<svg viewBox='0 0 1200 800' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='Layout tablero CAD-like'>
  {cad_grid()}
  <text x='42' y='44' class='blue' font-size='24'>E-003 · LAYOUT PRELIMINAR DE TABLERO · {_e(arch)}</text>
  <text x='42' y='70' class='small'>Distribución orientativa para cotización. Dimensiones finales dependen de marcas/modelos reales y disipación térmica.</text>
  <g transform='translate(170 110)'>
    <rect x='0' y='0' width='560' height='500' rx='14' fill='#0b1722' stroke='#9edcff' stroke-width='3'/>
    <rect x='24' y='22' width='512' height='38' fill='#123044' stroke='#55c8ff'/><text x='38' y='48' class='txt'>RIEL SUPERIOR · QF / FM / CONTROL</text>
    <rect x='52' y='86' width='112' height='76' class='device2'/><text x='70' y='128' class='small'>QF-01</text>
    <rect x='194' y='86' width='112' height='76' class='device'/><text x='213' y='128' class='small'>FM-01</text>
    <rect x='336' y='86' width='142' height='76' class='device'/><text x='352' y='128' class='small'>T1/FUS</text>
    <rect x='24' y='206' width='512' height='38' fill='#123044' stroke='#55c8ff'/><text x='38' y='232' class='txt'>{_e(middle_title)}</text>
    {middle_devices}
    <rect x='24' y='404' width='512' height='38' fill='#123044' stroke='#55c8ff'/><text x='38' y='430' class='txt'>BORNERAS / CANALETA / RESERVA</text>
    <rect x='52' y='462' width='430' height='20' fill='#ffb33a'/><text x='494' y='478' class='small'>TB1</text>
    <path d='M24 74 h512 M24 190 h512 M24 388 h512' stroke='#1d4c68' stroke-width='10' stroke-linecap='round'/>
  </g>
  <g transform='translate(795 130)' font-family='Inter,Arial'>
    <rect x='0' y='0' width='300' height='420' rx='16' class='device'/>
    <text x='24' y='34' class='blue'>Puerta / operador</text>
    <circle cx='72' cy='98' r='22' fill='#d73737'/><text x='114' y='105' class='txt'>S-ESTOP</text>
    <circle cx='72' cy='158' r='18' fill='#3bf28b'/><text x='114' y='165' class='txt'>SUBIR</text>
    <circle cx='72' cy='214' r='18' fill='#55c8ff'/><text x='114' y='221' class='txt'>BAJAR</text>
    <circle cx='72' cy='270' r='18' fill='#ffb33a'/><text x='114' y='277' class='txt'>FALLA</text>
    <rect x='44' y='326' width='210' height='48' rx='8' class='device2'/><text x='70' y='356' class='txt'>PLACA / ROTULADO</text>
  </g>
  <text x='170' y='642' class='warn'>MarketPilot Lock: layout, borneras, cables y Draw.io obedecen la arquitectura principal; no mezclar VFD con KM1/KM2.</text>
  {revision_block('E-003 Layout tablero', i.project_name)}
</svg>
""".strip()


def terminal_schedule(i: ProjectIntake, architecture: Dict[str, Any] | str | None = None) -> List[Dict[str, Any]]:
    arch = _arch_id(architecture)
    lab = _labels(i)
    rows = [
        {"terminal": "TB1-01", "wire": "W101", "from": "T1 secondary L+", "to": "S0 STOP NC", "function": "Alimentación control", "gauge": "#16 AWG Cu", "color": "Rojo"},
        {"terminal": "TB1-02", "wire": "W102", "from": "S0 STOP NC", "to": "S-ESTOP NC", "function": "Cadena de paro", "gauge": "#16 AWG Cu", "color": "Rojo"},
        {"terminal": "TB1-03", "wire": "W103", "from": "S-ESTOP NC", "to": "CR coil", "function": "Permisivo maestro", "gauge": "#16 AWG Cu", "color": "Rojo"},
    ]
    if arch in {"vfd_smart", "plc_hmi_control"}:
        rows += [
            {"terminal": "TB1-04", "wire": "W201", "from": f"S1 {lab['cmd1']}", "to": f"VFD DI1 {lab['di1']}", "function": f"Orden {lab['cmd1'].lower()} por entrada digital", "gauge": "#16 AWG Cu", "color": "Azul"},
            {"terminal": "TB1-05", "wire": "W301", "from": f"S2 {lab['cmd2']}", "to": f"VFD DI2 {lab['di2']}", "function": f"Orden {lab['cmd2'].lower()} por entrada digital", "gauge": "#16 AWG Cu", "color": "Azul"},
            {"terminal": "TB1-06", "wire": "W401", "from": "VFD RO1 RUN", "to": lab["aux"], "function": lab["aux_desc"], "gauge": "#16 AWG Cu", "color": "Naranja"},
            {"terminal": "TB1-07", "wire": "W501", "from": "VFD FAULT / FM", "to": "ALM", "function": "Alarma/falla variador o fase", "gauge": "#16 AWG Cu", "color": "Amarillo"},
            {"terminal": "TB1-08", "wire": "W601", "from": lab["permissive"], "to": "VFD DI3/DI4 permissive", "function": f"Permisivos específicos: {lab['note']}", "gauge": "#16 AWG Cu", "color": "Violeta"},
        ]
    elif arch == "star_delta":
        rows += [
            {"terminal": "TB1-04", "wire": "W201", "from": "START", "to": "KM-L coil", "function": "Arranque principal", "gauge": "#16 AWG Cu", "color": "Azul"},
            {"terminal": "TB1-05", "wire": "W202", "from": "TSD Y", "to": "KM-Y coil", "function": "Etapa estrella", "gauge": "#16 AWG Cu", "color": "Azul"},
            {"terminal": "TB1-06", "wire": "W203", "from": "TSD Δ", "to": "KM-Δ coil", "function": "Etapa triángulo", "gauge": "#16 AWG Cu", "color": "Azul"},
        ]
    else:
        rows += [
            {"terminal": "TB1-04", "wire": "W201", "from": f"S1 {lab['cmd1']}", "to": "KM1 coil", "function": f"Orden {lab['cmd1'].lower()}", "gauge": "#16 AWG Cu", "color": "Azul"},
            {"terminal": "TB1-05", "wire": "W301", "from": f"S2 {lab['cmd2']}", "to": "KM2 coil", "function": f"Orden {lab['cmd2'].lower()} si aplica", "gauge": "#16 AWG Cu", "color": "Azul"},
            {"terminal": "TB1-06", "wire": "W401", "from": "KM/AUX", "to": lab["aux"], "function": lab["aux_desc"], "gauge": "#16 AWG Cu", "color": "Naranja"},
            {"terminal": "TB1-07", "wire": "W501", "from": "OL/FM", "to": "ALM", "function": "Alarma/falla", "gauge": "#16 AWG Cu", "color": "Amarillo"},
        ]
    rows.append({"terminal": "TB1-99", "wire": "W000", "from": "Control common", "to": "L-", "function": "Retorno control", "gauge": "#16 AWG Cu", "color": "Blanco"})
    if not i.needs_reversing and arch not in {"vfd_smart", "plc_hmi_control", "star_delta"}:
        rows = [r for r in rows if r["wire"] != "W301"]
    return rows


def wire_schedule(i: ProjectIntake, calc: Dict[str, Any], architecture: Dict[str, Any] | str | None = None) -> List[Dict[str, Any]]:
    arch = _arch_id(architecture)
    lab = _labels(i)
    conductor = calc.get("conductor_preliminary", "Por validar")
    if arch in {"vfd_smart", "plc_hmi_control"}:
        rows = [
            {"cable": "C-PWR-01", "from": "QF-01", "to": "K1/VFD-01", "conductors": "3F+PE", "size": conductor, "length_m": round(i.cable_run_m * 0.08 + 2.0, 1), "service": "Alimentación VFD dentro tablero", "verify": "SCCR/radio/EMC"},
            {"cable": "C-MTR-01", "from": "VFD-01", "to": "MTR-01", "conductors": "3F+PE", "size": conductor, "length_m": round(i.cable_run_m * 1.18, 1), "service": "Salida VFD a motor", "verify": "longitud, cable apantallado si aplica, dv/dt"},
            {"cable": "C-CNT-01", "from": "TB1", "to": "Botonera", "conductors": "8C", "size": "#16 AWG Cu", "length_m": 8.0, "service": f"Mando {lab['cmd1']}/{lab['cmd2']} a entradas VFD", "verify": "IP/ambiente"},
            {"cable": "C-PRM-01", "from": "TB1", "to": lab["permissive"], "conductors": "4C", "size": "#16 AWG Cu", "length_m": 12.0, "service": f"Permisivos: {lab['note']}", "verify": "posición/sensor/setpoint"},
        ]
        if _machine_type(i) == "hoist" or i.needs_brake:
            rows.insert(2, {"cable": "C-BRK-01", "from": "VFD/BRK-CTRL", "to": "Freno", "conductors": "2C+PE", "size": "#16/#14 AWG según placa", "length_m": round(i.cable_run_m * 1.05, 1), "service": "Freno electromecánico", "verify": "tensión/corriente de freno"})
        return rows
    if arch == "star_delta":
        return [
            {"cable": "C-PWR-01", "from": "QF-01", "to": "KM-L/KM-Y/KM-Δ", "conductors": "3F+PE", "size": conductor, "length_m": round(i.cable_run_m * 0.1 + 2.0, 1), "service": "Fuerza tablero", "verify": "enclavamiento"},
            {"cable": "C-MTR-01", "from": "KM-L/KM-Y/KM-Δ", "to": "MTR-01", "conductors": "6F+PE", "size": conductor, "length_m": round(i.cable_run_m * 1.18, 1), "service": "Motor 6 terminales", "verify": "placa y caja de bornes"},
        ]
    rows = [
        {"cable": "C-PWR-01", "from": "QF-01", "to": "KM1/KM2" if i.needs_reversing else "KM1", "conductors": "3F+PE", "size": conductor, "length_m": round(i.cable_run_m * 0.08 + 2.0, 1), "service": "Dentro tablero", "verify": "calibre/radio"},
        {"cable": "C-MTR-01", "from": "OL-01", "to": "MTR-01", "conductors": "3F+PE", "size": conductor, "length_m": round(i.cable_run_m * 1.18, 1), "service": "Fuerza motor", "verify": "canalización/caída"},
        {"cable": "C-CNT-01", "from": "TB1", "to": "Botonera", "conductors": "8C", "size": "#16 AWG Cu", "length_m": 8.0, "service": "Mando", "verify": "IP/ambiente"},
    ]
    if _machine_type(i) == "hoist":
        rows.append({"cable": "C-LS-01", "from": "TB1", "to": "Final carrera sup/inf", "conductors": "4C", "size": "#16 AWG Cu", "length_m": 12.0, "service": "Seguridad de recorrido", "verify": "posición mecánica"})
    return rows


def drawio_xml(i: ProjectIntake, calc: Dict[str, Any], architecture: Dict[str, Any] | str | None = None) -> str:
    arch = _arch_id(architecture)
    project = xml_escape(i.project_name)
    flc = xml_escape(str(calc.get("full_load_current_a", "--")))
    breaker = xml_escape(str(calc.get("breaker_size_a", "--")))
    if arch in {"vfd_smart", "plc_hmi_control"}:
        cells = f'''
        <mxCell id="qf" value="QF-01 MCCB 3P&#xa;{breaker} A preliminar" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf" vertex="1" parent="1"><mxGeometry x="420" y="100" width="220" height="70" as="geometry" /></mxCell>
        <mxCell id="k1" value="K1 Contactor línea / seguridad" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366" vertex="1" parent="1"><mxGeometry x="420" y="220" width="220" height="70" as="geometry" /></mxCell>
        <mxCell id="vfd" value="VFD-01 Variador&#xa;Rampas / diagnóstico / freno" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656" vertex="1" parent="1"><mxGeometry x="420" y="340" width="220" height="80" as="geometry" /></mxCell>
        <mxCell id="m" value="MTR-01 Motor {i.motor_power_hp:g} HP&#xa;FLA {flc} A" style="ellipse;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450" vertex="1" parent="1"><mxGeometry x="465" y="535" width="130" height="90" as="geometry" /></mxCell>
        <mxCell id="e1" edge="1" parent="1" source="qf" target="k1" style="endArrow=block;html=1;rounded=0"><mxGeometry relative="1" as="geometry" /></mxCell>
        <mxCell id="e2" edge="1" parent="1" source="k1" target="vfd" style="endArrow=block;html=1;rounded=0"><mxGeometry relative="1" as="geometry" /></mxCell>
        <mxCell id="e3" edge="1" parent="1" source="vfd" target="m" style="endArrow=block;html=1;rounded=0"><mxGeometry relative="1" as="geometry" /></mxCell>'''
    else:
        cells = f'''
        <mxCell id="qf" value="QF-01 MCCB 3P&#xa;{breaker} A preliminar" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf" vertex="1" parent="1"><mxGeometry x="420" y="110" width="220" height="70" as="geometry" /></mxCell>
        <mxCell id="km" value="KM1/KM2 Contactores según arquitectura" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366" vertex="1" parent="1"><mxGeometry x="420" y="240" width="220" height="70" as="geometry" /></mxCell>
        <mxCell id="ol" value="OL-01 Sobrecarga" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656" vertex="1" parent="1"><mxGeometry x="420" y="370" width="220" height="70" as="geometry" /></mxCell>
        <mxCell id="m" value="MTR-01 Motor {i.motor_power_hp:g} HP&#xa;FLA {flc} A" style="ellipse;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450" vertex="1" parent="1"><mxGeometry x="465" y="510" width="130" height="90" as="geometry" /></mxCell>
        <mxCell id="e1" edge="1" parent="1" source="qf" target="km" style="endArrow=block;html=1;rounded=0"><mxGeometry relative="1" as="geometry" /></mxCell>
        <mxCell id="e2" edge="1" parent="1" source="km" target="ol" style="endArrow=block;html=1;rounded=0"><mxGeometry relative="1" as="geometry" /></mxCell>
        <mxCell id="e3" edge="1" parent="1" source="ol" target="m" style="endArrow=block;html=1;rounded=0"><mxGeometry relative="1" as="geometry" /></mxCell>'''
    return f'''<mxfile host="ControlPro" modified="{datetime.now(timezone.utc).isoformat()}" agent="ControlPro Advisor OS V12" version="24.0.0">
  <diagram id="controlpro-e001" name="E-001 Unifilar {xml_escape(arch)}">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="title" value="ControlPro OS V12 - {project} - {xml_escape(arch)}" style="text;html=1;strokeColor=none;fillColor=none;fontSize=18;fontStyle=1" vertex="1" parent="1"><mxGeometry x="40" y="30" width="700" height="40" as="geometry" /></mxCell>
        {cells}
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
