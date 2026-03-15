"""Web UI server for image storer."""

import base64
import re
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory

from . import storage

app = Flask(__name__, static_folder=None)
app.config["MAX_CONTENT_LENGTH"] = 32 * 1024 * 1024  # 32 MB


@app.route("/api/list")
def api_list():
    images = storage.list_images()
    for img in images:
        img["url"] = f"/snapshots/{img['id']}"
    return jsonify(images)


@app.route("/snapshots/<path:filename>")
def serve_snapshot(filename):
    path = storage.get_image_path(filename)
    if path is None:
        return "", 404
    return send_from_directory(path.parent, path.name, max_age=3600)


@app.route("/api/upload", methods=["POST"])
def api_upload():
    # Multipart form (drag-drop / file input)
    if request.files:
        added = []
        files = request.files.getlist("files") or list(request.files.values())
        for f in files:
            if f and (getattr(f, "filename", None) or getattr(f, "content_type", "").startswith("image/")):
                name = storage.add_image(f.stream, f.content_type, getattr(f, "filename", None) or "")
                added.append({"id": name, "url": f"/snapshots/{name}"})
        if added:
            return jsonify({"added": added}), 201

    # JSON with base64 image (paste)
    if request.is_json:
        data = request.get_json()
        if isinstance(data, dict) and "image" in data:
            b64 = data["image"]
            if isinstance(b64, str):
                # optional data URL prefix
                b64 = re.sub(r"^data:image/\w+;base64,", "", b64)
                raw = base64.b64decode(b64)
                content_type = (data.get("content_type") or "image/png").strip()
                name = storage.add_image_from_bytes(raw, content_type)
                return jsonify({"added": [{"id": name, "url": f"/snapshots/{name}"}]}), 201
    return jsonify({"error": "No image data"}), 400


@app.route("/api/snapshots/<path:image_id>", methods=["DELETE"])
def api_remove(image_id):
    if storage.remove_image(image_id):
        return "", 204
    return "", 404


@app.route("/api/clear", methods=["POST"])
def api_clear():
    n = storage.clear_all()
    return jsonify({"removed": n}), 200


@app.route("/")
def index():
    return _INDEX_HTML


# Single-page UI: drop zone, paste, gallery
_INDEX_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Snapshot Bucket</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Outfit:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0d0d0f;
      --surface: #16161a;
      --border: #2a2a30;
      --muted: #6b6b7b;
      --text: #e4e4e7;
      --accent: #22d3ee;
      --accent-dim: #0891b2;
      --danger: #f43f5e;
      --radius: 12px;
      --radius-sm: 8px;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: 'Outfit', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 1.5rem;
    }
    h1 {
      font-size: 1.5rem;
      font-weight: 600;
      margin-bottom: 1rem;
      font-family: 'JetBrains Mono', monospace;
      color: var(--accent);
    }
    .drop-zone {
      border: 2px dashed var(--border);
      background: var(--surface);
      border-radius: var(--radius);
      padding: 2.5rem;
      text-align: center;
      margin-bottom: 1.5rem;
      transition: border-color .2s, background .2s;
    }
    .drop-zone.drag-over { border-color: var(--accent); background: rgba(34, 211, 238, 0.06); }
    .drop-zone p { color: var(--muted); font-size: 0.95rem; }
    .drop-zone kbd { font-family: 'JetBrains Mono', monospace; background: var(--border); padding: .2em .5em; border-radius: 4px; font-size: 0.85em; }
    .gallery {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(160px, 1fr));
      gap: 1rem;
    }
    .card {
      background: var(--surface);
      border-radius: var(--radius-sm);
      overflow: hidden;
      border: 1px solid var(--border);
      position: relative;
      aspect-ratio: 1;
    }
    .card img {
      width: 100%;
      height: 100%;
      object-fit: cover;
      display: block;
    }
    .card .actions {
      position: absolute;
      top: 6px;
      right: 6px;
      display: flex;
      gap: 4px;
      opacity: 0;
      transition: opacity .2s;
    }
    .card:hover .actions { opacity: 1; }
    .card button {
      width: 28px;
      height: 28px;
      border: none;
      border-radius: 6px;
      background: rgba(0,0,0,.7);
      color: var(--text);
      cursor: pointer;
      font-size: 14px;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    .card button:hover { background: var(--danger); }
    .toolbar {
      display: flex;
      align-items: center;
      gap: 1rem;
      margin-bottom: 1rem;
    }
    .toolbar button {
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      padding: .4rem .75rem;
      border-radius: var(--radius-sm);
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      cursor: pointer;
    }
    .toolbar button:hover { border-color: var(--accent); color: var(--accent); }
    .toolbar button.danger:hover { border-color: var(--danger); color: var(--danger); }
    .empty { color: var(--muted); text-align: center; padding: 2rem; }
    #toast {
      position: fixed;
      bottom: 1.5rem;
      left: 50%;
      transform: translateX(-50%) translateY(100px);
      background: var(--surface);
      border: 1px solid var(--accent);
      color: var(--accent);
      padding: .5rem 1rem;
      border-radius: var(--radius-sm);
      font-size: 0.9rem;
      opacity: 0;
      transition: transform .25s, opacity .25s;
    }
    #toast.show { transform: translateX(-50%) translateY(0); opacity: 1; }
    .lightbox {
      position: fixed;
      inset: 0;
      background: rgba(0,0,0,.9);
      display: none;
      align-items: center;
      justify-content: center;
      z-index: 100;
      cursor: pointer;
    }
    .lightbox.show { display: flex; }
    .lightbox img { max-width: 90vw; max-height: 90vh; object-fit: contain; }
  </style>
