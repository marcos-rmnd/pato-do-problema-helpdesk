const API = "";

function token(){ return localStorage.getItem("pato_token"); }
function role(){ return localStorage.getItem("pato_role"); }
function uname(){ return localStorage.getItem("pato_name"); }

function escapeHtml(value){
  return String(value || "").replace(/[&<>"']/g, c => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", "\"":"&quot;", "'":"&#39;"
  }[c]));
}

function setSession(t, r, n){
  localStorage.setItem("pato_token", t);
  localStorage.setItem("pato_role", r);
  localStorage.setItem("pato_name", n);
}
function logout(){
  ["pato_token", "pato_role", "pato_name", "pato_default_channel", "pato_default_frequency"].forEach(k => localStorage.removeItem(k));
  location.href = "index.html";
}

async function api(path, method="GET", body=null){
  const headers = { "Content-Type":"application/json" };
  const t = token();
  if(t) headers["Authorization"] = "Bearer " + t;
  const res = await fetch(API + path, {
    method, headers,
    body: body ? JSON.stringify(body) : null
  });
  const data = await res.json().catch(()=> ({}));
  if(res.status === 401 && t){ logout(); throw new Error("Sessão expirada"); }
  if(!res.ok) throw new Error(data.detail || "Não foi possível concluir a ação agora.");
  return data;
}
function guard(expected){
  if(!token()){ location.href="index.html"; return; }
  if(expected === "auth"){ return; }
  const r = role();
  if(expected === "cliente" && r !== "cliente"){ location.href="painel.html"; }
  if(expected === "tech" && !["N1","N2","N3"].includes(r)){ location.href="cliente.html"; }
}

function priClass(p){
  return ({Crítica:"crit", Alta:"alta", Média:"media", Baixa:"baixa"})[p] || "media";
}

function statusClass(s){
  return ({
    "Aberto":"aberto",
    "Em análise":"andamento",
    "Em atendimento":"andamento",
    "Aguardando cliente":"aguardando",
    "Aguardando terceiro":"aguardando",
    "Resolvido":"resolvido",
    "Encerrado":"resolvido"
  })[s] || "aberto";
}

function slaClass(sla){
  return "sla-" + ((sla && sla.state) || "ok");
}

function ticketSla(t){
  return (t && t.sla) || { label:"No prazo", state:"ok", hours_left:0 };
}

function toast(msg, type="ok"){
  let host = document.getElementById("toastHost");
  if(!host){
    host = document.createElement("div");
    host.id = "toastHost";
    host.className = "toast-host";
    document.body.appendChild(host);
  }
  const el = document.createElement("div");
  el.className = "toast " + type;
  el.textContent = msg;
  host.appendChild(el);
  requestAnimationFrame(()=>el.classList.add("show"));
  setTimeout(()=>{ el.classList.remove("show"); setTimeout(()=>el.remove(),220); }, 3200);
}

function copyText(text, label="Copiado"){
  if(navigator.clipboard){
    navigator.clipboard.writeText(text).then(()=>toast(label));
  } else {
    toast(text);
  }
}

async function downloadUrl(url, filename=""){
  const headers = {};
  const t = token();
  if(t) headers["Authorization"] = "Bearer " + t;

  const res = await fetch(API + url, { headers });
  if(res.status === 401){ logout(); return; }
  if(!res.ok){
    const data = await res.json().catch(()=>({}));
    toast(data.detail || "Não foi possível baixar o arquivo.", "err");
    return;
  }

  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = objectUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(objectUrl);
}

function canTech(){
  return ["N1","N2","N3"].includes(role());
}

async function openProfile(){
  const me = await api("/api/me");
  let ov = document.getElementById("profileOverlay");
  if(ov) ov.remove();
  ov = document.createElement("div");
  ov.id = "profileOverlay";
  ov.className = "editor-overlay";
  ov.innerHTML = `
    <div class="editor-box">
      <div class="row-between mb"><h2 style="margin:0">Perfil</h2><button class="btn-ghost btn-sm" onclick="document.getElementById('profileOverlay').remove()">Fechar</button></div>
      <div class="detail-grid mb">
        <div class="detail-item"><div class="k">E-mail</div><div class="v">${escapeHtml(me.email)}</div></div>
        <div class="detail-item"><div class="k">Papel</div><div class="v">${escapeHtml(me.role)}</div></div>
      </div>
      <div class="field"><label class="fl">Nome</label><input class="in" id="profileName" value="${escapeHtml(me.name)}"></div>
      <div class="field"><label class="fl">Canal padrão</label><select class="in" id="profileChannel">
        <option>Chat</option>
      </select></div>
      <div class="field"><label class="fl">Frequência padrão</label><select class="in" id="profileFrequency">
        <option>Apenas atualizações importantes</option><option>Atualizações automáticas</option><option>Acompanhamento prioritário</option>
      </select></div>
      <button class="btn" style="width:100%" onclick="saveProfile()">Salvar preferências</button>
    </div>`;
  document.body.appendChild(ov);
  document.getElementById("profileChannel").value = localStorage.getItem("pato_default_channel") || "Chat";
  document.getElementById("profileFrequency").value = localStorage.getItem("pato_default_frequency") || "Apenas atualizações importantes";
}

async function saveProfile(){
  const name = document.getElementById("profileName").value.trim();
  const updated = await api("/api/me","PUT",{name});
  localStorage.setItem("pato_name", updated.name);
  localStorage.setItem("pato_default_channel", document.getElementById("profileChannel").value);
  localStorage.setItem("pato_default_frequency", document.getElementById("profileFrequency").value);
  const who = document.getElementById("who");
  if(who) who.textContent = updated.name;
  toast("Perfil atualizado.");
  document.getElementById("profileOverlay").remove();
}

function revealView(el){
  if(!el) return;
  el.classList.remove("view-live");
  void el.offsetWidth;
  el.classList.add("view-live");
}

function revealChildren(el){
  if(!el) return;
  el.classList.remove("reveal-stagger");
  void el.offsetWidth;
  el.classList.add("reveal-stagger");
}

function skeletonRows(count=3){
  return Array.from({length:count},()=>'<div class="skeleton-row"></div>').join("");
}

function setBusy(btn, busy, label){
  if(!btn) return;
  if(busy){
    btn.dataset.idleText = btn.textContent;
    btn.disabled = true;
    btn.classList.add("is-busy");
    if(label) btn.textContent = label;
  } else {
    btn.disabled = false;
    btn.classList.remove("is-busy");
    if(btn.dataset.idleText) btn.textContent = btn.dataset.idleText;
    delete btn.dataset.idleText;
  }
}

function flashElement(el){
  if(!el) return;
  el.classList.remove("success-pulse");
  void el.offsetWidth;
  el.classList.add("success-pulse");
}
