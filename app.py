import os
import json
import base64
import re
import logging
import requests
from flask import Flask, request, render_template_string

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("reloop_ai")

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip() or "gemini-3.8-flash"
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


# Curated starter database for common models. Values are stored snapshots, not live quotes.
# Repair figures from third-party/authorised-provider listings must be rechecked before payment.
STORED_PRICE_DATABASE = [
    {
        "aliases": ["samsung galaxy a15 5g", "galaxy a15 5g", "sm-a156"],
        "brand": "Samsung", "model": "Galaxy A15 5G",
        "repair_by_issue": {
            "display": "₹3,370 listed display-part price (labour/tax may be extra)",
            "battery": "₹1,580 listed battery-part price (labour/tax may be extra)"
        },
        "replacement": "₹12,000–₹18,000 (indicative retail band; verify current price)",
        "source_title": "Galaxy A15 5G parts listing; verify with Samsung service",
        "source_url": "https://samsung-parts.trackit.co.in/india/mobile/galaxy-a15-5g",
        "official_url": "https://www.samsung.com/in/support/spare-part-pricing-list-for-repair/",
        "source_note": "Third-party parts listing; Samsung says listed spare-part prices may exclude labour and GST. Confirm the exact variant and final quote."
    },
    {
        "aliases": ["iphone 17 pro max"], "brand": "Apple", "model": "iPhone 17 Pro Max",
        "repair_by_issue": {"display": "₹44,346 listed display replacement charge", "battery": "₹7,363 listed battery replacement charge"},
        "replacement": "₹1,40,000–₹1,80,000 (indicative retail band; verify current price)",
        "source_title": "Aptronix India iPhone repair charges",
        "source_url": "https://portal.aptronixindia.com/service/replacement-charges",
        "official_url": "https://support.apple.com/en-in/iphone/repair",
        "source_note": "Aptronix-listed service charges; final fees may vary. Confirm the current Apple/AASP quote."
    },
    {
        "aliases": ["iphone 17 pro"], "brand": "Apple", "model": "iPhone 17 Pro",
        "repair_by_issue": {"display": "₹37,506 listed display replacement charge", "battery": "₹7,363 listed battery replacement charge"},
        "replacement": "₹1,20,000–₹1,60,000 (indicative retail band; verify current price)",
        "source_title": "Aptronix India iPhone repair charges",
        "source_url": "https://portal.aptronixindia.com/service/replacement-charges",
        "official_url": "https://support.apple.com/en-in/iphone/repair",
        "source_note": "Aptronix-listed service charges; final fees may vary. Confirm the current Apple/AASP quote."
    },
    {
        "aliases": ["iphone 17"], "brand": "Apple", "model": "iPhone 17",
        "repair_by_issue": {"display": "₹37,506 listed display replacement charge", "battery": "₹6,115 listed battery replacement charge"},
        "replacement": "₹75,000–₹1,00,000 (indicative retail band; verify current price)",
        "source_title": "Aptronix India iPhone repair charges",
        "source_url": "https://portal.aptronixindia.com/service/replacement-charges",
        "official_url": "https://support.apple.com/en-in/iphone/repair",
        "source_note": "Aptronix-listed service charges; final fees may vary. Confirm the current Apple/AASP quote."
    },
    {
        "aliases": ["iphone 16 pro max"], "brand": "Apple", "model": "iPhone 16 Pro Max",
        "repair_by_issue": {"display": "₹41,078 listed display replacement charge", "battery": "₹7,363 listed battery replacement charge"},
        "replacement": "₹1,00,000–₹1,40,000 (indicative retail band; verify current price)",
        "source_title": "Aptronix India iPhone repair charges",
        "source_url": "https://portal.aptronixindia.com/service/replacement-charges",
        "official_url": "https://support.apple.com/en-in/iphone/repair",
        "source_note": "Aptronix-listed service charges; final fees may vary. Confirm the current Apple/AASP quote."
    },
    {
        "aliases": ["iphone 16 pro"], "brand": "Apple", "model": "iPhone 16 Pro",
        "repair_by_issue": {"display": "₹34,742 listed display replacement charge", "battery": "₹7,363 listed battery replacement charge"},
        "replacement": "₹90,000–₹1,20,000 (indicative retail band; verify current price)",
        "source_title": "Aptronix India iPhone repair charges",
        "source_url": "https://portal.aptronixindia.com/service/replacement-charges",
        "official_url": "https://support.apple.com/en-in/iphone/repair",
        "source_note": "Aptronix-listed service charges; final fees may vary. Confirm the current Apple/AASP quote."
    },
    {
        "aliases": ["iphone 16 plus"], "brand": "Apple", "model": "iPhone 16 Plus",
        "repair_by_issue": {"display": "₹34,742 listed display replacement charge", "battery": "₹6,115 listed battery replacement charge"},
        "replacement": "₹70,000–₹95,000 (indicative retail band; verify current price)",
        "source_title": "Aptronix India iPhone repair charges",
        "source_url": "https://portal.aptronixindia.com/service/replacement-charges",
        "official_url": "https://support.apple.com/en-in/iphone/repair",
        "source_note": "Aptronix-listed service charges; final fees may vary. Confirm the current Apple/AASP quote."
    },
    {
        "aliases": ["iphone 16"], "brand": "Apple", "model": "iPhone 16",
        "repair_by_issue": {"display": "₹26,928 listed display replacement charge", "battery": "₹6,115 listed battery replacement charge"},
        "replacement": "₹55,000–₹80,000 (indicative retail band; verify current price)",
        "source_title": "Aptronix India iPhone repair charges",
        "source_url": "https://portal.aptronixindia.com/service/replacement-charges",
        "official_url": "https://support.apple.com/en-in/iphone/repair",
        "source_note": "Aptronix-listed service charges; final fees may vary. Confirm the current Apple/AASP quote."
    },
    {
        "aliases": ["iphone 15 pro max"], "brand": "Apple", "model": "iPhone 15 Pro Max",
        "repair_by_issue": {"display": "₹39,211 listed display replacement charge", "battery": "₹6,115 listed battery replacement charge"},
        "replacement": "₹85,000–₹1,25,000 (indicative retail/availability band; verify current price)",
        "source_title": "Aptronix India iPhone repair charges",
        "source_url": "https://portal.aptronixindia.com/service/replacement-charges",
        "official_url": "https://support.apple.com/en-in/iphone/repair",
        "source_note": "Aptronix-listed service charges; final fees may vary. Confirm the current Apple/AASP quote."
    }
]

