# 🤖 J.A.R.V.I.S. Brain Core — Home Assistant Local Add-on (HP t620 / amd64)

Add-on สำหรับติดตั้งระบบ **J.A.R.V.I.S. (จาวิส)** ให้รันเป็นสมองกลางตลอด 24 ชั่วโมงบน **Home Assistant OS** บนเครื่อง HP t620 (192.168.1.33)

---

## 📁 โครงสร้างโฟลเดอร์ Add-on
```
jarvis/
├── config.yaml          # กำหนดสิทธิ์ amd64 และพอร์ต 5050
├── Dockerfile           # สร้าง Container Python 3.11 บน x86_64
├── requirements.txt     # ไลบรารี Python
├── run.sh               # สคริปต์รันอัตโนมัติ
├── server.py            # API Server (Flask) พอร์ต 5050
├── ha_brain.py          # สมองคำนวณและตอบคำถาม
└── ha_client.py         # ตัวเชื่อมต่อ Home Assistant Core API
```

---

## 🚀 ขั้นตอนการติดตั้งบนเครื่อง Home Assistant (HP t620)

### วิธีที่ 1: ติดตั้งผ่าน Samba Share (ง่ายที่สุด)
1. ใน Home Assistant ติดตั้ง Add-on ชื่อ **Samba share**
2. บน Mac เปิด Finder กด `Cmd + K` แล้วพิมพ์:
   `smb://192.168.1.33/addons`
3. คัดลอกโฟลเดอร์ `ha-addon-jarvis` จาก Mac ไปวางในโฟลเดอร์ `addons` แล้วเปลี่ยนชื่อโฟลเดอร์เป็น `jarvis`
4. ไปที่หน้าเว็บ Home Assistant:
   **Settings (การตั้งค่า) → Add-ons (ส่วนเสริม) → Add-on Store (ที่มุมขวาล่าง)**
5. กดปุ่มจุดสามจุดมุมบนขวา `...` แล้วเลือก **Check for updates**
6. เลื่อนดูด้านบนสุดจะพบหัวข้อ **Local add-ons** และมี **J.A.R.V.I.S. Brain Core** ปรากฏขึ้นมา!
7. กด **Install** → ติ๊ก **Start on boot** และ **Watchdog** → กด **Start**

### วิธีที่ 2: ติดตั้งผ่าน Studio Code Server / File Editor
1. เปิด **Studio Code Server** บน Home Assistant
2. ไปที่โฟลเดอร์ `/addons/` แล้วสร้างโฟลเดอร์ใหม่ชื่อ `jarvis`
3. วางไฟล์ทั้งหมดลงใน `/addons/jarvis/`
4. ไปที่ Add-on Store กด **Check for updates** แล้วกด **Install**

---

## ⚙️ การตั้งค่าในแท็บ Configuration (ของ Add-on)
* **gemini_api_key:** นำ API Key ของ Gemini มาวาง (ถ้ามี) เพื่อเปิดโหมดถาม-ตอบรอบรู้ระดับโลก
* **mac_agent_url:** IP ของเครื่อง Mac ในบ้าน เช่น `http://192.168.1.xxx:5050` เพื่อให้จาวิสบน HA สั่งเปิดเพลง YouTube บน Mac ได้
