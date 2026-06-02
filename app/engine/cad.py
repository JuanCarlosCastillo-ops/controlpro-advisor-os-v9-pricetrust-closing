from __future__ import annotations

from datetime import datetime, timezone
from html import escape
from typing import Any, Dict, List
from xml.sax.saxutils import escape as xml_escape

from .models import ProjectIntake


def _e(value: Any) -> str:
    return escape(str(value), quote=True)


def revision_block(title: str, project: str, rev: str = "A") -> str:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    return f"""
    <g class='title-block' font-family='Inter, Arial'>
      <rect x='686' y='650' width='466' height='126' fill='#0a1622' stroke='#9edcff' stroke-width='1.3'/>
      <line x1='686' y1='682' x2='1152' y2='682' stroke='#9edcff' stroke-width='1'/>
      <line x1='686' y1='714' x2='1152' y2='714' stroke='#9edcff' stroke-width='1'/>
      <line x1='894' y1='650' x2='894' y2='776' stroke='#9edcff' stroke-width='1'/>
      <line x1='1016' y1='714' x2='1016' y2='776' stroke='#9edcff' stroke-width='1'/>
      <text x='700' y='672' fill='#55c8ff' font-size='17' font-weight='800'>CONTROLPRO ADVISOR OS V7</text>
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
        .tag{fill:#071019;stroke:#55c8ff;stroke-width:1.3;rx:8}
        .txt{fill:#e6f7ff;font-family:Inter,Arial;font-size:15px}
        .small{fill:#a8c7da;font-family:Inter,Arial;font-size:12px}
        .blue{fill:#55c8ff;font-family:Inter,Arial;font-size:16px;font-weight:800}
        .warn{fill:#ffcf8a;font-family:Inter,Arial;font-size:12px}
      </style>
    </defs>
    <rect width='1200' height='800' fill='#061019'/>
    <rect width='1200' height='800' fill='url(#gridMajor)' opacity='0.64'/>
    """


def single_line_cad_svg(i: ProjectIntake, calc: Dict[str, Any]) -> str:
    flc = calc.get("full_load_current_a", "--")
    breaker = calc.get("breaker_size_a", "--")
    overload = calc.get("overload_setting_a", "--")
    conductor = calc.get("conductor_preliminary", "--")
    kaic = f"{i.short_circuit_available_ka} kA" if i.short_circuit_available_ka else "PENDIENTE"
    return f"""
<svg viewBox='0 0 1200 800' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='Diagrama unifilar CAD-like'>
  {cad_grid()}
  <text x='42' y='44' class='blue' font-size='24'>E-001 · DIAGRAMA UNIFILAR PRELIMINAR</text>
  <text x='42' y='70' class='small'>Proyecto: {_e(i.project_name)} · Aplicación: {_e(i.application)} · Ubicación: {_e(i.location_city)}, {_e(i.location_province)}</text>

  <g id='feeder'>
    <line x1='600' y1='95' x2='600' y2='145' class='bus'/>
    <rect x='500' y='145' width='200' height='56' class='device2'/>
    <text x='525' y='168' class='txt'>QF-01 · MCCB 3P</text>
    <text x='525' y='188' class='small'>{breaker} A · {int(i.voltage)} V · kAIC: {kaic}</text>
    <line x1='600' y1='201' x2='600' y2='250' class='bus'/>

    <rect x='500' y='250' width='200' height='56' class='device'/>
    <text x='525' y='273' class='txt'>FM-01 · Monitor fase</text>
    <text x='525' y='293' class='small'>Pérdida / secuencia / subtensión</text>
    <line x1='600' y1='306' x2='600' y2='358' class='bus'/>

    <rect x='472' y='358' width='256' height='70' class='device2'/>
    <text x='495' y='382' class='txt'>KM1/KM2 · Inversión enclavada</text>
    <text x='495' y='404' class='small'>AC-3 · bobina {int(i.control_voltage)} V · enclavamiento mecánico</text>
    <line x1='600' y1='428' x2='600' y2='478' class='bus'/>

    <rect x='500' y='478' width='200' height='56' class='device'/>
    <text x='525' y='501' class='txt'>OL-01 · Sobrecarga</text>
    <text x='525' y='521' class='small'>Ajuste preliminar: {overload} A</text>
    <line x1='600' y1='534' x2='600' y2='606' class='bus'/>

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
    <rect x='900' y='420' width='158' height='52' class='device2'/>
    <text x='923' y='452' class='txt'>TB-CONTROL</text>
  </g>

  <g id='terminales'>
    <rect x='72' y='126' width='292' height='176' class='device'/>
    <text x='96' y='154' class='blue'>Leyenda / tags</text>
    <text x='96' y='184' class='txt'>QF-01: Interruptor principal</text>
    <text x='96' y='210' class='txt'>KM1: Subir / KM2: Bajar</text>
    <text x='96' y='236' class='txt'>OL-01: Sobrecarga motor</text>
    <text x='96' y='262' class='txt'>TB: Borneras cableadas</text>
    <text x='96' y='288' class='warn'>Pendiente crítico: SCCR/kAIC real</text>
  </g>

  {revision_block('E-001 Unifilar', i.project_name)}
</svg>
""".strip()


