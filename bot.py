import logging
import asyncio
import threading
import time
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

BOT_TOKEN = "8516151329:AAEHVVwBcj4fAm_WaNL6Rpb6uDW2vSxIeBA"
ADMIN_ID = 824354773
GROUP_ID = -1004327610337

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

pending_brons = {}
bot_app = None
main_loop = None

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"📍 Chat ID: <code>{chat_id}</code>\nTuri: {chat_type}",
        parse_mode="HTML"
    )

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Mirage Game Club boti.\n\n"
        "🎮 miragegameclub.netlify.app\n"
        "📞 +998 95 888 98 98"
    )

# Tugma bosilganda
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    action, bron_id = query.data.split("_", 1)
    bron = pending_brons.get(bron_id)

    if not bron:
        await query.edit_message_text("⚠️ Bron topilmadi.")
        return

    tel = bron.get("telefon", "")
    bron_type = bron.get("type", "bron")

    if action == "confirm":
        if bron_type == "bron":
            admin_msg = (
                f"✅ <b>BRON TASDIQLANDI</b>\n\n"
                f"📍 {bron.get('zona')} | {bron.get('odam')}\n"
                f"📅 {bron.get('sana')} 🕐 {bron.get('soat')}\n"
                f"📞 {tel}"
            )
            client_msg = (
                f"✅ <b>Broningiz tasdiqlandi!</b>\n\n"
                f"🎮 Mirage Game Club\n"
                f"📍 {bron.get('zona')}\n"
                f"👥 {bron.get('odam')}\n"
                f"📅 {bron.get('sana')} soat {bron.get('soat')}\n\n"
                f"Sizi kutamiz! 🕹\n📞 +998 95 888 98 98"
            )
        else:
            admin_msg = f"✅ <b>TURNIR QABUL</b>\n👤 {bron.get('ism')} | {bron.get('jamoa')}\n📞 {tel}"
            client_msg = (
                f"🏆 <b>Turnir arizangiz qabul qilindi!</b>\n\n"
                f"👤 {bron.get('ism')} | ⚔️ {bron.get('jamoa')}\n\n"
                f"Omad! 🎯\n📞 +998 95 888 98 98"
            )

        await query.edit_message_text(admin_msg, parse_mode="HTML")
        try:
            await context.bot.send_message(chat_id=GROUP_ID, text=admin_msg, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Guruh xato: {e}")
        try:
            await context.bot.send_message(chat_id=tel, text=client_msg, parse_mode="HTML")
        except:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ Mijozga xabar yuborilmadi.\n📞 {tel}\n\n{client_msg}",
                parse_mode="HTML"
            )

    elif action == "reject":
        if bron_type == "bron":
            admin_msg = f"❌ <b>Bron rad etildi</b>\n📞 {tel}"
            client_msg = f"❌ <b>So'ragan vaqtda joy yo'q.</b>\n\nBoshqa vaqt tanlang:\n📞 +998 95 888 98 98"
        else:
            admin_msg = f"❌ <b>Turnir rad etildi</b>\n📞 {tel}"
            client_msg = f"❌ <b>Arizangiz qabul qilinmadi.</b>\n📞 +998 95 888 98 98"

        await query.edit_message_text(admin_msg, parse_mode="HTML")
        try:
            await context.bot.send_message(chat_id=GROUP_ID, text=admin_msg, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Guruh xato: {e}")
        try:
            await context.bot.send_message(chat_id=tel, text=client_msg, parse_mode="HTML")
        except:
            await context.bot.send_message(chat_id=ADMIN_ID, text=f"⚠️ Mijozga xabar yuborilmadi.\n📞 {tel}")

    pending_brons.pop(bron_id, None)

# Saytdan bron kelganda
async def process_bron(data: dict):
    bron_type = data.get("type", "bron")
    ts = int(time.time())
    tel = data.get('telefon', 'x').replace('+', '').replace(' ', '')
    bron_id = f"{bron_type}_{tel}_{ts}"
    pending_brons[bron_id] = data

    if bron_type == "bron":
        text = (
            f"🎮 <b>YANGI BRON</b>\n\n"
            f"📍 Zona: <b>{data.get('zona','—')}</b>\n"
            f"👥 Odamlar: <b>{data.get('odam','—')}</b>\n"
            f"📅 Qachon: <b>{data.get('sana','—')}</b>\n"
            f"🕐 Soat: <b>{data.get('soat','—')}</b>\n"
            f"📞 Telefon: <b>{data.get('telefon','—')}</b>"
        )
        btn1, btn2 = "✅ Tasdiqlash", "❌ Rad etish"
    else:
        text = (
            f"🏆 <b>TURNIR ARIZASI</b>\n\n"
            f"👤 Ism: <b>{data.get('ism','—')}</b>\n"
            f"⚔️ Jamoa: <b>{data.get('jamoa','—')}</b>\n"
            f"🎯 Faceit: <b>{data.get('faceit','—')}</b>\n"
            f"🏅 Premier: <b>{data.get('premier','—')}</b>\n"
            f"✈️ Telegram: <b>{data.get('telegram','—')}</b>\n"
            f"📞 Telefon: <b>{data.get('telefon','—')}</b>"
        )
        btn1, btn2 = "✅ Qabul qilish", "❌ Rad etish"

    keyboard = [[
        InlineKeyboardButton(btn1, callback_data=f"confirm_{bron_id}"),
        InlineKeyboardButton(btn2, callback_data=f"reject_{bron_id}"),
    ]]
    markup = InlineKeyboardMarkup(keyboard)

    await bot_app.bot.send_message(chat_id=ADMIN_ID, text=text, parse_mode="HTML", reply_markup=markup)
    try:
        await bot_app.bot.send_message(
            chat_id=GROUP_ID,
            text=text + "\n\n⏳ <i>Admin ko'rib chiqmoqda...</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Guruh xato: {e}")

# Flask
flask_app = Flask(__name__)

@flask_app.route("/webhook/bron", methods=["POST"])
def webhook_bron():
    data = request.get_json()
    if not data:
        return jsonify({"error": "no data"}), 400
    future = asyncio.run_coroutine_threadsafe(process_bron(data), main_loop)
    try:
        future.result(timeout=15)
    except Exception as e:
        logger.error(f"Webhook xato: {e}")
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "ok"}), 200

@flask_app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "bot": "Mirage Game Club"}), 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

# Main
def main():
    global bot_app, main_loop

    main_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(main_loop)

    bot_app = Application.builder().token(BOT_TOKEN).build()
    bot_app.add_handler(CommandHandler("start", start))
    bot_app.add_handler(CommandHandler("chatid", get_chat_id))
    bot_app.add_handler(CallbackQueryHandler(button_callback))

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask ishga tushdi!")

    logger.info("Bot polling boshlanmoqda...")
    bot_app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
