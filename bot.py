import logging
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)

# =====================
# SOZLAMALAR
# =====================
BOT_TOKEN = "8516151329:AAEHVVwBcj4fAm_WaNL6Rpb6uDW2vSxIeBA"
ADMIN_ID = 824354773  # Sizning Telegram ID
GROUP_ID = -1003790445484  # Mirage guruh ID

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Bronlar vaqtincha xotirada saqlanadi
pending_brons = {}

# =====================
# /start KOMANDASI
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Salom! Men Mirage Game Club botiman.\n\n"
        "🎮 Bron qilish uchun saytga o'ting:\n"
        "🔗 miragegameclub.netlify.app\n\n"
        "📞 Qo'shimcha ma'lumot: +998 95 888 98 98"
    )

# =====================
# WEBHOOK — SAYTDAN KELGAN BRON
# =====================
async def handle_webhook(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Saytdan kelgan bron ma'lumotlarini qayta ishlaydi"""
    pass

# =====================
# SAYTDAN BRON QABUL QILISH (HTTP endpoint orqali)
# =====================
async def receive_bron(data: dict, application):
    """Saytdan bron kelganda adminга yuboradi"""
    bron_type = data.get("type", "bron")

    if bron_type == "bron":
        bron_id = f"bron_{data.get('telefon', 'unknown').replace('+', '').replace(' ', '')}_{int(__import__('time').time())}"
        pending_brons[bron_id] = data

        text = (
            f"🎮 <b>YANGI BRON</b>\n\n"
            f"📍 Zona: <b>{data.get('zona', '—')}</b>\n"
            f"👥 Odamlar: <b>{data.get('odam', '—')}</b>\n"
            f"📅 Sana: <b>{data.get('sana', '—')}</b>\n"
            f"🕐 Soat: <b>{data.get('soat', '—')}</b>\n"
            f"📞 Telefon: <b>{data.get('telefon', '—')}</b>\n\n"
            f"🆔 ID: <code>{bron_id}</code>"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"confirm_{bron_id}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{bron_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await application.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )

        # Guruhga ham yuborish (tugmalarsiz)
        await application.bot.send_message(
            chat_id=GROUP_ID,
            text=text + "\n\n⏳ <i>Admin ko'rib chiqmoqda...</i>",
            parse_mode="HTML"
        )

    elif bron_type == "turnir":
        bron_id = f"turnir_{data.get('telefon', 'unknown').replace('+', '').replace(' ', '')}_{int(__import__('time').time())}"
        pending_brons[bron_id] = data

        text = (
            f"🏆 <b>TURNIR ARIZASI</b>\n\n"
            f"👤 Ism: <b>{data.get('ism', '—')}</b>\n"
            f"⚔️ Jamoa: <b>{data.get('jamoa', '—')}</b>\n"
            f"🎯 Faceit: <b>{data.get('faceit', '—')}</b>\n"
            f"🏅 Premier: <b>{data.get('premier', '—')}</b>\n"
            f"✈️ Telegram: <b>{data.get('telegram', '—')}</b>\n"
            f"📞 Telefon: <b>{data.get('telefon', '—')}</b>\n\n"
            f"🆔 ID: <code>{bron_id}</code>"
        )

        keyboard = [
            [
                InlineKeyboardButton("✅ Qabul qilish", callback_data=f"confirm_{bron_id}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_{bron_id}"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await application.bot.send_message(
            chat_id=ADMIN_ID,
            text=text,
            parse_mode="HTML",
            reply_markup=reply_markup
        )

        # Guruhga ham yuborish
        await application.bot.send_message(
            chat_id=GROUP_ID,
            text=text + "\n\n⏳ <i>Admin ko'rib chiqmoqda...</i>",
            parse_mode="HTML"
        )

# =====================
# ADMIN TUGMA BOSDI
# =====================
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    action, bron_id = data.split("_", 1)
    bron = pending_brons.get(bron_id)

    if not bron:
        await query.edit_message_text("⚠️ Bu bron topilmadi yoki allaqachon ko'rib chiqilgan.")
        return

    telefon = bron.get("telefon", "").strip()
    bron_type = bron.get("type", "bron")

    if action == "confirm":
        # Adminга tasdiq xabari
        if bron_type == "bron":
            admin_text = (
                f"✅ <b>BRON TASDIQLANDI</b>\n\n"
                f"📍 {bron.get('zona')} | {bron.get('odam')}\n"
                f"📅 {bron.get('sana')} soat {bron.get('soat')}\n"
                f"📞 {telefon}"
            )
            # Mijozga yuboriladigan xabar
            client_text = (
                f"✅ <b>Bronингиз tasdiqlandi!</b>\n\n"
                f"🎮 <b>Mirage Game Club</b>\n\n"
                f"📍 Zona: <b>{bron.get('zona')}</b>\n"
                f"👥 Odamlar: <b>{bron.get('odam')}</b>\n"
                f"📅 Sana: <b>{bron.get('sana')}</b>\n"
                f"🕐 Soat: <b>{bron.get('soat')}</b>\n\n"
                f"Siz kelishingizni kutamiz! 🕹\n"
                f"📞 Savol bo'lsa: +998 95 888 98 98"
            )
        else:
            admin_text = (
                f"✅ <b>TURNIR ARIZASI QABUL QILINDI</b>\n\n"
                f"👤 {bron.get('ism')} | {bron.get('jamoa')}\n"
                f"📞 {telefon}"
            )
            client_text = (
                f"🏆 <b>Turnir arizangiz qabul qilindi!</b>\n\n"
                f"<b>Mirage Game Club</b>\n\n"
                f"👤 Ism: <b>{bron.get('ism')}</b>\n"
                f"⚔️ Jamoa: <b>{bron.get('jamoa')}</b>\n\n"
                f"Turnir haqida qo'shimcha ma'lumot beriladi.\n"
                f"Omad! 🎯\n"
                f"📞 Savol bo'lsa: +998 95 888 98 98"
            )

        await query.edit_message_text(admin_text, parse_mode="HTML")

        # Guruhga tasdiqlash xabari
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=admin_text,
            parse_mode="HTML"
        )

        # Mijozga Telegram orqali xabar yuborish
        try:
            # Telefon raqamdan foydalanib Telegram'da qidirish
            # Eslatma: Bu faqat mijoz avval botga /start yuborganda ishlaydi
            await context.bot.send_message(
                chat_id=telefon,
                text=client_text,
                parse_mode="HTML"
            )
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=f"📱 Mijozga xabar yuborildi: {telefon}"
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"⚠️ Mijozga avtomatik xabar yuborib bo'lmadi.\n"
                    f"📞 Qo'lda bog'laning: {telefon}\n\n"
                    f"💬 Yuboriladigan xabar:\n{client_text}"
                ),
                parse_mode="HTML"
            )

        # Bronni ro'yxatdan o'chirish
        pending_brons.pop(bron_id, None)

    elif action == "reject":
        if bron_type == "bron":
            admin_text = f"❌ <b>Bron rad etildi</b>\n📞 {telefon}"
            client_text = (
                f"❌ <b>Afsuski, so'ragan vaqtingizda joy mavjud emas.</b>\n\n"
                f"🎮 <b>Mirage Game Club</b>\n\n"
                f"Boshqa vaqtni tanlang yoki biz bilan bog'laning:\n"
                f"📞 +998 95 888 98 98\n"
                f"✈️ @miragesitebot"
            )
        else:
            admin_text = f"❌ <b>Turnir arizasi rad etildi</b>\n📞 {telefon}"
            client_text = (
                f"❌ <b>Afsuski, turnir arizangiz qabul qilinmadi.</b>\n\n"
                f"Qo'shimcha ma'lumot uchun:\n"
                f"📞 +998 95 888 98 98"
            )

        await query.edit_message_text(admin_text, parse_mode="HTML")

        # Guruhga rad xabari
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=admin_text,
            parse_mode="HTML"
        )

        try:
            await context.bot.send_message(
                chat_id=telefon,
                text=client_text,
                parse_mode="HTML"
            )
        except Exception as e:
            await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=(
                    f"⚠️ Mijozga rad xabari yuborib bo'lmadi.\n"
                    f"📞 Qo'lda xabar bering: {telefon}"
                )
            )

        pending_brons.pop(bron_id, None)

# =====================
# WEBHOOK SERVER (Flask)
# =====================
from flask import Flask, request, jsonify
import threading
import asyncio

flask_app = Flask(__name__)
application = None

@flask_app.route("/webhook/bron", methods=["POST"])
def webhook_bron():
    """Saytdan bron keladi"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data"}), 400

    logger.info(f"Bron keldi: {data}")

    # Async funksiyani sync muhitda chaqirish
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(receive_bron(data, application))
    finally:
        loop.close()

    return jsonify({"status": "ok"}), 200

@flask_app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "running", "bot": "Mirage Game Club Bot"}), 200

def run_flask():
    flask_app.run(host="0.0.0.0", port=8080, debug=False)

# =====================
# BOT ISHGA TUSHIRISH
# =====================
def main():
    global application

    application = Application.builder().token(BOT_TOKEN).build()

    # Handlerlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_callback))

    # Flask ni alohida threadda ishga tushirish
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask webhook server ishga tushdi (port 8080)")

    # Botni polling bilan ishga tushirish
    logger.info("Mirage Game Club Bot ishga tushdi!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
