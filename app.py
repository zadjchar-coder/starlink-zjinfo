import os
from flask import Flask, render_template_string, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'une_cle_secrete_tres_difficile_a_deviner_12345'

# --- CONFIGURATION DE LA BASE DE DONNÉES ---
if os.environ.get('RENDER'):
    db_path = '/tmp/starlink.db'
else:
    db_path = os.path.join(os.path.dirname(__file__), 'starlink.db')

app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(250), nullable=False)

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

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

_db_initialized = False

@app.before_request
def initialize_database_if_needed():
    global _db_initialized
    if not _db_initialized:
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            admin_user = User(username='admin', password=generate_password_hash('admin123'))
            db.session.add(admin_user)
            db.session.commit()
        _db_initialized = True

AUTH_HTML = """
<!DOCTYPE html>
<html lang="fr">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Starlink ZJinfo - {{ title }}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#0B132B;color:#fff;font-family:system-ui,-apple-system,sans-serif;display:flex;align-items:center;justify-content:center;min-height:100vh;padding:20px}
.auth-card{background:#111827;border:1px solid #1F2937;border-radius:20px;padding:32px;width:100%;max-width:400px;box-shadow:0 10px 25px rgba(0,0,0,0.5)}
.logo{text-align:center;font-size:40px;margin-bottom:10px}
h2{text-align:center;color:#3B82F6;margin-bottom:8px;font-size:24px}
p.subtitle{text-align:center;color:#94A3B8;font-size:14px;margin-bottom:24px}
label{display:block;color:#D1D5DB;font-size:14px;margin-bottom:6px;font-weight:500}
input{width:100%;padding:12px;background:#1F2937;border:1px solid #374151;border-radius:10px;color:#fff;font-size:15px;margin-bottom:16px}
input:focus{outline:none;border-color:#3B82F6;box-shadow:0 0 0 3px rgba(59,130,246,0.1)}
button{width:100%;padding:14px;background:#2563EB;border:none;border-radius:10px;color:#fff;font-weight:600;font-size:16px;cursor:pointer;transition:0.2s;margin-top:8px}
button:hover{background:#1D4ED8}
.footer-link{text-align:center;margin-top:20px;font-size:14px;color:#9CA3AF}
.footer-link a{color:#3B82F6;text-decoration:none;font-weight:600}
.footer-link a:hover{text-decoration:underline}
.alert{background:#FEE2E2;color:#991B1B;padding:12px;border-radius:10px;font-size:14px;margin-bottom:16px;text-align:center;font-weight:500}
</style>
</head>
<body>
<div class="auth-card">
  <div class="logo">📡</div>
  <h2>{{ title }}</h2>
  <p class="subtitle">Gestion WiFi Starlink ZJinfo</p>
  {% with messages = get_flashed_messages() %}
    {% if messages %}
      {% for message in messages %}
        <div class="alert">{{ message }}</div>
      {% endfor %}
    {% endif %}
  {% endwith %}
  <form method="POST">
    <label>Nom d'utilisateur</label>
    <input name="username" placeholder="Ex: admin" required autocomplete="off">
    <label>Mot de passe</label>
    <input type="password" name="password" placeholder="••••••••" required>
    <button type="submit">{{ btn_text }}</button>
  </form>
  <div class="footer-link">
    {% if action == 'login' %}
      Pas encore de compte ? <a href="{{ url_for('register') }}">S'inscrire</a>
    {% else %}
      Déjà un compte ? <a href="{{ url_for('login') }}">Se connecter</a>
    {% endif %}
  </div>
</div>
</body>
</html>
"""

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
.header{background:#0B132B;padding:16px;border-bottom:1px solid #1C2541;display:flex;align-items:center;justify-content:space-between;gap:12px}
.header-left{display:flex;align-items:center;gap:12px}
.header-icon{background:#2563EB;padding:10px;border-radius:12px;font-size:20px}
.header h1{color:#3B82F6;font-size:22px;font-weight:700}
.header p{color:#94A3B8;font-size:13px}
.btn-logout{background:#374151;padding:8px 14px;border-radius:8px;color:#fff;text-decoration:none;font-size:13px;font-weight:600;border:1px solid #4B5563;transition:0.2s}
.btn-logout:hover{background:#EF4444;border-color:#DC2626}
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
.stat-card{background:#111827;border:1px solid #1F2937;border-radius:16px;padding:16px;transition:0.2s;cursor:pointer;position:relative}
.stat-card:hover{border-color:#3B82F6;background:#1F2937}
.stat-card.active-filter{border-color:#2563EB;background:#1C2541}
.stat-label{color:#9CA3AF;font-size:13px;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px}
.stat-value{font-size:26px;font-weight:700}
.caisse-detail {font-size: 11px; color: #9CA3AF; margin-top: 6px; border-top: 1px solid #1F2937; padding-top: 6px; text-align: left; line-height: 1.5;}
.caisse-detail span {color: #E5E7EB; font-weight: 600;}
.popup-hover {
  position: absolute; top: 105%; left: 50%; transform: translateX(-50%);
  background: #1F2937; border: 1px solid #374151; padding: 12px; min-width: 180px;
  max-width: 240px; border-radius: 10px; box-shadow: 0 10px 20px rgba(0,0,0,0.6);
  z-index: 99; display: none; max-height: 180px; overflow-y: auto; text-align: left;
}
.popup-hover h4 { font-size: 11px; color: #3B82F6; text-transform: uppercase; margin-bottom: 6px; border-bottom: 1px solid #374151; padding-bottom: 4px; }
.popup-item { font-size: 13px; padding: 3px 0; border-bottom: 1px dashed #2D3748; color: #E5E7EB; }
.popup-item:last-child { border-bottom: none; }
.stat-card:hover .popup-hover { display: block; }
.list-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px;flex-wrap:wrap;gap:10px}
.list-title{display:flex;align-items:center;gap:8px;font-size:18px;font-weight:600}
.search{background:#1F2937;border:1px solid #374151;border-radius:10px;padding:10px 14px;color:#fff;width:160px;font-size:14px}
.search:focus{outline:none;border-color:#3B82F6}
table{width:100%;border-collapse:collapse;font-size:13px}
th{color:#9CA3AF;text-align:left;padding:14px 8px;font-weight:600;border-bottom:2px solid #1F2937;text-transform:uppercase;font-size:11px;letter-spacing:0.5px}
td{padding:14px 8px;border-bottom:1px solid #1F2937;color:#E5E7EB;vertical-align:middle}
.row-client:hover td{background:#1F2937}
.badge{padding:5px 10px;border-radius:20px;font-size:11px;font-weight:600;text-transform:uppercase}
.badge-attente{background:#FEF3C7;color:#92400E}
.badge-actif{background:#D1FAE5;color:#065F46}
.badge-expire{background:#FEE2E2;color:#991B1B}
.btn-sm{padding:7px 12px;font-size:11px;width:auto;margin:2px;border-radius:6px;font-weight:600;cursor:pointer;border:none;color:#fff}
.empty{padding:60px;text-align:center;color:#6B7280;font-size:14px}
.countdown{font-weight:700;font-family:'Courier New',monospace;font-size:14px}
.countdown.normal{color:#10B981}
.countdown.warning{color:#F59E0B}
.countdown.danger{color:#EF4444;animation:blink 1s infinite}
@keyframes blink{0%,100%{opacity:1}50%{opacity:0.4}}
@media(min-width:768px){.stats{grid-template-columns:repeat(5,1fr)}}
.time-input-container {display: grid; grid-template-columns: 1fr 1fr; gap: 10px;}
.edit-time-grid {display: grid; grid-template-columns: 1fr 1fr; gap: 10px;}
.benefice-table th { background: #1F2937; color: #3B82F6; font-size: 13px; padding: 16px 12px; }
.benefice-table td { font-size: 15px; padding: 16px 12px; font-weight: 500; }
.valeur-gain { color: #10B981; font-weight: 700; font-family: 'Courier New', monospace; }
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
.hint-longpress { text-align: center; color: #6B7280; font-size: 11px; margin-top: 4px; }
.alert-title { font-size: 18px; font-weight: bold; text-align: center; margin-bottom: 12px; display: flex; align-items: center; justify-content: center; gap: 8px; }
.alert-text { font-size: 14px; color: #E5E7EB; text-align: center; margin-bottom: 20px; line-height: 1.5; }
</style>
</head>
<body>

<div class="header">
  <div class="header-left">
    <div class="header-icon">📡</div>
    <div>
      <h1>Starlink ZJinfo</h1>
      <p>Session active : <strong style="color:#10B981;">{{ current_user.username }}</strong></p>
    </div>
  </div>
  <a href="{{ url_for('logout') }}" class="btn-logout">🚪 Déconnexion</a>
</div>

<div class="container">
  <div class="stats">
    <div class="stat-card" id="card-all" onclick="filtrerParStatut('tous')">
      <div class="stat-label">Total Clients</div>
      <div class="stat-value" id="total">0</div>
      <div class="popup-hover"><h4>📋 Tous les clients</h4><div id="pop-all">Aucun</div></div>
    </div>
    <div class="stat-card" id="card-attente" onclick="filtrerParStatut('attente')">
      <div class="stat-label">En Attente</div>
      <div class="stat-value" style="color:#F59E0B" id="attente">0</div>
      <div class="popup-hover"><h4>⏳ En attente</h4><div id="pop-attente">Aucun</div></div>
    </div>
    <div class="stat-card" id="card-actif" onclick="filtrerParStatut('actif')">
      <div class="stat-label">Actifs</div>
      <div class="stat-value" style="color:#10B981" id="actifs">0</div>
      <div class="popup-hover"><h4>🟢 Clients actifs</h4><div id="pop-actifs">Aucun</div></div>
    </div>
    <div class="stat-card" id="card-expiré" onclick="filtrerParStatut('expiré')">
      <div class="stat-label">Expirés</div>
      <div class="stat-value" style="color:#EF4444" id="expires">0</div>
      <div class="popup-hover"><h4>🔴 Forfaits expirés</h4><div id="pop-expires">Aucun</div></div>
    </div>
    <div class="stat-card" id="card-caisse" onclick="basculerVue('benefices')">
      <div class="stat-label">💲 Encaissé Total</div>
      <div class="stat-value" style="color:#3B82F6" id="caisse">0 Ar</div>
      <div class="caisse-detail">
        Mois : <span id="caisse-mois">0 Ar</span><br>
        An : <span id="caisse-an">0 Ar</span>
      </div>
    </div>
  </div>

  <div id="vue-clients">
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
    </div>

    <div class="card">
      <div class="list-header">
        <div class="list-title" id="titre-liste-clients">📋 Liste des clients</div>
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

  <div id="vue-benefices" style="display: none;">
    <div class="card">
      <div class="list-header" style="border-bottom: 1px solid #1F2937; padding-bottom: 12px; margin-bottom: 20px;">
        <div class="list-title" style="font-size: 22px; color: #10B981;">📊 Tableau de bord des Bénéfices</div>
        <button class="btn-sm btn-secondary" onclick="basculerVue('clients')" style="padding: 10px 18px; font-size: 14px;">⬅️ Retour aux clients</button>
      </div>
      <div style="overflow-x:auto;">
        <table class="benefice-table">
          <thead>
            <tr>
              <th>PÉRIODE DE VENTE</th>
              <th>CHIFFRE D'AFFAIRES GÉNÉRÉ (AR)</th>
              <th>NOMBRE DE TRANSACTIONS</th>
            </tr>
          </thead>
          <tbody>
            <tr><td>📅 Aujourd'hui</td><td class="valeur-gain" id="gain-jour">0 Ar</td><td id="count-jour" style="color: #9CA3AF;">0 txn</td></tr>
            <tr><td>🗓️ Cette Semaine (7 jours)</td><td class="valeur-gain" id="gain-semaine" style="color: #3B82F6;">0 Ar</td><td id="count-semaine" style="color: #9CA3AF;">0 txn</td></tr>
            <tr><td>🌙 Ce Mois-ci</td><td class="valeur-gain" id="gain-mois" style="color: #F59E0B;">0 Ar</td><td id="count-mois" style="color: #9CA3AF;">0 txn</td></tr>
            <tr><td>🚀 Cette Année</td><td class="valeur-gain" id="gain-an" style="color: #A855F7;">0 Ar</td><td id="count-an" style="color: #9CA3AF;">0 txn</td></tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</div>

<div class="modal-overlay" id="editModal">
  <div class="modal-box">
    <div class="list-title" id="editModalTitre" style="color:#3B82F6">📝 Modifier la fiche</div>
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
    <button class="btn-red" onclick="fermerModalAlert()">Arrêter le son</button>
  </div>
</div>

<script>
let clients = [];
let statutFiltreActuel = 'tous';
let indexEnCours = null;
let indexSuppressionEnCours = null;
let ignoreNextClick = false; // Verrou anti-conflit
let alerteAudio = new Audio('https://www.soundjay.com/buttons/sounds/button-3.mp3'); 
alerteAudio.loop = true;

document.addEventListener('click', function() {
  alerteAudio.play().then(() => { alerteAudio.pause(); alerteAudio.currentTime = 0; }).catch(() => {});
}, { once: true });

async function chargerPermanence() {
  try {
    let r = await fetch('/api/clients');
    if(r.ok) { clients = await r.json(); afficher(); }
  } catch(e) { console.error(e); }
}

function basculerVue(vue) {
  if (vue === 'benefices') {
    document.getElementById('vue-clients').style.display = 'none';
    document.getElementById('vue-benefices').style.display = 'block';
    document.getElementById('card-caisse').classList.add('active-filter');
    document.querySelectorAll('.stat-card:not(#card-caisse)').forEach(c => c.classList.remove('active-filter'));
  } else {
    document.getElementById('vue-benefices').style.display = 'none';
    document.getElementById('vue-clients').style.display = 'block';
    document.getElementById('card-caisse').classList.remove('active-filter');
    filtrerParStatut(statutFiltreActuel);
  }
}

function calculerPrixAutomatique() {
  let hInput = document.getElementById('ajoutHeures').value;
  let mInput = document.getElementById('ajoutMinutes').value;
  if(hInput === "" && mInput === "") { document.getElementById('montant').value = ""; return; }
  let heures = parseInt(hInput) || 0; let minutes = parseInt(mInput) || 0;
  document.getElementById('montant').value = (heures * 1000) + Math.round(minutes * (500 / 30));
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

function filtrerParStatut(statut) {
  statutFiltreActuel = statut;
  if (document.getElementById('vue-clients').style.display === 'none') return;
  
  document.querySelectorAll('.stat-card').forEach(card => card.classList.remove('active-filter'));
  
  if (statut === 'tous') document.getElementById('card-all').classList.add('active-filter');
  else if (statut === 'actif') document.getElementById('card-actif').classList.add('active-filter');
  else if (statut === 'attente') document.getElementById('card-attente').classList.add('active-filter');
  else if (statut === 'expiré') document.getElementById('card-expiré').classList.add('active-filter');
  
  let titreText = "📋 Liste des clients";
  if (statut !== 'tous') titreText += ` (${statut}s)`;
  document.getElementById('titre-liste-clients').textContent = titreText;

  afficher(document.getElementById('search').value);
}

function afficher(filtreTexte=''){
  let html = ''; 
  let liste = clients;
  
  if (statutFiltreActuel !== 'tous') liste = liste.filter(c => c.statut === statutFiltreActuel);
  if (filtreTexte) liste = liste.filter(c => c.nom.toLowerCase().includes(filtreTexte.toLowerCase()));

  if(liste.length === 0){
    html = `<tr><td colspan="7" class="empty">Aucun client trouvé dans cette catégorie</td></tr>`;
  } else {
    liste.forEach((c)=>{
      let idx = clients.indexOf(c);
      let badge = c.statut==='actif'?'badge-actif':c.statut==='attente'?'badge-attente':'badge-expire';
      
      let actions = c.statut==='attente' 
        ? `<button class="btn-sm btn-green" onclick="activer(event, ${idx})">Activer</button>`
        : `<button class="btn-sm btn-green" onclick="relancerOptionnel(event, ${idx})">Relancer</button>`;
      actions += `<button class="btn-sm btn-red" onclick="ouvrirModalConfirm(event, ${idx})">Suppr</button>`;

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
  
  let maintenant = new Date();
  let totalOrigine = 0;
  let totalJour = 0, txJour = 0;
  let totalSemaine = 0, txSemaine = 0;
  let totalMois = 0, txMois = 0;
  let totalAn = 0, txAn = 0;

  let listeAll = [], listeAttente = [], listeActif = [], listeExpire = [];

  let uneSemaineAgo = new Date();
  uneSemaineAgo.setDate(maintenant.getDate() - 7);
  uneSemaineAgo.setHours(0,0,0,0);

  clients.forEach(c => {
    if (!c.date) return;
    let dateClient = new Date(c.date);
    let montant = parseInt(c.montant) || 0;
    totalOrigine += montant;

    let itemHtml = `<div class="popup-item">👤 ${c.nom} <span style="font-size:11px;color:#9CA3AF">(${c.forfait})</span></div>`;
    listeAll.push(itemHtml);
    if(c.statut === 'attente') listeAttente.push(itemHtml);
    if(c.statut === 'actif') listeActif.push(itemHtml);
    if(c.statut === 'expiré') listeExpire.push(itemHtml);

    if (dateClient.getFullYear() === maintenant.getFullYear()) {
      totalAn += montant; txAn++;
      if (dateClient.getMonth() === maintenant.getMonth()) {
        totalMois += montant; txMois++;
        if (dateClient.getDate() === maintenant.getDate()) {
          totalJour += montant; txJour++;
        }
      }
    }
    if (dateClient >= uneSemaineAgo) {
      totalSemaine += montant; txSemaine++;
    }
  });

  document.getElementById('pop-all').innerHTML = listeAll.join('') || 'Aucun client';
  document.getElementById('pop-attente').innerHTML = listeAttente.join('') || 'Aucun client';
  document.getElementById('pop-actifs').innerHTML = listeActif.join('') || 'Aucun client actif';
  document.getElementById('pop-expires').innerHTML = listeExpire.join('') || 'Aucun forfait expiré';

  document.getElementById('total').textContent = clients.length;
  document.getElementById('attente').textContent = clients.filter(c=>c.statut==='attente').length;
  document.getElementById('actifs').textContent = clients.filter(c=>c.statut==='actif').length;
  document.getElementById('expires').textContent = clients.filter(c=>c.statut==='expiré').length;
  document.getElementById('caisse').textContent = totalOrigine.toLocaleString('fr-FR')+' Ar';

  document.getElementById('caisse-mois').textContent = totalMois.toLocaleString('fr-FR') + ' Ar';
  document.getElementById('caisse-an').textContent = totalAn.toLocaleString('fr-FR') + ' Ar';

  document.getElementById('gain-jour').textContent = totalJour.toLocaleString('fr-FR') + ' Ar';
  document.getElementById('count-jour').textContent = txJour + ' txn';
  document.getElementById('gain-semaine').textContent = totalSemaine.toLocaleString('fr-FR') + ' Ar';
  document.getElementById('count-semaine').textContent = txSemaine + ' txn';
  document.getElementById('gain-mois').textContent = totalMois.toLocaleString('fr-FR') + ' Ar';
  document.getElementById('count-mois').textContent = txMois + ' txn';
  document.getElementById('gain-an').textContent = totalAn.toLocaleString('fr-FR') + ' Ar';
  document.getElementById('count-an').textContent = txAn + ' txn';

  attacherEvenementsAppuiLong();
}

let timerAppuiLong;
function attacherEvenementsAppuiLong() {
  document.querySelectorAll('.client-row-element').forEach(row => {
    let index = row.getAttribute('data-index');
    
    let startPress = (e) => {
      // Si la cible touchée est un bouton, on ignore l'appui long
      if(e.target.tagName.toLowerCase() === 'button') return;
      
      ignoreNextClick = false;
      clearTimeout(timerAppuiLong);
      timerAppuiLong = setTimeout(() => {
        ignoreNextClick = true; // Empêche le clic normal après l'ouverture du modal
        ouvrirModalEditionComplete(index);
      }, 700);
    };

    let endPress = () => { clearTimeout(timerAppuiLong); };

    row.addEventListener('touchstart', startPress, { passive: true });
    row.addEventListener('touchend', endPress);
    row.addEventListener('touchmove', endPress);
    row.addEventListener('mousedown', startPress);
    row.addEventListener('mouseup', endPress);
    row.addEventListener('mouseleave', endPress);
  });
}

function ouvrirModalEditionComplete(i) {
  indexEnCours = parseInt(i); let c = clients[indexEnCours]; if(!c) return;
  document.getElementById('editNom').value = c.nom; document.getElementById('editMontant').value = c.montant;
  document.getElementById('editMac').value = c.mac || ''; document.getElementById('editStatut').value = c.statut;
  document.getElementById('editHeures').value = ''; document.getElementById('editMinutes').value = '';
  document.getElementById('editModal').classList.add('active');
}

async function validerEditionComplete() {
  if(indexEnCours === null) return; let c = clients[indexEnCours];
  let h = parseInt(document.getElementById('editHeures').value) || 0;
  let m = parseInt(document.getElementById('editMinutes').value) || 0;
  
  let texteForfait = c.forfait;
  if(h > 0 || m > 0) {
     texteForfait = (h > 0 ? h + " Heure" + (h>1?"s":"") : "") + (m > 0 ? (h>0?" + ":"") + m + " min" : "");
  }
  
  let payload = {
    nom: document.getElementById('editNom').value.trim(),
    montant: parseInt(document.getElementById('editMontant').value) || 0,
    mac: document.getElementById('editMac').value.trim(),
    statut: document.getElementById('editStatut').value,
    forfait: texteForfait
  };

  if (payload.statut === 'actif') {
    let baseDate = new Date();
    baseDate.setHours(baseDate.getHours() + h); baseDate.setMinutes(baseDate.getMinutes() + m);
    payload.expire = baseDate.toISOString(); payload.alerte = false;
  } else if (payload.statut === 'expiré') {
    payload.expire = new Date().toISOString(); payload.alerte = true;
  } else { payload.expire = null; payload.alerte = false; }

  await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
  fermerModalEdit(); chargerPermanence();
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
  chargerPermanence();
}

async function activer(e, i){
  if (e) { e.stopPropagation(); e.preventDefault(); }
  if (ignoreNextClick) return;
  
  let c = clients[i]; let now = new Date(); let totalMin = 0;
  if(c.forfait){
    c.forfait.split('+').forEach(seg => {
      let num = parseInt(seg.trim()) || 0;
      if (seg.includes('Heure')) totalMin += num * 60; else if (seg.includes('min')) totalMin += num;
    });
  }
  now.setMinutes(now.getMinutes() + totalMin);
  await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ statut: 'actif', expire: now.toISOString(), alerte: false }) });
  chargerPermanence();
}

async function relancerOptionnel(e, i) {
  if (e) { e.stopPropagation(); e.preventDefault(); }
  if (ignoreNextClick) return;
  
  let c = clients[i]; let now = new Date(); let totalMin = 0;
  if(c.forfait){
    c.forfait.split('+').forEach(seg => {
      let num = parseInt(seg.trim()) || 0;
      if (seg.includes('Heure')) totalMin += num * 60; else if (seg.includes('min')) totalMin += num;
    });
  }
  now.setMinutes(now.getMinutes() + totalMin);
  await fetch(`/api/clients/${c.id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ statut: 'actif', expire: now.toISOString(), alerte: false }) });
  chargerPermanence();
}

function ouvrirModalConfirm(e, i) {
  if (e) { e.stopPropagation(); e.preventDefault(); }
  if (ignoreNextClick) return;
  
  indexSuppressionEnCours = i; 
  document.getElementById('confirmModalText').innerHTML = `Supprimer définitivement <strong>${clients[i].nom}</strong> ?`; 
  document.getElementById('btnConfirmOk').onclick = validerSuppression; 
  document.getElementById('confirmModal').classList.add('active'); 
}

async function validerSuppression() {
  if (indexSuppressionEnCours !== null) {
    await fetch(`/api/clients/${clients[indexSuppressionEnCours].id}`, { method: 'DELETE' });
    fermerModalConfirm(); chargerPermanence();
  }
}
function fermerModalConfirm() { document.getElementById('confirmModal').classList.remove('active'); indexSuppressionEnCours = null; }
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
  if(recalculerTout) { chargerPermanence(); } 
  else {
    document.querySelectorAll('.cell-countdown').forEach(td => {
      let statut = td.getAttribute('data-statut'); let expire = td.getAttribute('data-expire');
      if (statut === 'actif' && expire) td.innerHTML = getCountdown(expire);
    });
  }
}

setInterval(verifier,1000);
window.onload = chargerPermanence;
</script>
</body>
</html>
"""

# --- ROUTES FLASK ---
@app.route('/')
@login_required
def index():
    return render_template_string(HTML_CONTENT)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        u = User.query.filter_by(username=request.form.get('username')).first()
        if u and check_password_hash(u.password, request.form.get('password')):
            login_user(u)
            return redirect(url_for('index'))
        flash("Identifiants incorrects.")
    return render_template_string(AUTH_HTML, title="Connexion", btn_text="Se connecter", action="login")

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if User.query.filter_by(username=username).first():
            flash("Ce nom d'utilisateur existe déjà.")
        else:
            new_user = User(username=username, password=generate_password_hash(password))
            db.session.add(new_user)
            db.session.commit()
            flash("Compte créé avec succès ! Connectez-vous.")
            return redirect(url_for('login'))
    return render_template_string(AUTH_HTML, title="Inscription", btn_text="Créer un compte", action="register")

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --- API REST JSON ---
@app.route('/api/clients', methods=['GET'])
@login_required
def get_clients():
    cls = Client.query.order_by(Client.id.desc()).all()
    return jsonify([c.to_dict() for c in cls])

@app.route('/api/clients', methods=['POST'])
@login_required
def add_client():
    data = request.json
    c = Client(
        nom=data.get('nom'),
        forfait=data.get('forfait'),
        montant=data.get('montant'),
        mac=data.get('mac', '')
    )
    db.session.add(c)
    db.session.commit()
    return jsonify(c.to_dict()), 201

@app.route('/api/clients/<int:id>', methods=['PUT'])
@login_required
def update_client(id):
    c = Client.query.get_or_404(id)
    data = request.json
    if 'nom' in data: c.nom = data['nom']
    if 'forfait' in data: c.forfait = data['forfait']
    if 'montant' in data: c.montant = data['montant']
    if 'mac' in data: c.mac = data['mac']
    if 'statut' in data: c.statut = data['statut']
    if 'expire' in data: c.expire = data['expire']
    if 'alerte' in data: c.alerte = data['alerte']
    db.session.commit()
    return jsonify(c.to_dict())

@app.route('/api/clients/<int:id>', methods=['DELETE'])
@login_required
def delete_client(id):
    c = Client.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)))