PAGE = r"""
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#050a18">
<meta name="description" content="ReLoop AI — explainable electronics repair and component-recovery intelligence.">
<title>ReLoop AI | Circular Electronics Intelligence</title>
<style>
:root{
  color-scheme:dark;
  --bg:#050a18;
  --bg2:#081329;
  --panel:rgba(12,24,49,.88);
  --panel2:#0a1630;
  --line:rgba(62,139,255,.25);
  --line-strong:rgba(69,164,255,.58);
  --blue:#35a7ff;
  --cyan:#69efff;
  --blue-deep:#1675ff;
  --muted:#9eafca;
  --white:#f2f7ff;
  --orange:#ffc779;
  --shadow:0 18px 55px rgba(0,0,0,.24);
}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{
  margin:0;min-height:100vh;overflow-x:hidden;position:relative;
  background:
    radial-gradient(ellipse at 12% 8%,rgba(18,100,255,.17),transparent 35%),
    radial-gradient(ellipse at 88% 30%,rgba(0,225,255,.09),transparent 32%),
    linear-gradient(145deg,var(--bg),#071126 52%,#040914);
  color:var(--white);font:15px/1.65 Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",Arial,sans-serif;
}
body:before{
  content:"";position:fixed;inset:0;pointer-events:none;z-index:0;opacity:.22;
  background-image:linear-gradient(rgba(70,144,255,.09) 1px,transparent 1px),
                   linear-gradient(90deg,rgba(70,144,255,.09) 1px,transparent 1px);
  background-size:38px 38px;
  mask-image:linear-gradient(to bottom,black,transparent 88%);
}
body:after{
  content:"";position:fixed;width:360px;height:360px;right:-210px;top:160px;
  border:1px solid rgba(53,167,255,.16);border-radius:50%;
  box-shadow:0 0 0 28px rgba(53,167,255,.025),0 0 0 58px rgba(53,167,255,.02);
  pointer-events:none;z-index:0;
}
header,main,footer{position:relative;z-index:1}
header{
  padding:17px 5%;border-bottom:1px solid rgba(81,151,255,.2);
  display:flex;justify-content:space-between;align-items:center;gap:14px;
  background:rgba(5,10,24,.78);backdrop-filter:blur(18px);
  position:sticky;top:0;z-index:5;
}
.brand{display:flex;align-items:center;gap:11px}
.logo-mark{
  width:39px;height:39px;border-radius:12px;display:grid;place-items:center;
  border:1px solid rgba(105,239,255,.48);
  background:linear-gradient(145deg,rgba(53,167,255,.22),rgba(22,117,255,.06));
  color:var(--cyan);font-size:21px;box-shadow:inset 0 0 20px rgba(53,167,255,.08),0 0 24px rgba(53,167,255,.12)
}
.logo{font-size:21px;font-weight:850;letter-spacing:-.8px;line-height:1.1}
.logo span{color:var(--cyan)}
.brand-sub{font-size:9px;color:#8da7cb;letter-spacing:1.65px;margin-top:4px}
.pill{
  border:1px solid rgba(75,158,255,.35);border-radius:30px;padding:7px 12px;
  color:#a9dfff;font-size:10px;letter-spacing:1.3px;font-weight:800;
  background:rgba(22,117,255,.07);white-space:nowrap
}
main{max-width:1120px;margin:auto;padding:35px 20px 64px}
.hero{padding:34px 0 29px;position:relative}\n.hero:before{content:"";display:block;width:58px;height:3px;margin-bottom:23px;background:linear-gradient(90deg,var(--blue),var(--cyan));border-radius:4px;box-shadow:0 0 18px rgba(53,167,255,.55)}
.eyebrow{color:var(--cyan);font-size:11px;font-weight:850;letter-spacing:2.3px;text-transform:uppercase}
.eyebrow:before{content:"";display:inline-block;width:20px;height:2px;background:var(--blue);vertical-align:middle;margin-right:9px;box-shadow:0 0 10px var(--blue)}
.hero h1{font-size:clamp(38px,6.5vw,66px);line-height:1.04;letter-spacing:-2.8px;margin:17px 0 15px;max-width:790px}
.hero h1 span{
  color:transparent;background:linear-gradient(90deg,#55b8ff 0%,#70f1ff 54%,#4a8dff 100%);
  -webkit-background-clip:text;background-clip:text
}
.hero p{color:var(--muted);max-width:650px;font-size:16px;margin:0}
.hero-meta{display:flex;gap:9px;flex-wrap:wrap;margin-top:22px}
.meta-chip{display:inline-flex;align-items:center;gap:7px;padding:6px 10px;border:1px solid rgba(87,149,231,.2);border-radius:8px;background:rgba(9,24,49,.58);font-size:11px;color:#b6c7e1}
.dot{width:6px;height:6px;border-radius:50%;background:var(--cyan);box-shadow:0 0 9px var(--cyan)}
.layout{display:grid;grid-template-columns:minmax(0,.95fr) minmax(0,1.05fr);gap:19px;align-items:start}
.card{
  position:relative;min-width:0;overflow:hidden;
  background:linear-gradient(145deg,rgba(13,28,56,.94),rgba(7,17,37,.96));
  border:1px solid var(--line);border-radius:19px;padding:23px;
  box-shadow:var(--shadow);backdrop-filter:blur(12px)
}
.card:before{content:"";position:absolute;left:0;top:0;width:100%;height:2px;background:linear-gradient(90deg,transparent,var(--blue),var(--cyan),transparent);opacity:.85}
.card-head{display:flex;justify-content:space-between;align-items:flex-start;gap:12px;margin-bottom:15px}
.section-code{font-size:10px;letter-spacing:1.8px;color:#79baff;font-weight:850}
h2{font-size:19px;letter-spacing:-.35px;margin:4px 0 7px}
p{color:var(--muted)}
.card-intro{font-size:12px;margin:0 0 16px;color:#9eafca}
.micro-tag{font-size:9px;color:#9fddff;border:1px solid rgba(53,167,255,.25);padding:5px 8px;border-radius:7px;white-space:nowrap;letter-spacing:1px}
label{display:block;margin:15px 0 7px;font-weight:750;font-size:12px;color:#dceaff}
input,textarea,select{
  width:100%;padding:12px 13px;border-radius:10px;
  border:1px solid rgba(81,143,224,.28);background:rgba(4,12,28,.8);
  color:var(--white);font:inherit;outline:none;transition:border-color .2s,box-shadow .2s
}
input:focus,textarea:focus,select:focus{border-color:var(--blue);box-shadow:0 0 0 3px rgba(53,167,255,.12)}
input::placeholder,textarea::placeholder{color:#637795}
input[type=file]{font-size:12px;padding:10px}
input[type=file]::file-selector-button{border:1px solid rgba(76,157,255,.35);background:#10284b;color:#c6e8ff;border-radius:7px;padding:7px 9px;margin-right:10px;cursor:pointer}
textarea{min-height:100px;resize:vertical}
.field-hint{font-size:10px;color:#7388a9;margin-top:5px}
button{
  display:flex;justify-content:center;align-items:center;gap:9px;
  background:linear-gradient(105deg,#1c83ff,#36c5ff 58%,#68efff);
  color:#04101f;border:1px solid rgba(156,239,255,.7);border-radius:11px;
  padding:14px 18px;font-weight:900;font-size:14px;letter-spacing:.1px;
  cursor:pointer;width:100%;margin-top:20px;
  box-shadow:0 8px 24px rgba(27,133,255,.22),inset 0 1px 0 rgba(255,255,255,.35);
  transition:transform .18s,filter .18s,box-shadow .18s
}
button:hover{filter:brightness(1.08);transform:translateY(-1px);box-shadow:0 11px 30px rgba(27,133,255,.32)}
button:active{transform:translateY(0)}
.notice{
  background:rgba(15,42,73,.62);border:1px solid rgba(71,157,255,.27);
  border-radius:11px;padding:12px 13px;margin:15px 0;color:#c6e6ff;font-size:12px
}
.notice strong{color:#eaf7ff}
.result{margin-top:22px}
.report-empty{min-height:230px;display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;padding:20px 8px}
.scan-icon{width:68px;height:68px;border-radius:19px;display:grid;place-items:center;font-size:29px;color:var(--cyan);border:1px solid rgba(86,184,255,.35);background:radial-gradient(circle at 50% 35%,rgba(51,168,255,.2),rgba(9,24,49,.3));box-shadow:0 0 35px rgba(37,140,255,.1);margin-bottom:17px}
.report-empty h3{margin:0 0 7px;font-size:16px}
.report-empty p{font-size:12px;max-width:290px;margin:0}
.statgrid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:9px;margin:17px 0}
.stat{padding:12px;background:rgba(4,12,28,.72);border:1px solid rgba(74,139,220,.2);border-radius:11px;overflow-wrap:anywhere;min-width:0}
.stat strong{display:block;font-size:14px;color:#c9edff;line-height:1.4}
.stat span{display:block;font-size:9px;color:#839bbd;margin-top:5px;text-transform:uppercase;letter-spacing:.6px}
.verdict{font-size:29px;font-weight:950;letter-spacing:-.7px;color:var(--cyan);margin:3px 0;text-shadow:0 0 22px rgba(53,167,255,.2)}
.result h3{font-size:13px;margin:21px 0 7px;color:#e0eeff}
.result p{font-size:13px}
ul{padding-left:19px}
li{margin:7px 0;color:#b7c8e1;font-size:12px}
a{color:#73dfff;overflow-wrap:anywhere;text-decoration-color:rgba(115,223,255,.35);text-underline-offset:3px}
a:hover{color:white}
.small{font-size:11px;color:#8499b8}
.status-line{display:flex;align-items:center;gap:8px;font-size:10px;color:#91a8c8;letter-spacing:.8px;margin-bottom:13px}
.status-line .dot{flex-shrink:0}
.report-divider{height:1px;background:linear-gradient(90deg,rgba(53,167,255,.45),rgba(53,167,255,.02));margin:18px 0}
footer{max-width:1120px;margin:auto;padding:0 20px 28px;text-align:center;color:#7185a4;font-size:11px;position:relative;z-index:1}
.footer-mark{color:#9fddff}
.footer-rule{height:1px;max-width:460px;margin:0 auto 17px;background:linear-gradient(90deg,transparent,rgba(53,167,255,.65),rgba(105,239,255,.55),transparent)}
.footer-copy{letter-spacing:.15px}
.prototype-note{max-width:850px;margin:0 auto 22px;padding:12px 16px;border:1px solid rgba(75,158,255,.28);border-radius:12px;background:linear-gradient(100deg,rgba(14,42,78,.72),rgba(8,22,47,.72));color:#c6e8ff;font-size:12px;line-height:1.7}
.prototype-note strong{color:#69efff}
.team-credit{max-width:850px;margin:18px auto 0;padding:17px 18px;border:1px solid rgba(53,167,255,.25);border-radius:14px;background:rgba(7,19,42,.72);box-shadow:0 0 28px rgba(25,120,255,.07)}
.team-title{color:#69efff;font-weight:900;letter-spacing:2px;font-size:11px;margin-bottom:11px}
.team-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 18px;text-align:left}
.team-member{color:#78c8ff;font-size:12px;line-height:1.6}
.team-member strong{color:#b8e8ff;font-weight:800}
.team-member span{color:#6fa9e8;font-size:11px}
.powered-by{display:flex;align-items:center;justify-content:center;gap:8px;margin-top:9px;color:#718db4;font-size:9px;letter-spacing:2.2px}
.powered-by:before,.powered-by:after{content:"";width:24px;height:1px;background:rgba(105,239,255,.45)}
.powered-by strong{font-size:11px;letter-spacing:2.8px;color:#69efff;text-shadow:0 0 14px rgba(53,167,255,.45)}
.card:after{content:"";position:absolute;right:13px;bottom:13px;width:24px;height:24px;border-right:1px solid rgba(105,239,255,.2);border-bottom:1px solid rgba(105,239,255,.2);border-radius:0 0 7px 0;pointer-events:none}
.hero:after{content:"R / 01";position:absolute;right:4px;bottom:27px;color:rgba(111,178,255,.38);font-size:10px;font-weight:800;letter-spacing:2px}
@media(max-width:760px){.hero:after{display:none}.footer-copy{line-height:1.9}.team-grid{grid-template-columns:1fr}}
@media(max-width:760px){
  header{padding:13px 16px}.brand-sub{letter-spacing:1px}.pill{font-size:8px;padding:6px 8px;letter-spacing:.7px}
  main{padding:22px 13px 42px}.hero{padding:25px 0 24px}.hero h1{letter-spacing:-1.8px}
  .layout{grid-template-columns:1fr}.card{padding:19px}.statgrid{grid-template-columns:repeat(3,minmax(0,1fr))}
}
@media(max-width:420px){
  .brand-sub{display:none}.logo{font-size:19px}.logo-mark{width:35px;height:35px}
  .pill{max-width:130px;white-space:normal;text-align:center;line-height:1.35}
  .statgrid{grid-template-columns:1fr}.stat{display:flex;justify-content:space-between;align-items:center;gap:12px}.stat span{margin:0;text-align:right}
}
@media(prefers-reduced-motion:reduce){html{scroll-behavior:auto}*,*:before,*:after{transition:none!important}}
</style>
</head>
<body>
<header>
 <div class="brand">
  <div class="logo-mark" aria-hidden="true">⌘</div>
  <div>
   <div class="logo">ReLoop<span> AI</span></div>
   <div class="brand-sub">CIRCULAR ELECTRONICS INTELLIGENCE</div>
  </div>
 </div>
 <div class="pill">THE CODEX</div>
</header>
<main>
 <section class="hero">
  <div class="eyebrow">ELECTRONICS REPAIR INTELLIGENCE</div>
  <h1>Give your device<br>a <span>second life.</span></h1>
  <p>Inspect visible damage, compare repair and replacement options, and make a more informed decision about the next life of your electronics.</p>
  <div class="hero-meta">
   <span class="meta-chip"><i class="dot"></i> Image-assisted inspection</span>
   <span class="meta-chip"><i class="dot"></i> Evidence-aware decisions</span>
   <span class="meta-chip"><i class="dot"></i> Circular-use pathways</span>
  </div>
 </section>

 <div class="layout">
  <section class="card">
   <div class="card-head">
    <div>
     <div class="section-code">01 / DEVICE INPUT</div>
     <h2>Device inspection</h2>
    </div>
    <span class="micro-tag">INPUT MODULE</span>
   </div>
   <p class="card-intro">Add a clear photo and the symptoms you have observed. The system will assess visible clues and identify where more information is needed.</p>
   <form method="post" enctype="multipart/form-data">
    <label for="photo">Device or component image *</label>
    <input id="photo" type="file" name="photo" accept="image/png,image/jpeg,image/webp" required>
    <div class="field-hint">JPG, PNG or WebP · Maximum 8 MB</div>

    <label for="symptoms">Symptoms and observed damage *</label>
    <textarea id="symptoms" name="symptoms" required
    placeholder="Example: Laptop overheats, fan makes noise, shuts down after 10 minutes...">{{ symptoms }}</textarea>

    <label for="model">Brand, model or component (if known)</label>
    <input id="model" name="model" value="{{ model }}"
    placeholder="Example: Dell Inspiron, model unknown">

    <label for="budget">Repair budget (INR, optional)</label>
    <input id="budget" name="budget" type="number" min="0" value="{{ budget }}"
    placeholder="Example: 2500">
    <button type="submit"><span aria-hidden="true">✨</span> Analyse my device</button>
   </form>
   <div class="notice"><strong>Safety note</strong><br>Do not open batteries, power supplies or mains-powered devices. A photo cannot confirm hidden internal faults; consult a qualified technician when needed.</div>
  </section>

  <section class="card">
   <div class="card-head">
    <div>
     <div class="section-code">02 / DECISION OUTPUT</div>
     <h2>Intelligence report</h2>
    </div>
    <span class="micro-tag">ANALYSIS MODULE</span>
   </div>
   <div class="status-line"><i class="dot"></i> EXPLAINABLE DECISION SUPPORT</div>
   {% if not result %}
    <div class="report-empty">
     <div class="scan-icon" aria-hidden="true">⌁</div>
     <h3>Your report starts here</h3>
     <p>Submit a device image and symptoms to generate an inspection summary and a suggested circular-use pathway.</p>
    </div>
    <div class="report-divider"></div>
    <div class="statgrid">
     <div class="stat"><strong>Vision AI</strong><span>Image inspection</span></div>
     <div class="stat"><strong>Web search</strong><span>Price evidence</span></div>
     <div class="stat"><strong>3 pathways</strong><span>Decision support</span></div>
    </div>
   {% else %}
    {% if result.error %}
      <div class="notice"><strong>Analysis needs attention</strong><br>{{ result.error }}</div>
    {% else %}
      <div class="eyebrow">{% if 'Rule-based' in (result.confidence or '') %}DEMO ENGINE ANALYSIS{% else %}AI-ASSISTED INSPECTION{% endif %}</div>
      <h2>{{ result.device }}</h2>
      <p>{{ result.damage }}</p>
      <div class="statgrid">
       <div class="stat"><strong>{{ result.confidence }}</strong><span>Identification confidence</span></div>
       <div class="stat"><strong>{{ result.repair_cost }}</strong><span>Repair estimate</span></div>
       <div class="stat"><strong>{{ result.replace_cost }}</strong><span>Replacement estimate</span></div>
      </div>
      {% if result.questions %}
       <div class="notice"><strong>More details needed</strong>
       <ul>{% for q in result.questions %}<li>{{ q }}</li>{% endfor %}</ul>
       Please add the answers in the model or symptoms fields and analyse again.</div>
      {% else %}
       <div class="report-divider"></div>
       <div class="eyebrow">RECOMMENDED PATHWAY</div>
       <div class="verdict">{{ result.decision }}</div>
       <p>{{ result.reason }}</p>
       <h3>Why this recommendation?</h3>
       <ul>{% for item in result.reasons %}<li>{{ item }}</li>{% endfor %}</ul>
       <h3>Cost, affordability and usefulness</h3>
       <p>{{ result.comparison }}</p>
       <h3>Price and technical sources</h3>
       {% if result.sources %}
        <ul>{% for s in result.sources %}
         <li><a href="{{ s.url }}" target="_blank" rel="noopener">{{ s.title }}</a>
         — {{ s.summary }}</li>
        {% endfor %}</ul>
       {% else %}
        <p><strong>Offline reference estimate:</strong> the repair and replacement ranges above are generated from ReLoop AI's built-in planning rules. If the model matches the stored price database, model-specific reference figures are used; otherwise, a broad average range for that device category is shown.</p>
        <ul>
         <li><strong>Cost method:</strong> compare estimated repair cost with indicative replacement cost and the device's likely remaining useful life.</li>
         <li><strong>Technical decision factors:</strong> reported symptoms, safety concerns, repair feasibility, parts availability, and possible reuse or material recovery.</li>
         <li><strong>Price status:</strong> offline reference estimate, not a live quote. Treat these figures as planning estimates, not a verified shop quote.</li>
        </ul>
       {% endif %}
      {% endif %}
      <div class="report-divider"></div>
      <p class="small">AI-generated decision support, not a physical diagnosis. Verify prices, compatibility, warranty and repair safety with a qualified technician.</p>
    {% endif %}
   {% endif %}
  </section>
 </div>
</main>
<footer>
 <div class="prototype-note"><strong>DEMO PROTOTYPE ONLY</strong> — This prototype demonstrates the intended ReLoop AI workflow. The full, production-ready ReLoop AI will be developed after qualifying for Round 2.</div>
 <div class="footer-rule"></div>
 <div class="footer-copy"><span class="footer-mark">ReLoop AI</span> · Repair first when safe and practical · Recover useful components · Recycle responsibly</div>
 <div class="team-credit">
  <div class="team-title">🔵 TEAM RELOOP AI</div>
  <div class="team-grid">
   <div class="team-member"><strong>Abishajesudhas</strong> <span>· Team Leader · 146110026</span></div>
   <div class="team-member"><strong>Aakashwar.s</strong> <span>· 146110004</span></div>
   <div class="team-member"><strong>Abenav</strong> <span>· 146110015</span></div>
   <div class="team-member"><strong>Ankitha</strong> <span>· 146110059</span></div>
   <div class="team-member"><strong>Anisha</strong> <span>· 146110058</span></div>
  </div>
 </div>
 <div class="powered-by">POWERED BY <strong>THE CODEX</strong></div>
</footer>
</body>
</html>
"""


