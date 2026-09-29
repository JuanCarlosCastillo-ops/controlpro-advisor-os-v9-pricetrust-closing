const state = { dashboard:null, assets:[], incidents:[], workOrders:[], audit:[] };
const $ = (id) => document.getElementById(id);
const esc = (v='') => String(v).replace(/[&<>'"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c]));
const fmt = (iso) => iso ? new Date(iso).toLocaleString('es-EC',{dateStyle:'short',timeStyle:'short'}) : '—';

async function api(path, options={}) {
  const key = localStorage.getItem('teod_api_key');
  const headers = {'Content-Type':'application/json', ...(options.headers||{})};
  if (key) headers['X-TEOD-API-Key'] = key;
  const res = await fetch(path, {...options, headers});
  if (!res.ok) throw new Error((await res.json().catch(()=>({detail:res.statusText}))).detail || 'Error');
  return res.json();
}
function toast(msg){const el=$('toast');el.textContent=msg;el.classList.add('show');setTimeout(()=>el.classList.remove('show'),2600)}
function badge(value){const v=esc(value||'');return '<span class="badge '+v+'">'+v+'</span>'}

async function refresh(){
  const [health,dashboard,assets,incidents,orders,audit] = await Promise.all([
    api('/api/ops/health'), api('/api/ops/dashboard'), api('/api/ops/assets'), api('/api/ops/incidents'), api('/api/ops/work-orders'), api('/api/ops/audit?limit=40')
  ]);
  $('system-status').textContent = health.status === 'ok' ? 'Sistema operativo' : 'Revisar sistema';
  Object.assign(state,{dashboard,assets,incidents,workOrders:orders,audit});
  renderAll();
}
function renderAll(){
  const c=state.dashboard.counts;
  $('m-assets').textContent=c.assets;$('m-incidents').textContent=c.open_incidents;$('m-critical').textContent=c.critical_incidents;$('m-approvals').textContent=c.pending_approvals;
  $('recent-incidents').innerHTML = state.dashboard.recent_incidents.length ? state.dashboard.recent_incidents.map(i=>'<div class="list-item"><div><strong>'+esc(i.title)+'</strong><small>'+esc(i.status)+' · '+fmt(i.created_at)+'</small></div>'+badge(i.severity)+'</div>').join('') : '<div class="empty">Sin incidencias.</div>';
  const pending=state.workOrders.filter(w=>w.status==='pending_approval').slice(0,6);
  $('recent-orders').innerHTML = pending.length ? pending.map(w=>'<div class="list-item"><div><strong>'+esc(w.title)+'</strong><small>'+esc(w.priority)+' · '+fmt(w.created_at)+'</small></div><button class="approve-btn" onclick="approveOrder(\''+w.id+'\')">Aprobar</button></div>').join('') : '<div class="empty">No hay aprobaciones pendientes.</div>';
  $('assets-table').innerHTML = table(['Tag','Activo','Tipo','Ubicación','V','A','Criticidad'], state.assets.map(a=>['<span class="tag">'+esc(a.tag)+'</span>',esc(a.name),esc(a.asset_type),esc(a.location),a.voltage_v??'—',a.rated_current_a??'—',badge(a.criticality)]));
  $('incidents-table').innerHTML = table(['Incidencia','Activo','Severidad','Estado','Fuente','Creada'], state.incidents.map(i=>[esc(i.title),'<span class="mono">'+esc(i.asset_id||'—')+'</span>',badge(i.severity),esc(i.status),esc(i.source),fmt(i.created_at)]));
  $('orders-table').innerHTML = table(['Orden','Prioridad','Estado','Aprobación','Creada'], state.workOrders.map(w=>[esc(w.title),badge(w.priority),badge(w.status),w.status==='pending_approval'?'<button class="approve-btn" onclick="approveOrder(\''+w.id+'\')">Aprobar</button>':esc(w.approved_by||'—'),fmt(w.created_at)]));
  $('audit-list').innerHTML = state.audit.length ? state.audit.map(e=>'<div class="event"><strong>'+esc(e.event_type)+'</strong><small>'+esc(e.entity_type)+' · '+esc(e.actor)+' · '+fmt(e.occurred_at)+'</small></div>').join('') : '<div class="empty">Sin eventos.</div>';
  const select=$('incident-asset');
  select.innerHTML='<option value="">Sin asociar</option>'+state.assets.map(a=>'<option value="'+esc(a.id)+'">'+esc(a.tag)+' — '+esc(a.name)+'</option>').join('');
}
function table(headers, rows){if(!rows.length)return '<div class="empty">Sin registros.</div>';return '<table class="data-table"><thead><tr>'+headers.map(h=>'<th>'+h+'</th>').join('')+'</tr></thead><tbody>'+rows.map(r=>'<tr>'+r.map(c=>'<td>'+c+'</td>').join('')+'</tr>').join('')+'</tbody></table>'}

async function approveOrder(id){
  const approver=prompt('Nombre de quien aprueba la orden:'); if(!approver)return;
  try{await api('/api/ops/work-orders/'+id+'/approve',{method:'POST',body:JSON.stringify({approver,note:'Aprobación desde TEOD Industrial AI Hub'})});toast('Orden aprobada y auditada');await refresh()}catch(e){toast('Error: '+e.message)}
}
window.approveOrder=approveOrder;

document.querySelectorAll('.nav-item').forEach(btn=>btn.addEventListener('click',()=>{
  document.querySelectorAll('.nav-item').forEach(x=>x.classList.remove('active'));btn.classList.add('active');
  document.querySelectorAll('.view').forEach(x=>x.classList.remove('active'));$((btn.dataset.view)+'-view').classList.add('active');
  const titles={dashboard:'Resumen operacional',assets:'Activos industriales',incidents:'Gestión de incidencias',workorders:'Órdenes de trabajo',audit:'Auditoría y trazabilidad'};$('page-title').textContent=titles[btn.dataset.view];
}));
$('new-incident-btn').addEventListener('click',()=>$('incident-dialog').showModal());
$('close-dialog').addEventListener('click',()=>$('incident-dialog').close());$('cancel-dialog').addEventListener('click',()=>$('incident-dialog').close());
$('seed-btn').addEventListener('click',async()=>{try{const r=await api('/api/ops/demo/seed',{method:'POST'});toast(r.seeded?'Caso industrial cargado':'Ya existen activos');await refresh()}catch(e){toast('Error: '+e.message)}});
$('incident-form').addEventListener('submit',async(e)=>{
  e.preventDefault(); const measurements={};
  if($('incident-temp').value)measurements.temperature_c=Number($('incident-temp').value);if($('incident-current').value)measurements.current_a=Number($('incident-current').value);
  const payload={asset_id:$('incident-asset').value||null,title:$('incident-title').value,description:$('incident-description').value,severity:$('incident-severity').value,source:'web_ui',measurements,attachments:[]};
  try{await api('/api/ops/incidents',{method:'POST',body:JSON.stringify(payload)});$('incident-dialog').close();$('incident-form').reset();toast('Incidencia analizada por 5 agentes');await refresh()}catch(err){toast('Error: '+err.message)}
});
refresh().catch(e=>{ $('system-status').textContent='Error de conexión'; toast('No se pudo cargar: '+e.message); });
