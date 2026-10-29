import os
import json
import base64
import re
import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "gpt-4o-mini")

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
.hero{padding:34px 0 29px;position:relative}
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
 <div class="pill">EXPLAINABLE · CIRCULAR TECH</div>
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
      <div class="eyebrow">AI INSPECTION</div>
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
        <p>No live sources were returned. Prices are not verified.</p>
       {% endif %}
      {% endif %}
      <div class="report-divider"></div>
      <p class="small">AI-generated decision support, not a physical diagnosis. Verify prices, compatibility, warranty and repair safety with a qualified technician.</p>
    {% endif %}
   {% endif %}
  </section>
 </div>
</main>
<footer><span class="footer-mark">ReLoop AI</span> · Repair first when safe and practical · Recover useful components · Recycle responsibly</footer>
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
    """Call the vision-capable AI model using the Responses API."""
    response = requests.post(
        "https://api.openai.com/v1/responses",
        headers={
            "Authorization": f"Bearer {OPENAI_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": AI_MODEL,
            "instructions": instructions,
            "input": [{"role": "user", "content": content}],
            "max_output_tokens": 1400
        },
        timeout=90
    )
    response.raise_for_status()
    data = response.json()
    parts = []
    for item in data.get("output", []):
        for part in item.get("content", []):
            if part.get("type") == "output_text":
                parts.append(part.get("text", ""))
    if not parts:
        raise ValueError("The AI returned no readable text.")
    return extract_json("\n".join(parts))


def search_web(query):
    """Search current public web pages. Empty list means no live evidence."""
    if not TAVILY_API_KEY:
        return []
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
        timeout=35
    )
    response.raise_for_status()
    return response.json().get("results", [])


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

        if not OPENAI_API_KEY:
            result = {"error": "Vision AI is not connected yet. Add OPENAI_API_KEY in your hosting service's environment variables."}
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
                        "replace_cost": "Not estimated"
                    }
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
            except requests.HTTPError as exc:
                status = exc.response.status_code if exc.response is not None else "unknown"
                result = {"error": f"An API returned HTTP {status}. Check the API key, access and usage limits in your hosting settings."}
            except requests.RequestException:
                result = {"error": "A network/API request failed. Check the API keys and try again."}
            except (ValueError, KeyError, json.JSONDecodeError) as exc:
                result = {"error": f"Could not complete the analysis: {str(exc)[:220]}"}
            except Exception:
                result = {"error": "Unexpected error. Check the server logs for details."}

    return render_template_string(
        PAGE, result=result, symptoms=symptoms, model=model, budget=budget
    )


@app.errorhandler(413)
def too_large(_error):
    return "Image too large. Please upload an image under 8 MB.", 413


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=False)
