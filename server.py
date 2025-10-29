# server.py
from flask import Flask, request, jsonify, send_file, render_template_string, redirect, url_for
import threading, yt_dlp, os, uuid, time

app = Flask(__name__)

DOWNLOAD_DIR = "downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

state = {
    "status": "idle",
    "percent": 0.0,
    "filename": "",
    "message": ""
}

def progress_hook(d):
    try:
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            pct = (downloaded / total * 100) if total else 0.0
            state.update({"status": "downloading", "percent": round(pct, 1)})
        elif d.get("status") == "finished":
            state.update({"status": "finalizing", "percent": 100.0})
    except Exception as e:
        state.update({"status": "error", "message": str(e)})

def download_worker(url):
    global state
    tmpname = f"{uuid.uuid4().hex}.mp4"
    outtmpl = os.path.join(DOWNLOAD_DIR, tmpname)
    ydl_opts = {
        "format": "best[height<=360][ext=mp4]/best[ext=mp4]/best",
        "outtmpl": outtmpl,
        "progress_hooks": [progress_hook],
        "quiet": True,
        "no_warnings": True,
    }

    try:
        state.update({"status": "downloading", "percent": 0.0, "filename": tmpname, "message": "starting"})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
        state.update({"status": "done", "percent": 100.0, "filename": tmpname, "message": "completed"})
    except Exception as e:
        state.update({"status": "error", "message": str(e)})
        try:
            if os.path.exists(outtmpl):
                os.remove(outtmpl)
        except:
            pass

@app.route("/")
def index():
    html = """
    <!doctype html>
    <html lang="ar" dir="rtl">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1">
      <title>Abdu Videos</title>
      <style>
        body{background:#0b0b0b;color:#eee;font-family:Arial, "Cairo", sans-serif;display:flex;flex-direction:column;align-items:center;padding:40px;}
        .card{width:100%;max-width:760px;background:#111;padding:24px;border-radius:12px;box-shadow:0 6px 20px rgba(0,0,0,0.5);}
        h1{color:#ff4d4f;margin:0 0 12px}
        input[type=text]{width:100%;padding:12px;border-radius:8px;border:none;background:#0f0f0f;color:#fff;font-size:16px;margin-bottom:12px;direction:ltr}
        button{padding:12px 18px;border-radius:8px;border:none;font-weight:700;cursor:pointer;}
        .btn-download{background:#ff4d4f;color:white}
        .note{color:#bbb;margin-top:12px;font-size:14px}
        #progress{margin-top:18px;color:#9bd; font-weight:600}
      </style>
    </head>
    <body>
      <div class="card">
        <h1>🎬 Abdu Videos</h1>
        <p>ألصقي رابط يوتيوب والتحميل هيبدأ تلقائيًا (جودة حتى 360p).</p>
        <form id="f" action="/start" method="post" onsubmit="start(event)">
          <input id="url" name="url" type="text" placeholder="https://www.youtube.com/watch?v=..." required>
          <div style="display:flex;gap:8px;">
            <button class="btn-download" type="submit">ابدأ التحميل</button>
          </div>
        </form>
        <div id="progress" style="display:none"></div>
        <div class="note">الفيديو يتحذف تلقائيًا من السيرفر بعد ما يتحمل على جهازك.</div>
      </div>

    <script>
      let pollInterval = null;
      function start(e){
        e.preventDefault();
        const url = document.getElementById('url').value.trim();
        if(!url) return alert('ادخلي رابط يوتيوب');
        fetch('/start', {
          method: 'POST',
          headers: {'Content-Type':'application/json'},
          body: JSON.stringify({url})
        }).then(r=>r.json()).then(data=>{
          if(data.ok){
            document.getElementById('progress').style.display = 'block';
            pollStatus();
          } else {
            alert('حصل خطأ: ' + (data.msg || ''));
          }
        }).catch(err=>{
          alert('خطأ في الاتصال: ' + err);
        });
      }

      function pollStatus(){
        if(pollInterval) clearInterval(pollInterval);
        pollInterval = setInterval(async ()=>{
          try{
            let res = await fetch('/status');
            let j = await res.json();
            if(j.status === 'downloading'){
              document.getElementById('progress').innerText = '📥 جاري التحميل: ' + j.percent + '%';
            } else if(j.status === 'finalizing'){
              document.getElementById('progress').innerText = '⏳ جاري تجهيز الملف...';
            } else if(j.status === 'done'){
              document.getElementById('progress').innerText = '✅ اكتمل التحميل — جاري البدء في التنزيل...';
              clearInterval(pollInterval);
              window.location = '/get';
            } else if(j.status === 'error'){
              clearInterval(pollInterval);
              document.getElementById('progress').innerText = '❌ حدث خطأ: ' + j.message;
            }
          }catch(e){
            console.error(e);
          }
        }, 1500);
      }
    </script>
    </body>
    </html>
    """
    return render_template_string(html)

@app.route("/start", methods=["POST"])
def start():
    data = request.get_json() or {}
    url = data.get("url")
    if not url:
        return jsonify({"ok": False, "msg": "no url"})
    if state.get("status") in ("downloading", "finalizing"):
        return jsonify({"ok": False, "msg": "server busy, try later"})
    state.update({"status": "idle", "percent": 0.0, "filename": "", "message": ""})
    t = threading.Thread(target=download_worker, args=(url,), daemon=True)
    t.start()
    return jsonify({"ok": True})

@app.route("/status")
def status():
    return jsonify(state)

@app.route("/get")
def get_file():
    if state.get("status") != "done":
        return redirect(url_for("index"))
    fname = state.get("filename")
    path = os.path.join(DOWNLOAD_DIR, fname)
    if not os.path.exists(path):
        return "file missing", 404
    def cleanup():
        try:
            os.remove(path)
        except:
            pass
    threading.Timer(3.0, cleanup).start()  # يمسح الملف بعد 3 ثواني
    return send_file(path, as_attachment=True, download_name=f"abdu_video_{int(time.time())}.mp4")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
