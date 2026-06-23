import logging
import time
import requests
import threading
from flask import Flask, request, jsonify
from flask import Flask, request, jsonify
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import asyncio

BOT_TOKEN = "8516151329:AAEHVVwBcj4fAm_WaNL6Rpb6uDW2vSxIeBA"
ADMIN_ID = 824354773
GROUP_ID = -1004327610337
TG_API = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

pending_brons = {}

# =====================
# TELEGRAM API — oddiy requests bilan (threaddan xavfsiz)
# =====================
def tg_send(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        import json
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        r = requests.post(f"{TG_API}/sendMessage", json=payload, timeout=10)
        logger.info(f"sendMessage -> {chat_id}: {r.status_code} {r.text[:200]}")
        return r.json()
    except Exception as e:
        logger.error(f"tg_send xato: {e}")
        return None

def tg_edit(chat_id, message_id, text):
    try:
        r = requests.post(f"{TG_API}/editMessageText", json={
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML"
        }, timeout=10)
        return r.json()
    except Exception as e:
        logger.error(f"tg_edit xato: {e}")

def tg_answer(callback_query_id):
    try:
        requests.post(f"{TG_API}/answerCallbackQuery", json={"callback_query_id": callback_query_id}, timeout=5)
    except:
        pass

# =====================
# BRON KELGANDA
# =====================
def handle_new_bron(data: dict):
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

    markup = {
        "inline_keyboard": [[
            {"text": btn1, "callback_data": f"confirm_{bron_id}"},
            {"text": btn2, "callback_data": f"reject_{bron_id}"}
        ]]
    }

    # Adminга
    tg_send(ADMIN_ID, text, markup)

    # Guruhga
    group_text = text + "\n\n⏳ <i>Admin ko'rib chiqmoqda...</i>"
    result = tg_send(GROUP_ID, group_text)
    if result and not result.get("ok"):
        logger.error(f"Guruhga yuborishda xato: {result}")

# =====================
# POLLING — callback handler
# =====================
def handle_callback(update_data):
    cq = update_data.get("callback_query", {})
    if not cq:
        return

    tg_answer(cq["id"])
    cb_data = cq.get("data", "")
    msg = cq.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")

    if "_" not in cb_data:
        return

    action, bron_id = cb_data.split("_", 1)
    bron = pending_brons.get(bron_id)

    if not bron:
        tg_edit(chat_id, message_id, "⚠️ Bron topilmadi.")
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
            client_msg = f"🏆 <b>Turnir arizangiz qabul qilindi!</b>\n\nOmad! 🎯\n📞 +998 95 888 98 98"

        tg_edit(chat_id, message_id, admin_msg)
        tg_send(GROUP_ID, admin_msg)
        result = tg_send(tel, client_msg)
        if not result or not result.get("ok"):
            tg_send(ADMIN_ID, f"⚠️ Mijozga xabar yuborilmadi.\n📞 {tel}\n\n{client_msg}")

    elif action == "reject":
        if bron_type == "bron":
            admin_msg = f"❌ <b>Bron rad etildi</b>\n📞 {tel}"
            client_msg = f"❌ <b>So'ragan vaqtda joy yo'q.</b>\n\nBoshqa vaqt:\n📞 +998 95 888 98 98"
        else:
            admin_msg = f"❌ <b>Turnir rad etildi</b>\n📞 {tel}"
            client_msg = f"❌ <b>Arizangiz qabul qilinmadi.</b>\n📞 +998 95 888 98 98"

        tg_edit(chat_id, message_id, admin_msg)
        tg_send(GROUP_ID, admin_msg)
        result = tg_send(tel, client_msg)
        if not result or not result.get("ok"):
            tg_send(ADMIN_ID, f"⚠️ Mijozga xabar yuborilmadi.\n📞 {tel}")

    pending_brons.pop(bron_id, None)

# =====================
# POLLING LOOP
# =====================
def polling_loop():
    offset = None
    logger.info("Polling boshlandi!")
    while True:
        try:
            params = {"timeout": 30, "allowed_updates": ["callback_query", "message"]}
            if offset:
                params["offset"] = offset
            r = requests.get(f"{TG_API}/getUpdates", params=params, timeout=35)
            data = r.json()
            if not data.get("ok"):
                time.sleep(3)
                continue
            for update in data.get("result", []):
                offset = update["update_id"] + 1
                if "callback_query" in update:
                    handle_callback(update)
                elif "message" in update:
                    msg = update["message"]
                    text = msg.get("text", "")
                    chat_id = msg["chat"]["id"]
                    if text.startswith("/start"):
                        tg_send(chat_id, "👋 Salom! Mirage Game Club boti.\n\n🎮 miragegameclub.netlify.app\n📞 +998 95 888 98 98")
                    elif text.startswith("/chatid"):
                        tg_send(ADMIN_ID, f"📍 Chat ID: <code>{chat_id}</code>\nTuri: {msg['chat']['type']}")
        except Exception as e:
            logger.error(f"Polling xato: {e}")
            time.sleep(5)

# =====================
# FLASK
# =====================
flask_app = Flask(__name__)

@flask_app.route("/webhook/bron", methods=["POST"])
def webhook_bron():
    data = request.get_json()
    if not data:
        return jsonify({"error": "no data"}), 400
    logger.info(f"Bron keldi: {data}")
    threading.Thread(target=handle_new_bron, args=(data,), daemon=True).start()
    return jsonify({"status": "ok"}), 200

@flask_app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200

# =====================
# MAIN
# =====================
if __name__ == "__main__":
    polling_thread = threading.Thread(target=polling_loop, daemon=True)
    polling_thread.start()

    logger.info("Flask ishga tushdi!")
    flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
