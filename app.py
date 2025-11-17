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
      select,
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
      select:focus,
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
          <!-- STEP 1 -->
          <div class="field">
            <div class="step-label">Step 1</div>
            <div class="field-title">What is the situation?</div>
            <textarea
              name="context"
              id="context"
              placeholder="Example: We have been talking for a month and he suddenly pulled back after last weekend.">{{ context or "" }}</textarea>
            <p class="hint">Totally optional. It just helps the interpretation feel more accurate.</p>
          </div>

          <!-- STEP 2: screenshots -->
          <div class="field">
            <div class="step-label">Step 2</div>
            <div class="field-title">Add the conversation</div>
            <input type="file" name="images" id="images" accept="image/*" multiple>
            <p class="hint">Best option is 1 to 3 screenshots of the chat from your phone, earliest messages first. Assume you are the blue bubble.</p>
          </div>

          <div class="or-divider">
            <span></span> or paste the messages <span></span>
          </div>

          <!-- STEP 2B: text -->
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
