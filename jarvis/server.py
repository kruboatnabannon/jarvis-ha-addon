"""
server.py - REST API Server สำหรับ J.A.R.V.I.S. บน Home Assistant (พอร์ต 5050)
ทำหน้าที่เป็นเซิร์ฟเวอร์สมองกลางตลอด 24 ชั่วโมง
รองรับมาตรฐาน REST API เดียวกันกับ Mac สำหรับการเชื่อมต่อของแอป Android และอุปกรณ์ในบ้าน
"""

import os
import json
import urllib.parse
from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from ha_brain import JarvisHABrain

app = Flask(__name__)
CORS(app)

brain = JarvisHABrain()

VERSION_INFO = {
    "status": "success",
    "version": "2.7.1",
    "version_code": 271,
    "release_name": "HA 24/7 Central Brain Core (Tailscale & Mobile Sync)",
    "platform": "Home Assistant OS",
    "server": "Home Assistant J.A.R.V.I.S. Central Brain"
}

@app.route('/', methods=['GET'])
@app.route('/health', methods=['GET'])
@app.route('/api/health', methods=['GET'])
def health_check():
    """ตรวจสอบความพร้อมของระบบจาวิสบน Home Assistant (รองรับ Mobile App Ping)"""
    ha_status = brain.ha.is_connected()
    return jsonify({
        "status": "online",
        "assistant": "J.A.R.V.I.S.",
        "platform": "Home Assistant OS",
        "version": VERSION_INFO["version"],
        "ha_connected": ha_status,
        "gemini_active": brain.model is not None,
        "active_model": brain.active_model_name
    })

@app.route('/version', methods=['GET'])
@app.route('/api/version', methods=['GET'])
def get_version():
    """ส่งข้อมูลเวอร์ชันระบบให้แอปมือถือ"""
    return jsonify(VERSION_INFO)

@app.route('/command', methods=['POST'])
@app.route('/api/command', methods=['POST'])
@app.route('/api/chat', methods=['POST'])
def process_command():
    """รับคำสั่งข้อความ/เสียง และตอบกลับเป็นคำตอบของจาวิส (รูปแบบเดียวกับ Mac API)"""
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("command") or data.get("text") or data.get("q") or data.get("message", "")

    if not text:
        # Fallback query params if any
        text = request.args.get("text") or request.args.get("q") or ""

    if not text:
        return jsonify({"status": "error", "message": "No command provided"}), 400

    print(f"📥 [HA Jarvis Input]: {text}")
    response = brain.process(text)
    print(f"🗣️ [HA Jarvis Output]: {response}")

    return jsonify({
        "status": "success",
        "command": text,
        "response": response,
        "audio_url": f"/api/tts?text={urllib.parse.quote(response)}"
    })

@app.route('/api/arbitration/claim', methods=['POST'])
def arbitration_claim():
    """รองรับ endpoint การตัดสินคำสั่งข้ามอุปกรณ์ เพื่อให้แอปมือถือทำงานได้อย่างราบรื่น"""
    data = request.get_json(force=True, silent=True) or {}
    cmd = data.get("command", "")
    return jsonify({
        "status": "execute",
        "execute": True,
        "winner": "HA_CENTRAL",
        "action": "execute_local",
        "message": f"Home Assistant ศูนย์กลางรับคำสั่ง: {cmd}"
    })

@app.route('/api/notify', methods=['POST'])
def notify():
    """รับการแจ้งเตือนจาก Home Assistant Automation เพื่อให้จาวิสรับรู้หรือพูดเตือน"""
    data = request.get_json(force=True, silent=True) or {}
    msg = data.get("message", "")
    print(f"📢 [HA Notification]: {msg}")

    if msg:
        brain.forward_to_mac(f"พูดว่า {msg}")

    return jsonify({"status": "received", "message": msg})

if __name__ == '__main__':
    print("🚀 [J.A.R.V.I.S. Home Assistant]: เปิดบริการเซิร์ฟเวอร์กลาง 24 ชม. บนพอร์ต 5050...")
    app.run(host='0.0.0.0', port=5050)
