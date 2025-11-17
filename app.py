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
        color-scheme: light;
      }
      * {
        box-sizing: border-box;
      }
      body {
        margin: 0;
        padding: 0;
        font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        background: #f5f5f7;
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
        background: #ffffff;
        border-radius: 18px;
        box-shadow: 0 10px 30px rgba(15, 23, 42, 0.08);
        padding: 24px 20px 28px;
      }
      @media (min-width: 720px) {
        .card {
          padding: 28px 28px 32px;
        }
      }
      h1 {
        margin: 0 0 6px;
        font-size: 1.6rem;
        font-weight: 650;
        letter-spacing: -0.02em;
      }
      .tagline {
        margin: 0 0 4px;
        font-size: 0.98rem;
        color: #111827;
        font-weight: 500;
      }
      .subline {
        margin: 0 0 18px;
        font-size: 0.9rem;
        color: #4b5563;
      }
      .step-label {
        font-size: 0.8rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: #6b7280;
        margin-bottom: 4px;
      }
      .field {
        margin-bottom: 16px;
      }
      .field-title {
        font-weight: 600;
        font-size: 0.95rem;
        margin-bottom: 4px;
      }
      .hint {
        font-size: 0.8rem;
        color: #6b7280;
        margin-top: 3px;
      }
      textarea,
      input[type="file"] {
        width: 100%;
        font-family: inherit;
        font-size: 0.94rem;
        padding: 8px 9px;
        border-radius: 10px;
        border: 1px solid #e5e7eb;
        outline: none;
        background: #f9fafb;
        transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
      }
      textarea {
        min-height: 90px;
        resize: vertical;
      }
      textarea:focus,
      input[type="file"]:focus {
        border-color: #6366f1;
        box-shadow: 0 0 0 1px rgba(99, 102, 241, 0.2);
        background: #ffffff;
      }
      .error {
        margin-bottom: 12px;
        padding: 10px 12px;
        border-radius: 10px;
        background: #fef2f2;
        color: #b91c1c;
        font-size: 0.86rem;
      }
      .button-row {
        margin-top: 10px;
      }
      button[type="submit"] {
        display: inline-flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        padding: 9px 18px;
        border-radius: 999px;
        border: none;
        font-family: inherit;
        font-size: 0.96rem;
        font-weight: 600;
        cursor: pointer;
        background: linear-gradient(135deg, #6366f1, #8b5cf6);
        color: #ffffff;
        box-shadow: 0 8px 18px rgba(79, 70, 229, 0.35);
        transition: transform 0.1s ease, box-shadow 0.1s ease, opacity 0.15s ease;
      }
      button[type="submit"]:hover {
        transform: translateY(-1px);
        box-shadow: 0 10px 24px rgba(79, 70, 229, 0.4);
        opacity: 0.98;
      }
      button[type="submit"]:active {
        transform: translateY(0);
        box-shadow: 0 4px 12px rgba(79, 70, 229, 0.4);
      }
      .button-caption {
        margin-top: 4px;
        font-size: 0.8rem;
        color: #6b7280;
      }
      .or-divider {
        display: flex;
        align-items: center;
        gap: 8px;
        margin: 10px 0;
        font-size: 0.78rem;
        color: #9ca3af;
        text-transform: uppercase;
        letter-spacing: 0.12em;
      }
      .or-divider span {
        flex: 1;
        height: 1px;
        background: #e5e7eb;
      }
      .result {
        white-space: pre-wrap;
        border-radius: 14px;
        border: 1px solid #e5e7eb;
        padding: 14px 14px 16px;
        margin-top: 22px;
        background: #f9fafb;
        font-size: 0.92rem;
        color: #111827;
      }
      .result strong {
        display: block;
        margin-bottom: 6px;
        font-size: 0.94rem;
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
            <p class="hint">Totally optional. It just helps the interpretation feel more accurate.</p>
          </div>

          <div class="field">
            <div class="step-label">Step 2</div>
            <div class="field-title">Add the conversation</div>
            <input type="file" name="images" id="images" accept="image/*" multiple>
            <p class="hint">Best option is 1 to 3 screenshots of the chat from your phone, earliest messages first. Assume you are the blue bubble.</p>
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
            <div class="button-caption">You get a short breakdown of what his messages likely meant, without the overthinking spiral.</div>
          </div>
        </form>

        {% if result %}
          <div class="result">
            <strong>Here is what this probably means</strong>
            {{ result }}
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

CRITICAL CONSTRAINTS:
- Do NOT retell the conversation.
- Do NOT paraphrase messages.
- Do NOT write long paragraphs.
- Total output should usually stay under 220 words.
- Each bullet should be short and direct (max ~15 words).
- Tone: clear, honest, a bit blunt, but not cruel. No therapy voice.

Format the answer in EXACTLY these four sections, with headings:

1. Quick Take
- 1–2 short sentences that give the main vibe (e.g., "He is keeping you as a backup while avoiding direct rejection.")

2. What They Were Probably Trying To Do
- 3–6 bullets
- Focus on motives and strategy (e.g., "Keeping you interested without committing," "Avoiding conflict," "Testing if you will chase.")
- No restating what they wrote. Only interpret why.

3. Signals About Their Interest Level
- 3 bullets
- Comment on consistency, effort, responsiveness, and emotional availability.
- End with a final line: "Overall interest level: Low / Mixed / High" (pick one).

4. Other Ways This Could Go
- 2 bullets with alternative but plausible interpretations.
- Phrase clearly as possibilities (e.g., "They might actually be slammed but still interested.")
- No more than 2 bullets.

Do NOT give advice about what the user should do next.
Do NOT suggest exact replies.
Your entire job is to decode what the other person was probably trying to signal.
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
            error = "Server is missing the OpenAI API key. (This is a setup issue, not your fault.)"
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
