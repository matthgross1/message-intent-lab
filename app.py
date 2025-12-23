import base64
import datetime as dt
import logging
import os
import re
import sqlite3
import uuid

from flask import Flask, jsonify, make_response, render_template_string, request
from openai import OpenAI
import stripe

APP_NAME = "Message Intent Lab"
TAGLINE = "Trying to figure out if he is ghosting or just bad at texting? I will decode it."
MAX_UPLOAD_BYTES = 8 * 1024 * 1024
DB_PATH = os.path.join(os.path.dirname(__file__), "mil.db")
COOKIE_NAME = "mil_uid"
COOKIE_MAX_AGE = 31536000
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN")
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_PRICE_DECODE_10 = os.getenv("STRIPE_PRICE_DECODE_10")
STRIPE_PRICE_DECODE_25 = os.getenv("STRIPE_PRICE_DECODE_25")
STRIPE_PRICE_DECODE_50 = os.getenv("STRIPE_PRICE_DECODE_50")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_BYTES

API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=API_KEY) if API_KEY else None

if STRIPE_SECRET_KEY:
    stripe.api_key = STRIPE_SECRET_KEY

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
        background: #0F0F12;
        color: #F5F5F5;
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
        background: #17171C;
        border-radius: 18px;
        padding: 28px 24px 32px;
        box-shadow: 0 18px 45px rgba(0, 0, 0, 0.6);
        border: 1px solid rgba(255, 255, 255, 0.12);
      }

      h1 {
        margin: 0 0 8px;
        font-size: 1.8rem;
        font-weight: 720;
        color: #F5F5F5;
        letter-spacing: -0.03em;
      }

      .tagline {
        margin: 0 0 6px;
        font-size: 1.02rem;
        font-weight: 520;
        color: #F5F5F5;
      }

      .subline {
        margin: 0 0 22px;
        font-size: 0.92rem;
        color: #B8B8B8;
      }

      .step-label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        margin-bottom: 4px;
        color: #B8B8B8;
      }

      .field {
        margin-bottom: 18px;
      }

      .field-title {
        font-size: 1rem;
        font-weight: 600;
        margin-bottom: 4px;
        color: #F5F5F5;
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
        background: #17171C;
        color: #F5F5F5;
        transition: border 0.15s ease, background 0.15s ease;
      }

      textarea {
        min-height: 110px;
        resize: vertical;
      }

      textarea:focus,
      input[type="file"]:focus {
        border-color: #FF6F61;
        background: #1C1C22;
      }

      textarea::placeholder {
        color: #B8B8B8;
      }

      .hint {
        font-size: 0.8rem;
        color: #B8B8B8;
        margin-top: 3px;
      }

      .error {
        padding: 10px 12px;
        border-radius: 10px;
        background: rgba(229, 83, 61, 0.15);
        color: #F5F5F5;
        margin-bottom: 16px;
        border: 1px solid rgba(229, 83, 61, 0.7);
      }

      .limit-panel {
        margin: 18px 0 20px;
        padding: 16px 16px 18px;
        border-radius: 16px;
        background: linear-gradient(160deg, rgba(255, 111, 97, 0.12), rgba(23, 23, 28, 0.95));
        border: 1px solid rgba(255, 111, 97, 0.35);
        box-shadow: 0 12px 28px rgba(255, 111, 97, 0.2);
      }

      .limit-title {
        margin: 0 0 6px;
        font-size: 1.1rem;
        font-weight: 700;
        color: #F5F5F5;
      }

      .limit-sub {
        margin: 0 0 12px;
        font-size: 0.92rem;
        color: #B8B8B8;
      }

      .limit-actions {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 10px;
      }

      .limit-btn {
        padding: 8px 14px;
        border-radius: 999px;
        border: 1px solid transparent;
        font-family: inherit;
        font-size: 0.9rem;
        font-weight: 600;
        cursor: pointer;
      }

      .limit-btn.primary {
        background: #FF6F61;
        color: #0F0F12;
        border-color: rgba(255, 111, 97, 0.8);
      }

      .limit-btn.primary:hover {
        background: #FF857A;
      }

      .limit-btn.secondary {
        background: #17171C;
        color: #F5F5F5;
        border-color: rgba(255, 180, 172, 0.4);
      }

      .limit-btn.secondary.loading {
        opacity: 0.7;
        cursor: wait;
      }

      .limit-footer {
        margin: 0;
        font-size: 0.82rem;
        color: #B8B8B8;
      }

      .banner {
        padding: 10px 12px;
        border-radius: 10px;
        margin-bottom: 16px;
        border: 1px solid rgba(255, 180, 172, 0.3);
        background: rgba(255, 111, 97, 0.12);
        color: #F5F5F5;
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
        background: #FF6F61;
        color: #0F0F12;
        box-shadow: 0 10px 28px rgba(255, 111, 97, 0.45);
        transition: transform 0.15s ease, box-shadow 0.15s ease;
      }

      button[type="submit"]:hover {
        transform: translateY(-2px);
        background: #FF857A;
        box-shadow: 0 14px 36px rgba(255, 111, 97, 0.6);
      }

      button[type="submit"]:active {
        transform: translateY(0);
        box-shadow: 0 6px 18px rgba(255, 111, 97, 0.45);
      }

      .button-caption {
        margin-top: 6px;
        font-size: 0.83rem;
        color: #B8B8B8;
      }

      .or-divider {
        display: flex;
        align-items: center;
        gap: 10px;
        margin: 14px 0;
        font-size: 0.75rem;
        color: #B8B8B8;
        text-transform: uppercase;
        letter-spacing: 0.15em;
      }

      .or-divider span {
        flex: 1;
        height: 1px;
        background: #2A2A32;
      }

      /* Result card */

      .result {
        margin-top: 26px;
        padding: 20px 18px;
        background: #17171C;
        border: 1px solid #4b4b5b;
        border-radius: 20px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.7);
        color: #F5F5F5;
      }

      .quick-take {
        font-size: 1.05rem;
        font-weight: 660;
        margin-bottom: 12px;
        color: #F5F5F5;
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
        background: #2A1F1E;
        border: 1px solid rgba(255, 180, 172, 0.35);
        color: #FFB4AC;
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
        color: #B8B8B8;
      }

      .share-btn {
        padding: 4px 10px;
        border-radius: 999px;
        border: 1px solid #4b5563;
        background: #17171C;
        color: #F5F5F5;
        font-size: 0.78rem;
        font-weight: 600;
        cursor: pointer;
        display: inline-flex;
        align-items: center;
        gap: 6px;
      }

      .share-btn:hover {
        background: #1C1C22;
        border-color: #7A7A84;
      }

      .share-btn:active {
        background: #0F0F12;
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
        color: #B8B8B8;
      }

      .section ul {
        margin: 0 0 6px 1.1rem;
        padding: 0;
      }

      .section li {
        margin-bottom: 4px;
        color: #F5F5F5;
      }

      .section p {
        margin: 4px 0;
        color: #B8B8B8;
        line-height: 1.35;
      }

      /* Loading spinner on button */

      .btn-spinner {
        display: none;
        width: 14px;
        height: 14px;
        border-radius: 999px;
        border: 2px solid rgba(245, 245, 245, 0.4);
        border-top-color: #F5F5F5;
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

        {% if banner %}
          <div class="banner">{{ banner }}</div>
        {% endif %}

        {% if limit_reached %}
          <div class="limit-panel">
            <h2 class="limit-title">Those are your free reads for today</h2>
            <p class="limit-sub">Come back tomorrow for more. Your next decode resets automatically.</p>
            <div class="limit-actions">
              <button type="button" class="limit-btn primary" id="limit-refresh-btn">Come back tomorrow</button>
              <button type="button" class="limit-btn secondary" id="limit-share-btn">Share this app</button>
              {% if stripe_enabled %}
                <button type="button" class="limit-btn secondary js-pack-btn" data-pack="10">Get 10 more decodes</button>
                <button type="button" class="limit-btn secondary js-pack-btn" data-pack="25">Get 25 more decodes</button>
                <button type="button" class="limit-btn secondary js-pack-btn" data-pack="50">Get 50 more decodes</button>
              {% endif %}
            </div>
            {% if not stripe_enabled %}
              <p class="limit-sub">Paid packs are coming soon.</p>
            {% endif %}
            <p class="limit-footer">Overthinking responsibly.</p>
          </div>
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
            <button type="submit" id="submit-btn" {% if limit_reached %}disabled{% endif %}>
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

    async function shareApp() {
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
    }

    var shareBtn = document.getElementById("share-btn");
    if (shareBtn) {
      shareBtn.addEventListener("click", shareApp);
    }

    var limitShareBtn = document.getElementById("limit-share-btn");
    if (limitShareBtn) {
      limitShareBtn.addEventListener("click", shareApp);
    }

    var limitRefreshBtn = document.getElementById("limit-refresh-btn");
    if (limitRefreshBtn) {
      limitRefreshBtn.addEventListener("click", function () {
        window.scrollTo({ top: 0, behavior: "smooth" });
      });
    }

    var packButtons = document.querySelectorAll(".js-pack-btn");
    if (packButtons.length) {
      packButtons.forEach(function (btn) {
        btn.addEventListener("click", async function () {
          if (btn.classList.contains("loading")) return;
          btn.classList.add("loading");
          var originalLabel = btn.textContent;
          btn.textContent = "Redirecting...";
          try {
            const response = await fetch("/create-checkout-session/decode-pack", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({ pack: btn.dataset.pack })
            });
            if (!response.ok) {
              throw new Error("Checkout failed");
            }
            const data = await response.json();
            if (data.url) {
              window.location.href = data.url;
            } else {
              throw new Error("Missing checkout URL");
            }
          } catch (e) {
            console.error("Checkout error:", e);
            alert("Checkout could not start. Please try again in a moment.");
            btn.classList.remove("loading");
            btn.textContent = originalLabel;
          }
        });
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


def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    free_uses_today INTEGER NOT NULL DEFAULT 0,
                    free_uses_date TEXT,
                    total_decodes INTEGER NOT NULL DEFAULT 0,
                    last_decode_at TEXT,
                    is_paid INTEGER NOT NULL DEFAULT 0,
                    followup_credits INTEGER NOT NULL DEFAULT 0,
                    paid_decode_credits INTEGER NOT NULL DEFAULT 0,
                    lifetime_paid_decodes INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.commit()
            migrate_db(conn)
    except Exception:
        logger.exception("Database init failed")


def migrate_db(conn):
    columns = {row["name"] for row in conn.execute("PRAGMA table_info(users)").fetchall()}
    additions = []
    if "paid_decode_credits" not in columns:
        additions.append("ALTER TABLE users ADD COLUMN paid_decode_credits INTEGER NOT NULL DEFAULT 0")
    if "lifetime_paid_decodes" not in columns:
        additions.append("ALTER TABLE users ADD COLUMN lifetime_paid_decodes INTEGER NOT NULL DEFAULT 0")
    for statement in additions:
        try:
            conn.execute(statement)
        except Exception:
            logger.exception("Database migration failed")
    if additions:
        conn.commit()


def get_or_create_user_id(req):
    cookie_value = req.cookies.get(COOKIE_NAME)
    if cookie_value:
        return cookie_value, False
    return str(uuid.uuid4()), True


def load_or_create_user(user_id):
    try:
        with get_db_connection() as conn:
            row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
            if row:
                return row
            created_at = dt.datetime.now(dt.timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO users (
                    id, created_at, free_uses_today, free_uses_date,
                    total_decodes, last_decode_at, is_paid, followup_credits,
                    paid_decode_credits, lifetime_paid_decodes
                )
                VALUES (?, ?, 0, ?, 0, NULL, 0, 0, 0, 0)
                """,
                (user_id, created_at, created_at[:10]),
            )
            conn.commit()
            return conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    except Exception:
        logger.exception("Database load/create failed")
        return None


def reset_daily_counter_if_needed(user_row):
    if not user_row:
        return False
    today = dt.datetime.now(dt.timezone.utc).date().isoformat()
    if user_row["free_uses_date"] == today:
        return False
    try:
        with get_db_connection() as conn:
            conn.execute(
                "UPDATE users SET free_uses_today = 0, free_uses_date = ? WHERE id = ?",
                (today, user_row["id"]),
            )
            conn.commit()
        return True
    except Exception:
        logger.exception("Failed to reset daily counter")
        return False


def increment_usage(user_row):
    if not user_row:
        return False
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    today = now[:10]
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                UPDATE users
                SET free_uses_today = free_uses_today + ?,
                    free_uses_date = ?,
                    total_decodes = total_decodes + 1,
                    last_decode_at = ?
                WHERE id = ?
                """,
                (1, today, now, user_row["id"]),
            )
            conn.commit()
        return True
    except Exception:
        logger.exception("Failed to increment usage")
        return False


def increment_usage_paid(user_row):
    if not user_row:
        return False
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    today = now[:10]
    try:
        with get_db_connection() as conn:
            conn.execute(
                """
                UPDATE users
                SET paid_decode_credits = paid_decode_credits - 1,
                    lifetime_paid_decodes = lifetime_paid_decodes + 1,
                    free_uses_date = ?,
                    total_decodes = total_decodes + 1,
                    last_decode_at = ?
                WHERE id = ? AND paid_decode_credits > 0
                """,
                (today, now, user_row["id"]),
            )
            conn.commit()
        return True
    except Exception:
        logger.exception("Failed to decrement paid credits")
        return False


def stripe_enabled():
    return bool(
        STRIPE_SECRET_KEY
        and STRIPE_WEBHOOK_SECRET
        and STRIPE_PRICE_DECODE_10
        and STRIPE_PRICE_DECODE_25
        and STRIPE_PRICE_DECODE_50
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


@app.route("/_admin/usage")
def admin_usage():
    if not ADMIN_TOKEN:
        return ("Not Found", 404)

    token = request.args.get("token", "")
    if token != ADMIN_TOKEN:
        return ("Forbidden", 403)

    try:
        with get_db_connection() as conn:
            totals = conn.execute(
                """
                SELECT
                    COUNT(*) AS users,
                    COALESCE(SUM(total_decodes), 0) AS total_decodes,
                    COALESCE(SUM(free_uses_today), 0) AS free_uses_today
                FROM users
                """
            ).fetchone()

        return jsonify(
            users=totals["users"],
            total_decodes=totals["total_decodes"],
            free_uses_today=totals["free_uses_today"],
        )
    except Exception:
        logger.exception("Admin usage lookup failed")
        return ("Server error", 500)


@app.route("/create-checkout-session/decode-pack", methods=["POST"])
def create_checkout_session():
    if not stripe_enabled():
        return jsonify(error="Stripe is not configured"), 400

    user_id, needs_cookie = get_or_create_user_id(request)
    user_row = load_or_create_user(user_id)
    if not user_row:
        return jsonify(error="User unavailable"), 500
    payload = request.get_json(silent=True) or {}
    pack = str(payload.get("pack", "")).strip()
    price_map = {
        "10": STRIPE_PRICE_DECODE_10,
        "25": STRIPE_PRICE_DECODE_25,
        "50": STRIPE_PRICE_DECODE_50,
    }
    price_id = price_map.get(pack)
    if not price_id:
        return jsonify(error="Invalid pack"), 400

    base_url = request.url_root.rstrip("/")
    try:
        session = stripe.checkout.Session.create(
            mode="payment",
            line_items=[{"price": price_id, "quantity": 1}],
            client_reference_id=user_id,
            metadata={"mil_uid": user_id, "pack_size": pack},
            success_url=f"{base_url}/?checkout=success",
            cancel_url=f"{base_url}/?checkout=cancel",
        )
        response = make_response(jsonify(url=session.url))
        if needs_cookie:
            response.set_cookie(
                COOKIE_NAME,
                user_id,
                max_age=COOKIE_MAX_AGE,
                httponly=True,
                secure=True,
                samesite="Lax",
            )
        return response
    except Exception:
        logger.exception("Stripe checkout session creation failed")
        return jsonify(error="Stripe error"), 500


@app.route("/stripe-webhook", methods=["POST"])
def stripe_webhook():
    if not STRIPE_WEBHOOK_SECRET:
        return ("Webhook not configured", 400)

    payload = request.get_data()
    sig_header = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except Exception:
        logger.exception("Stripe webhook signature verification failed")
        return ("Invalid signature", 400)

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {}) or {}
        user_id = metadata.get("mil_uid")
        pack_size = metadata.get("pack_size")
        try:
            credits = int(pack_size)
        except (TypeError, ValueError):
            credits = 0

        if user_id and credits > 0:
            try:
                with get_db_connection() as conn:
                    conn.execute(
                        """
                        UPDATE users
                        SET paid_decode_credits = paid_decode_credits + ?
                        WHERE id = ?
                        """,
                        (credits, user_id),
                    )
                    conn.commit()
                    row = conn.execute(
                        "SELECT paid_decode_credits FROM users WHERE id = ?", (user_id,)
                    ).fetchone()
                logger.info(
                    "[PAYMENT] user=%s pack=%s credits_now=%s",
                    user_id,
                    credits,
                    row["paid_decode_credits"] if row else "unknown",
                )
            except Exception:
                logger.exception("Failed to apply Stripe credits")

    return ("OK", 200)


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    context = ""
    thread = ""
    limit_blocked = False
    limit_reached = False
    banner = None
    used_paid_credit = False
    user_id, needs_cookie = get_or_create_user_id(request)

    if request.method == "GET":
        checkout_state = request.args.get("checkout")
        if checkout_state in {"success", "cancel"}:
            user_row = load_or_create_user(user_id)
            if checkout_state == "success":
                if user_row:
                    banner = f"Unlocked. You now have {user_row['paid_decode_credits']} decodes."
                else:
                    banner = "Unlocked. Your decodes will appear shortly."
            elif checkout_state == "cancel":
                banner = "Checkout canceled."

    if request.method == "POST":
        context = request.form.get("context", "").strip()
        thread = request.form.get("thread", "").strip()
        images = request.files.getlist("images") if "images" in request.files else []

        user_row = load_or_create_user(user_id)
        if not user_row:
            error = "We hit a server issue. Please try again in a moment."
            limit_blocked = True
        else:
            reset_daily_counter_if_needed(user_row)
            user_row = load_or_create_user(user_id)

            if not user_row:
                error = "We hit a server issue. Please try again in a moment."
                limit_blocked = True
            else:
                if user_row["paid_decode_credits"] > 0:
                    used_paid_credit = True
                elif user_row["free_uses_today"] >= 2:
                    limit_blocked = True
                    limit_reached = True

        timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
        logger.info(
            "[SUBMISSION] time=%s user_id=%s has_images=%s has_text=%s context_len=%s blocked=%s paid_path=%s",
            timestamp,
            user_id,
            bool(images),
            bool(thread),
            len(context),
            limit_blocked,
            used_paid_credit,
        )

        if not error and not limit_reached and (not API_KEY or client is None):
            error = "Server is missing the OpenAI API key. This is a setup issue, not your fault."
        elif not error and not limit_reached:
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
                        if used_paid_credit:
                            increment_usage_paid(user_row)
                        else:
                            increment_usage(user_row)
                    except Exception:
                        logger.exception("OpenAI analysis failed")
                        error = "Something went wrong while analyzing the conversation."

    response = make_response(
        render_template_string(
        HTML_TEMPLATE,
        app_name=APP_NAME,
        tagline=TAGLINE,
        result=result,
        error=error,
        limit_reached=limit_reached,
        stripe_enabled=stripe_enabled(),
        banner=banner,
        context=context,
        thread=thread,
        )
    )
    if needs_cookie:
        response.set_cookie(
            COOKIE_NAME,
            user_id,
            max_age=COOKIE_MAX_AGE,
            httponly=True,
            secure=True,
            samesite="Lax",
        )
    return response


# Premium features will be added here later.
# Limit panel is rendered in the main template when limit_reached is True,
# which is set in the index route when the daily free limit is hit.

if __name__ == "__main__":
    init_db()
    port = int(os.getenv("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)


init_db()
