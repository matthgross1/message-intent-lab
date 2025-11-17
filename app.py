import os
import base64
from flask import Flask, render_template_string, request
from openai import OpenAI

app = Flask(__name__)

# Get API key from environment
API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY) if API_KEY else None

HTML_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <title>Message Intent Lab</title>
    <meta charset="utf-8">
    <style>
      body { font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 40px; max-width: 800px; }
      textarea { width: 100%; min-height: 200px; font-family: inherit; padding: 8px; }
      input, button, select { font-family: inherit; padding: 6px 10px; }
      .field { margin-bottom: 16px; }
      .label { font-weight: 600; margin-bottom: 4px; display: block; }
      .result { white-space: pre-wrap; border: 1px solid #ddd; padding: 16px; border-radius: 8px; margin-top: 24px; }
      .error { color: #b00020; margin-top: 16px; }
      .hint { font-size: 0.9rem; color: #555; }
    </style>
  </head>
  <body>
    <h1>Message Intent Lab</h1>
    <p>Upload screenshots or paste a text thread to get a behavioral-science read on the other person's likely intentions.</p>

    {% if error %}
      <div class="error"><strong>Error:</strong> {{ error }}</div>
    {% endif %}

    <form method="POST" enctype="multipart/form-data">
      <div class="field">
        <label class="label" for="who">Who are you in the conversation?</label>
        <select name="who" id="who" required>
          <option value="">Select...</option>
          <option {% if who == "Person A / first speaker" %}selected{% endif %}>Person A / first speaker</option>
          <option {% if who == "Person B / second speaker" %}selected{% endif %}>Person B / second speaker</option>
          <option {% if who == "Blue bubbles" %}selected{% endif %}>Blue bubbles</option>
          <option {% if who == "Gray bubbles" %}selected{% endif %}>Gray bubbles</option>
        </select>
      </div>

      <div class="field">
        <label class="label" for="context">Optional: 1–2 sentences of context</label>
        <textarea name="context" id="context" placeholder="e.g., We've been casually dating for 2 months. Things felt normal until last week.">{{ context or "" }}</textarea>
      </div>

      <div class="field">
        <label class="label" for="images">Screenshots (PNG/JPG/HEIC, earliest message first)</label>
        <input type="file" name="images" id="images" accept="image/*" multiple>
        <div class="hint">You can upload 1–3 screenshots of the conversation, or skip this and just paste the text below.</div>
      </div>

      <div class="field">
        <label class="label" for="thread">Text thread (paste in order, earliest at the top)</label>
        <textarea name="thread" id="thread" placeholder="Optional if you uploaded screenshots. Paste the conversation here in order.">{{ thread or "" }}</textarea>
        <div class="hint">If you upload screenshots, I'll try to read the text from them first and only fall back to this box if needed.</div>
      </div>

      <button type="submit">Analyze intentions</button>
    </form>

    {% if result %}
      <div class="result">
        <h2>Intent Snapshot</h2>
        {{ result }}
      </div>
    {% endif %}
  </body>
</html>
"""

SYSTEM_PROMPT = """
You are a behavioral scientist specializing in interpersonal communication, attachment patterns, and conflict dynamics.

The user will share a text message conversation and briefly describe who they are in the exchange. Your job is to infer likely intentions and emotional motives of the other person, not to give definitive answers.

Please give your output in exactly four sections, clearly labeled:

1. Surface-Level Summary (2–3 sentences)
2. Likely Intentions of the Other Person (3–5 bullets)
3. Emotional / Psychological Patterns You See (1–2 paragraphs)
4. Ambiguities and Alternative Reads (2–3 bullets)

Do NOT tell the client what to text back. Do NOT give life advice. Focus on helping them see the pattern beneath the words.
"""

def extract_text_from_images(files):
    """
    Given a list of Werkzeug FileStorage objects (uploaded screenshots),
    call the vision model to extract raw text. Returns a single big string.
    """
    if not files:
        return ""

    all_text = []

    for img in files:
        if not img or img.filename == "":
            continue

        try:
            img_bytes = img.read()
            if not img_bytes:
                continue

            b64 = base64.b64encode(img_bytes).decode("utf-8")

            # Vision OCR call
            resp = client.chat.completions.create(
                model="gpt-4.1-mini",  # supports vision
                messages=[
                    {
                        "role": "system",
                        "content": "You are an OCR engine. Extract ONLY the visible text from this screenshot of a messaging conversation. Do not add explanation, labels, or commentary."
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Extract the raw text exactly as it appears in the chat bubble order."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=0.0,
            )

            text_chunk = resp.choices[0].message.content.strip()
            if text_chunk:
                all_text.append(text_chunk)

        except Exception as e:
            print("Error during OCR for an image:", repr(e))
            # Don't crash on one bad image; just continue

    return "\n\n".join(all_text).strip()


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    who = ""
    context = ""
    thread = ""

    if request.method == "POST":
        who = request.form.get("who", "").strip()
        context = request.form.get("context", "").strip()
        thread = request.form.get("thread", "").strip()
        images = request.files.getlist("images") if "images" in request.files else []

        if not API_KEY or client is None:
            error = "Server is missing the OpenAI API key. (This is a setup issue, not your fault.)"
        else:
            # First try to use screenshots, if provided
            ocr_text = ""
            if images:
                ocr_text = extract_text_from_images(images)

            conversation_text = ocr_text or thread

            if not conversation_text:
                error = "Please upload at least one screenshot or paste the conversation text."
            else:
                user_input = f"""
Who I am in the conversation: {who or "not specified"}

Context: {context or "none provided"}

Text conversation (from screenshots and/or pasted text):
{conversation_text}
""".strip()

                try:
                    completion = client.chat.completions.create(
                        model="gpt-4.1-mini",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": user_input}
                        ],
                        temperature=0.4,
                    )
                    result = completion.choices[0].message.content
                except Exception as e:
                    print("Error calling OpenAI for intent analysis:", repr(e))
                    error = "Something went wrong while analyzing the conversation."

    return render_template_string(
        HTML_TEMPLATE,
        result=result,
        error=error,
        who=who,
        context=context,
        thread=thread,
    )


if __name__ == "__main__":
    # Local testing only; Railway uses gunicorn via Procfile
    app.run(host="0.0.0.0", port=8000)
