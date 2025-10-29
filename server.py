from flask import Flask, send_file, request
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
      <head>
        <title>Abdu Videos</title>
        <style>
          body {background:#111; color:#fff; text-align:center; font-family:Arial;}
          input {padding:10px; width:300px; border:none; border-radius:10px;}
          button {padding:10px 20px; border:none; border-radius:10px; background:#6200EE; color:white; cursor:pointer;}
          button:hover {background:#3700B3;}
        </style>
      </head>
      <body>
        <h2>🎬 Abdu Videos Downloader</h2>
        <form action="/download" method="get">
          <input type="text" name="url" placeholder="رابط الفيديو" required>
          <br><br>
          <button type="submit">تجهيز الرابط وتحميل</button>
        </form>
      </body>
    </html>
    '''

@app.route('/download')
def download_video():
    url = request.args.get('url')
    if not url:
        return "❌ مفيش رابط"

    ydl_opts = {
        'format': 'best[height<=360]',
        'outtmpl': 'video.mp4'
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    return send_file('video.mp4', as_attachment=True)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
