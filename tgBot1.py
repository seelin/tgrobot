import os
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("知道了", callback_data="yes"),InlineKeyboardButton("好吧", callback_data="no")]]
    await update.message.reply_text(
        "你好！我是你的机器人。发送任意文字我会原样回复。", reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message and update.message.text:
        cmdTxt=update.message.text.strip()
        cmdStr=cmdTxt
        cmdarr=cmdTxt.split(".")
        cmdTxt=cmdarr[0]
        w =  cmdarr[1] if len(cmdarr)>=2 else "c"
        t2fcode = cmdarr[2] if len(cmdarr)>=3 else ''  
        result = f"{cmdTxt} {w} {t2fcode}"
        await update.message.reply_text(result)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()  # 关闭 loading
    await query.edit_message_text(f"你按了：{query.data}")

def main():
    token=os.getenv('BOT_TOKEN')
    if not token:
        print("BOT_TOKEN is None")
        return

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))   
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))  
    
    print("Bot 已启动，使用轮询中... (Ctrl+C 停止)")
    app.run_polling()

if __name__ == "__main__":
    main()
