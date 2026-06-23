import logging
import asyncio
import threading
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =====================
# SOZLAMALAR
# =====================
BOT_TOKEN = "8516151329:AAEHVVwBcj4fAm_WaNL6Rpb6uDW2vSxIeBA"
ADMIN_ID = 824354773
GROUP_ID = -1003790445484

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bronlar xotirada
pending_brons = {}

# Global application
app_instance = None
loop = None

# =====================
# /start
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men Mirage Game Club botiman.\n\n"
        "🎮 Bron qilish uchun:\n"
        "🔗 miragegameclub.netlify.app\n\n"
        "📞 +998 95 888 98 98"
    )

# =====================
# ADMIN TUGMA
# =====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    parts = data.split("_", 1)
    if len(parts) != 2:
        return

    action, bron_id = parts
    bron = pending_brons.get(bron_id)

    if not bron:
        await query.edit_message_text("⚠️ Bu bron topilmadi yoki allaqachon ko'rib chiqilgan.")
        return

    telefon = bron.get("telefon", "").strip()
    bron_type = bron.get("type", "bron")

    if action == "confirm":
        if bron_type == "bron":
            admin_text = (
                f"✅ <b>BRON TASDIQLANDI</b>\n\n"
                f"📍 {bron.get('zona')} | {bron.get('odam')}\n"
                f"📅 {bron.get('sana')} 🕐 {bron.get('soat')}\n"
                f"📞 {telefon}"
            )
            client_text = (
                f"✅ <b>Broningiz tasdiqlandi!</b>\n\n"
                f"🎮 <b>Mirage Game Club</b>\n\n"
                f"📍 Zona: <b>{bron.get('zona')}</b>\n"
                f"👥 Odamlar: <b>{bron.get('odam')}</b>\n"
                f"📅 {bron.get('sana')} soat <b>{bron.get('soat')}</b>\n\n"
                f"Sizi kutamiz! 🕹\n"
                f"📞 Savol: +998 95 888 98 98"
            )
        else:
            admin_text = (
                f"✅ <b>TURNIR QABUL QILINDI</b>\n\n"
                f"👤 {bron.get('ism')} | {bron.get('jamoa')}\n"
                f"📞 {telefon}"
            )
            client_text = (
                f"🏆 <b>Turnir arizangiz qabul qilindi!</b>\n\n"
                f"👤 {bron.get('ism')} | {bron.get('jamoa')}\n\n"
                f"Turnir haqida xabar beriladi. Omad! 🎯\n"
                f"📞 Savol: +998 95 888 98 98"
            )

        await query.edit_message_text(admin_text, parse_mode="HTML")

        # Guruhga xabar
        try:
            await context.bot.send_message(chat_id=GROUP_ID, text=admin_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Guruhga yuborishda xato: {e}")

        # Mijozga xabar
        try:
            await context.bot.send_message(chat_id=telefon, text=client_text, parse_mode="HTML")
        except Exception as e:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ Mijozga xabar yuborib bo'lmadi.\n📞 Qo'lda bog'laning: {telefon}\n\n{client_text}",
                parse_mode="HTML"
            )

    elif action == "reject":
        if bron_type == "bron":
            admin_text = f"❌ <b>Bron rad etildi</b>\n📞 {telefon}"
            client_text = (
                f"❌ <b>So'ragan vaqtingizda joy mavjud emas.</b>\n\n"
                f"Boshqa vaqtni tanlang:\n"
                f"📞 +998 95 888 98 98\n"
                f"📸 @mirage.shahrixon"
            )
        else:
            admin_text = f"❌ <b>Turnir arizasi rad etildi</b>\n📞 {telefon}"
            client_text = (
                f"❌ <b>Turnir arizangiz qabul qilinmadi.</b>\n\n"
                f"📞 +998 95 888 98 98"
            )

        await query.edit_message_text(admin_text, parse_mode="HTML")

        try:
            await context.bot.send_message(chat_id=GROUP_ID, text=admin_text, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Guruhga yuborishda xato: {e}")

        try:
            await context.bot.send_message(chat_id=telefon, text=client_text, parse_mode="HTML")
        except Exception as e:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"⚠️ Mijozga xabar yuborib bo'lmadi.\n📞 {telefon}"
            )

    pending_brons.pop(bron_id, None)

