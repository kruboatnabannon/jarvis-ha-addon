"""
server.py - REST API Server สำหรับ J.A.R.V.I.S. บน Home Assistant (พอร์ต 5050)
เปิดรับคำสั่งจากแอป Home Assistant, มือถือ Android, หรือเครื่อง Mac ในบ้าน
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from ha_brain import JarvisHABrain

app = Flask(__name__)
CORS(app)

brain = JarvisHABrain()

@app.route('/health', methods=['GET'])
def health_check():
    """ตรวจสอบความพร้อมของระบบจาวิสบน Home Assistant"""
    ha_status = brain.ha.is_connected()
    return jsonify({
        "status": "online",
        "assistant": "J.A.R.V.I.S.",
        "platform": "Home Assistant OS (HP t620)",
        "ha_connected": ha_status,
        "gemini_active": brain.model is not None
    })

@app.route('/command', methods=['POST'])
@app.route('/api/chat', methods=['POST'])
def process_command():
    """รับคำสั่งข้อความ/เสียง และตอบกลับเป็นคำตอบของจาวิส"""
    data = request.get_json(force=True, silent=True) or {}
    text = data.get("command") or data.get("text") or data.get("message", "")
    
    if not text:
        return jsonify({"error": "No command provided"}), 400

    print(f"📥 [HA Jarvis Input]: {text}")
    response = brain.process(text)
    print(f"🗣️ [HA Jarvis Output]: {response}")

    return jsonify({
        "status": "success",
        "command": text,
        "response": response
    })

@app.route('/api/notify', methods=['POST'])
def notify():
    """รับการแจ้งเตือนจาก Home Assistant Automation เพื่อให้จาวิสรับรู้หรือพูดเตือน"""
    data = request.get_json(force=True, silent=True) or {}
    msg = data.get("message", "")
    print(f"📢 [HA Notification]: {msg}")
    
    # ส่งต่อให้ Mac พูดเตือนด้วยหาก Mac เปิดอยู่
    if msg:
        brain.forward_to_mac(f"พูดว่า {msg}")

    return jsonify({"status": "received", "message": msg})

if __name__ == '__main__':
    print("🚀 [J.A.R.V.I.S.]: กำลังเปิดบริการบนพอร์ต 5050...")
    app.run(host='0.0.0.0', port=5050)
