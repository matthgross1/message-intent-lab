import base64
import datetime as dt
import logging
import os
import re

from flask import Flask, render_template_string, request
from openai import OpenAI

APP_NAME = "Message Intent Lab"
TAGLINE = "Trying to figure out if he is ghosting or just bad at texting? I will decode it."
MAX_UPLOAD_BYTES = 8 * 1024 * 1024

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

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
        background: #050509;
        color: #f9fafb;
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
        background: #12121a;
        border-radius: 18px;
        padding: 28px 24px 32px;
        box-shadow: 0 18px 45px rgba(0, 0, 0, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.12);
      }

      h1 {
        margin: 0 0 8px;
        font-size: 1.8rem;
        font-weight: 720;
        color: #ffffff;
        letter-spacing: -0.03em;
      }

      .tagline {
        margin: 0 0 6px;
        font-size: 1.02rem;
        font-weight: 520;
        color: #f3f4ff;
      }

      .subline {
        margin: 0 0 22px;
        font-size: 0.92rem;
        color: #d1d5db;
      }

      .step-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 4px;
        color: #9ca3af;
      }

      .field {
        margin-bottom: 18px;
      }

      .field-title {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 4px;
        color: #f9fafb;
      }

      textarea,
      input[type="file"] {
        width: 100%;
        font-family: inherit;
        font-size: 0.94rem;
        padding: 10px 12px;
        border-radius: 10px;
        border: 1px solid #3f3f4c;
        outline: none;
        background: #181822;
        color: #f9fafb;
        transition: border 0.15s ease, background 0.15s ease;
      }

      textarea {
        min-height: 110px;
        resize: vertical;
      }

      textarea:focus,
      input[type="file"]:focus {
        border-color: #8b5cf6;
        background: #1f1f2b;
      }

      textarea::placeholder {
        color: #9ca3af;
      }

      .hint {
        font-size: 0.8rem;
        color: #d1d5db;
        margin-top: 3px;
      }

      .error {
        padding: 10px 12px;
        border-radius: 10px;
        background: rgba(248, 113, 113, 0.12);
        color: #fecaca;
        margin-bottom: 16px;
        border: 1px solid rgba(248, 113, 113, 0.6);
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
        background: radial-gradient(circle at 20% 0, #a855f7, #6366f1);
        color: #ffffff;
        box-shadow: 0 10px 28px rgba(79, 70, 229, 0.6);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
      }

      button[type="submit"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 14px 36px rgba(79, 70, 229, 0.75);
      }

      button[type="submit"]:active {
        transform: translateY(0);
        box-shadow: 0 6px 18px rgba(79, 70, 229, 0.65);
      }

      .button-caption {
        margin-top: 6px;
        font-size: 0.83rem;
        color: #e5e7eb;
      }

      .or-divider {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 14px 0;
        font-size: 0.75rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.15em;
      }

      .or-divider span {
        flex: 1;
        height: 1px;
        background: #27272f;
      }

      /* Result card */

      .result {
        margin-top: 26px;
        padding: 20px 18px;
        background: #181824;
        border: 1px solid #4b4b5b;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
        color: #f9fafb;
      }

      .quick-take {
        font-size: 1.05rem;
        font-weight: 660;
        margin-bottom: 12px;
        color: #fefefe;
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
        background: rgba(59, 130, 246, 0.18);
        border: 1px solid rgba(129, 140, 248, 0.8);
        color: #e0e7ff;
      }

      .result-header {
        display: flex;
        align-items: center;
        justify-content: space-between;
        margin-bottom: 10px;
      }

      .result-label {
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.14em;
        color: #9ca3af;
      }

      .share-btn {
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid #4b5563;
        background: #111827;
        color: #e5e7eb;
        font-size: 0.78rem;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }

      .share-btn:hover {
        background: #1f2937;
        border-color: #6b7280;
      }

      .share-btn:active {
        background: #030712;
      }

      .result-body {
        margin-top: 4px;
      }

      .section {
        margin-top: 12px;
      }

      .section h3 {
        margin: 0 0 6px;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.11em;
        color: #9ca3af;
      }

      .section ul {
        margin: 0 0 6px 1.1rem;
        padding: 0;
      }

      .section li {
        margin-bottom: 4px;
        color: #e5e7eb;
      }

      .section p {
        margin: 4px 0;
        color: #e5e7eb;
        line-height: 1.35;
      }

      /* Loading spinner on button */

      .btn-spinner {
        display: none;
        width: 14px;
        height: 14px;
        border-radius: 999px;
        border: 2px solid rgba(249, 250, 251, 0.4);
        border-top-color: #ffffff;
        margin-left: 8px;
        animation: spin 0.7s linear infinite;
      }

      button.loading .btn-spinner {
        display: inline-block;
      }

      button.loading .btn-label {
        opacity: 0.7;
      }

      button.loading {
        cursor: wait;
      }

      @keyframes spin {
        to {
          transform: rotate(360deg);
        }
      }
    </style>
  </head>
  <body>
    <div class="page">
      <div class="card">
        <h1>{{ app_name }}</h1>
        <p class="tagline">{{ tagline }}</p>
        <p class="subline">When someone texts weird and your brain will not shut up about it. Upload screenshots and get a plain English read on what he was probably trying to do.</p>

        {% if error %}
          <div class="error"><strong>Whoops.</strong> {{ error }}</div>
        {% endif %}

        <form id="analyze-form" method="POST" enctype="multipart/form-data">
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
            <button type="submit" id="submit-btn">
              <span class="btn-label">Decode the vibe</span>
              <span class="btn-spinner" aria-hidden="true"></span>
            </button>
            <div class="button-caption">You get a short breakdown of what his messages likely meant, without the spiral.</div>
          </div>
        </form>

  {% if result %}
  <div class="result">
    <div class="result-header">
      <span class="result-label">Result</span>
      <button type="button" class="share-btn" id="share-btn">Share</button>
    </div>
    <div class="result-body">
      {{ result|safe }}
    </div>
  </div>
{% endif %}

      </div>
    </div>

   <script>
  document.addEventListener("DOMContentLoaded", function () {
    var form = document.getElementById("analyze-form");
    var button = document.getElementById("submit-btn");
    var label = button ? button.querySelector(".btn-label") : null;

    if (form && button && label) {
      form.addEventListener("submit", function () {
        if (button.classList.contains("loading")) return;

        button.classList.add("loading");
        button.disabled = true;
        label.textContent = "Decoding...";
      });
    }

    var shareBtn = document.getElementById("share-btn");
    if (shareBtn) {
      shareBtn.addEventListener("click", async function () {
        const baseUrl = window.location.href.split("?")[0];
        const shareText = "Here is the vibe read I got from Message Intent Lab:";
        try {
          if (navigator.share) {
            await navigator.share({
              title: "Message Intent Lab",
              text: shareText,
              url: baseUrl
            });
          } else if (navigator.clipboard) {
            await navigator.clipboard.writeText(baseUrl);
            alert("Link copied. Paste it in your group chat.");
          } else {
            alert("Sharing is not supported in this browser. You can still screenshot this.");
          }
        } catch (e) {
          console.error("Share failed:", e);
        }
      });
    }
  });
</script>

  </body>
</html>
"""

OCR_SYSTEM_PROMPT = (
    "You are an OCR engine. Extract only the visible text from this screenshot "
    "of a messaging conversation. Do not add explanation, labels, or commentary."
)

OCR_USER_PROMPT = "Extract the raw text exactly as it appears in the chat bubble order."

ANALYSIS_SYSTEM_PROMPT = """
You are a behavioral scientist specializing in mixed signals in dating and friendships.

The user will share a text message conversation and a bit of context. Assume the user is the blue bubble unless they say otherwise.

Your job is to decode the OTHER person's likely intentions and emotional motives. The user already knows what the messages literally said. They are here for SUBTEXT, not recap.

CRITICAL RULES:
- Do not retell or paraphrase the conversation.
- Do not write long paragraphs.
- Total output should usually stay under 200 words.
- Bullets should be short and direct (about 15 words or less).
- Tone: clear, honest, a little blunt, not clinical, not self help.
- Do not include <script> tags, <style> tags, or external links.

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


def log_submission(has_images, has_text, context_len):
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    logger.info(
        "[SUBMISSION] time=%s has_images=%s has_text=%s context_len=%s",
        timestamp,
        has_images,
        has_text,
        context_len,
    )


def strip_disallowed_html(raw_html):
    if not raw_html:
        return raw_html

    sanitized = re.sub(r"<script[^>]*>.*?</script>", "", raw_html, flags=re.DOTALL | re.IGNORECASE)
    sanitized = re.sub(r"<style[^>]*>.*?</style>", "", sanitized, flags=re.DOTALL | re.IGNORECASE)
    sanitized = re.sub(r"<link[^>]*?>", "", sanitized, flags=re.DOTALL | re.IGNORECASE)
    return sanitized.strip()


def extract_text_from_images(files):
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
                    {"role": "system", "content": OCR_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": OCR_USER_PROMPT},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{b64}"
                                },
                            },
                        ],
                    },
                ],
                temperature=0.0,
            )

            text_chunk = resp.choices[0].message.content.strip()
            if text_chunk:
                all_text.append(text_chunk)

        except Exception:
            logger.exception("OCR failed for an uploaded image")

    return "\n\n".join(all_text).strip()


