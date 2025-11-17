import os
import base64
from flask import Flask, render_template_string, request
from openai import OpenAI

app = Flask(__name__)

API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY) if API_KEY else None

HTML_TEMPLATE = """
<!doctype html>
<html>
  <head>
    <title>Message Intent Lab</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
      :root {
        color-scheme: dark;
      }

      * {
        box-sizing: border-box;
      }

      body {
        margin: 0;
        padding: 0;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #0c0c12;
        color: #f3f4f6;
      }

      .page {
        min-height: 100vh;
        display: flex;
        align-items: flex-start;
        justify-content: center;
        padding: 24px 12px 40px;
      }

      .card {
        width: 100%;
        max-width: 640px;
        background: #13131a;
        border-radius: 18px;
        padding: 28px 24px 32px;
        box-shadow: 0 15px 45px rgba(0, 0, 0, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.06);
      }

      h1 {
        margin: 0 0 8px;
        font-size: 1.75rem;
        font-weight: 700;
        color: #fafafa;
        letter-spacing: -0.03em;
      }

      .tagline {
        margin: 0 0 6px;
        font-size: 1.05rem;
        font-weight: 500;
        color: #c5c6d0;
      }

      .subline {
        margin: 0 0 22px;
        font-size: 0.92rem;
        color: #8f90a0;
      }

      .step-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 4px;
        color: #7c7d88;
      }

      .field {
        margin-bottom: 18px;
      }

      .field-title {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 4px;
        color: #e4e4eb;
      }

      textarea,
      input[type="file"] {
        width: 100%;
        font-family: inherit;
        font-size: 0.92rem;
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid #2b2c34;
        outline: none;
        background: #181820;
        color: #ffffff;
        transition: border 0.15s ease, background 0.15s ease;
      }

      textarea {
        min-height: 110px;
        resize: vertical;
      }

      textarea:focus,
      input[type="file"]:focus {
        border-color: #5d5dfc;
        background: #1e1e27;
      }

      .hint {
        font-size: 0.8rem;
        color: #6a6b78;
        margin-top: 3px;
      }

      .error {
        padding: 10px 12px;
        border-radius: 10px;
        background: rgba(255, 0, 0, 0.15);
        color: #ff9b9b;
        margin-bottom: 16px;
        border: 1px solid rgba(255, 0, 0, 0.25);
      }

      .button-row {
        margin-top: 12px;
        text-align: center;
      }

      button[type="submit"] {
        padding: 10px 22px;
        border-radius: 999px;
        border: none;
        font-family: inherit;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        background: linear-gradient(135deg, #5d5dfc, #9b5dfc);
        color: #ffffff;
        box-shadow: 0 8px 25px rgba(93, 93, 252, 0.35);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
      }

      button[type="submit"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 32px rgba(93, 93, 252, 0.45);
      }

      button[type="submit"]:active {
        transform: translateY(0);
        box-shadow: 0 6px 16px rgba(93, 93, 252, 0.4);
      }

      .button-caption {
        margin-top: 6px;
        font-size: 0.83rem;
        color: #73748a;
      }

      .or-divider {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 14px 0;
        font-size: 0.75rem;
        color: #5f6070;
        text-transform: uppercase;
        letter-spacing: 0.15em;
      }

      .or-divider span {
        flex: 1;
        height: 1px;
        background: #2d2d35;
      }

      /* Result card */

      .result {
        margin-top: 26px;
        padding: 20px 18px;
        background: #181820;
        border: 1px solid #30303a;
        border-radius: 20px;
        box-shadow: 0 8px 35px rgba(0, 0, 0, 0.45);
        color: #ececf5;
      }

      .quick-take {
        font-size: 1.05rem;
        font-weight: 650;
        margin-bottom: 12px;
        color: #eaeaff;
      }

      .badges {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 16px;
      }

      .badge {
        padding: 4px 10px;
        border-radius: 999px;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(93, 93, 252, 0.15);
        border: 1px solid rgba(93, 93, 252, 0.45);
        color: #b1b1ff;
      }

      .section {
        margin-top: 12px;
      }

      .section h3 {
        margin: 0 0 6px;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.11em;
        color: #8f90a5;
      }

      .section ul {
        margin: 0 0 6px 1.1rem;
        padding: 0;
      }

      .section li {
        margin-bottom: 4px;
        color: #d5d5e0;
      }

      .section p {
        margin: 4px 0;
        color: #c2c2d3;
        line-height: 1.35;
      }
    </style>
  </head>
  <body>
    <div class="page">
      <div class="card">
        <h1>Message Intent Lab</h1>
        <p class="tagline">Trying to figure out if he is ghosting or just bad at texting? I will decode it.</p>
        <p class="subline">When someone texts weird and your brain will not shut up about it. Upload screenshots and get a plain English read on what he was probably trying to do.</p>

        {% if error %}
          <div class="error"><strong>Whoops.</strong> {{ error }}</div>
        {% endif %}

        <form method="POST" enctype="multipart/form-data">
          <div class="field">
            <div class="step-label">Step 1</div>
            <div class="field-title">What is the situation?</div>
            <textarea
              name="context"
              id="context"
              placeholder="Example: We have been talking for a month and he suddenly pulled back after last weekend.">{{ context or "" }}</textarea>
            <p class="hint">Optional, it just helps the interpretation feel more accurate.</p>
          </div>

          <div class="field">
            <div class="step-label">Step 2</div>
            <div class="field-title">Add the conversation</div>
            <input type="file" name="images" id="images" accept="image/*" multiple>
            <p class="hint">Best option is 1 to 3 screenshots from your phone, earliest messages first. Assume you are the blue bubble.</p>
          </div>

          <div class="or-divider">
            <span></span> or paste the messages <span></span>
          </div>

          <div class="field">
            <div class="field-title">Or paste the messages instead</div>
            <textarea
              name="thread"
              id="thread"
              placeholder="Copy the chat and paste it here, starting from the first message.">{{ thread or "" }}</textarea>
          </div>

          <div class="button-row">
            <button type="submit">Decode the vibe</button>
            <div class="button-caption">You get a short breakdown of what his messages likely meant, without the spiral.</div>
          </div>
        </form>

        {% if result %}
          <div class="result">
            {{ result|safe }}
          </div>
        {% endif %}
      </div>
    </div>
  </body>
</html>
"""

