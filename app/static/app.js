const $ = (q) => document.querySelector(q);
const $$ = (q) => [...document.querySelectorAll(q)];
const numericFields = new Set(['motor_power_hp','voltage','phases','frequency_hz','full_load_amps','efficiency','power_factor','service_factor','rpm','starts_per_hour','ambient_temp_c','altitude_m','cable_run_m','control_voltage','labor_days_panel','labor_days_field','margin_percent','contingency_percent','load_capacity_ton','field_photos_count','short_circuit_available_ka','quote_valid_days','client_budget_limit']);
let currentPack = null;

function money(v){ return '$' + Number(v || 0).toLocaleString('es-EC',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function pct(v){ return Number(v || 0).toLocaleString('es-EC',{maximumFractionDigits:1}) + '%'; }
function setTextSafe(sel, value){ const el=$(sel); if(el) el.textContent=value; }
function setHtmlSafe(sel, value){ const el=$(sel); if(el) el.innerHTML=value; }
function showToast(msg){ const t=$('#toast'); t.textContent=msg; t.classList.add('show'); setTimeout(()=>t.classList.remove('show'),2600); }

function formToPayload(){
  const fd = new FormData($('#intakeForm'));
  const payload = {};
  for (const [k,v] of fd.entries()) {
    if (numericFields.has(k)) payload[k] = (v === '' || v === null) ? null : Number(v);
    else payload[k] = v;
  }
  ['needs_reversing','needs_brake','needs_limit_switches','needs_estop','needs_phase_monitor','nameplate_photo_confirmed','panel_photo_confirmed','site_photo_confirmed','auto_block_low_confidence'].forEach(k=>payload[k]=fd.has(k));
  if (!payload.full_load_amps || Number.isNaN(payload.full_load_amps)) payload.full_load_amps = null;
  return payload;
}

function setBusy(flag){ $('#generateBtn').disabled = flag; $('#generateBtn').textContent = flag ? 'Generando expediente...' : 'Generar expediente'; }

async function generate(){
  setBusy(true);
  try{
    const res = await fetch('/api/generate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(formToPayload())});
    if(!res.ok) throw new Error(await res.text());
    currentPack = await res.json();
    renderPack(currentPack);
    showToast('Expediente técnico-comercial generado');
  }catch(e){ console.error(e); showToast('Error generando: revisa datos de entrada'); }
  finally{ setBusy(false); }
}

async function exportEndpoint(endpoint, filename){
  const payload = formToPayload();
  const res = await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
  if(!res.ok){ showToast('No se pudo exportar'); return; }
  const text = await res.text();
  const blob = new Blob([text],{type:'text/markdown;charset=utf-8'});
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=filename; a.click(); URL.revokeObjectURL(url);
  showToast('Archivo exportado');
}

function renderPack(pack){
  $('#headline').textContent = pack.executive_verdict.headline;
  $('#verdict').textContent = pack.executive_verdict.verdict;
  $('#kpiCompleteness').textContent = pct(pack.statistics.engineering_completeness_percent);
  $('#kpiMarket').textContent = pct(pack.statistics.market_coverage_percent);
  $('#kpiPrice').textContent = money(pack.budget.recommended_sell_price);
  $('#kpiRFQ').textContent = pack.statistics.rfq_required_items;
  $('#ringMini').textContent = pct(pack.statistics.engineering_completeness_percent);
  $('#statusText').textContent = pack.validation.status;
  $('#singleLineSvg').innerHTML = pack.diagrams.single_line_svg;
  $('#controlSvg').innerHTML = pack.diagrams.control_ladder_svg;
  $('#panelSvg').innerHTML = pack.diagrams.panel_preview_svg;
  renderPrecision(pack);
  renderPriceTrustDashboard(pack);
  renderSavingsDashboard(pack);
  renderCAD(pack);
  renderGuidedFlow(pack);
  renderReviewBoard(pack);
  renderCalculations(pack);
  renderOptions(pack);
  renderBOM(pack);
  renderMarket(pack);
  renderBudget(pack);
  renderStats(pack);
  renderValidation(pack);
  renderDeliverables(pack);
  $('#rfqMessage').value = pack.rfq.message;
}

function renderPrecision(pack){
  setTextSafe('#qualityScore', pct(pack.data_quality?.score_percent || 0));
  setTextSafe('#quoteReadiness', pack.quote_readiness?.status || '--');
  setTextSafe('#constructionGate', pack.release_gates?.construction_ready ? 'Pasa a revisión' : 'Bloqueada');
  setHtmlSafe('#auditRows', (pack.consistency_audit?.checks || []).map(c=>`<div class="audit-item ${c.status}"><b>${c.name}</b><span>${c.status} · ${c.severity}</span><p>${c.detail}</p><small>${c.action}</small></div>`).join(''));
  setHtmlSafe('#assumptionRows', (pack.assumption_ledger || []).map(a=>`<div class="audit-item"><b>${a.topic}</b><span>Confianza: ${a.confidence}</span><p>${a.assumption}</p><small>${a.verification}</small></div>`).join(''));
}




function renderPriceTrustDashboard(pack){
  const s = pack.market?.summary || {};
  const audit = s.candidate_offer_audit || {};
  const cards = [
    ['PriceGuard global', pct(s.priceguard_score_percent || 0)],
    ['Veredicto', s.priceguard_verdict || 'Revisable'],
    ['Precios verdes', s.green_count || 0],
    ['Precios amarillos', s.yellow_count || 0],
    ['Precios rojos', s.red_count || 0],
    ['Ofertas auditadas', audit.total_candidate_offers || 0],
    ['Bajos rechazados', audit.suspicious_low_rejected || 0],
    ['Altos marcados', audit.suspicious_high_flagged || 0],
    ['RFQ requeridos', s.needs_rfq_count || 0],
  ];
  setHtmlSafe('#priceTrustCards', cards.map(([a,b])=>`<div><small>${a}</small><b>${b}</b></div>`).join(''));
  setHtmlSafe('#priceTrustPolicy', `<b>Regla de verdad:</b> ${s.truth_status || 'Precio cerrado solo con proveedor confirmado.'}<br><b>Alcance:</b> ${s.catalog_scope || 'Catálogo piloto + RFQ.'}`);
}

function renderSavingsDashboard(pack){
  const st = pack.statistics || {};
  const audit = st.candidate_offer_audit || {};
  const b = pack.budget || {};
  const rows = [
    ['Tiempo manual típico', st.estimated_manual_quote_hours || '4–8 h'],
    ['Con ControlPro', st.estimated_controlpro_quote_hours || '35–75 min'],
    ['Ahorro estimado', st.time_saved_estimate || '2–6 h'],
    ['Valor cotizado', money(b.recommended_sell_price || 0)],
    ['Margen sugerido', money(b.margin || 0)],
    ['Entregables listos', st.deliverables_ready || 0],
  ];
  setHtmlSafe('#savingsCards', rows.map(([a,b])=>`<div><small>${a}</small><b>${b}</b></div>`).join(''));
  const examples = (audit.blocked_examples || []).slice(0,4).map(x=>`<div class="audit-item warn"><b>${x.component_id}</b><span>${x.supplier} · ${money(x.price_usd)}</span><p>${x.brand_model}</p><small>Bloqueado/marcado: ${x.flags.join(', ')}</small></div>`).join('');
  setHtmlSafe('#candidateAudit', examples || '<div class="audit-item ok"><b>Sin anomalías candidatas fuertes</b><p>El catálogo piloto no muestra outliers graves para este caso.</p></div>');
}

function renderCAD(pack){
  const cad = pack.cad_outputs || {};
  const terminals = cad.terminal_schedule || [];
  const wires = cad.wire_schedule || [];
  setHtmlSafe('#terminalRows', terminals.map(r=>`<tr><td><b>${r.terminal}</b></td><td>${r.wire}</td><td>${r.from}</td><td>${r.to}</td><td>${r.function}</td></tr>`).join(''));
  setHtmlSafe('#wireRows', wires.map(r=>`<tr><td><b>${r.cable}</b></td><td>${r.from}</td><td>${r.to}</td><td>${r.conductors}</td><td>${r.size}</td><td>${r.length_m}</td></tr>`).join(''));
}

async function loadIntegrationStatus(){
  try{
    const [statusRes, envRes] = await Promise.all([fetch('/api/integrations/status'), fetch('/api/integrations/env-template')]);
    const status = await statusRes.json();
    const env = await envRes.text();
    setHtmlSafe('#apiStatusRows', (status.services || []).map(s=>`<div class="api-card ${s.configured?'ok':(s.enabled?'warn':'off')}"><b>${s.name}</b><span>${s.status}</span><p>${s.note}</p><small>${s.missing?.length ? 'Falta: '+s.missing.join(', ') : 'Listo para usar cuando el flujo lo active.'}</small></div>`).join(''));
    const envEl = $('#envTemplate'); if(envEl) envEl.value = env;
  }catch(e){ console.warn(e); }
}

function renderGuidedFlow(pack){
  const flow = pack.guided_flow || {};
  const actions = flow.next_best_actions || [];
  const steps = flow.modo_rapido || [];
  setHtmlSafe('#guidedSteps', `<b>Ruta del asesor:</b><div class="step-row">${steps.map(x=>`<span>${x}</span>`).join('')}</div><p><b>Siguiente acción:</b> ${actions[0] || 'Generar expediente y revisar compuertas.'}</p><small>${flow.market_status || ''}</small>`);
}

function renderReviewBoard(pack){
  const board = pack.review_board || {};
  const personas = board.personas || [];
  setHtmlSafe('#reviewBoardRows', personas.map(p=>`<div class="review-card"><b>${p.perfil}</b><span>${p.estado}</span><p><b>Pidió:</b> ${p.lo_que_exigia}</p><p><b>V11 responde:</b> ${p.respuesta_v10 || "Resuelto en esta versión"}</p></div>`).join('') + `<div class="review-card strong"><b>Veredicto</b><span>${board.veredicto || ''}</span><p>${board.regla_de_venta || ''}</p><small>${board.pendiente_realista || ''}</small></div>`);
}

function renderCalculations(pack){
  const c = pack.calculations;
  const cards = [
    ['Corriente nominal', `${c.full_load_current_a} A`, 'Base de protecciones y BOM', 'Confirmar con placa real'],
    ['Breaker preliminar', `${c.breaker_size_a} A`, 'Para presupuesto', 'Validar kAIC/SCCR'],
    ['Sobrecarga', `${c.overload_setting_a} A`, 'Ajuste preliminar', 'Depende de clase y placa'],
    ['Conductor', c.conductor_preliminary, 'Calibre preliminar', 'Validar tabla/canalización'],
    ['Caída tensión', `${c.voltage_drop_percent}%`, 'Estimación', 'Ajustar con longitud real'],
    ['Transformador control', `${c.control_transformer_va} VA`, 'Control preliminar', 'Confirmar cargas reales'],
    ['Arranque estimado', c.starting_current_estimate, 'DOL aproximado', 'Variable según motor/carga'],
  ];
  $('#calcCards').innerHTML = cards.map(([a,b,d,n])=>`<div class="metric-card"><small>${a}</small><b>${b}</b><p>${d}</p><small>${n}</small></div>`).join('');
}

function renderOptions(pack){
  $('#recommendedBadge').textContent = 'Recomendado: ' + pack.recommended_option.name;
  $('#optionsGrid').innerHTML = pack.alternatives.map(o=>`
    <div class="option-card">
      <h4>${o.name}</h4><p>${o.fit}</p>
      <small><b>Cómo funciona:</b> ${o.how_it_works || 'Solución de arranque/control.'}</small>
      <small><b>Cuándo es mejor:</b> ${o.better_when || o.sell_when}</small>
      <small><b>Impacto en precio:</b> ${o.price_impact || o.initial_cost}</small>
      <div class="bar"><span style="width:${o.control_quality}%"></span></div><small>Calidad de control ${o.control_quality}%</small>
      <div class="bar"><span style="width:${o.safety_depth}%"></span></div><small>Profundidad de seguridad ${o.safety_depth}%</small>
      <div class="bar"><span style="width:${100-(o.complexity||50)}%"></span></div><small>Facilidad de implementación ${100-(o.complexity||50)}%</small>
      <p><b>Riesgo:</b> ${o.risk}</p><p><b>Vender cuando:</b> ${o.sell_when}</p>
    </div>`).join('');
}

function renderBOM(pack){
  $('#bomRows').innerHTML = pack.requirements.map(r=>`<tr><td>${r.category}</td><td><b>${r.item}</b><br><small>${r.component_id}</small></td><td>${r.qty} ${r.unit}</td><td>${r.spec}<br><small>${r.risk_note || ''}</small></td><td>${(r.critical_checks || []).join(', ')}</td></tr>`).join('');
}

function renderMarket(pack){
  const s = pack.market.summary;
  $('#marketSummary').innerHTML = [
    ['Materiales', money(s.materials_cost)],
    ['Cobertura catálogo', pct(s.coverage_percent)],
    ['PriceGuard', pct(s.priceguard_score_percent)],
    ['Verdes / Amarillos / Rojos', `${s.green_count}/${s.yellow_count}/${s.red_count}`],
    ['RFQ requeridos', s.needs_rfq_count],
    ['Autocorregidos', s.auto_corrected_count || 0]
  ].map(([a,b])=>`<div class="summary-card"><small>${a}</small><b>${b}</b></div>`).join('') + `<div class="summary-card wide"><small>Regla de verdad</small><b>${s.truth_status || 'Precio cerrado solo con proveedor confirmado.'}</b></div>`;
  $('#marketRows').innerHTML = pack.market.price_decisions.map(d=>{
    const o = d.selected_offer;
    const provider = o ? `${o.supplier_name}<br><small>${o.brand} ${o.model} · ${o.city}</small>` : 'Sin proveedor<br><small>Usar RFQ</small>';
    const source = o ? `${o.source_type}<br><small>stock: ${o.stock_status} · ${o.lead_time_days} días · vigencia ${o.valid_until}</small>` : 'estimado';
    const band = d.market_band || {};
    const flags = (d.anomaly_flags || []).length ? `<br><small>Alertas: ${d.anomaly_flags.join(', ')}</small>` : '';
    return `<tr><td><b>${d.component_id}</b><br><small>Cant. ${d.qty}</small></td><td>${provider}</td><td><b>${money(d.unit_cost)}</b><br><small>Total ${money(d.extended_cost)} · banda mediana ${money(band.median||0)}</small></td><td>${source}</td><td><span class="semaforo ${d.semaphore_color}">${d.semaphore_color}</span><br><small>PG ${d.priceguard_score}% · ${d.confidence_label}</small>${flags}</td><td>${d.action_required}<br><small>${d.price_explanation || d.decision_note}</small></td></tr>`;
  }).join('');
}

function renderBudget(pack){
  const b = pack.budget;
  const rows = [
    ['Materiales', b.materials], ['Armado tablero', b.panel_labor], ['Instalación campo', b.field_labor], ['Ingeniería', b.engineering], ['Transporte/logística', b.transport_logistics], ['Contingencia', b.contingency], ['Margen', b.margin], ['Precio piso', b.floor_price], ['Precio recomendado', b.recommended_sell_price], ['Precio premium', b.premium_price]
  ];
  $('#budgetRows').innerHTML = rows.map(([k,v],idx)=>`<div class="budget-row"><span>${k}</span><strong class="${idx>=8?'accent':''}">${money(v)}</strong></div>`).join('') + `<p>${b.commercial_note}</p><p><b>Confianza de precio:</b> ${b.price_confidence}</p>`;
}

function renderStats(pack){
  const s = pack.statistics;
  const rows = [
    ['Completitud', pct(s.engineering_completeness_percent)], ['Cobertura mercado', pct(s.market_coverage_percent)], ['Confianza cotización', s.quote_confidence], ['Carga revisor', s.reviewer_correction_load], ['Ahorro estimado', s.time_saved_estimate], ['Entregables', s.deliverables_ready], ['Ítems RFQ', s.rfq_required_items], ['PriceGuard', pct(s.priceguard_score_percent || 0)], ['Semáforo precio', `${s.priceguard_green||0} V / ${s.priceguard_yellow||0} A / ${s.priceguard_red||0} R`], ['Autocorrecciones', s.auto_corrected_prices || 0], ['Ejecución', s.execution_days_estimate]
  ];
  $('#statsGrid').innerHTML = rows.map(([a,b])=>`<div><small>${a}</small><b>${b}</b></div>`).join('');
}

function renderValidation(pack){
  $('#ringValue').textContent = pct(pack.statistics.engineering_completeness_percent);
  $('#reviewerEffort').textContent = 'Carga de corrección humana: ' + pack.statistics.reviewer_correction_load;
  $('#validationText').textContent = pack.human_review_notice;
  $('#validationGates').innerHTML = pack.validation.gates.map(g=>`<li>${g}</li>`).join('');
}

function renderDeliverables(pack){
  $('#deliverableGrid').innerHTML = pack.deliverables.map(d=>`<div class="deliverable-card"><b>${d.name}</b><p>${d.description}</p></div>`).join('');
}


async function exportBinary(endpoint, filename){
  const res = await fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(formToPayload())});
  if(!res.ok){ showToast('No se pudo exportar'); return; }
  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a'); a.href=url; a.download=filename; a.click(); URL.revokeObjectURL(url);
  showToast('Archivo exportado');
}

function applyTemplate(name){
  const data = {
    hoist: {project_name:'Guinche de izaje — Cotización técnica premium', application:'Guinche / winche de izaje', load_type:'Izaje / guinche', motor_power_hp:25, voltage:460, phases:3, full_load_amps:30.4, needs_reversing:true, needs_brake:true, needs_limit_switches:true, needs_estop:true, needs_phase_monitor:true, user_notes:'Reemplazar tablero existente del guinche. Mantener huella de montaje. Considerar crecimiento futuro con variador.'},
    pump: {project_name:'Bomba industrial — Arranque protegido', application:'Bomba centrífuga industrial', load_type:'Bomba', motor_power_hp:10, voltage:220, phases:3, full_load_amps:null, needs_reversing:false, needs_brake:false, needs_limit_switches:false, needs_estop:true, needs_phase_monitor:true, user_notes:'Cotizar tablero para bomba con protección de motor, piloto de marcha/falla y opción de automatización futura.'},
    compressor: {project_name:'Compresor industrial — Control y protección', application:'Compresor de aire', load_type:'Compresor', motor_power_hp:30, voltage:440, phases:3, full_load_amps:null, needs_reversing:false, needs_brake:false, needs_limit_switches:false, needs_estop:true, needs_phase_monitor:true, user_notes:'Evaluar arranque y protección considerando alto torque y frecuencia de arranque.'},
    panel: {project_name:'Tablero de motor — Cotización técnica', application:'Motor industrial general', load_type:'Motor', motor_power_hp:15, voltage:220, phases:3, full_load_amps:null, needs_reversing:false, needs_brake:false, needs_limit_switches:false, needs_estop:true, needs_phase_monitor:true, user_notes:'Cotización rápida para tablero de control y fuerza.'}
  }[name];
  if(!data) return;
  Object.entries(data).forEach(([k,v])=>{ const el=document.querySelector(`[name="${k}"]`); if(!el) return; if(el.type==='checkbox') el.checked=Boolean(v); else el.value = v ?? ''; });
  showToast('Plantilla aplicada: ' + name);
  generate();
}

async function loadExample(){
  const res = await fetch('/api/example'); const data = await res.json();
  Object.entries(data).forEach(([k,v])=>{
    const el = document.querySelector(`[name="${k}"]`);
    if(!el) return;
    if(el.type === 'checkbox') el.checked = Boolean(v); else el.value = v ?? '';
  });
  showToast('Caso demo cargado');
  generate();
}

function setupPhotos(){
  $('#photoInput')?.addEventListener('change', (ev)=>{
    const files = [...ev.target.files].slice(0,8);
    if(!files.length) return;
    $('#photoStrip').innerHTML = '';
    files.forEach(f=>{
      const url = URL.createObjectURL(f);
      const card = document.createElement('div');
      card.className = 'photo-card';
      card.style.backgroundImage = `linear-gradient(180deg,transparent,rgba(0,0,0,.72)), url(${url})`;
      card.style.backgroundSize = 'cover'; card.style.backgroundPosition = 'center';
      card.innerHTML = `<span>${f.name}</span><small>evidencia local</small>`;
      $('#photoStrip').appendChild(card);
    });
  });
}

function setupNav(){
  $$('.sidebar a').forEach(a=>a.addEventListener('click',()=>{$$('.sidebar a').forEach(x=>x.classList.remove('active')); a.classList.add('active');}));
}

$('#generateBtn').addEventListener('click', generate);
$('#loadExampleBtn').addEventListener('click', loadExample);
$('#exportBtn').addEventListener('click', ()=>exportEndpoint('/api/export/markdown','controlpro_expediente_tecnico.md'));
$('#proposalBtn').addEventListener('click', ()=>exportEndpoint('/api/export/client-proposal','controlpro_propuesta_cliente.md'));
$('#pdfBtn')?.addEventListener('click', ()=>exportBinary('/api/export/pdf','controlpro_reporte_tecnico_comercial.pdf'));
$('#xlsxBtn')?.addEventListener('click', ()=>exportBinary('/api/export/bom-xlsx','controlpro_bom_cotizable.xlsx'));
$('#drawioBtn')?.addEventListener('click', ()=>exportBinary('/api/export/cad/drawio','controlpro_e001_unifilar.drawio'));
$('#wireBtn')?.addEventListener('click', ()=>exportBinary('/api/export/cad/wire-schedule-csv','controlpro_lista_cables.csv'));
$('#singleSvgBtn')?.addEventListener('click', ()=>exportBinary('/api/export/cad/single-line-svg','controlpro_e001_unifilar.svg'));
$('#controlSvgBtn')?.addEventListener('click', ()=>exportBinary('/api/export/cad/control-ladder-svg','controlpro_e002_ladder.svg'));
$('#panelSvgBtn')?.addEventListener('click', ()=>exportBinary('/api/export/cad/panel-layout-svg','controlpro_e003_layout_tablero.svg'));
$('#terminalBtn')?.addEventListener('click', ()=>exportBinary('/api/export/cad/terminal-schedule-csv','controlpro_lista_borneras.csv'));
$('#copyEnvBtn')?.addEventListener('click', async()=>{ await navigator.clipboard.writeText($('#envTemplate').value || ''); showToast('Plantilla .env copiada'); });
$$('.quick-chip').forEach(btn=>btn.addEventListener('click', ()=>applyTemplate(btn.dataset.template)));
$('#copyRfqBtn').addEventListener('click', async()=>{ await navigator.clipboard.writeText($('#rfqMessage').value || ''); showToast('RFQ copiado'); });
setupPhotos(); setupNav(); loadIntegrationStatus(); generate();
