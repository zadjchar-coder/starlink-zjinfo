import os
from flask import Flask, render_template_string, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app = Flask(__name__)

# Configuration de la base de données SQLite persistante sur le cloud
db_path = os.path.join(os.path.dirname(__file__), 'starlink.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Modèle de données pour la table Client
class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), default=lambda: datetime.utcnow().isoformat())
    nom = db.Column(db.String(100), nullable=False)
    forfait = db.Column(db.String(100), nullable=False)
    montant = db.Column(db.Integer, nullable=False)
    mac = db.Column(db.String(50), nullable=True)
    statut = db.Column(db.String(20), default='attente')
    expire = db.Column(db.String(50), nullable=True)
    alerte = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            "id": self.id,
            "date": self.date,
            "nom": self.nom,
            "forfait": self.forfait,
            "montant": self.montant,
            "mac": self.mac,
            "statut": self.statut,
            "expire": self.expire,
            "alerte": self.alerte
        }

# FORCE LA CRÉATION DE LA BASE DE DONNÉES SUR RENDER
@app.before_request
def create_tables():
    db.create_all()

# Interface HTML et JavaScript intégrée pour le fonctionnement en ligne
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta http-equiv="Cache-Control" content="no-cache">
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
<title>Starlink ZJinfo</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0B132B;color:#fff;font-family:system-ui,-apple-system,sans-serif;-webkit-user-select:none;user-select:none}
.header{background:#0B132B;padding:16px;border-bottom:1px solid #1C2541;display:flex;align-items:center;gap:12px}
.header-icon{background:#2563EB;padding:10px;border-radius:12px;font-size:20px}
.header h1{color:#3B82F6;font-size:22px;font-weight:700}
.header p{color:#94A3B8;font-size:13px}
.container{padding:16px;max-width:1200px;margin:0 auto}
.card{background:#111827;border:1px solid #1F2937;border-radius:16px;padding:20px;margin-bottom:16px}
label{display:block;color:#D1D5DB;font-size:14px;margin-bottom:6px;margin-top:12px;font-weight:500}
input,select{width:100%;padding:12px;background:#1F2937;border:1px solid #374151;border-radius:10px;color:#fff;font-size:15px}
input:focus,select:focus{outline:none;border-color:#3B82F6;box-shadow:0 0 0 3px rgba(59,130,246,0.1)}
button{width:100%;padding:14px;background:#2563EB;border:none;border-radius:10px;color:#fff;font-weight:600;font-size:16px;margin-top:16px;cursor:pointer;transition:0.2s}
button:hover{background:#1D4ED8}
button:active{transform:scale(0.98)}
.btn-group{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:16px}
.btn-secondary{background:#374151}
.btn-secondary:hover{background:#4B5563}
.btn-green{background:#10B981}
.btn-green:hover{background:#059669}
.btn-red{background:#EF4444}
.btn-red:hover{background:#DC2626}
.stats{display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-bottom:16px}
.stat-card{background:#111827;border:1px solid #1F2937;border-radius:16px;padding:16px;transition:0.2s}
.stat-card:hover{border-color:#3B82F6}
.stat-label{color:#9CA3AF;font-size:13px;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px}
.stat-value{font-size:26px;font-weight:700}
.list-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:10px}
.list-title{display:flex;align-items:center;gap:8px;font-size:18px;font-weight:600}
.search{background:#1F2937;border:1px solid #374151;border-radius:10px;padding:10px 14px;color:#fff;width:160px;font-size:14px}
.search:focus{outline:none;border-color:#3B82F6}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:#9CA3AF;text-align:left;padding:14px 8px;font-weight:600;border-bottom:2px solid #1F2937;text-transform:uppercase;font-size:11px;letter-spacing:0.5px}
td{padding:14px 8px;border-bottom:1px solid #1F2937;color:#E5E7EB;vertical-align:middle}
.row-client{cursor:pointer}
.row-client:hover td{background:#1F2937}
.badge{padding:5px 10px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase}
.badge-attente{background:#FEF3C7;color:#92400E}
.badge-actif{background:#D1FAE5;color:#065F46}
.badge-expire{background:#FEE2E2;color:#991B1B}
.btn-sm{padding:7px 12px;font-size:11px;width:auto;margin:2px;border-radius:6px;font-weight:600}
.empty{padding:60px;text-align:center;color:#6B7280;font-size:14px}
.countdown{font-weight:700;font-family:'Courier New',monospace;font-size:14px}
.countdown.normal{color:#10B981}
.countdown.warning{color:#F59E0B}
.countdown.danger{color:#EF4444;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.4}}
@media(min-width:768px){.stats{grid-template-columns:repeat(5,1fr)}}
.sync-status{font-size:12px;color:#10B981;text-align:center;margin-top:8px}
.time-input-container {display: grid; grid-template-columns: 1fr 1fr; gap: 10px;}
.edit-time-grid {display: grid; grid-template-columns: 1fr 1fr; gap: 10px;}

.modal-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(5, 8, 22, 0.85); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 1000; 
  opacity: 0; pointer-events: none; transition: opacity 0.20s ease;
}
.modal-overlay.active { opacity: 1; pointer-events: auto; }
.modal-box {
  background: #111827; border: 1px solid #1F2937; border-radius: 20px;
  padding: 24px; width: 92%; max-width: 410px; box-shadow: 0 20px 40px rgba(0,0,0,0.7);
  max-height: 90vh; overflow-y: auto;
  transform: scale(0.95); transition: transform 0.20s ease;
}
.modal-overlay.active .modal-box { transform: scale(1); }
.modal-info { background: #1F2937; padding: 12px; border-radius: 10px; margin-top: 8px; font-size: 13px; color: #9CA3AF; border-left: 4px solid #3B82F6; }
.hint-longpress { text-align: center; color: #6B7280; font-size: 11px; margin-top: 4px; }
.alert-title { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 12px; display: flex; align-items: center; justify-content: center; gap: 8px; }
.alert-text { font-size: 14px; color: #E5E7EB; text-align: center; margin-bottom: 20px; line-height: 1.5; }
</style>
</head>
<body>

<div class="header">
  <div class="header-icon">📡</div>
  <div>
    <h1>Starlink ZJinfo</h1>
    <p>Gestion WiFi - Base de données Cloud</p>
  </div>
</div>

<div class="container">
  <div class="stats">
    <div class="stat-card"><div class="stat-label">Total Clients</div><div class="stat-value" id="total">0</div></div>
    <div class="stat-card"><div class="stat-label">En Attente</div><div class="stat-value" style="color:#F59E0B" id="attente">0</div></div>
    <div class="stat-card"><div class="stat-label">Actifs</div><div class="stat-value" style="color:#10B981" id="actifs">0</div></div>
    <div class="stat-card"><div class="stat-label">Expirés</div><div class="stat-value" style="color:#EF4444" id="expires">0</div></div>
    <div class="stat-card"><div class="stat-label">Encaissé</div><div class="stat-value" style="color:#3B82F6" id="caisse">0 Ar</div></div>
  </div>

  <div class="card">
    <div class="list-title" style="margin-bottom:16px">👤 Ajouter un client</div>
    <label>Nom du client</label>
    <input id="nom" placeholder="Ex: zino">
    
    <label>Ajuster la durée</label>
    <div class="time-input-container">
      <div>
        <span style="font-size:12px; color:#9CA3AF">Heure(s)</span>
        <input id="ajoutHeures" type="number" placeholder="Ex: 1" min="0" oninput="calculerPrixAutomatique()">
      </div>
      <div>
        <span style="font-size:12px; color:#9CA3AF">Minute(s)</span>
        <input id="ajoutMinutes" type="number" placeholder="Ex: 5" min="0" max="59" oninput="calculerPrixAutomatique()">
      </div>
    </div>
    
    <label>Montant (Ariary)</label>
    <input id="montant" type="number" placeholder="Ex: 1000" min="0">
    
    <label>Adresse MAC (optionnel)</label>
    <input id="mac" placeholder="00:1A:2B:3C:4D:5E">
    <button onclick="ajouter()">+ Ajouter le client</button>
    <div class="sync-status">☁️ Toutes vos données sont sécurisées en ligne</div>
  </div>

  <div class="card">
    <div class="list-header">
      <div class="list-title">📋 Liste des clients</div>
      <input class="search" placeholder="Rechercher..." id="search" oninput="filtrer()">
    </div>
    <p class="hint-longpress">💡 Appuyez longuement sur une ligne pour modifier les détails du client</p>
    <div style="overflow-x:auto; margin-top:8px">
    <table>
      <thead>
        <tr>
          <th>DATE</th>
          <th>NOM</th>
          <th>FORFAIT</th>
          <th>MONTANT</th>
          <th>EXPIRE / CHRONO</th>
          <th>STATUT</th>
          <th>ACTIONS</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
    </div>
  </div>
</div>

<div class="modal-overlay" id="prolongarModal">
  <div class="modal-box">
    <div class="list-title" id="prolongarTitre" style="color:#10B981">🕒 Ajouter du temps</div>
    <div class="modal-info" id="modalEtatActuel">Calcul...</div>
    <label>Temps additionnel</label>
    <div class="edit-time-grid">
      <div><span style="font-size:12px; color:#9CA3AF">Heure(s)</span><input id="modalHeures" type="number" placeholder="0" min="0" oninput="calculerPrixAutomatiqueModal()"></div>
      <div><span style="font-size:12px; color:#9CA3AF">Minute(s)</span><input id="modalMinutes" type="number" placeholder="30" min="0" oninput="calculerPrixAutomatiqueModal()"></div>
    </div>
    <label>Montant supplémentaire (Ar)</label>
    <input id="modalMontant" type="number" value="500" min="0">
    <div class="btn-group">
      <button class="btn-green" onclick="validerProlongation()">Valider</button>
      <button class="btn-secondary" onclick="fermerModal()">Annuler</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="editModal">
  <div class="modal-box">
    <div class="list-title" id="editModalTitre" style="color:#3B82F6">📝 Modifier la fiche</div>
    <div class="modal-info" id="editModalEtatActuel">Calcul...</div>
    <label>Nom du client</label>
    <input id="editNom">
    <label>Ajuster la durée</label>
    <div class="edit-time-grid">
      <div><span style="font-size:12px; color:#9CA3AF">Heure(s)</span><input id="editHeures" type="number" min="0"></div>
      <div><span style="font-size:12px; color:#9CA3AF">Minute(s)</span><input id="editMinutes" type="number" min="0" max="59"></div>
    </div>
    <label>Montant Global (Ar)</label>
    <input id="editMontant" type="number" min="0">
    <label>Adresse MAC</label>
    <input id="editMac">
    <label>Statut</label>
    <select id="editStatut">
      <option value="attente">En attente</option>
      <option value="actif">Actif</option>
      <option value="expiré">Expiré</option>
    </select>
    <div class="btn-group">
      <button class="btn-green" onclick="validerEditionComplete()">Enregistrer</button>
      <button class="btn-secondary" onclick="fermerModalEdit()">Annuler</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="confirmModal">
  <div class="modal-box" style="max-width: 350px;">
    <div class="alert-title" style="color:#EF4444">🗑️ Supprimer le client</div>
    <div class="alert-text" id="confirmModalText">Voulez-vous supprimer ce client ?</div>
    <div class="btn-group">
      <button class="btn-red" id="btnConfirmOk">Oui, Supprimer</button>
      <button class="btn-secondary" onclick="fermerModalConfirm()">Annuler</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="alertModal">
  <div class="modal-box" style="max-width: 380px; border-color: #EF4444;">
    <div class="alert-title" style="color:#EF4444; animation: blink 1s infinite;">⏰ TEMPS EXPIRÉ !</div>
    <div class="alert-text" id="alertModalText">Le forfait est terminé.</div>
    <div class="modal-info" style="border-left-color: #EF4444; margin-bottom: 15px; text-align: center; color:#fff;">
      ⚠️ Désactivez sa connexion sur l'antenne Starlink.
    </div>
    <button class="btn-red" onclick="fermerModalAlert()">Arrêter le son</button>
  </div>
</div>

<script>
let clients = [];
let indexEnCours = null;
let indexSuppressionEnCours = null;
let alerteAudio = new Audio('https://www.soundjay.com/buttons/sounds/button-3.mp3'); 
alerteAudio.loop = true;

document.addEventListener('click', function() {
  alerteAudio.play().then(() => { alerteAudio.pause(); alerteAudio.currentTime = 0; }).catch(() => {});
}, { once: true });

async function chargerDepuisServeur() {
  try {
    let response = await fetch('/api/clients');
    clients = await response.json();
    afficher();
  } catch(e) { console.error("Erreur de connexion cloud", e); }
}

function calculerPrixAutomatique() {
  let hInput = document.getElementById('ajoutHeures').value;
  let mInput = document.getElementById('ajoutMinutes').value;
  if(hInput === "" && mInput === "") { document.getElementById('montant').value = ""; return; }
  let heures = parseInt(hInput) || 0; let minutes = parseInt(mInput) || 0;
  document.getElementById('montant').value = (heures * 1000) + Math.round(minutes * (500 / 30));
}

function calculerPrixAutomatiqueModal() {
  let heures = parseInt(document.getElementById('modalHeures').value) || 0;
  let minutes = parseInt(document.getElementById('modalMinutes').value) || 0;
  document.getElementById('modalMontant').value = (heures * 1000) + Math.round(minutes * (500 / 30));
}

function sonnerAlerte(nom, forfait){
  alerteAudio.currentTime = 0; alerteAudio.play().catch(e => {});
  if(navigator.vibrate) { navigator.vibrate([600, 250, 600]); }
  document.getElementById('alertModalText').innerHTML = `Le forfait de <strong style="color:#3B82F6;">${nom}</strong> (${forfait}) est fini.`;
  document.getElementById('alertModal').classList.add('active');
}

function fermerModalAlert() { alerteAudio.pause(); alerteAudio.currentTime = 0; document.getElementById('alertModal').classList.remove('active'); }

function formatDate(d){
  if(!d) return '-'; d = new Date(d);
  return d.toLocaleDateString('fr-FR',{day:'2-digit',month:'2-digit'})+' '+d.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'});
}

function getCountdown(expire){
  if(!expire) return '-';
  let diff = new Date(expire) - new Date();
  if(diff <= 0) return '<span class="countdown danger">Expiré</span>';
  let h = Math.floor(diff/3600000); let m = Math.floor((diff%3600000)/60000); let s = Math.floor((diff%60000)/1000);
  let className = diff < 300000 ? 'countdown danger' : diff < 900000 ? 'countdown warning' : 'countdown normal';
  if(h > 0) return `<span class="${className}">${h}h ${m}m</span>`;
  return `<span class="${className}">${m}:${s.toString().padStart(2,'0')}</span>`;
}

function afficher(filtre=''){
  let html = '';
  let liste = clients.filter(c => c.nom.toLowerCase().includes(filtre.toLowerCase()));

  if(liste.length === 0){
    html = `<tr><td colspan="7" class="empty">Aucun client trouvé</td></tr>`;
  } else {
    liste.forEach((c)=>{
      let idx = clients.indexOf(c);
      let badge = c.statut==='actif'?'badge-actif':c.statut==='attente'?'badge-attente':'badge-expire';
      let actions = c.statut==='attente' 
        ? `<button class="btn-sm btn-green" onclick="event.stopPropagation(); activer(${idx})">Activer</button>`
        : `<button class="btn-sm btn-green" onclick="event.stopPropagation(); ouvrirModalProlongation(${idx})">${c.statut==='actif'?'+Temps':'Relancer'}</button>`;
      actions += `<button class="btn-sm btn-red" onclick="event.stopPropagation(); ouvrirModalConfirm(${idx})">Suppr</button>`;

      let expireDisplay = c.statut==='actif'? getCountdown(c.expire) : formatDate(c.expire);

      html += `<tr id="row-${idx}" class="client-row-element" data-index="${idx}">
        <td>${formatDate(c.date)}</td>
        <td><strong>${c.nom}</strong></td>
        <td>${c.forfait}</td>
        <td>${parseInt(c.montant).toLocaleString('fr-FR')} Ar</td>
        <td class="cell-countdown" data-expire="${c.expire||''}" data-statut="${c.statut}">${expireDisplay}</td>
        <td><span class="badge ${badge}">${c.statut}</span></td>
        <td>${actions}</td>
      </tr>`;
    });
  }

  document.getElementById('tbody').innerHTML = html;
  document.getElementById('total').textContent = clients.length;
  document.getElementById('attente').textContent = clients.filter(c=>c.statut==='attente').length;
  document.getElementById('actifs').textContent = clients.filter(c=>c.statut==='actif').length;
  document.getElementById('expires').textContent = clients.filter(c=>c.statut==='expiré').length;
  document.getElementById('caisse').textContent = clients.reduce((sum,c)=>sum+parseInt(c.montant||0),0).toLocaleString('fr-FR')+' Ar';

  attacherEvenementsAppuiLong();
  miseAjourDirecteModals();
}

let timerAppuiLong;
function attacherEvenementsAppuiLong() {
  document.querySelectorAll('.client-row-element').forEach(row => {
    let index = row.getAttribute('data-index');
    row.addEventListener('touchstart', () => { clearTimeout(timerAppuiLong); timerAppuiLong = setTimeout(() => { ouvrirModalEditionComplete(index); }, 700); }, { passive: true });
    row.addEventListener('touchend', () => clearTimeout(timerAppuiLong));
    row.addEventListener('touchmove', () => clearTimeout(timerAppuiLong));
    row.addEventListener('mousedown', () => { clearTimeout(timerAppuiLong); timerAppuiLong = setTimeout(() => { ouvrirModalEditionComplete(index); }, 700); });
    row.addEventListener('mouseup', () => clearTimeout(timerAppuiLong));
    row.addEventListener('mouseleave', () => clearTimeout(timerAppuiLong));
  });
}

function ouvrirModalEditionComplete(i) {
  indexEnCours = parseInt(i); let c = clients[indexEnCours]; if(!c) return;
  document.getElementById('editModalTitre').textContent = `📝 Fiche de : ${c.nom}`;
  document.getElementById('editNom').value = c.nom; document.getElementById('editMontant').value = c.montant;
  document.getElementById('editMac').value = c.mac || ''; document.getElementById('editStatut').value = c.statut;
  
  let totalMinutes = 0;
  if(c.forfait) {
    c.forfait.split('+').forEach(seg => {
      let num = parseInt(seg.trim()) || 0;
      if (seg.includes('Heure')) totalMinutes += num * 60; else if (seg.includes('min')) totalMinutes += num;
    });
  }
  let h = Math.floor(totalMinutes / 60); let m = totalMinutes % 60;
  document.getElementById('editHeures').value = h > 0 ? h : ''; document.getElementById('editMinutes').value = m > 0 ? m : '';
  document.getElementById('editModal').classList.add('active');
}

async function validerEditionComplete() {
  if(indexEnCours === null) return; let c = clients[indexEnCours];
  let h = parseInt(document.getElementById('editHeures').value) || 0;
  let m = parseInt(document.getElementById('editMinutes').value) || 0;
  
  let texteForfait = (h > 0 ? h + " Heure" + (h>1?"s":"") : "") + (m > 0 ? (h>0?" + ":"") + m + " min" : "");
  if (h === 0 && m === 0) texteForfait = "Sans forfait";
  
  let payload = {
    nom: document.getElementById('editNom').value.trim(),
    montant: parseInt(document.getElementById('editMontant').value) || 0,
    mac: document.getElementById('editMac').value.trim(),
    statut: document.getElementById('editStatut').value,
    forfait: texteForfait
  };

  if (payload.statut === 'actif') {
    let baseDate = (c.statut === 'actif' && c.expire) ? new Date(c.date) : new Date();
    baseDate.setHours(baseDate.getHours() + h); baseDate.setMinutes(baseDate.getMinutes() + m);
    payload.expire = baseDate.toISOString(); payload.alerte = false;
  } else if (payload.statut === 'expiré') {
    payload.expire = new Date().toISOString(); payload.alerte = true;
  } else { payload.expire = null; payload.alerte = false; }

  await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  fermerModalEdit(); chargerDepuisServeur();
}

function fermerModalEdit() { document.getElementById('editModal').classList.remove('active'); indexEnCours = null; }

async function ajouter(){
  let nom = document.getElementById('nom').value.trim();
  let h = parseInt(document.getElementById('ajoutHeures').value) || 0;
  let m = parseInt(document.getElementById('ajoutMinutes').value) || 0;
  let montant = parseInt(document.getElementById('montant').value) || 0;
  let mac = document.getElementById('mac').value.trim();
  if(!nom || (h === 0 && m === 0) || !montant) return;

  let texteForfait = (h > 0 ? h + " Heure" + (h>1?"s":"") : "") + (m > 0 ? (h>0?" + ":"") + m + " min" : "");

  await fetch('/api/clients', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nom: nom, forfait: texteForfait, montant: montant, mac: mac })
  });

  document.getElementById('nom').value=''; document.getElementById('mac').value='';
  document.getElementById('ajoutHeures').value=''; document.getElementById('ajoutMinutes').value=''; document.getElementById('montant').value='';
  chargerDepuisServeur();
}

async function activer(i){
  let c = clients[i]; let now = new Date(); let totalMin = 0;
  if(c.forfait){
    c.forfait.split('+').forEach(seg => {
      let num = parseInt(seg.trim()) || 0;
      if (seg.includes('Heure')) totalMin += num * 60; else if (seg.includes('min')) totalMin += num;
    });
  }
  now.setMinutes(now.getMinutes() + totalMin);
  await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ statut: 'actif', expire: now.toISOString(), alerte: false }) });
  chargerDepuisServeur();
}

function ouvrirModalProlongation(i) {
  indexEnCours = i; let c = clients[i];
  document.getElementById('prolongarTitre').textContent = `➕ Prolonger : ${c.nom}`;
  document.getElementById('modalHeures').value = ""; document.getElementById('modalMinutes').value = "30";
  calculerPrixAutomatiqueModal(); document.getElementById('prolongarModal').classList.add('active');
}

async function validerProlongation() {
  if (indexEnCours === null) return; let c = clients[indexEnCours];
  let h = parseInt(document.getElementById('modalHeures').value) || 0;
  let m = parseInt(document.getElementById('modalMinutes').value) || 0;
  let baseDate = (c.statut === 'actif' && c.expire) ? new Date(c.expire) : new Date();
  baseDate.setMinutes(baseDate.getMinutes() + (h * 60) + m);
  
  let texteAjout = (h > 0 ? h + " Heure" + (h>1?"s":"") : "") + (m > 0 ? " + " + m + " min" : "");

  await fetch(`/api/clients/${c.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      statut: 'actif', expire: baseDate.toISOString(), alerte: false,
      montant: (parseInt(c.montant) || 0) + (parseInt(document.getElementById('modalMontant').value) || 0),
      forfait: c.forfait + " + " + texteAjout
    })
  });
  fermerModal(); chargerDepuisServeur();
}

function fermerModal() { document.getElementById('prolongarModal').classList.remove('active'); indexEnCours = null; }
function ouvrirModalConfirm(i) { indexSuppressionEnCours = i; document.getElementById('confirmModalText').innerHTML = `Supprimer définitivement <strong>${clients[i].nom}</strong> ?`; document.getElementById('btnConfirmOk').onclick = validerSuppression; document.getElementById('confirmModal').classList.add('active'); }

async function validerSuppression() {
  if (indexSuppressionEnCours !== null) {
    await fetch(`/api/clients/${clients[indexSuppressionEnCours].id}`, { method: 'DELETE' });
    fermerModalConfirm(); chargerDepuisServeur();
  }
}
function fermerModalConfirm() { document.getElementById('confirmModal').classList.remove('active'); indexSuppressionEnCours = null; }

function miseAjourDirecteModals() {
  if (indexEnCours === null) return;
  if (document.getElementById('prolongarModal').classList.contains('active')) {
    let c = clients[indexEnCours]; let infoBox = document.getElementById('modalEtatActuel');
    let diff = c.expire ? new Date(c.expire) - new Date() : -1;
    if (c.statut === 'expiré' || diff <= 0) { infoBox.innerHTML = `Forfait : <span style="color:#EF4444; font-weight:bold;">Expiré</span>`; }
    else { let h = Math.floor(diff/3600000); let m = Math.floor((diff%3600000)/60000); infoBox.innerHTML = `Restant : <span style="color:#10B981; font-weight:bold;">${h}h ${m}m</span>`; }
  }
}

function filtrer(){ afficher(document.getElementById('search').value); }

async function verifier(){
  let now = new Date(); let recalculerTout = false;
  for(let c of clients) {
    if(c.statut==='actif' && c.expire && new Date(c.expire)<now && !c.alerte){
      c.statut='expiré'; c.alerte = true; recalculerTout = true;
      await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ statut: 'expiré', alerte: true }) });
      sonnerAlerte(c.nom,c.forfait);
    }
  }
  if(recalculerTout) { chargerDepuisServeur(); } 
  else {
    document.querySelectorAll('.cell-countdown').forEach(td => {
      let statut = td.getAttribute('data-statut'); let expire = td.getAttribute('data-expire');
      if (statut === 'actif' && expire) td.innerHTML = getCountdown(expire);
    });
    if(indexEnCours !== null) miseAjourDirecteModals();
  }
}

setInterval(verifier,1000);
window.onload = chargerDepuisServeur;
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    return jsonify([c.to_dict() for c in clients])

@app.route('/api/clients', methods=['POST'])
def add_client():
    data = request.json
    nouveau = Client(nom=data['nom'], forfait=data['forfait'], montant=data['montant'], mac=data.get('mac', ''))
    db.session.add(nouveau)
    db.session.commit()
    return jsonify(nouveau.to_dict()), 201

@app.route('/api/clients/<int:id>', methods=['PUT'])
def update_client(id):
    client = Client.query.get_or_404(id)
    data = request.json
    client.nom = data.get('nom', client.nom)
    client.forfait = data.get('forfait', client.forfait)
    client.montant = data.get('montant', client.montant)
    client.mac = data.get('mac', client.mac)
    client.statut = data.get('statut', client.statut)
    client.expire = data.get('expire', client.expire)
    client.alerte = data.get('alerte', client.alerte)
    db.session.commit()
    return jsonify(client.to_dict())

@app.route('/api/clients/<int:id>', methods=['DELETE'])
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True)  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: rgba(5, 8, 22, 0.85); backdrop-filter: blur(4px);
  display: flex; align-items: center; justify-content: center; z-index: 1000; 
  opacity: 0; pointer-events: none; transition: opacity 0.20s ease;
}
.modal-overlay.active { opacity: 1; pointer-events: auto; }
.modal-box {
  background: #111827; border: 1px solid #1F2937; border-radius: 20px;
  padding: 24px; width: 92%; max-width: 410px; box-shadow: 0 20px 40px rgba(0,0,0,0.7);
  max-height: 90vh; overflow-y: auto;
  transform: scale(0.95); transition: transform 0.20s ease;
}
.modal-overlay.active .modal-box { transform: scale(1); }
.modal-info { background: #1F2937; padding: 12px; border-radius: 10px; margin-top: 8px; font-size: 13px; color: #9CA3AF; border-left: 4px solid #3B82F6; }
.hint-longpress { text-align: center; color: #6B7280; font-size: 11px; margin-top: 4px; }
.alert-title { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 12px; display: flex; align-items: center; justify-content: center; gap: 8px; }
.alert-text { font-size: 14px; color: #E5E7EB; text-align: center; margin-bottom: 20px; line-height: 1.5; }
</style>
</head>
<body>

<div class="header">
  <div class="header-icon">📡</div>
  <div>
    <h1>Starlink ZJinfo</h1>
    <p>Gestion WiFi - Base de données Cloud</p>
  </div>
</div>

<div class="container">
  <div class="stats">
    <div class="stat-card"><div class="stat-label">Total Clients</div><div class="stat-value" id="total">0</div></div>
    <div class="stat-card"><div class="stat-label">En Attente</div><div class="stat-value" style="color:#F59E0B" id="attente">0</div></div>
    <div class="stat-card"><div class="stat-label">Actifs</div><div class="stat-value" style="color:#10B981" id="actifs">0</div></div>
    <div class="stat-card"><div class="stat-label">Expirés</div><div class="stat-value" style="color:#EF4444" id="expires">0</div></div>
    <div class="stat-card"><div class="stat-label">Encaissé</div><div class="stat-value" style="color:#3B82F6" id="caisse">0 Ar</div></div>
  </div>

  <div class="card">
    <div class="list-title" style="margin-bottom:16px">👤 Ajouter un client</div>
    <label>Nom du client</label>
    <input id="nom" placeholder="Ex: zino">
    
    <label>Ajuster la durée</label>
    <div class="time-input-container">
      <div>
        <span style="font-size:12px; color:#9CA3AF">Heure(s)</span>
        <input id="ajoutHeures" type="number" placeholder="Ex: 1" min="0" oninput="calculerPrixAutomatique()">
      </div>
      <div>
        <span style="font-size:12px; color:#9CA3AF">Minute(s)</span>
        <input id="ajoutMinutes" type="number" placeholder="Ex: 5" min="0" max="59" oninput="calculerPrixAutomatique()">
      </div>
    </div>
    
    <label>Montant (Ariary)</label>
    <input id="montant" type="number" placeholder="Ex: 1000" min="0">
    
    <label>Adresse MAC (optionnel)</label>
    <input id="mac" placeholder="00:1A:2B:3C:4D:5E">
    <button onclick="ajouter()">+ Ajouter le client</button>
    <div class="sync-status">☁️ Toutes vos données sont sécurisées en ligne</div>
  </div>

  <div class="card">
    <div class="list-header">
      <div class="list-title">📋 Liste des clients</div>
      <input class="search" placeholder="Rechercher..." id="search" oninput="filtrer()">
    </div>
    <p class="hint-longpress">💡 Appuyez longuement sur une ligne pour modifier les détails du client</p>
    <div style="overflow-x:auto; margin-top:8px">
    <table>
      <thead>
        <tr>
          <th>DATE</th>
          <th>NOM</th>
          <th>FORFAIT</th>
          <th>MONTANT</th>
          <th>EXPIRE / CHRONO</th>
          <th>STATUT</th>
          <th>ACTIONS</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
    </div>
  </div>
</div>

<div class="modal-overlay" id="prolongarModal">
  <div class="modal-box">
    <div class="list-title" id="prolongarTitre" style="color:#10B981">🕒 Ajouter du temps</div>
    <div class="modal-info" id="modalEtatActuel">Calcul...</div>
    <label>Temps additionnel</label>
    <div class="edit-time-grid">
      <div><span style="font-size:12px; color:#9CA3AF">Heure(s)</span><input id="modalHeures" type="number" placeholder="0" min="0" oninput="calculerPrixAutomatiqueModal()"></div>
      <div><span style="font-size:12px; color:#9CA3AF">Minute(s)</span><input id="modalMinutes" type="number" placeholder="30" min="0" oninput="calculerPrixAutomatiqueModal()"></div>
    </div>
    <label>Montant supplémentaire (Ar)</label>
    <input id="modalMontant" type="number" value="500" min="0">
    <div class="btn-group">
      <button class="btn-green" onclick="validerProlongation()">Valider</button>
      <button class="btn-secondary" onclick="fermerModal()">Annuler</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="editModal">
  <div class="modal-box">
    <div class="list-title" id="editModalTitre" style="color:#3B82F6">📝 Modifier la fiche</div>
    <div class="modal-info" id="editModalEtatActuel">Calcul...</div>
    <label>Nom du client</label>
    <input id="editNom">
    <label>Ajuster la durée</label>
    <div class="edit-time-grid">
      <div><span style="font-size:12px; color:#9CA3AF">Heure(s)</span><input id="editHeures" type="number" min="0"></div>
      <div><span style="font-size:12px; color:#9CA3AF">Minute(s)</span><input id="editMinutes" type="number" min="0" max="59"></div>
    </div>
    <label>Montant Global (Ar)</label>
    <input id="editMontant" type="number" min="0">
    <label>Adresse MAC</label>
    <input id="editMac">
    <label>Statut</label>
    <select id="editStatut">
      <option value="attente">En attente</option>
      <option value="actif">Actif</option>
      <option value="expiré">Expiré</option>
    </select>
    <div class="btn-group">
      <button class="btn-green" onclick="validerEditionComplete()">Enregistrer</button>
      <button class="btn-secondary" onclick="fermerModalEdit()">Annuler</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="confirmModal">
  <div class="modal-box" style="max-width: 350px;">
    <div class="alert-title" style="color:#EF4444">🗑️ Supprimer le client</div>
    <div class="alert-text" id="confirmModalText">Voulez-vous supprimer ce client ?</div>
    <div class="btn-group">
      <button class="btn-red" id="btnConfirmOk">Oui, Supprimer</button>
      <button class="btn-secondary" onclick="fermerModalConfirm()">Annuler</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="alertModal">
  <div class="modal-box" style="max-width: 380px; border-color: #EF4444;">
    <div class="alert-title" style="color:#EF4444; animation: blink 1s infinite;">⏰ TEMPS EXPIRÉ !</div>
    <div class="alert-text" id="alertModalText">Le forfait est terminé.</div>
    <div class="modal-info" style="border-left-color: #EF4444; margin-bottom: 15px; text-align: center; color:#fff;">
      ⚠️ Désactivez sa connexion sur l'antenne Starlink.
    </div>
    <button class="btn-red" onclick="fermerModalAlert()">Arrêter le son</button>
  </div>
</div>

<script>
let clients = [];
let indexEnCours = null;
let indexSuppressionEnCours = null;
let alerteAudio = new Audio('https://www.soundjay.com/buttons/sounds/button-3.mp3'); 
alerteAudio.loop = true;

document.addEventListener('click', function() {
  alerteAudio.play().then(() => { alerteAudio.pause(); alerteAudio.currentTime = 0; }).catch(() => {});
}, { once: true });

async function chargerDepuisServeur() {
  try {
    let response = await fetch('/api/clients');
    clients = await response.json();
    afficher();
  } catch(e) { console.error("Erreur de connexion cloud", e); }
}

function calculerPrixAutomatique() {
  let hInput = document.getElementById('ajoutHeures').value;
  let mInput = document.getElementById('ajoutMinutes').value;
  if(hInput === "" && mInput === "") { document.getElementById('montant').value = ""; return; }
  let heures = parseInt(hInput) || 0; let minutes = parseInt(mInput) || 0;
  document.getElementById('montant').value = (heures * 1000) + Math.round(minutes * (500 / 30));
}

function calculerPrixAutomatiqueModal() {
  let heures = parseInt(document.getElementById('modalHeures').value) || 0;
  let minutes = parseInt(document.getElementById('modalMinutes').value) || 0;
  document.getElementById('modalMontant').value = (heures * 1000) + Math.round(minutes * (500 / 30));
}

function sonnerAlerte(nom, forfait){
  alerteAudio.currentTime = 0; alerteAudio.play().catch(e => {});
  if(navigator.vibrate) { navigator.vibrate([600, 250, 600]); }
  document.getElementById('alertModalText').innerHTML = `Le forfait de <strong style="color:#3B82F6;">${nom}</strong> (${forfait}) est fini.`;
  document.getElementById('alertModal').classList.add('active');
}

function fermerModalAlert() { alerteAudio.pause(); alerteAudio.currentTime = 0; document.getElementById('alertModal').classList.remove('active'); }

function formatDate(d){
  if(!d) return '-'; d = new Date(d);
  return d.toLocaleDateString('fr-FR',{day:'2-digit',month:'2-digit'})+' '+d.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'});
}

function getCountdown(expire){
  if(!expire) return '-';
  let diff = new Date(expire) - new Date();
  if(diff <= 0) return '<span class="countdown danger">Expiré</span>';
  let h = Math.floor(diff/3600000); let m = Math.floor((diff%3600000)/60000); let s = Math.floor((diff%60000)/1000);
  let className = diff < 300000 ? 'countdown danger' : diff < 900000 ? 'countdown warning' : 'countdown normal';
  if(h > 0) return `<span class="${className}">${h}h ${m}m</span>`;
  return `<span class="${className}">${m}:${s.toString().padStart(2,'0')}</span>`;
}

function afficher(filtre=''){
  let html = '';
  let liste = clients.filter(c => c.nom.toLowerCase().includes(filtre.toLowerCase()));

  if(liste.length === 0){
    html = `<tr><td colspan="7" class="empty">Aucun client trouvé</td></tr>`;
  } else {
    liste.forEach((c)=>{
      let idx = clients.indexOf(c);
      let badge = c.statut==='actif'?'badge-actif':c.statut==='attente'?'badge-attente':'badge-expire';
      let actions = c.statut==='attente' 
        ? `<button class="btn-sm btn-green" onclick="event.stopPropagation(); activer(${idx})">Activer</button>`
        : `<button class="btn-sm btn-green" onclick="event.stopPropagation(); ouvrirModalProlongation(${idx})">${c.statut==='actif'?'+Temps':'Relancer'}</button>`;
      actions += `<button class="btn-sm btn-red" onclick="event.stopPropagation(); ouvrirModalConfirm(${idx})">Suppr</button>`;

      let expireDisplay = c.statut==='actif'? getCountdown(c.expire) : formatDate(c.expire);

      html += `<tr id="row-${idx}" class="client-row-element" data-index="${idx}">
        <td>${formatDate(c.date)}</td>
        <td><strong>${c.nom}</strong></td>
        <td>${c.forfait}</td>
        <td>${parseInt(c.montant).toLocaleString('fr-FR')} Ar</td>
        <td class="cell-countdown" data-expire="${c.expire||''}" data-statut="${c.statut}">${expireDisplay}</td>
        <td><span class="badge ${badge}">${c.statut}</span></td>
        <td>${actions}</td>
      </tr>`;
    });
  }

  document.getElementById('tbody').innerHTML = html;
  document.getElementById('total').textContent = clients.length;
  document.getElementById('attente').textContent = clients.filter(c=>c.statut==='attente').length;
  document.getElementById('actifs').textContent = clients.filter(c=>c.statut==='actif').length;
  document.getElementById('expires').textContent = clients.filter(c=>c.statut==='expiré').length;
  document.getElementById('caisse').textContent = clients.reduce((sum,c)=>sum+parseInt(c.montant||0),0).toLocaleString('fr-FR')+' Ar';

  attacherEvenementsAppuiLong();
  miseAjourDirecteModals();
}

let timerAppuiLong;
function attacherEvenementsAppuiLong() {
  document.querySelectorAll('.client-row-element').forEach(row => {
    let index = row.getAttribute('data-index');
    row.addEventListener('touchstart', () => { clearTimeout(timerAppuiLong); timerAppuiLong = setTimeout(() => { ouvrirModalEditionComplete(index); }, 700); }, { passive: true });
    row.addEventListener('touchend', () => clearTimeout(timerAppuiLong));
    row.addEventListener('touchmove', () => clearTimeout(timerAppuiLong));
    row.addEventListener('mousedown', () => { clearTimeout(timerAppuiLong); timerAppuiLong = setTimeout(() => { ouvrirModalEditionComplete(index); }, 700); });
    row.addEventListener('mouseup', () => clearTimeout(timerAppuiLong));
    row.addEventListener('mouseleave', () => clearTimeout(timerAppuiLong));
  });
}

function ouvrirModalEditionComplete(i) {
  indexEnCours = parseInt(i); let c = clients[indexEnCours]; if(!c) return;
  document.getElementById('editModalTitre').textContent = `📝 Fiche de : ${c.nom}`;
  document.getElementById('editNom').value = c.nom; document.getElementById('editMontant').value = c.montant;
  document.getElementById('editMac').value = c.mac || ''; document.getElementById('editStatut').value = c.statut;
  
  let totalMinutes = 0;
  if(c.forfait) {
    c.forfait.split('+').forEach(seg => {
      let num = parseInt(seg.trim()) || 0;
      if (seg.includes('Heure')) totalMinutes += num * 60; else if (seg.includes('min')) totalMinutes += num;
    });
  }
  let h = Math.floor(totalMinutes / 60); let m = totalMinutes % 60;
  document.getElementById('editHeures').value = h > 0 ? h : ''; document.getElementById('editMinutes').value = m > 0 ? m : '';
  document.getElementById('editModal').classList.add('active');
}

async function validerEditionComplete() {
  if(indexEnCours === null) return; let c = clients[indexEnCours];
  let h = parseInt(document.getElementById('editHeures').value) || 0;
  let m = parseInt(document.getElementById('editMinutes').value) || 0;
  
  let texteForfait = (h > 0 ? h + " Heure" + (h>1?"s":"") : "") + (m > 0 ? (h>0?" + ":"") + m + " min" : "");
  if (h === 0 && m === 0) texteForfait = "Sans forfait";
  
  let payload = {
    nom: document.getElementById('editNom').value.trim(),
    montant: parseInt(document.getElementById('editMontant').value) || 0,
    mac: document.getElementById('editMac').value.trim(),
    statut: document.getElementById('editStatut').value,
    forfait: texteForfait
  };

  if (payload.statut === 'actif') {
    let baseDate = (c.statut === 'actif' && c.expire) ? new Date(c.date) : new Date();
    baseDate.setHours(baseDate.getHours() + h); baseDate.setMinutes(baseDate.getMinutes() + m);
    payload.expire = baseDate.toISOString(); payload.alerte = false;
  } else if (payload.statut === 'expiré') {
    payload.expire = new Date().toISOString(); payload.alerte = true;
  } else { payload.expire = null; payload.alerte = false; }

  await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  fermerModalEdit(); chargerDepuisServeur();
}

function fermerModalEdit() { document.getElementById('editModal').classList.remove('active'); indexEnCours = null; }

async function ajouter(){
  let nom = document.getElementById('nom').value.trim();
  let h = parseInt(document.getElementById('ajoutHeures').value) || 0;
  let m = parseInt(document.getElementById('ajoutMinutes').value) || 0;
  let montant = parseInt(document.getElementById('montant').value) || 0;
  let mac = document.getElementById('mac').value.trim();
  if(!nom || (h === 0 && m === 0) || !montant) return;

  let texteForfait = (h > 0 ? h + " Heure" + (h>1?"s":"") : "") + (m > 0 ? (h>0?" + ":"") + m + " min" : "");

  await fetch('/api/clients', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nom: nom, forfait: texteForfait, montant: montant, mac: mac })
  });

  document.getElementById('nom').value=''; document.getElementById('mac').value='';
  document.getElementById('ajoutHeures').value=''; document.getElementById('ajoutMinutes').value=''; document.getElementById('montant').value='';
  chargerDepuisServeur();
}

async function activer(i){
  let c = clients[i]; let now = new Date(); let totalMin = 0;
  if(c.forfait){
    c.forfait.split('+').forEach(seg => {
      let num = parseInt(seg.trim()) || 0;
      if (seg.includes('Heure')) totalMin += num * 60; else if (seg.includes('min')) totalMin += num;
    });
  }
  now.setMinutes(now.getMinutes() + totalMin);
  await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ statut: 'actif', expire: now.toISOString(), alerte: false }) });
  chargerDepuisServeur();
}

function ouvrirModalProlongation(i) {
  indexEnCours = i; let c = clients[i];
  document.getElementById('prolongarTitre').textContent = `➕ Prolonger : ${c.nom}`;
  document.getElementById('modalHeures').value = ""; document.getElementById('modalMinutes').value = "30";
  calculerPrixAutomatiqueModal(); document.getElementById('prolongarModal').classList.add('active');
}

async function validerProlongation() {
  if (indexEnCours === null) return; let c = clients[indexEnCours];
  let h = parseInt(document.getElementById('modalHeures').value) || 0;
  let m = parseInt(document.getElementById('modalMinutes').value) || 0;
  let baseDate = (c.statut === 'actif' && c.expire) ? new Date(c.expire) : new Date();
  baseDate.setMinutes(baseDate.getMinutes() + (h * 60) + m);
  
  let texteAjout = (h > 0 ? h + " Heure" + (h>1?"s":"") : "") + (m > 0 ? " + " + m + " min" : "");

  await fetch(`/api/clients/${c.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      statut: 'actif', expire: baseDate.toISOString(), alerte: false,
      montant: (parseInt(c.montant) || 0) + (parseInt(document.getElementById('modalMontant').value) || 0),
      forfait: c.forfait + " + " + texteAjout
    })
  });
  fermerModal(); chargerDepuisServeur();
}

function fermerModal() { document.getElementById('prolongarModal').classList.remove('active'); indexEnCours = null; }
function ouvrirModalConfirm(i) { indexSuppressionEnCours = i; document.getElementById('confirmModalText').innerHTML = `Supprimer définitivement <strong>${clients[i].nom}</strong> ?`; document.getElementById('btnConfirmOk').onclick = validerSuppression; document.getElementById('confirmModal').classList.add('active'); }

async function validerSuppression() {
  if (indexSuppressionEnCours !== null) {
    await fetch(`/api/clients/${clients[indexSuppressionEnCours].id}`, { method: 'DELETE' });
    fermerModalConfirm(); chargerDepuisServeur();
  }
}
function fermerModalConfirm() { document.getElementById('confirmModal').classList.remove('active'); indexSuppressionEnCours = null; }

function miseAjourDirecteModals() {
  if (indexEnCours === null) return;
  if (document.getElementById('prolongarModal').classList.contains('active')) {
    let c = clients[indexEnCours]; let infoBox = document.getElementById('modalEtatActuel');
    let diff = c.expire ? new Date(c.expire) - new Date() : -1;
    if (c.statut === 'expiré' || diff <= 0) { infoBox.innerHTML = `Forfait : <span style="color:#EF4444; font-weight:bold;">Expiré</span>`; }
    else { let h = Math.floor(diff/3600000); let m = Math.floor((diff%3600000)/60000); infoBox.innerHTML = `Restant : <span style="color:#10B981; font-weight:bold;">${h}h ${m}m</span>`; }
  }
}

function filtrer(){ afficher(document.getElementById('search').value); }

async function verifier(){
  let now = new Date(); let recalculerTout = false;
  for(let c of clients) {
    if(c.statut==='actif' && c.expire && new Date(c.expire)<now && !c.alerte){
      c.statut='expiré'; c.alerte = true; recalculerTout = true;
      await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ statut: 'expiré', alerte: true }) });
      sonnerAlerte(c.nom,c.forfait);
    }
  }
  if(recalculerTout) { chargerDepuisServeur(); } 
  else {
    document.querySelectorAll('.cell-countdown').forEach(td => {
      let statut = td.getAttribute('data-statut'); let expire = td.getAttribute('data-expire');
      if (statut === 'actif' && expire) td.innerHTML = getCountdown(expire);
    });
    if(indexEnCours !== null) miseAjourDirecteModals();
  }
}

setInterval(verifier,1000);
window.onload = chargerDepuisServeur;
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    return jsonify([c.to_dict() for c in clients])

@app.route('/api/clients', methods=['POST'])
def add_client():
    data = request.json
    nouveau = Client(nom=data['nom'], forfait=data['forfait'], montant=data['montant'], mac=data.get('mac', ''))
    db.session.add(nouveau)
    db.session.commit()
    return jsonify(nouveau.to_dict()), 201

@app.route('/api/clients/<int:id>', methods=['PUT'])
def update_client(id):
    client = Client.query.get_or_404(id)
    data = request.json
    client.nom = data.get('nom', client.nom)
    client.forfait = data.get('forfait', client.forfait)
    client.montant = data.get('montant', client.montant)
    client.mac = data.get('mac', client.mac)
    client.statut = data.get('statut', client.statut)
    client.expire = data.get('expire', client.expire)
    client.alerte = data.get('alerte', client.alerte)
    db.session.commit()
    return jsonify(client.to_dict())

@app.route('/api/clients/<int:id>', methods=['DELETE'])
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True).modal-overlay.active { opacity: 1; pointer-events: auto; }
.modal-box {
  background: #111827; border: 1px solid #1F2937; border-radius: 20px;
  padding: 24px; width: 92%; max-width: 410px; box-shadow: 0 20px 40px rgba(0,0,0,0.7);
  max-height: 90vh; overflow-y: auto;
  transform: scale(0.95); transition: transform 0.20s ease;
}
.modal-overlay.active .modal-box { transform: scale(1); }
.modal-info { background: #1F2937; padding: 12px; border-radius: 10px; margin-top: 8px; font-size: 13px; color: #9CA3AF; border-left: 4px solid #3B82F6; }
.hint-longpress { text-align: center; color: #6B7280; font-size: 11px; margin-top: 4px; }
.alert-title { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 12px; display: flex; align-items: center; justify-content: center; gap: 8px; }
.alert-text { font-size: 14px; color: #E5E7EB; text-align: center; margin-bottom: 20px; line-height: 1.5; }
</style>
</head>
<body>

<div class="header">
  <div class="header-icon">📡</div>
  <div>
    <h1>Starlink ZJinfo</h1>
    <p>Gestion WiFi - Base de données Cloud</p>
  </div>
</div>

<div class="container">
  <div class="stats">
    <div class="stat-card"><div class="stat-label">Total Clients</div><div class="stat-value" id="total">0</div></div>
    <div class="stat-card"><div class="stat-label">En Attente</div><div class="stat-value" style="color:#F59E0B" id="attente">0</div></div>
    <div class="stat-card"><div class="stat-label">Actifs</div><div class="stat-value" style="color:#10B981" id="actifs">0</div></div>
    <div class="stat-card"><div class="stat-label">Expirés</div><div class="stat-value" style="color:#EF4444" id="expires">0</div></div>
    <div class="stat-card"><div class="stat-label">Encaissé</div><div class="stat-value" style="color:#3B82F6" id="caisse">0 Ar</div></div>
  </div>

  <div class="card">
    <div class="list-title" style="margin-bottom:16px">👤 Ajouter un client</div>
    <label>Nom du client</label>
    <input id="nom" placeholder="Ex: zino">
    
    <label>Ajuster la durée</label>
    <div class="time-input-container">
      <div>
        <span style="font-size:12px; color:#9CA3AF">Heure(s)</span>
        <input id="ajoutHeures" type="number" placeholder="Ex: 1" min="0" oninput="calculerPrixAutomatique()">
      </div>
      <div>
        <span style="font-size:12px; color:#9CA3AF">Minute(s)</span>
        <input id="ajoutMinutes" type="number" placeholder="Ex: 5" min="0" max="59" oninput="calculerPrixAutomatique()">
      </div>
    </div>
    
    <label>Montant (Ariary)</label>
    <input id="montant" type="number" placeholder="Ex: 1000" min="0">
    
    <label>Adresse MAC (optionnel)</label>
    <input id="mac" placeholder="00:1A:2B:3C:4D:5E">
    <button onclick="ajouter()">+ Ajouter le client</button>
    <div class="sync-status">☁️ Toutes vos données sont sécurisées en ligne</div>
  </div>

  <div class="card">
    <div class="list-header">
      <div class="list-title">📋 Liste des clients</div>
      <input class="search" placeholder="Rechercher..." id="search" oninput="filtrer()">
    </div>
    <p class="hint-longpress">💡 Appuyez longuement sur une ligne pour modifier les détails du client</p>
    <div style="overflow-x:auto; margin-top:8px">
    <table>
      <thead>
        <tr>
          <th>DATE</th>
          <th>NOM</th>
          <th>FORFAIT</th>
          <th>MONTANT</th>
          <th>EXPIRE / CHRONO</th>
          <th>STATUT</th>
          <th>ACTIONS</th>
        </tr>
      </thead>
      <tbody id="tbody"></tbody>
    </table>
    </div>
  </div>
</div>

<div class="modal-overlay" id="prolongarModal">
  <div class="modal-box">
    <div class="list-title" id="prolongarTitre" style="color:#10B981">🕒 Ajouter du temps</div>
    <div class="modal-info" id="modalEtatActuel">Calcul...</div>
    <label>Temps additionnel</label>
    <div class="edit-time-grid">
      <div><span style="font-size:12px; color:#9CA3AF">Heure(s)</span><input id="modalHeures" type="number" placeholder="0" min="0" oninput="calculerPrixAutomatiqueModal()"></div>
      <div><span style="font-size:12px; color:#9CA3AF">Minute(s)</span><input id="modalMinutes" type="number" placeholder="30" min="0" oninput="calculerPrixAutomatiqueModal()"></div>
    </div>
    <label>Montant supplémentaire (Ar)</label>
    <input id="modalMontant" type="number" value="500" min="0">
    <div class="btn-group">
      <button class="btn-green" onclick="validerProlongation()">Valider</button>
      <button class="btn-secondary" onclick="fermerModal()">Annuler</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="editModal">
  <div class="modal-box">
    <div class="list-title" id="editModalTitre" style="color:#3B82F6">📝 Modifier la fiche</div>
    <div class="modal-info" id="editModalEtatActuel">Calcul...</div>
    <label>Nom du client</label>
    <input id="editNom">
    <label>Ajuster la durée</label>
    <div class="edit-time-grid">
      <div><span style="font-size:12px; color:#9CA3AF">Heure(s)</span><input id="editHeures" type="number" min="0"></div>
      <div><span style="font-size:12px; color:#9CA3AF">Minute(s)</span><input id="editMinutes" type="number" min="0" max="59"></div>
    </div>
    <label>Montant Global (Ar)</label>
    <input id="editMontant" type="number" min="0">
    <label>Adresse MAC</label>
    <input id="editMac">
    <label>Statut</label>
    <select id="editStatut">
      <option value="attente">En attente</option>
      <option value="actif">Actif</option>
      <option value="expiré">Expiré</option>
    </select>
    <div class="btn-group">
      <button class="btn-green" onclick="validerEditionComplete()">Enregistrer</button>
      <button class="btn-secondary" onclick="fermerModalEdit()">Annuler</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="confirmModal">
  <div class="modal-box" style="max-width: 350px;">
    <div class="alert-title" style="color:#EF4444">🗑️ Supprimer le client</div>
    <div class="alert-text" id="confirmModalText">Voulez-vous supprimer ce client ?</div>
    <div class="btn-group">
      <button class="btn-red" id="btnConfirmOk">Oui, Supprimer</button>
      <button class="btn-secondary" onclick="fermerModalConfirm()">Annuler</button>
    </div>
  </div>
</div>

<div class="modal-overlay" id="alertModal">
  <div class="modal-box" style="max-width: 380px; border-color: #EF4444;">
    <div class="alert-title" style="color:#EF4444; animation: blink 1s infinite;">⏰ TEMPS EXPIRÉ !</div>
    <div class="alert-text" id="alertModalText">Le forfait est terminé.</div>
    <div class="modal-info" style="border-left-color: #EF4444; margin-bottom: 15px; text-align: center; color:#fff;">
      ⚠️ Désactivez sa connexion sur l'antenne Starlink.
    </div>
    <button class="btn-red" onclick="fermerModalAlert()">Arrêter le son</button>
  </div>
</div>

<script>
let clients = [];
let indexEnCours = null;
let indexSuppressionEnCours = null;
let alerteAudio = new Audio('https://www.soundjay.com/buttons/sounds/button-3.mp3'); 
alerteAudio.loop = true;

document.addEventListener('click', function() {
  alerteAudio.play().then(() => { alerteAudio.pause(); alerteAudio.currentTime = 0; }).catch(() => {});
}, { once: true });

async function chargerDepuisServeur() {
  try {
    let response = await fetch('/api/clients');
    clients = await response.json();
    afficher();
  } catch(e) { console.error("Erreur de connexion cloud", e); }
}

function calculerPrixAutomatique() {
  let hInput = document.getElementById('ajoutHeures').value;
  let mInput = document.getElementById('ajoutMinutes').value;
  if(hInput === "" && mInput === "") { document.getElementById('montant').value = ""; return; }
  let heures = parseInt(hInput) || 0; let minutes = parseInt(mInput) || 0;
  document.getElementById('montant').value = (heures * 1000) + Math.round(minutes * (500 / 30));
}

function calculerPrixAutomatiqueModal() {
  let heures = parseInt(document.getElementById('modalHeures').value) || 0;
  let minutes = parseInt(document.getElementById('modalMinutes').value) || 0;
  document.getElementById('modalMontant').value = (heures * 1000) + Math.round(minutes * (500 / 30));
}

function sonnerAlerte(nom, forfait){
  alerteAudio.currentTime = 0; alerteAudio.play().catch(e => {});
  if(navigator.vibrate) { navigator.vibrate([600, 250, 600]); }
  document.getElementById('alertModalText').innerHTML = `Le forfait de <strong style="color:#3B82F6;">${nom}</strong> (${forfait}) est fini.`;
  document.getElementById('alertModal').classList.add('active');
}

function fermerModalAlert() { alerteAudio.pause(); alerteAudio.currentTime = 0; document.getElementById('alertModal').classList.remove('active'); }

function formatDate(d){
  if(!d) return '-'; d = new Date(d);
  return d.toLocaleDateString('fr-FR',{day:'2-digit',month:'2-digit'})+' '+d.toLocaleTimeString('fr-FR',{hour:'2-digit',minute:'2-digit'});
}

function getCountdown(expire){
  if(!expire) return '-';
  let diff = new Date(expire) - new Date();
  if(diff <= 0) return '<span class="countdown danger">Expiré</span>';
  let h = Math.floor(diff/3600000); let m = Math.floor((diff%3600000)/60000); let s = Math.floor((diff%60000)/1000);
  let className = diff < 300000 ? 'countdown danger' : diff < 900000 ? 'countdown warning' : 'countdown normal';
  if(h > 0) return `<span class="${className}">${h}h ${m}m</span>`;
  return `<span class="${className}">${m}:${s.toString().padStart(2,'0')}</span>`;
}

function afficher(filtre=''){
  let html = '';
  let liste = clients.filter(c => c.nom.toLowerCase().includes(filtre.toLowerCase()));

  if(liste.length === 0){
    html = `<tr><td colspan="7" class="empty">Aucun client trouvé</td></tr>`;
  } else {
    liste.forEach((c)=>{
      let idx = clients.indexOf(c);
      let badge = c.statut==='actif'?'badge-actif':c.statut==='attente'?'badge-attente':'badge-expire';
      let actions = c.statut==='attente' 
        ? `<button class="btn-sm btn-green" onclick="event.stopPropagation(); activer(${idx})">Activer</button>`
        : `<button class="btn-sm btn-green" onclick="event.stopPropagation(); ouvrirModalProlongation(${idx})">${c.statut==='actif'?'+Temps':'Relancer'}</button>`;
      actions += `<button class="btn-sm btn-red" onclick="event.stopPropagation(); ouvrirModalConfirm(${idx})">Suppr</button>`;

      let expireDisplay = c.statut==='actif'? getCountdown(c.expire) : formatDate(c.expire);

      html += `<tr id="row-${idx}" class="client-row-element" data-index="${idx}">
        <td>${formatDate(c.date)}</td>
        <td><strong>${c.nom}</strong></td>
        <td>${c.forfait}</td>
        <td>${parseInt(c.montant).toLocaleString('fr-FR')} Ar</td>
        <td class="cell-countdown" data-expire="${c.expire||''}" data-statut="${c.statut}">${expireDisplay}</td>
        <td><span class="badge ${badge}">${c.statut}</span></td>
        <td>${actions}</td>
      </tr>`;
    });
  }

  document.getElementById('tbody').innerHTML = html;
  document.getElementById('total').textContent = clients.length;
  document.getElementById('attente').textContent = clients.filter(c=>c.statut==='attente').length;
  document.getElementById('actifs').textContent = clients.filter(c=>c.statut==='actif').length;
  document.getElementById('expires').textContent = clients.filter(c=>c.statut==='expiré').length;
  document.getElementById('caisse').textContent = clients.reduce((sum,c)=>sum+parseInt(c.montant||0),0).toLocaleString('fr-FR')+' Ar';

  attacherEvenementsAppuiLong();
  miseAjourDirecteModals();
}

let timerAppuiLong;
function attacherEvenementsAppuiLong() {
  document.querySelectorAll('.client-row-element').forEach(row => {
    let index = row.getAttribute('data-index');
    row.addEventListener('touchstart', () => { clearTimeout(timerAppuiLong); timerAppuiLong = setTimeout(() => { ouvrirModalEditionComplete(index); }, 700); }, { passive: true });
    row.addEventListener('touchend', () => clearTimeout(timerAppuiLong));
    row.addEventListener('touchmove', () => clearTimeout(timerAppuiLong));
    row.addEventListener('mousedown', () => { clearTimeout(timerAppuiLong); timerAppuiLong = setTimeout(() => { abrirModalEditionComplete(index); }, 700); });
    row.addEventListener('mouseup', () => clearTimeout(timerAppuiLong));
    row.addEventListener('mouseleave', () => clearTimeout(timerAppuiLong));
  });
}

function ouvrirModalEditionComplete(i) {
  indexEnCours = parseInt(i); let c = clients[indexEnCours]; if(!c) return;
  document.getElementById('editModalTitre').textContent = `📝 Fiche de : ${c.nom}`;
  document.getElementById('editNom').value = c.nom; document.getElementById('editMontant').value = c.montant;
  document.getElementById('editMac').value = c.mac || ''; document.getElementById('editStatut').value = c.statut;
  
  let totalMinutes = 0;
  if(c.forfait) {
    c.forfait.split('+').forEach(seg => {
      let num = parseInt(seg.trim()) || 0;
      if (seg.includes('Heure')) totalMinutes += num * 60; else if (seg.includes('min')) totalMinutes += num;
    });
  }
  let h = Math.floor(totalMinutes / 60); let m = totalMinutes % 60;
  document.getElementById('editHeures').value = h > 0 ? h : ''; document.getElementById('editMinutes').value = m > 0 ? m : '';
  document.getElementById('editModal').classList.add('active');
}

async function validerEditionComplete() {
  if(indexEnCours === null) return; let c = clients[indexEnCours];
  let h = parseInt(document.getElementById('editHeures').value) || 0;
  let m = parseInt(document.getElementById('editMinutes').value) || 0;
  
  let texteForfait = (h > 0 ? h + " Heure" + (h>1?"s":"") : "") + (m > 0 ? (h>0?" + ":"") + m + " min" : "");
  if (h === 0 && m === 0) texteForfait = "Sans forfait";
  
  let payload = {
    nom: document.getElementById('editNom').value.trim(),
    montant: parseInt(document.getElementById('editMontant').value) || 0,
    mac: document.getElementById('editMac').value.trim(),
    statut: document.getElementById('editStatut').value,
    forfait: texteForfait
  };

  if (payload.statut === 'actif') {
    let baseDate = (c.statut === 'actif' && c.expire) ? new Date(c.date) : new Date();
    baseDate.setHours(baseDate.getHours() + h); baseDate.setMinutes(baseDate.getMinutes() + m);
    payload.expire = baseDate.toISOString(); payload.alerte = false;
  } else if (payload.statut === 'expiré') {
    payload.expire = new Date().toISOString(); payload.alerte = true;
  } else { payload.expire = null; payload.alerte = false; }

  await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  fermerModalEdit(); chargerDepuisServeur();
}

function fermerModalEdit() { document.getElementById('editModal').classList.remove('active'); indexEnCours = null; }

async function ajouter(){
  let nom = document.getElementById('nom').value.trim();
  let h = parseInt(document.getElementById('ajoutHeures').value) || 0;
  let m = parseInt(document.getElementById('ajoutMinutes').value) || 0;
  let montant = parseInt(document.getElementById('montant').value) || 0;
  let mac = document.getElementById('mac').value.trim();
  if(!nom || (h === 0 && m === 0) || !montant) return;

  let texteForfait = (h > 0 ? h + " Heure" + (h>1?"s":"") : "") + (m > 0 ? (h>0?" + ":"") + m + " min" : "");

  await fetch('/api/clients', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ nom: nom, forfait: texteForfait, montant: montant, mac: mac })
  });

  document.getElementById('nom').value=''; document.getElementById('mac').value='';
  document.getElementById('ajoutHeures').value=''; document.getElementById('ajoutMinutes').value=''; document.getElementById('montant').value='';
  chargerDepuisServeur();
}

async function activer(i){
  let c = clients[i]; let now = new Date(); let totalMin = 0;
  if(c.forfait){
    c.forfait.split('+').forEach(seg => {
      let num = parseInt(seg.trim()) || 0;
      if (seg.includes('Heure')) totalMin += num * 60; else if (seg.includes('min')) totalMin += num;
    });
  }
  now.setMinutes(now.getMinutes() + totalMin);
  await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ statut: 'actif', expire: now.toISOString(), alerte: false }) });
  chargerDepuisServeur();
}

function ouvrirModalProlongation(i) {
  indexEnCours = i; let c = clients[i];
  document.getElementById('prolongarTitre').textContent = `➕ Prolonger : ${c.nom}`;
  document.getElementById('modalHeures').value = ""; document.getElementById('modalMinutes').value = "30";
  calculerPrixAutomatiqueModal(); document.getElementById('prolongarModal').classList.add('active');
}

async function validerProlongation() {
  if (indexEnCours === null) return; let c = clients[indexEnCours];
  let h = parseInt(document.getElementById('modalHeures').value) || 0;
  let m = parseInt(document.getElementById('modalMinutes').value) || 0;
  let baseDate = (c.statut === 'actif' && c.expire) ? new Date(c.expire) : new Date();
  baseDate.setMinutes(baseDate.getMinutes() + (h * 60) + m);
  
  let texteAjout = (h > 0 ? h + " Heure" + (h>1?"s":"") : "") + (m > 0 ? " + " + m + " min" : "");

  await fetch(`/api/clients/${c.id}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      statut: 'actif', expire: baseDate.toISOString(), alerte: false,
      montant: (parseInt(c.montant) || 0) + (parseInt(document.getElementById('modalMontant').value) || 0),
      forfait: c.forfait + " + " + texteAjout
    })
  });
  fermerModal(); chargerDepuisServeur();
}

function fermerModal() { document.getElementById('prolongarModal').classList.remove('active'); indexEnCours = null; }
function ouvrirModalConfirm(i) { indexSuppressionEnCours = i; document.getElementById('confirmModalText').innerHTML = `Supprimer définitivement <strong>${clients[i].nom}</strong> ?`; document.getElementById('btnConfirmOk').onclick = validerSuppression; document.getElementById('confirmModal').classList.add('active'); }

async function validerSuppression() {
  if (indexSuppressionEnCours !== null) {
    await fetch(`/api/clients/${clients[indexSuppressionEnCours].id}`, { method: 'DELETE' });
    fermerModalConfirm(); chargerDepuisServeur();
  }
}
function fermerModalConfirm() { document.getElementById('confirmModal').classList.remove('active'); indexSuppressionEnCours = null; }

function miseAjourDirecteModals() {
  if (indexEnCours === null) return;
  if (document.getElementById('prolongarModal').classList.contains('active')) {
    let c = clients[indexEnCours]; let infoBox = document.getElementById('modalEtatActuel');
    let diff = c.expire ? new Date(c.expire) - new Date() : -1;
    if (c.statut === 'expiré' || diff <= 0) { infoBox.innerHTML = `Forfait : <span style="color:#EF4444; font-weight:bold;">Expiré</span>`; }
    else { let h = Math.floor(diff/3600000); let m = Math.floor((diff%3600000)/60000); infoBox.innerHTML = `Restant : <span style="color:#10B981; font-weight:bold;">${h}h ${m}m</span>`; }
  }
}

function filtrer(){ afficher(document.getElementById('search').value); }

async function verifier(){
  let now = new Date(); let recalculerTout = false;
  for(let c of clients) {
    if(c.statut==='actif' && c.expire && new Date(c.expire)<now && !c.alerte){
      c.statut='expiré'; c.alerte = true; recalculerTout = true;
      await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ statut: 'expiré', alerte: true }) });
      sonnerAlerte(c.nom,c.forfait);
    }
  }
  if(recalculerTout) { chargerDepuisServeur(); } 
  else {
    document.querySelectorAll('.cell-countdown').forEach(td => {
      let statut = td.getAttribute('data-statut'); let expire = td.getAttribute('data-expire');
      if (statut === 'actif' && expire) td.innerHTML = getCountdown(expire);
    });
    if(indexEnCours !== null) miseAjourDirecteModals();
  }
}

setInterval(verifier,1000);
window.onload = chargerDepuisServeur;
</script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_CONTENT)

@app.route('/api/clients', methods=['GET'])
def get_clients():
    clients = Client.query.all()
    return jsonify([c.to_dict() for c in clients])

@app.route('/api/clients', methods=['POST'])
def add_client():
    data = request.json
    nouveau = Client(nom=data['nom'], forfait=data['forfait'], montant=data['montant'], mac=data.get('mac', ''))
    db.session.add(nouveau)
    db.session.commit()
    return jsonify(nouveau.to_dict()), 201

@app.route('/api/clients/<int:id>', methods=['PUT'])
def update_client(id):
    client = Client.query.get_or_404(id)
    data = request.json
    client.nom = data.get('nom', client.nom)
    client.forfait = data.get('forfait', client.forfait)
    client.montant = data.get('montant', client.montant)
    client.mac = data.get('mac', client.mac)
    client.statut = data.get('statut', client.statut)
    client.expire = data.get('expire', client.expire)
    client.alerte = data.get('alerte', client.alerte)
    db.session.commit()
    return jsonify(client.to_dict())

@app.route('/api/clients/<int:id>', methods=['DELETE'])
def delete_client(id):
    client = Client.query.get_or_404(id)
    db.session.delete(client)
    db.session.commit()
    return jsonify({"success": True})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
