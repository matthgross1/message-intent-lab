import os
import base64
from flask import Flask, render_template_string, request
from openai import OpenAI

app = Flask(__name__)
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

HTML_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <title>Message Intent Lab</title>
    <meta charset="utf-8">
    <style>
      body { font-family: system-ui; margin: 40px; max-width: 800px; }
      textarea { width: 100%; min-height: 200px; padding: 8px; }
      input, button, select { padding: 6px 10px; }
      .field { margin-bottom: 16px; }
      .label { font-weight: 600; margin-bottom: 4px; display: block; }
      .result { white-space: pre-wrap; border: 1px solid #ddd; padding: 16px; border-radius: 8px; margin-top: 24px; }
    </style>
  </head>
  <body>
    <h1>Message Intent Lab</h1>
    <p>Paste a confusing or emotionally loaded text thread to get a behavioral-science read on the other person's likely intentions.</p>

    <form method="POST">
      <div class="field">
        <label class="label">Who are you in the conversation?</label>
        <select name="who" required>
          <option value="">Select...</option>
          <option>Person A / first speaker</option>
          <option>Person B / second speaker</option>
          <option>Blue bubbles</option>
          <option>Gray bubbles</option>
        </select>
      </div>

      <div class="field">
        <label class="label">Optional: context</label>
        <textarea name="context"></textarea>
      </div>

      <div class="field">
        <label class="label">Text thread (paste in order)</label>
        <textarea name="thread" required></textarea>
      </div>

      <button type="submit">Analyze</button>
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
You are a behavioral scientist specializing in interpersonal communication and attachment dynamics.

The user will paste a text conversation and identify who they are. Infer the other person's likely intentions. Output ONLY these four sections:

1. Surface-Level Summary (2–3 sentences)
2. Likely Intentions (3–5 bullets)
3. Emotional/Psychological Patterns (1–2 paragraphs)
4. Ambiguities (2–3 bullets)

No advice. No instructions on what to text back.
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        who = request.form.get("who", "")
        context = request.form.get("context", "")
        thread = request.form.get("thread", "")

        user_input = f"""
Who I am: {who}
Context: {context}
Text thread:
{thread}
"""

        completion = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_input}
            ],
            temperature=0.4,
        )

        result = completion.choices[0].message.content

    return render_template_string(HTML_TEMPLATE, result=result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