def extract_json(text):
    """Read a JSON object from an AI response."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("The AI did not return structured JSON.")
    return json.loads(text[start:end + 1])


def ask_ai(instructions, content):
    """Call Gemini with text and optional base64 image content; return a JSON object."""
    if not GEMINI_API_KEY:
        raise ValueError(
            "Gemini AI is not connected. Add GEMINI_API_KEY in Render Environment settings."
        )

    gemini_parts = []
    for item in content:
        item_type = item.get("type")
        if item_type == "input_text":
            gemini_parts.append({"text": item.get("text", "")})
        elif item_type == "input_image":
            image_url = item.get("image_url", "")
            match = re.match(r"^data:([^;]+);base64,(.+)$", image_url, re.DOTALL)
            if not match:
                raise ValueError("The uploaded image could not be prepared for Gemini.")
            gemini_parts.append({
                "inlineData": {
                    "mimeType": match.group(1),
                    "data": match.group(2)
                }
            })

    if not gemini_parts:
        raise ValueError("No text or image content was provided to the AI.")

    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    try:
        response = requests.post(
            url,
            headers={
                "x-goog-api-key": GEMINI_API_KEY,
                "Content-Type": "application/json"
            },
            json={
                "systemInstruction": {"parts": [{"text": instructions}]},
                "contents": [{"role": "user", "parts": gemini_parts}],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "temperature": 0.2,
                    "maxOutputTokens": 1400
                }
            },
            timeout=(10, 65)
        )
    except requests.Timeout as exc:
        logger.warning("Gemini request timed out (model=%s): %s", GEMINI_MODEL, type(exc).__name__)
        raise RuntimeError("Gemini took too long to respond. Please try a smaller JPG/PNG image or try again shortly.") from exc
    except requests.RequestException as exc:
        logger.warning("Gemini network request failed (model=%s): %s", GEMINI_MODEL, type(exc).__name__)
        raise RuntimeError("Could not connect to Gemini. Check the Render service/network and try again.") from exc

    if not response.ok:
        try:
            api_error = response.json().get("error", {})
            detail = api_error.get("message", "")
        except (ValueError, AttributeError):
            detail = ""
        logger.warning("Gemini returned HTTP %s (model=%s): %s", response.status_code, GEMINI_MODEL, detail[:300])
        raise requests.HTTPError(
            f"Gemini HTTP {response.status_code}: {detail[:300]}", response=response
        )
    data = response.json()
    candidates = data.get("candidates", [])
    if not candidates:
        feedback = data.get("promptFeedback", {}).get("blockReason")
        if feedback:
            raise ValueError(f"Gemini blocked this request: {feedback}.")
        raise ValueError("Gemini returned no response. Check model access and API quota.")

    response_parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [part.get("text", "") for part in response_parts if part.get("text")]
    if not text_parts:
        raise ValueError("Gemini returned no readable text. Try another image or model.")
    return extract_json("\n".join(text_parts))




def estimate_cost_ranges(model, symptoms):
    """Return rough India planning ranges; these are not live prices or quotes."""
    text = f"{model or ''} {symptoms or ''}".lower()
    if any(k in text for k in ("laptop", "notebook", "dell inspiron", "macbook", "thinkpad")):
        repair = "₹1,500–₹10,000 (rough estimate)"
        replacement = "₹25,000–₹70,000 (rough estimate)"
        if any(k in text for k in ("screen", "display", "hinge")):
            repair = "₹3,000–₹15,000 (rough estimate; part/model dependent)"
        elif any(k in text for k in ("battery", "charging", "keyboard", "fan")):
            repair = "₹1,500–₹7,000 (rough estimate; part/model dependent)"
    elif any(k in text for k in ("phone", "mobile", "smartphone", "iphone", "galaxy", "redmi", "realme", "pixel")):
        repair = "₹800–₹6,000 (rough estimate)"
        replacement = "₹8,000–₹30,000 (rough estimate)"
        if any(k in text for k in ("screen", "display")):
            repair = "₹2,000–₹12,000 (rough estimate; model dependent)"
        elif "battery" in text:
            repair = "₹800–₹3,500 (rough estimate; model dependent)"
    elif any(k in text for k in ("tablet", "ipad")):
        repair = "₹1,000–₹8,000 (rough estimate)"
        replacement = "₹8,000–₹35,000 (rough estimate)"
        if any(k in text for k in ("screen", "display")):
            repair = "₹3,000–₹12,000 (rough estimate; model dependent)"
    elif any(k in text for k in ("tv", "television")):
        repair = "₹1,500–₹12,000 (rough estimate)"
        replacement = "₹10,000–₹50,000 (rough estimate)"
    elif any(k in text for k in ("earbud", "headphone", "headset", "speaker")):
        repair = "₹500–₹2,500 (rough estimate)"
        replacement = "₹1,000–₹8,000 (rough estimate)"
    else:
        repair = "₹500–₹5,000 (rough estimate; device type dependent)"
        replacement = "₹2,000–₹20,000 (rough estimate; device type dependent)"

    # If a genuine source-backed price already exists, do not overwrite it.
    return repair, replacement


def find_stored_price_record(model):
    """Find an exact/alias model match in the built-in price snapshot database."""
    text = re.sub(r"[^a-z0-9]+", " ", (model or "").lower()).strip()
    if not text:
        return None
    # Longest aliases first prevents e.g. iPhone 16 matching iPhone 16 Pro Max.
    records = sorted(STORED_PRICE_DATABASE, key=lambda row: max(map(len, row["aliases"])), reverse=True)
    for record in records:
        for alias in record["aliases"]:
            normal_alias = re.sub(r"[^a-z0-9]+", " ", alias.lower()).strip()
            if normal_alias and normal_alias in text:
                return record
    return None


def add_cost_estimates(result, model, symptoms):
    """Prefer stored model/issue prices where available; otherwise use broad ranges."""
    repair, replacement = estimate_cost_ranges(model, symptoms)
    repair_value = str(result.get("repair_cost", "")).strip()
    replace_value = str(result.get("replace_cost", "")).strip()
    unknown_values = ("", "not verified", "not estimated", "unknown", "n/a", "none")
    symptom_text = f"{model or ''} {symptoms or ''}".lower()
    record = find_stored_price_record(model)
    stored_repair = None
    if record:
        if any(term in symptom_text for term in ("screen", "display", "cracked", "broken glass")):
            stored_repair = record.get("repair_by_issue", {}).get("display")
        elif any(term in symptom_text for term in ("battery", "does not hold charge", "drains fast")):
            stored_repair = record.get("repair_by_issue", {}).get("battery")

    # Use stored model-specific figures instead of generic bands when the user
    # has not received a source-backed price from the live analysis.
    if stored_repair and (repair_value.lower() in unknown_values or "rough estimate" in repair_value.lower()):
        result["repair_cost"] = stored_repair
    elif repair_value.lower() in unknown_values:
        result["repair_cost"] = repair

    if record and (replace_value.lower() in unknown_values or "rough estimate" in replace_value.lower()):
        result["replace_cost"] = record.get("replacement", replacement)
    elif replace_value.lower() in unknown_values:
        result["replace_cost"] = replacement

    sources = result.get("sources") or []
    if record:
        source_urls = {source.get("url") for source in sources}
        for title, url, summary in [
            (record.get("source_title", "Stored price source"), record.get("source_url", ""), record.get("source_note", "")),
            ("Manufacturer repair pricing / service guidance", record.get("official_url", ""), "Manufacturer guidance. Final prices depend on exact variant, taxes, labour, warranty and technician diagnosis.")
        ]:
            if url and url not in source_urls:
                sources.append({"title": title, "url": url, "summary": summary})
                source_urls.add(url)
        result["sources"] = sources
        note = (f"Stored database match: {record['brand']} {record['model']}. "
                "Repair figures are from the linked price listing and may cover parts/service charges only. "
                "Replacement figures are indicative stored retail bands, not live prices. Verify the current final quote.")
    else:
        note = ("No exact model entry was found in the stored price database, so broad rule-based planning ranges are shown. "
                "These are not live prices or a technician quote; actual cost depends on exact model, part quality and diagnosis.")
    result["comparison"] = (str(result.get("comparison", "")).strip() + " " + note).strip()
    return result

def build_rule_based_fallback(model, symptoms, budget):
    """Create transparent rule-based guidance when Gemini is unavailable.

    This function deliberately does not claim to inspect or understand the uploaded image.
    """
    symptom_text = (symptoms or "").lower()
    device_name = model.strip() if model and model.strip() else "Electronics device (model not supplied)"

    urgent_terms = ("smoke", "sparks", "burning smell", "swollen battery", "bulging battery", "overheating", "wet", "liquid damage")
    if any(term in symptom_text for term in urgent_terms):
        decision = "INSPECT FIRST"
        reason = ("The symptom description may indicate a safety or internal-damage issue. Stop using or charging the device and have it checked by a qualified technician. This is a text-based rule, not an image diagnosis.")
        reasons = [
            "Safety-related symptoms need professional inspection before repair or reuse.",
            "The uploaded photo has not been analysed by AI in this fallback mode.",
            "Do not decide to recycle or replace solely from the symptom text."
        ]
    elif any(term in symptom_text for term in ("cracked", "broken screen", "screen", "display", "charging port", "connector", "keyboard", "speaker", "button")):
        decision = "REPAIR REVIEW"
        reason = "A repair assessment is a reasonable first step, but the actual fault and repairability have not been verified. This recommendation uses the symptom text only; the image was not analysed by AI."
        reasons = [
            "Ask a technician to confirm the failed component and repair cost.",
            "Compare the verified repair quote with the cost of a suitable replacement.",
            "Check parts availability, warranty, and data backup needs before deciding."
        ]
    else:
        decision = "INSPECT FIRST"
        reason = "There is not enough verified information to recommend repair, replacement, or recovery confidently. This fallback uses the symptom text only; the image was not analysed by AI."
        reasons = [
            "Record the exact model and symptoms.",
            "Get a technician's diagnosis and a written repair estimate.",
            "Compare repair cost and expected remaining useful life before choosing a pathway."
        ]

    # Offline fallback deliberately does not depend on live web search.
    # Model-specific stored prices are linked by add_cost_estimates(); unmatched
    # devices receive clearly labelled India planning ranges.
    sources = []

    result = {
        "device": device_name,
        "damage": "Assessment scope: this result uses the device details and symptom information provided. Image-based confirmation was not completed for this report.",
        "confidence": "Rule-based · not image-verified",
        "decision": decision,
        "reason": reason,
        "reasons": reasons,
        "comparison": (f"Budget entered: ₹{budget}. " if budget else "No budget supplied. ") + "The stored price database is checked for a model match; unmatched models use broad planning ranges.",
        "repair_cost": "Not verified",
        "replace_cost": "Not verified",
        "sources": sources,
        "questions": []
    }
    return add_cost_estimates(result, model, symptoms)

def search_web(query):
    """Search current public web pages. Empty list means no live evidence."""
    if not TAVILY_API_KEY:
        return []
    try:
        response = requests.post(
            "https://api.tavily.com/search",
            headers={"Content-Type": "application/json"},
            json={
                "api_key": TAVILY_API_KEY,
                "query": query,
                "search_depth": "basic",
                "max_results": 5,
                "topic": "general"
            },
            timeout=(8, 20)
        )
        if not response.ok:
            logger.warning("Tavily search returned HTTP %s; continuing without live web sources.", response.status_code)
            return []
        return response.json().get("results", [])
    except (requests.RequestException, ValueError) as exc:
        # Live pricing search is supplementary; analysis can still continue without it.
        logger.warning("Tavily search unavailable (%s); continuing without live web sources.", type(exc).__name__)
        return []


@app.route("/", methods=["GET", "POST"])
def home():
    result = None
    symptoms = ""
    model = ""
    budget = ""

    if request.method == "POST":
        symptoms = request.form.get("symptoms", "").strip()
        model = request.form.get("model", "").strip()
        budget = request.form.get("budget", "").strip()
        photo = request.files.get("photo")

        if not GEMINI_API_KEY:
            if not photo or not photo.filename:
                result = {"error": "Please choose a device image first."}
            elif not symptoms:
                result = {"error": "Please describe the symptoms first."}
            elif photo.mimetype not in ("image/jpeg", "image/png", "image/webp"):
                result = {"error": "Use a JPG, PNG or WebP image."}
            else:
                result = build_rule_based_fallback(model, symptoms, budget)
        elif not photo or not photo.filename:
            result = {"error": "Please choose a device image first."}
        elif not symptoms:
            result = {"error": "Please describe the symptoms first."}
        elif photo.mimetype not in ("image/jpeg", "image/png", "image/webp"):
            result = {"error": "Use a JPG, PNG or WebP image."}
        else:
            try:
                raw = photo.read()
                if len(raw) > 8 * 1024 * 1024:
                    raise ValueError("Image must be smaller than 8 MB.")
                encoded = base64.b64encode(raw).decode("utf-8")
                image_url = f"data:{photo.mimetype};base64,{encoded}"

                inspection = ask_ai(
                    "You inspect consumer electronics from photos and symptoms. "
                    "Never claim a hidden fault is certain from an image. "
                    "If device/component identity is uncertain, return questions "
                    "to ask before recommending a pathway. Return JSON only with "
                    "keys: device, component, damage, confidence, search_query, "
                    "questions. confidence must be a cautious text label, not a "
                    "fabricated calibrated probability. questions is an array.",
                    [
                        {"type": "input_text", "text":
                         f"Symptoms: {symptoms}\nModel details: {model or 'Not supplied'}\n"
                         "Identify what is visible, likely affected component, "
                         "and what information is missing. Do not invent model numbers."},
                        {"type": "input_image", "image_url": image_url}
                    ]
                )

                questions = inspection.get("questions", [])
                if questions:
                    result = {
                        "device": inspection.get("device", "Uncertain device"),
                        "damage": inspection.get("damage", "Identity needs clarification."),
                        "confidence": inspection.get("confidence", "Low"),
                        "questions": questions,
                        "repair_cost": "Not estimated",
                        "replace_cost": "Not estimated",
                        "comparison": "More information is needed for a confident assessment."
                    }
                    result = add_cost_estimates(result, model, symptoms)
                else:
                    query = inspection.get("search_query") or (
                        f"{model} {inspection.get('component', 'component')} "
                        "repair replacement price India INR"
                    )
                    pages = search_web(query)
                    sources = []
                    for p in pages:
                        url = p.get("url", "")
                        if url.startswith("https://") or url.startswith("http://"):
                            sources.append({
                                "title": p.get("title", "Source page")[:180],
                                "url": url,
                                "summary": p.get("content", "Open source for details")[:350]
                            })

                    evidence = [{
                        "title": s["title"], "url": s["url"],
                        "summary": s["summary"]
                    } for s in sources]

                    decision = ask_ai(
                        "You are ReLoop AI, an explainable electronics circularity "
                        "decision assistant. Return JSON only with keys: decision, "
                        "reason, reasons, comparison, repair_cost, replace_cost. "
                        "decision must be exactly REPAIR, REPLACE, or RECYCLE. "
                        "Use source evidence cautiously; search snippets may not "
                        "contain prices. Never invent a live price. If no verified "
                        "price appears, say 'Not verified'. Consider affordability, "
                        "repairability, likely remaining useful life, efficiency, "
                        "data/security, and environmental impact. Do not claim to "
                        "measure efficiency unless evidence supports it. Explain "
                        "uncertainty and recommend professional inspection when needed.",
                        [{"type": "input_text", "text":
                          f"Inspection: {json.dumps(inspection)}\n"
                          f"Symptoms: {symptoms}\nModel: {model or 'Unknown'}\n"
                          f"User repair budget INR: {budget or 'Not given'}\n"
                          f"Web search evidence: {json.dumps(evidence)}\n"
                          "Compare repair versus replacement. Only use RECYCLE "
                          "when repair/reuse is unsafe, impractical or uneconomic. "
                          "Do not treat absence of price evidence as a price of zero."}]
                    )
                    result = {
                        "device": inspection.get("device", "Uncertain device"),
                        "damage": inspection.get("damage", "Needs technician inspection."),
                        "confidence": inspection.get("confidence", "Uncertain"),
                        "decision": decision.get("decision", "REPAIR"),
                        "reason": decision.get("reason", "Review the evidence with a technician."),
                        "reasons": decision.get("reasons", []),
                        "comparison": decision.get("comparison", "Price evidence may be incomplete."),
                        "repair_cost": decision.get("repair_cost", "Not verified"),
                        "replace_cost": decision.get("replace_cost", "Not verified"),
                        "sources": sources,
                        "questions": []
                    }
                    result = add_cost_estimates(result, model or inspection.get("device", ""), symptoms)
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else "unknown"
                logger.warning("AI provider request failed (HTTP %s); using offline demo engine.", status)
                result = build_rule_based_fallback(model, symptoms, budget)
                result["comparison"] = (
                    "OFFLINE DEMO MODE: the cloud AI service did not complete this request. "
                    "This result uses the entered model/symptoms, transparent rules, and stored or category-level price estimates; "
                    "the uploaded image was not confirmed by vision AI. " + result["comparison"]
                )
            except requests.RequestException as exc:
                logger.warning("External API request failed: %s", type(exc).__name__)
                result = build_rule_based_fallback(model, symptoms, budget)
                result["comparison"] = "ReLoop AI demo decision engine: this report uses the submitted details, symptom rules, and stored reference-price data. Image-based AI confirmation was not completed for this result. " + result["comparison"]
            except RuntimeError as exc:
                result = build_rule_based_fallback(model, symptoms, budget)
                result["comparison"] = "ReLoop AI demo decision engine: this report uses the submitted details, symptom rules, and stored reference-price data. Image-based AI confirmation was not completed for this result. " + result["comparison"]
            except (ValueError, KeyError, json.JSONDecodeError) as exc:
                logger.warning("AI analysis/parsing did not complete (%s); using offline demo engine.", type(exc).__name__)
                result = build_rule_based_fallback(model, symptoms, budget)
                result["comparison"] = (
                    "OFFLINE DEMO MODE: the cloud AI service did not complete this request. "
                    "This result uses the entered model/symptoms, transparent rules, and stored or category-level price estimates; "
                    "the uploaded image was not confirmed by vision AI. " + result["comparison"]
                )
            except Exception as exc:
                logger.exception("Unexpected analysis error; using offline demo engine.")
                result = build_rule_based_fallback(model, symptoms, budget)
                result["comparison"] = (
                    "OFFLINE DEMO MODE: the cloud AI service did not complete this request. "
                    "This result uses the entered model/symptoms, transparent rules, and stored or category-level price estimates; "
                    "the uploaded image was not confirmed by vision AI. " + result["comparison"]
                )

    return render_template_string(
        PAGE, result=result, symptoms=symptoms, model=model, budget=budget
    )


@app.errorhandler(413)
def too_large(_error):
    return "Image too large. Please upload an image under 8 MB.", 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