def control_ladder_cad_svg(i: ProjectIntake) -> str:
    up = "SUBIR" if i.needs_reversing else "MARCHA"
    down = "BAJAR" if i.needs_reversing else "RUN"
    brake = "BRK" if i.needs_brake else "AUX"
    return f"""
<svg viewBox='0 0 1200 800' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='Diagrama ladder CAD-like'>
  {cad_grid()}
  <text x='42' y='44' class='blue' font-size='24'>E-002 · DIAGRAMA DE CONTROL / LADDER PRELIMINAR</text>
  <text x='42' y='70' class='small'>Control: {int(i.control_voltage)} V · lógica con paro, enclavamientos, finales y freno. Revisar numeración final antes de fabricación.</text>

  <g id='rails'>
    <line x1='90' y1='116' x2='90' y2='600' class='bus'/>
    <line x1='1110' y1='116' x2='1110' y2='600' class='bus'/>
    <text x='74' y='104' class='txt'>L+</text><text x='1094' y='104' class='txt'>L-</text>
  </g>

  <g id='rungs' class='wire'>
    <line x1='90' y1='150' x2='1110' y2='150'/>
    <line x1='90' y1='235' x2='1110' y2='235'/>
    <line x1='90' y1='320' x2='1110' y2='320'/>
    <line x1='90' y1='405' x2='1110' y2='405'/>
    <line x1='90' y1='490' x2='1110' y2='490'/>
    <line x1='90' y1='575' x2='1110' y2='575'/>
  </g>

  <g id='contacts' stroke='#e6f7ff' stroke-width='2.5' fill='none' font-family='Inter,Arial'>
    <path d='M170 126 v48 M196 126 v48 M278 126 v48 M304 126 v48 M402 126 v48 M428 126 v48'/>
    <circle cx='1000' cy='150' r='30'/>
    <path d='M170 211 v48 M196 211 v48 M310 211 v48 M336 211 v48 M492 211 v48 M518 211 v48 M650 211 v48 M676 211 v48'/>
    <circle cx='1000' cy='235' r='30'/>
    <path d='M170 296 v48 M196 296 v48 M310 296 v48 M336 296 v48 M492 296 v48 M518 296 v48 M650 296 v48 M676 296 v48'/>
    <circle cx='1000' cy='320' r='30'/>
    <path d='M170 381 v48 M196 381 v48 M350 381 v48 M376 381 v48 M528 381 v48 M554 381 v48'/>
    <circle cx='1000' cy='405' r='30'/>
    <path d='M170 466 v48 M196 466 v48 M350 466 v48 M376 466 v48'/>
    <circle cx='1000' cy='490' r='30'/>
    <path d='M170 551 v48 M196 551 v48 M350 551 v48 M376 551 v48 M528 551 v48 M554 551 v48'/>
    <circle cx='1000' cy='575' r='30'/>
  </g>

  <g font-family='Inter,Arial'>
    <text x='105' y='142' class='small'>R1</text><text x='160' y='116' class='txt'>S0 STOP NC</text><text x='260' y='116' class='txt'>S-ESTOP NC</text><text x='390' y='116' class='txt'>RESET</text><text x='980' y='156' class='txt'>CR</text>
    <text x='105' y='227' class='small'>R2</text><text x='160' y='201' class='txt'>CR NO</text><text x='294' y='201' class='txt'>S1 {up}</text><text x='472' y='201' class='txt'>LS-UP NC</text><text x='626' y='201' class='txt'>KM2 NC</text><text x='976' y='241' class='txt'>KM1</text>
    <text x='105' y='312' class='small'>R3</text><text x='160' y='286' class='txt'>CR NO</text><text x='294' y='286' class='txt'>S2 {down}</text><text x='472' y='286' class='txt'>LS-DN NC</text><text x='626' y='286' class='txt'>KM1 NC</text><text x='976' y='326' class='txt'>KM2</text>
    <text x='105' y='397' class='small'>R4</text><text x='160' y='371' class='txt'>KM1/KM2 NO</text><text x='330' y='371' class='txt'>OL NC</text><text x='504' y='371' class='txt'>FM OK</text><text x='976' y='411' class='txt'>{brake}</text>
    <text x='105' y='482' class='small'>R5</text><text x='160' y='456' class='txt'>OL TRIP</text><text x='330' y='456' class='txt'>FM FAIL</text><text x='968' y='496' class='txt'>ALM</text>
    <text x='105' y='567' class='small'>R6</text><text x='160' y='541' class='txt'>CR NO</text><text x='330' y='541' class='txt'>KM1 NO</text><text x='504' y='541' class='txt'>KM2 NO</text><text x='970' y='581' class='txt'>PIL</text>
  </g>

  <g id='terminal-tags' font-family='Inter,Arial'>
    <rect x='74' y='625' width='542' height='96' class='device'/>
    <text x='96' y='654' class='blue'>Numeración preliminar de cables</text>
    <text x='96' y='681' class='small'>W101 L+ → S0; W102 S0 → E-STOP; W103 E-STOP → CR; W201 CR → KM1; W301 CR → KM2; W401 KM1/KM2 → BRK.</text>
    <text x='96' y='704' class='warn'>Revisión de taller: confirmar borneras, colores, calibre de control y tensión real de bobinas/freno.</text>
  </g>
  {revision_block('E-002 Control ladder', i.project_name)}
</svg>
""".strip()


