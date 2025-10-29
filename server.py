from flask import Flask, request, send_file
import yt_dlp
import os

app = Flask(__name__)

@app.route('/')
def index():
    return '''
    <html dir="rtl" lang="ar">
    <head>
        <meta charset="UTF-8">
        <title>🎬 Abdu Videos</title>
        <style>
            body {
                background-color: #0d0d0d;
                color: #fff;
                text-align: center;
                font-family: 'Cairo', sans-serif;
                padding-top: 50px;
            }
            input {
                width: 60%%;
                padding: 10px;
                border-radius: 10px;
                border: none;
                font-size: 18px;
                margin: 10px;
            }
            button {
                background: #ff3333;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 10px;
                font-size: 18px;
                cursor: pointer;
            }
        </style>
    </head>
    <body>
        <h1>🎥 موقع Abdu Videos</h1>
        <p>أدخل رابط فيديو من يوتيوب لتحميله بجودة 360p</p>
        <form action="/download" method="get">
            <input type="text" name="url" placeholder="ضع رابط الفيديو هنا">
            <button type="submit">تحميل الفيديو 📥</button>
        </form>
    </body>
    </html>
    '''

@app.route('/download')
def download():
    url = request.args.get('url')
    if not url:
        return "❌ لم يتم إدخال رابط الفيديو"

    try:
        ydl_opts = {
            'format': 'best[height<=360]',
            'outtmpl': 'video.mp4',
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        return send_file("video.mp4", as_attachment=True, download_name="abdu_video.mp4")
    except Exception as e:
        return f"حدث خطأ أثناء التحميل: {e}"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)