# =====================
# BRON KELGANDA ADMIN + GURUHGA YUBORISH
# =====================
async def send_bron(data: dict):
    global app_instance

    bron_type = data.get("type", "bron")
    import time
    ts = int(time.time())
    tel = data.get('telefon', 'unknown').replace('+', '').replace(' ', '')
    bron_id = f"{bron_type}_{tel}_{ts}"
    pending_brons[bron_id] = data

    if bron_type == "bron":
        text = (
            f"🎮 <b>YANGI BRON</b>\n\n"
            f"📍 Zona: <b>{data.get('zona', '—')}</b>\n"
            f"👥 Odamlar: <b>{data.get('odam', '—')}</b>\n"
            f"📅 Qachon: <b>{data.get('sana', '—')}</b>\n"
            f"🕐 Soat: <b>{data.get('soat', '—')}</b>\n"
            f"📞 Telefon: <b>{data.get('telefon', '—')}</b>\n\n"
            f"🆔 <code>{bron_id}</code>"
        )
        confirm_text = "✅ Tasdiqlash"
        reject_text = "❌ Rad etish"
    else:
        text = (
            f"🏆 <b>TURNIR ARIZASI</b>\n\n"
            f"👤 Ism: <b>{data.get('ism', '—')}</b>\n"
            f"⚔️ Jamoa: <b>{data.get('jamoa', '—')}</b>\n"
            f"🎯 Faceit: <b>{data.get('faceit', '—')}</b>\n"
            f"🏅 Premier: <b>{data.get('premier', '—')}</b>\n"
            f"✈️ Telegram: <b>{data.get('telegram', '—')}</b>\n"
            f"📞 Telefon: <b>{data.get('telefon', '—')}</b>\n\n"
            f"🆔 <code>{bron_id}</code>"
        )
        confirm_text = "✅ Qabul qilish"
        reject_text = "❌ Rad etish"

    keyboard = [[
        InlineKeyboardButton(confirm_text, callback_data=f"confirm_{bron_id}"),
        InlineKeyboardButton(reject_text, callback_data=f"reject_{bron_id}"),
    ]]
    markup = InlineKeyboardMarkup(keyboard)

    # Adminга tugmalar bilan
    await app_instance.bot.send_message(
        chat_id=ADMIN_ID, text=text, parse_mode="HTML", reply_markup=markup
    )

    # Guruhga tugmalarsiz
    try:
        await app_instance.bot.send_message(
            chat_id=GROUP_ID,
            text=text + "\n\n⏳ <i>Admin ko'rib chiqmoqda...</i>",
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Guruhga yuborishda xato: {e}")

# =====================
# FLASK
# =====================
flask_app = Flask(__name__)

@flask_app.route("/webhook/bron", methods=["POST"])
def webhook_bron():
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400
    logger.info(f"Keldi: {data}")
    future = asyncio.run_coroutine_threadsafe(send_bron(data), loop)
    try:
        future.result(timeout=10)
    except Exception as e:
        logger.error(f"Xato: {e}")
        return jsonify({"error": str(e)}), 500
    return jsonify({"status": "ok"}), 200

@flask_app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running"}), 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)

# =====================
# MAIN
# =====================
async def main():
    global app_instance, loop
    loop = asyncio.get_event_loop()

    app_instance = Application.builder().token(BOT_TOKEN).build()
    app_instance.add_handler(CommandHandler("start", start))
    app_instance.add_handler(CallbackQueryHandler(button_callback))

    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask ishga tushdi (port 8080)")

    await app_instance.initialize()
    await app_instance.start()
    await app_instance.updater.start_polling()
    logger.info("Bot ishga tushdi!")

    # Doimiy ishlash
    try:
        await asyncio.Event().wait()
    finally:
        await app_instance.updater.stop()
        await app_instance.stop()
        await app_instance.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
