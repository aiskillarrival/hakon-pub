import time

from flask import Flask, jsonify, render_template_string, request

from hakon.r_s_s_article_fetcher import (
    RSS_URL as DEFAULT_RSS_URL,
)
from hakon.r_s_s_article_fetcher import (
    can_fetch,
    extract_article_text,
    fetch,
    parse_rss_items,
)

app = Flask(__name__)

INDEX_HTML = """\
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>hakon — RSS Article Fetcher</title>
<style>
  :root { color-scheme: dark; }
  body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
  h1 { font-size: 1.6rem; }
  input, button, textarea { font: inherit; }
  form { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
  input[name="rss_url"] { flex: 1; padding: 0.5rem; }
  button { padding: 0.5rem 1.2rem; cursor: pointer; }
  .card { background: #1e1e2e; border: 1px solid #333; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
  .card h3 { margin: 0 0 0.3rem; }
  .card .meta { color: #888; font-size: 0.85rem; }
  .card .snippet { margin-top: 0.6rem; padding: 0.6rem; background: #111; border-radius: 4px; font-size: 0.9rem; white-space: pre-wrap; }
  .error { color: #f87171; }
</style>
</head>
<body>
<h1>📰 hakon — RSS Article Fetcher</h1>
<form method="post" action="/api/fetch">
  <input name="rss_url" type="url" placeholder="RSS feed URL" value="{{ default_url }}">
  <button type="submit">Fetch</button>
</form>
<p>Or call <code>POST /api/fetch</code> with JSON <code>{"rss_url": "…"}</code> to get results as JSON.</p>
</body>
</html>"""

RESULT_HTML = """\
<!doctype html>-
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>hakon — Results</title>
<style>
  :root { color-scheme: dark; }
  body { font-family: system-ui, sans-serif; max-width: 720px; margin: 2rem auto; padding: 0 1rem; }
  a { color: #6cf; }
  .card { background: #1e1e2e; border: 1px solid #333; border-radius: 8px; padding: 1rem; margin-bottom: 1rem; }
  .card h3 { margin: 0 0 0.3rem; }
  .card .meta { color: #888; font-size: 0.85rem; }
  .card .snippet { margin-top: 0.6rem; padding: 0.6rem; background: #111; border-radius: 4px; font-size: 0.9rem; white-space: pre-wrap; }
  .error { color: #f87171; }
  .back { margin-bottom: 1.5rem; display: inline-block; }
</style>
</head>
<body>
<a class="back" href="/">← Back</a>
<h1>Results</h1>
<p>Feed: <code>{{ rss_url }}</code></p>
{% for item in items %}
<div class="card">
  <h3>{{ item.title }}</h3>
  <div class="meta">{{ item.pubDate }} · <a href="{{ item.link }}" target="_blank">{{ item.link }}</a></div>
  {% if item.media_links %}
  <div class="meta">Media: {{ item.media_links | join(", ") }}</div>
  {% endif %}
  {% if item.snippet %}
  <div class="snippet">{{ item.snippet }}</div>
  {% endif %}
</div>
{% endfor %}
{% if error %}
<div class="error">{{ error }}</div>
{% endif %}
</body>
</html>"""


@app.route("/")
def index() -> str:
    return render_template_string(INDEX_HTML, default_url=DEFAULT_RSS_URL)


@app.route("/api/fetch", methods=["POST"])
def api_fetch():
    # Accept JSON or form-encoded
    if request.is_json:
        data = request.get_json(silent=True) or {}
        rss_url = data.get("rss_url", DEFAULT_RSS_URL)
    else:
        rss_url = request.form.get("rss_url", DEFAULT_RSS_URL)

    if not rss_url:
        return jsonify({"error": "No rss_url provided"}), 400

    if not can_fetch(rss_url):
        return jsonify(
            {"error": f"Robots.txt disallows fetching: {rss_url}"}
        ), 403

    try:
        rss_xml = fetch(rss_url)
    except Exception as exc:
        return jsonify({"error": f"Failed to fetch RSS: {exc}"}), 502

    try:
        raw_items = list(parse_rss_items(rss_xml, limit=10))
    except Exception as exc:
        return jsonify({"error": f"Failed to parse RSS: {exc}"}), 502

    items: list[dict[str, object]] = []
    for item in raw_items:
        snippet = ""
        link = str(item.get("link", ""))
        if link and can_fetch(link):
            try:
                time.sleep(0.5)  # polite rate-limit
                html = fetch(link)
                snippet = extract_article_text(html, max_paragraphs=3)
            except Exception:
                snippet = ""

        items.append(
            {
                "title": item.get("title", ""),
                "link": link,
                "pubDate": item.get("pubDate", ""),
                "media_links": item.get("media_links", []),
                "snippet": snippet,
            }
        )

    # Return HTML if form-encoded; JSON otherwise
    want_html = (
        not request.is_json
        and request.accept_mimetypes.best_match(
            ["text/html", "application/json"]
        )
        == "text/html"
    )

    if want_html:
        return render_template_string(
            RESULT_HTML, rss_url=rss_url, items=items
        )

    return jsonify({"rss_url": rss_url, "items": items})


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