def build_analysis_input(context, conversation_text):
    return (
        f"Context: {context or 'none provided'}\n\n"
        "Text conversation (from screenshots and/or pasted text):\n"
        f"{conversation_text}"
    )


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

        log_submission(bool(images), bool(thread), len(context))

        if not API_KEY or client is None:
            error = "Server is missing the OpenAI API key. This is a setup issue, not your fault."
        else:
            ocr_text = extract_text_from_images(images) if images else ""

            if images and not ocr_text and not thread:
                error = "We could not read text from those screenshots. Try a clearer crop or paste the text instead."
            else:
                conversation_text = ocr_text or thread

                if not conversation_text:
                    error = "Please upload at least one screenshot or paste the conversation text."
                else:
                    user_input = build_analysis_input(context, conversation_text)

                    try:
                        completion = client.chat.completions.create(
                            model="gpt-4.1-mini",
                            messages=[
                                {"role": "system", "content": ANALYSIS_SYSTEM_PROMPT},
                                {"role": "user", "content": user_input},
                            ],
                            temperature=0.4,
                        )
                        raw_html = completion.choices[0].message.content
                        result = strip_disallowed_html(raw_html)
                    except Exception:
                        logger.exception("OpenAI analysis failed")
                        error = "Something went wrong while analyzing the conversation."

    return render_template_string(
        HTML_TEMPLATE,
        app_name=APP_NAME,
        tagline=TAGLINE,
        result=result,
        error=error,
        context=context,
        thread=thread,
    )


# Premium features will be added here later.

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