def panel_layout_cad_svg(i: ProjectIntake, requirements: List[Dict[str, Any]] | None = None) -> str:
    return f"""
<svg viewBox='0 0 1200 800' xmlns='http://www.w3.org/2000/svg' role='img' aria-label='Layout tablero CAD-like'>
  {cad_grid()}
  <text x='42' y='44' class='blue' font-size='24'>E-003 · LAYOUT PRELIMINAR DE TABLERO / BACKPLATE</text>
  <text x='42' y='70' class='small'>Distribución orientativa para cotización. Dimensiones finales dependen de marcas/modelos reales y disipación térmica.</text>
  <g transform='translate(170 110)'>
    <rect x='0' y='0' width='560' height='500' rx='14' fill='#0b1722' stroke='#9edcff' stroke-width='3'/>
    <rect x='24' y='22' width='512' height='38' fill='#123044' stroke='#55c8ff'/><text x='38' y='48' class='txt'>RIEL DIN SUPERIOR · CONTROL / PROTECCIONES</text>
    <rect x='52' y='86' width='112' height='76' class='device2'/><text x='70' y='128' class='small'>QF-01</text>
    <rect x='194' y='86' width='112' height='76' class='device'/><text x='213' y='128' class='small'>FM-01</text>
    <rect x='336' y='86' width='142' height='76' class='device'/><text x='352' y='128' class='small'>T1/FUS</text>

    <rect x='24' y='206' width='512' height='38' fill='#123044' stroke='#55c8ff'/><text x='38' y='232' class='txt'>RIEL DIN MEDIO · CONTACTORES / SOBRECARGA</text>
    <rect x='72' y='270' width='126' height='90' class='device2'/><text x='105' y='319' class='small'>KM1</text>
    <rect x='218' y='270' width='70' height='90' class='device'/><text x='235' y='319' class='small'>INT</text>
    <rect x='306' y='270' width='126' height='90' class='device2'/><text x='339' y='319' class='small'>KM2</text>
    <rect x='452' y='270' width='64' height='90' class='device'/><text x='466' y='319' class='small'>OL</text>

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
  <text x='170' y='642' class='warn'>Regla: no congelar layout hasta confirmar marca/modelo, dimensiones, disipación, radios de curva y acceso de mantenimiento.</text>
  {revision_block('E-003 Layout tablero', i.project_name)}
</svg>
""".strip()


def terminal_schedule(i: ProjectIntake) -> List[Dict[str, Any]]:
    rows = [
        {"terminal": "TB1-01", "wire": "W101", "from": "T1 secondary L+", "to": "S0 STOP NC", "function": "Alimentación control", "gauge": "#16 AWG Cu", "color": "Rojo"},
        {"terminal": "TB1-02", "wire": "W102", "from": "S0 STOP NC", "to": "S-ESTOP NC", "function": "Cadena de paro", "gauge": "#16 AWG Cu", "color": "Rojo"},
        {"terminal": "TB1-03", "wire": "W103", "from": "S-ESTOP NC", "to": "CR coil", "function": "Permisivo maestro", "gauge": "#16 AWG Cu", "color": "Rojo"},
        {"terminal": "TB1-04", "wire": "W201", "from": "S1 SUBIR", "to": "KM1 coil", "function": "Orden subir", "gauge": "#16 AWG Cu", "color": "Azul"},
        {"terminal": "TB1-05", "wire": "W301", "from": "S2 BAJAR", "to": "KM2 coil", "function": "Orden bajar", "gauge": "#16 AWG Cu", "color": "Azul"},
        {"terminal": "TB1-06", "wire": "W401", "from": "KM1/KM2 aux", "to": "BRK", "function": "Liberación freno", "gauge": "#16 AWG Cu", "color": "Naranja"},
        {"terminal": "TB1-07", "wire": "W501", "from": "OL/FM", "to": "ALM", "function": "Alarma/falla", "gauge": "#16 AWG Cu", "color": "Amarillo"},
        {"terminal": "TB1-08", "wire": "W000", "from": "Control common", "to": "L-", "function": "Retorno control", "gauge": "#16 AWG Cu", "color": "Blanco"},
    ]
    if not i.needs_reversing:
        rows = [r for r in rows if r["wire"] != "W301"]
    return rows


