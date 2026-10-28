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
<title>ReLoop AI | Circular Electronics Intelligence</title>
<style>
:root{--bg:#08130f;--panel:#10221a;--line:#244333;--green:#a9f16c;
--muted:#a8b9ad;--white:#f3f7f1;--orange:#ffca80}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--white);
font:15px/1.6 Arial,sans-serif}
header{padding:20px 5%;border-bottom:1px solid var(--line);
display:flex;justify-content:space-between;align-items:center;gap:12px}
.logo{font-size:22px;font-weight:800;letter-spacing:-1px}
.logo span{color:var(--green)}
.pill{border:1px solid var(--line);border-radius:30px;padding:6px 12px;
color:var(--green);font-size:12px}
main{max-width:1050px;margin:auto;padding:35px 18px 70px}
.hero{padding:25px 0 28px}
.eyebrow{color:var(--green);font-size:12px;font-weight:bold;letter-spacing:2px}
h1{font-size:clamp(32px,6vw,54px);line-height:1.08;letter-spacing:-2px;
margin:12px 0}
h1 span{color:var(--green)}
p{color:var(--muted)}
.layout{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.card{background:var(--panel);border:1px solid var(--line);
border-radius:18px;padding:22px;min-width:0}
h2{font-size:19px;margin:0 0 12px}
label{display:block;margin:15px 0 6px;font-weight:bold;font-size:13px}
input,textarea,select{width:100%;padding:12px;border-radius:10px;
border:1px solid var(--line);background:#091710;color:white;font:inherit}
input[type=file]{font-size:13px}
textarea{min-height:90px;resize:vertical}
button{background:var(--green);color:#10200c;border:0;border-radius:10px;
padding:14px 18px;font-weight:800;font-size:15px;cursor:pointer;width:100%;
margin-top:18px}
button:hover{filter:brightness(1.07)}
.small{font-size:12px;color:var(--muted)}
.notice{background:#172c20;border:1px solid #385c3b;border-radius:10px;
padding:12px;margin:14px 0;color:#d6e9d1;font-size:13px}
.result{margin-top:22px}
.verdict{font-size:30px;font-weight:900;color:var(--green);margin:4px 0}
.statgrid{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:15px 0}
.stat{padding:13px;background:#091710;border:1px solid var(--line);
border-radius:12px;overflow-wrap:anywhere}
.stat strong{display:block;font-size:16px}
.stat span{font-size:11px;color:var(--muted)}
ul{padding-left:20px}
li{margin:7px 0}
a{color:var(--green);overflow-wrap:anywhere}
footer{padding-top:25px;text-align:center;color:var(--muted);font-size:12px}
@media(max-width:700px){.layout{grid-template-columns:1fr}header{padding:16px}
main{padding:22px 13px 45px}.statgrid{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<header>
 <div class="logo">♻ ReLoop<span> AI</span></div>
 <div class="pill">EXPLAINABLE • CIRCULAR TECH</div>
</header>
<main>
 <section class="hero">
  <div class="eyebrow">ELECTRONICS REPAIR INTELLIGENCE</div>
  <h1>Give your device<br>a <span>second life.</span></h1>
  <p>Upload a photo, describe the symptoms, and explore evidence-based
  repair, replacement and recycling options.</p>
 </section>

 <div class="layout">
  <section class="card">
   <h2>01 / Device inspection</h2>
   <p class="small">A clear photo helps the AI inspect visible damage.</p>
   <form method="post" enctype="multipart/form-data">
    <label for="photo">Device or component image *</label>
    <input id="photo" type="file" name="photo" accept="image/png,image/jpeg,image/webp" required>
    <label for="symptoms">Symptoms and observed damage *</label>
    <textarea id="symptoms" name="symptoms" required
    placeholder="Example: Laptop overheats, fan makes noise, shuts down after 10 minutes...">{{ symptoms }}</textarea>
    <label for="model">Brand, model or component (if known)</label>
    <input id="model" name="model" value="{{ model }}"
    placeholder="Example: Dell Inspiron, model unknown">
    <label for="budget">Repair budget (INR, optional)</label>
    <input id="budget" name="budget" type="number" min="0" value="{{ budget }}"
    placeholder="Example: 2500">
    <button type="submit">✦ Analyse my device</button>
   </form>
   <div class="notice">For safety, do not open batteries, power supplies or
   mains-powered devices. The photo cannot confirm hidden internal faults.</div>
  </section>

  <section class="card">
   <h2>02 / Intelligence report</h2>
   {% if not result %}
    <p>Your report will appear here after you submit a device image and symptoms.</p>
    <div class="statgrid">
     <div class="stat"><strong>Vision AI</strong><span>Image inspection</span></div>
     <div class="stat"><strong>Web search</strong><span>Price evidence</span></div>
     <div class="stat"><strong>3 pathways</strong><span>Decision support</span></div>
    </div>
   {% else %}
    {% if result.error %}
      <div class="notice">{{ result.error }}</div>
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
      <p class="small">AI-generated decision support, not a physical diagnosis.
      Verify prices, compatibility, warranty and repair safety with a qualified technician.</p>
    {% endif %}
   {% endif %}
  </section>
 </div>
 <footer>ReLoop AI • Repair first when safe and practical • Recycle responsibly</footer>
</main>
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