</head>
<body>
  <h1>Snapshot Bucket</h1>
  <div class="drop-zone" id="dropZone">
    <p>Drop images here or <kbd>Ctrl+V</kbd> / <kbd>Cmd+V</kbd> to paste</p>
  </div>
  <div class="toolbar">
    <button type="button" id="clearBtn" class="danger">Clear all</button>
  </div>
  <div class="gallery" id="gallery"></div>
  <div class="empty" id="empty">No snapshots yet. Drop or paste to add.</div>
  <div class="lightbox" id="lightbox"><img src="" alt=""></div>
  <div id="toast"></div>

  <script>
    const gallery = document.getElementById('gallery');
    const empty = document.getElementById('empty');
    const dropZone = document.getElementById('dropZone');
    const clearBtn = document.getElementById('clearBtn');
    const lightbox = document.getElementById('lightbox');
    const toast = document.getElementById('toast');

    function showToast(msg) {
      toast.textContent = msg;
      toast.classList.add('show');
      setTimeout(() => toast.classList.remove('show'), 2500);
    }

    function render(list) {
      gallery.innerHTML = '';
      empty.style.display = list.length ? 'none' : 'block';
      list.forEach(img => {
        const card = document.createElement('div');
        card.className = 'card';
        const a = document.createElement('a');
        a.href = img.url;
        a.target = '_blank';
        const im = document.createElement('img');
        im.src = img.url;
        im.loading = 'lazy';
        im.alt = img.id;
        a.appendChild(im);
        card.appendChild(a);
        const actions = document.createElement('div');
        actions.className = 'actions';
        const delBtn = document.createElement('button');
        delBtn.textContent = '×';
        delBtn.title = 'Remove';
        delBtn.onclick = (e) => { e.preventDefault(); remove(img.id); };
        actions.appendChild(delBtn);
        card.appendChild(actions);
        im.onclick = (e) => { e.preventDefault(); lightbox.querySelector('img').src = img.url; lightbox.classList.add('show'); };
        gallery.appendChild(card);
      });
    }

    function load() {
      fetch('/api/list').then(r => r.json()).then(render).catch(() => showToast('Failed to load'));
    }

    function remove(id) {
      fetch('/api/snapshots/' + encodeURIComponent(id), { method: 'DELETE' })
        .then(r => { if (r.ok) { load(); showToast('Removed'); } });
    }

    clearBtn.onclick = () => {
      if (!confirm('Delete all snapshots?')) return;
      fetch('/api/clear', { method: 'POST' }).then(r => r.json()).then(d => { load(); showToast('Cleared ' + d.removed); });
    };

    lightbox.onclick = () => lightbox.classList.remove('show');

    function upload(files) {
      if (!files.length) return;
      const fd = new FormData();
      for (let i = 0; i < files.length; i++) fd.append('files', files[i]);
      fetch('/api/upload', { method: 'POST', body: fd })
        .then(r => r.json())
        .then(d => { load(); showToast('Added ' + (d.added?.length || 0) + ' image(s)'); })
        .catch(() => showToast('Upload failed'));
    }

    function pasteImage(dataUrl) {
      fetch('/api/upload', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ image: dataUrl })
      })
        .then(r => r.json())
        .then(d => { load(); showToast('Pasted'); })
        .catch(() => showToast('Paste failed'));
    }

    dropZone.ondragover = (e) => { e.preventDefault(); dropZone.classList.add('drag-over'); };
    dropZone.ondragleave = () => dropZone.classList.remove('drag-over');
    dropZone.ondrop = (e) => {
      e.preventDefault();
      dropZone.classList.remove('drag-over');
      const files = Array.from(e.dataTransfer.files).filter(f => f.type.startsWith('image/'));
      upload(files);
    };

    document.addEventListener('paste', (e) => {
      const item = e.clipboardData?.items && [].find.call(e.clipboardData.items, i => i.type.startsWith('image/'));
      if (!item) return;
      e.preventDefault();
      const file = item.getAsFile();
      const reader = new FileReader();
      reader.onload = () => pasteImage(reader.result);
      reader.readAsDataURL(file);
    });

    load();
  </script>
</body>
</html>
"""


def run(host: str = "127.0.0.1", port: int = 5847, debug: bool = False) -> None:
    app.run(host=host, port=port, debug=debug, threaded=True)