def wire_schedule(i: ProjectIntake, calc: Dict[str, Any]) -> List[Dict[str, Any]]:
    conductor = calc.get("conductor_preliminary", "Por validar")
    return [
        {"cable": "C-PWR-01", "from": "QF-01", "to": "KM1/KM2", "conductors": "3F+PE", "size": conductor, "length_m": round(i.cable_run_m * 0.08 + 2.0, 1), "service": "Dentro tablero", "verify": "calibre/radio"},
        {"cable": "C-MTR-01", "from": "OL-01", "to": "MTR-01", "conductors": "3F+PE", "size": conductor, "length_m": round(i.cable_run_m * 1.18, 1), "service": "Fuerza motor", "verify": "canalización/caída"},
        {"cable": "C-CNT-01", "from": "TB1", "to": "Botonera", "conductors": "8C", "size": "#16 AWG Cu", "length_m": 8.0, "service": "Mando", "verify": "IP/ambiente"},
        {"cable": "C-LS-01", "from": "TB1", "to": "Final carrera sup/inf", "conductors": "4C", "size": "#16 AWG Cu", "length_m": 12.0, "service": "Seguridad de recorrido", "verify": "posición mecánica"},
    ]


def drawio_xml(i: ProjectIntake, calc: Dict[str, Any]) -> str:
    # Archivo draw.io minimalista con bloques editables; sirve como puente para formalizar CAD/draw.io.
    project = xml_escape(i.project_name)
    flc = xml_escape(str(calc.get("full_load_current_a", "--")))
    breaker = xml_escape(str(calc.get("breaker_size_a", "--")))
    return f'''<mxfile host="ControlPro" modified="{datetime.now(timezone.utc).isoformat()}" agent="ControlPro Advisor OS V10" version="24.0.0">
  <diagram id="controlpro-e001" name="E-001 Unifilar">
    <mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="1169" pageHeight="827" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="title" value="ControlPro OS V10 - {project}" style="text;html=1;strokeColor=none;fillColor=none;fontSize=18;fontStyle=1" vertex="1" parent="1"><mxGeometry x="40" y="30" width="600" height="40" as="geometry" /></mxCell>
        <mxCell id="qf" value="QF-01 MCCB 3P&#xa;{breaker} A preliminar" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#dae8fc;strokeColor=#6c8ebf" vertex="1" parent="1"><mxGeometry x="420" y="110" width="220" height="70" as="geometry" /></mxCell>
        <mxCell id="km" value="KM1/KM2 Inversión enclavada" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#d5e8d4;strokeColor=#82b366" vertex="1" parent="1"><mxGeometry x="420" y="240" width="220" height="70" as="geometry" /></mxCell>
        <mxCell id="ol" value="OL-01 Sobrecarga" style="rounded=1;whiteSpace=wrap;html=1;fillColor=#fff2cc;strokeColor=#d6b656" vertex="1" parent="1"><mxGeometry x="420" y="370" width="220" height="70" as="geometry" /></mxCell>
        <mxCell id="m" value="MTR-01 Motor {i.motor_power_hp:g} HP&#xa;FLA {flc} A" style="ellipse;whiteSpace=wrap;html=1;fillColor=#f8cecc;strokeColor=#b85450" vertex="1" parent="1"><mxGeometry x="465" y="510" width="130" height="90" as="geometry" /></mxCell>
        <mxCell id="e1" edge="1" parent="1" source="qf" target="km" style="endArrow=block;html=1;rounded=0"><mxGeometry relative="1" as="geometry" /></mxCell>
        <mxCell id="e2" edge="1" parent="1" source="km" target="ol" style="endArrow=block;html=1;rounded=0"><mxGeometry relative="1" as="geometry" /></mxCell>
        <mxCell id="e3" edge="1" parent="1" source="ol" target="m" style="endArrow=block;html=1;rounded=0"><mxGeometry relative="1" as="geometry" /></mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>'''