SYSTEM_PROMPT = """
You are a behavioral scientist specializing in mixed signals in dating and friendships.

The user will share a text message conversation and a bit of context. Assume the user is the blue bubble unless they say otherwise.

Your job is to decode the OTHER person's likely intentions and emotional motives. The user already knows what the messages literally said. They are here for SUBTEXT, not recap.

CRITICAL RULES:
- Do not retell or paraphrase the conversation.
- Do not write long paragraphs.
- Total output should usually stay under 200 words.
- Bullets should be short and direct (about 15 words or less).
- Tone: clear, honest, a little blunt, not clinical, not self help.

Return valid HTML that fits exactly this structure:

<div class="quick-take">
  One short sentence with your main verdict. You can include one emoji if it fits.
</div>

<div class="badges">
  <span class="badge">Interest: Mixed</span>
  <span class="badge">Effort: Low</span>
  <span class="badge">Vibe: Avoidant</span>
</div>

<div class="section">
  <h3>Top signals</h3>
  <ul>
    <li>Short, sharp bullet about what their behavior suggests.</li>
    <li>Another bullet about a clear pattern or motive you see.</li>
    <li>Another bullet about how they manage distance, control, or attention.</li>
  </ul>
</div>

<div class="section">
  <h3>Deeper read</h3>
  <p>One short sentence about the emotional pattern behind their behavior.</p>
  <p>One short sentence about what they are probably trying to protect (ego, control, comfort, options).</p>
</div>

Guidelines:
- Always fill all four parts above.
- The three badges should always start with labels: Interest, Effort, Vibe.
- After the labels, use one or two words like Low, High, Mixed, Warm, Cold, Guarded, Confused.
- Focus on motives, strategy, and emotional patterns, not what was typed.
- Do not tell the user what they should do or what to text back.
- Your entire job is to decode what the other person was probably trying to signal.
"""

def extract_text_from_images(files):
    """
    Take a list of uploaded image files and use the vision model
    to extract raw text from screenshots of chats.
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

            resp = client.chat.completions.create(
                model="gpt-4.1-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an OCR engine. Extract only the visible text from this screenshot of a messaging conversation. Do not add explanation, labels, or commentary."
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
            # skip bad image, continue with others

    return "\n\n".join(all_text).strip()


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    context = ""
    thread = ""

    if request.method == "POST":
        context = request.form.get("context", "").strip()
        thread = request.form.get("thread", "").strip()
        images = request.files.getlist("images") if "images" in request.files else []

        if not API_KEY or client is None:
            error = "Server is missing the OpenAI API key. This is a setup issue, not your fault."
        else:
            ocr_text = ""
            if images:
                ocr_text = extract_text_from_images(images)

            conversation_text = ocr_text or thread

            if not conversation_text:
                error = "Please upload at least one screenshot or paste the conversation text."
            else:
                user_input = f"""
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
        context=context,
        thread=thread,
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
