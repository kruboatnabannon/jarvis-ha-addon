"""
ha_brain.py - สมองของ J.A.R.V.I.S. บน Home Assistant
ประมวลผลคำสั่ง ควบคุมอุปกรณ์บ้านอัจฉริยะ และส่งต่องานไปยังเครื่อง Mac
"""

import os
import re
import datetime
import requests
from ha_client import HomeAssistantClient

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

class JarvisHABrain:
    def __init__(self):
        self.ha = HomeAssistantClient()
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.mac_agent_url = os.getenv("MAC_AGENT_URL", "http://192.168.1.100:5050").rstrip("/")
        self.model = None

        if HAS_GEMINI and self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-2.5-flash")
                print("🧠 [J.A.R.V.I.S. Brain]: เชื่อมต่อสมอง Gemini Flash บน Home Assistant สำเร็จ!")
            except Exception as e:
                print(f"⚠️ [J.A.R.V.I.S. Brain]: ไม่สามารถเปิดใช้ Gemini: {e}")

    def get_time_info(self, query: str = "") -> str:
        """บอกเวลา วันที่ ตามมาตรฐานจาวิส"""
        now = datetime.datetime.now()
        thai_days = ["จันทร์", "อังคาร", "พุธ", "พฤหัสบดี", "ศุกร์", "เสาร์", "อาทิตย์"]
        thai_months = [
            "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
            "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม"
        ]
        day_name = thai_days[now.weekday()]
        month_name = thai_months[now.month - 1]
        year_be = now.year + 543
        time_str = now.strftime("%H นาฬิกา %M นาที")

        clean_q = query.lower() if query else ""
        if any(w in clean_q for w in ["วันอะไร", "วันที่เท่าไหร่", "วันที่", "เดือนอะไร", "ปีอะไร"]):
            return f"วันนี้วัน{day_name}ที่ {now.day} {month_name} พ.ศ. {year_be} ครับเจ้านาย"
        return f"ตอนนี้เวลา {time_str} ครับเจ้านาย"

    def handle_homeassistant_action(self, text: str) -> str:
        """ตรวจสอบและสั่งการอุปกรณ์ใน Home Assistant โดยตรง"""
        clean = text.lower().strip()

        # 1. สั่งเปิด/ปิดไฟ หรือ สวิตช์
        action = None
        if any(w in clean for w in ["เปิด", "turn on", "on"]):
            action = "turn_on"
        elif any(w in clean for w in ["ปิด", "turn off", "off"]):
            action = "turn_off"

        if action:
            # ดึงรายการอุปกรณ์ทั้งหมดจาก Home Assistant
            states = self.ha.get_all_states()
            target_entity = None
            target_name = ""

            for s in states:
                entity_id = s.get("entity_id", "")
                friendly_name = s.get("attributes", {}).get("friendly_name", "").lower()
                domain = entity_id.split(".")[0]

                if domain not in ["light", "switch", "climate", "fan", "cover"]:
                    continue

                # ตรวจสอบชื่ออุปกรณ์ตรงกับคำสั่ง
                if friendly_name and friendly_name in clean:
                    target_entity = entity_id
                    target_name = s.get("attributes", {}).get("friendly_name", friendly_name)
                    break

            if target_entity:
                domain = target_entity.split(".")[0]
                ok, res = self.ha.call_service(domain, action, {"entity_id": target_entity})
                action_th = "เปิด" if action == "turn_on" else "ปิด"
                if ok:
                    return f"{action_th}{target_name}ให้เรียบร้อยแล้วครับเจ้านาย"
                else:
                    return f"ไม่สามารถ{action_th}{target_name}ได้ครับ: {res}"

        return None

    def forward_to_mac(self, text: str) -> str:
        """ส่งคำสั่งควบคุมเครื่อง Mac (เช่น เล่นเพลง YouTube / ปรับเสียง) ไปยัง Mac Agent"""
        try:
            r = requests.post(f"{self.mac_agent_url}/command", json={"command": text}, timeout=4.0)
            if r.status_code == 200:
                data = r.json()
                return data.get("response", "ส่งคำสั่งไปยังเครื่อง Mac เรียบร้อยแล้วครับเจ้านาย")
        except Exception as e:
            return f"ไม่สามารถติดต่อเครื่อง Mac ({self.mac_agent_url}) ได้ครับ: เครื่อง Mac อาจปิดอยู่"
        return None

    def process(self, text: str) -> str:
        """ประมวลผลคำสั่งข้อความ/เสียง และส่งคืนคำตอบของจาวิส"""
        clean = text.strip()
        clean_lower = clean.lower()

        # 1. ทักทาย
        if any(w in clean_lower for w in ["สวัสดี", "หวัดดี", "ฮัลโหล", "ดีครับ"]):
            return "สวัสดีครับเจ้านาย จาวิสพร้อมรับใช้ตลอด 24 ชั่วโมงบน Home Assistant แล้วครับ"

        # 2. เวลา / วันที่
        if any(w in clean_lower for w in ["กี่โมง", "เวลา", "วันอะไร", "วันที่", "เดือน", "ปี"]):
            return self.get_time_info(clean)

        # 3. คำสั่งสำหรับ Mac โดยตรง (เปิดเพลง, YouTube, ข้ามโฆษณา)
        if any(w in clean_lower for w in ["เพลง", "youtube", "ยูทูป", "ข้ามโฆษณา", "เต็มจอ"]):
            mac_res = self.forward_to_mac(clean)
            if mac_res:
                return mac_res

        # 4. ตรวจสอบคำสั่ง Home Assistant (เปิด/ปิดไฟ แอร์ สวิตช์)
        ha_res = self.handle_homeassistant_action(clean)
        if ha_res:
            return ha_res

        # 5. ใช้ Gemini ประมวลผลบทสนทนาอัจฉริยะรอบด้าน
        if self.model:
            try:
                system_prompt = (
                    "คุณคือ J.A.R.V.I.S. ผู้ช่วยส่วนตัวรอบด้านของเจ้านาย "
                    "คุณกำลังรันอยู่บนเซิร์ฟเวอร์ Home Assistant ประจำบ้าน "
                    "ตอบกระชับ 1-2 ประโยค สุภาพ สุขุม ลงท้าย 'ครับเจ้านาย' เสมอ"
                )
                response = self.model.generate_content([system_prompt, clean])
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                print(f"⚠️ [Gemini Error]: {e}")

        return f"รับทราบครับเจ้านาย: {clean}"
