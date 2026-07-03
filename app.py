#!/usr/bin/env python3
import os
import time
import threading
import logging
from flask import Flask, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
bot_token = ""

logging.basicConfig(level=logging.INFO)

# 运行时统计（线程安全）
stats = {
    "start_time": time.time(),
    "message_count": 0,
    "unique_users": set(),
    "last_message": None,
}
stats_lock = threading.Lock()

# Telegram handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("点我", callback_data="btn_1")]]
    await update.message.reply_text(
        "你好！我是你的机器人。发送任意文字我会原样回复。", reply_markup=InlineKeyboardMarkup(keyboard)
    )
    with stats_lock:
        if update.effective_user:
            stats["unique_users"].add(update.effective_user.id)
        stats["last_message"] = {"user_id": update.effective_user.id if update.effective_user else None, "text": "/start"}

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        cmdTxt=update.message.text.strip()
        cmdStr=cmdTxt
        cmdarr=cmdTxt.split(".")
        cmdTxt=cmdarr[0]
        w =  cmdarr[1] if len(cmdarr)>=2 else "c"
        t2fcode = cmdarr[2] if len(cmdarr)>=3 else ''  
        result = f"{cmdTxt} {w} {t2fcode}"       
        await update.message.reply_text(f"{result}")
        with stats_lock:
            stats["message_count"] += 1
            if update.effective_user:
                stats["unique_users"].add(update.effective_user.id)
            stats["last_message"] = {"user_id": update.effective_user.id if update.effective_user else None, "text": update.message.text}

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query:
        return
    await query.answer()
    await query.edit_message_text(f"你按了：{query.data}")
    with stats_lock:
        if query.from_user:
            stats["unique_users"].add(query.from_user.id)
            stats["last_message"] = {"user_id": query.from_user.id, "text": query.data}

# 启动并运行 bot（会在单独线程中阻塞）
def run_bot(token: str):
    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    logging.info("Telegram bot: starting polling...")
    app.run_polling(stop_signals=None, close_loop=False))  # 阻塞，放在线程中运行
# Flask app 提供状态查询
flask_app = Flask(__name__)

@flask_app.route("/status")
def status():
    with stats_lock:
        uptime = int(time.time() - stats["start_time"])
        return jsonify({
            "running": bot_thread.is_alive(),
            "uptime_seconds": uptime,
            "message_count": stats["message_count"],
            "unique_user_count": len(stats["unique_users"]),
            "last_message": stats["last_message"],
        })

@flask_app.route("/health")
def health():
    return "ok"

if __name__ == "__main__":
    token = os.getenv("BOT_TOKEN",bot_token)
    if not token:
        logging.error("BOT_TOKEN is None'")
        raise SystemExit(1)

    # 启动 bot 线程
    logging.info(f"Starting BOT")
    bot_thread = threading.Thread(target=run_bot, args=(token,), daemon=True)
    bot_thread.start()

    # 启动 Flask（开发模式）。生产部署请用 gunicorn/uvicorn+容器或服务并注意并发/进程模型。
    port = int(os.getenv("BOT_PORT", "82"))
    logging.info(f"Starting Flask on 0.0.0.0:{port}")
    flask_app.run(host="0.0.0.0", port=port)
