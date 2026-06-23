import logging
import time
import requests
import threading
import json
from flask import Flask, request, jsonify

BOT_TOKEN = "8516151329:AAEHVVwBcj4fAm_WaNL6Rpb6uDW2vSxIeBA"
ADMIN_ID = 824354773
GROUP_ID = -1004327610337
API = f"https://api.telegram.org/bot{BOT_TOKEN}"

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
pending_brons = {}

def tg_send(chat_id, text, markup=None):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if markup:
        payload["reply_markup"] = json.dumps(markup)
    try:
        r = requests.post(f"{API}/sendMessage", json=payload, timeout=10)
        res = r.json()
        logger.info(f"send {chat_id}: {res.get('ok')} {res.get('description','')}")
        return res
    except Exception as e:
        logger.error(f"tg_send xato: {e}")

def tg_edit(chat_id, message_id, text):
    try:
        requests.post(f"{API}/editMessageText", json={"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}, timeout=10)
    except Exception as e:
        logger.error(f"tg_edit xato: {e}")

def tg_answer(cq_id):
    try:
        requests.post(f"{API}/answerCallbackQuery", json={"callback_query_id": cq_id}, timeout=5)
    except:
        pass

def handle_new_bron(data):
    bron_type = data.get("type", "bron")
    ts = int(time.time())
    tel = data.get('telefon', 'x').replace('+', '').replace(' ', '')
    bron_id = f"{bron_type}_{tel}_{ts}"
    pending_brons[bron_id] = data
    if bron_type == "bron":
        text = (f"🎮 <b>YANGI BRON</b>\n\n"
                f"📍 Zona: <b>{data.get('zona','—')}</b>\n"
                f"👥 Odamlar: <b>{data.get('odam','—')}</b>\n"
                f"📅 Qachon: <b>{data.get('sana','—')}</b>\n"
                f"🕐 Soat: <b>{data.get('soat','—')}</b>\n"
                f"📞 Telefon: <b>{data.get('telefon','—')}</b>")
        b1, b2 = "✅ Tasdiqlash", "❌ Rad etish"
    else:
        text = (f"🏆 <b>TURNIR ARIZASI</b>\n\n"
                f"👤 Ism: <b>{data.get('ism','—')}</b>\n"
                f"⚔️ Jamoa: <b>{data.get('jamoa','—')}</b>\n"
                f"🎯 Faceit: <b>{data.get('faceit','—')}</b>\n"
                f"🏅 Premier: <b>{data.get('premier','—')}</b>\n"
                f"✈️ Telegram: <b>{data.get('telegram','—')}</b>\n"
                f"📞 Telefon: <b>{data.get('telefon','—')}</b>")
        b1, b2 = "✅ Qabul qilish", "❌ Rad etish"
    markup = {"inline_keyboard": [[{"text": b1, "callback_data": f"confirm_{bron_id}"}, {"text": b2, "callback_data": f"reject_{bron_id}"}]]}
    tg_send(ADMIN_ID, text, markup)
    tg_send(GROUP_ID, text + "\n\n⏳ <i>Admin ko'rib chiqmoqda...</i>")

def handle_callback(upd):
    cq = upd.get("callback_query", {})
    if not cq:
        return
    tg_answer(cq["id"])
    cb = cq.get("data", "")
    msg = cq.get("message", {})
    chat_id = msg.get("chat", {}).get("id")
    message_id = msg.get("message_id")
    if "_" not in cb:
        return
    action, bron_id = cb.split("_", 1)
    bron = pending_brons.get(bron_id)
    if not bron:
        tg_edit(chat_id, message_id, "⚠️ Bron topilmadi.")
        return
    tel = bron.get("telefon", "")
    bron_type = bron.get("type", "bron")
    if action == "confirm":
        if bron_type == "bron":
            amsg = f"✅ <b>BRON TASDIQLANDI</b>\n\n📍 {bron.get('zona')} | {bron.get('odam')}\n📅 {bron.get('sana')} 🕐 {bron.get('soat')}\n📞 {tel}"
            cmsg = f"✅ <b>Broningiz tasdiqlandi!</b>\n\n🎮 Mirage Game Club\n📍 {bron.get('zona')}\n👥 {bron.get('odam')}\n📅 {bron.get('sana')} soat {bron.get('soat')}\n\nSizi kutamiz! 🕹\n📞 +998 95 888 98 98"
        else:
            amsg = f"✅ <b>TURNIR QABUL</b>\n👤 {bron.get('ism')} | {bron.get('jamoa')}\n📞 {tel}"
            cmsg = f"🏆 <b>Turnir arizangiz qabul qilindi!</b>\n\nOmad! 🎯\n📞 +998 95 888 98 98"
        tg_edit(chat_id, message_id, amsg)
        tg_send(GROUP_ID, amsg)
        r = tg_send(tel, cmsg)
        if not r or not r.get("ok"):
            tg_send(ADMIN_ID, f"⚠️ Mijozga xabar yuborilmadi.\n📞 {tel}\n\n{cmsg}")
    elif action == "reject":
        if bron_type == "bron":
            amsg = f"❌ <b>Bron rad etildi</b>\n📞 {tel}"
            cmsg = "❌ <b>So'ragan vaqtda joy yo'q.</b>\n\nBoshqa vaqt:\n📞 +998 95 888 98 98"
        else:
            amsg = f"❌ <b>Turnir rad etildi</b>\n📞 {tel}"
            cmsg = "❌ <b>Arizangiz qabul qilinmadi.</b>\n📞 +998 95 888 98 98"
        tg_edit(chat_id, message_id, amsg)
        tg_send(GROUP_ID, amsg)
        r = tg_send(tel, cmsg)
        if not r or not r.get("ok"):
            tg_send(ADMIN_ID, f"⚠️ Mijozga xabar yuborilmadi.\n📞 {tel}")
    pending_brons.pop(bron_id, None)

def polling_loop():
    offset = None
    logger.info("Polling boshlandi!")
    while True:
        try:
            params = {"timeout": 30, "allowed_updates": ["callback_query", "message"]}
            if offset:
                params["offset"] = offset
            r = requests.get(f"{API}/getUpdates", params=params, timeout=35)
            data = r.json()
            if not data.get("ok"):
                time.sleep(3)
                continue
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                if "callback_query" in upd:
                    handle_callback(upd)
                elif "message" in upd:
                    msg = upd["message"]
                    txt = msg.get("text", "")
                    cid = msg["chat"]["id"]
                    if txt.startswith("/start"):
                        tg_send(cid, "👋 Salom! Mirage Game Club boti.\n\n🎮 miragegameclub.netlify.app\n📞 +998 95 888 98 98")
                    elif txt.startswith("/chatid"):
                        tg_send(ADMIN_ID, f"📍 Chat ID: <code>{cid}</code>\nTuri: {msg['chat']['type']}")
        except Exception as e:
            logger.error(f"Polling xato: {e}")
            time.sleep(5)

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

if __name__ == "__main__":
    threading.Thread(target=polling_loop, daemon=True).start()
    logger.info("Flask ishga tushdi!")
    flask_app.run(host="0.0.0.0", port=8080, debug=False, use_reloader=False)
