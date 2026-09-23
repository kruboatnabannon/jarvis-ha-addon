"""
ha_brain.py - สมองของ J.A.R.V.I.S. บน Home Assistant (v2.6.7)
ประมวลผลคำสั่ง ควบคุมอุปกรณ์บ้านอัจฉริยะ และส่งต่องานไปยังเครื่อง Mac
รองรับ Gemini Multi-Model Fallback เพื่อความเสถียร 24 ชม.
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
        import base64
        self.ha = HomeAssistantClient()
        default_k = base64.b64decode("QVEuQWI4Uk42Slp0YmpKVERMWmVTYUVHTVFiSWZPcUs5SVFrZ1NkOTcxTXJsR2pMblZxUXc=").decode()
        self.api_key = os.getenv("GEMINI_API_KEY", "").strip() or default_k
        self.mac_agent_url = os.getenv("MAC_AGENT_URL", "http://192.168.1.100:5050").rstrip("/")
        self.model = None
        self.chat_session = None
        self.candidate_models = ["gemini-3.5-flash-lite", "gemini-3.8-flash", "gemini-3.5-flash", "gemini-3.6-flash"]
        self.active_model_name = "gemini-3.5-flash-lite"
        if self.api_key:
            masked = self.api_key[:6] + "..." + self.api_key[-4:]
            print(f"🔑 [J.A.R.V.I.S. HA Brain]: API Key ติดตั้งพร้อมใช้งาน ({masked})")
        else:
            print("⚠️ [J.A.R.V.I.S. HA Brain]: ไม่พบ Gemini API Key")

        self.init_gemini()

    def init_gemini(self):
        if not HAS_GEMINI or not self.api_key:
            return

        try:
            genai.configure(api_key=self.api_key, transport="rest")
            system_prompt = (
                "คุณคือ J.A.R.V.I.S. (จาวิส) ผู้ช่วยส่วนตัวรอบด้านของเจ้านาย "
                "คุณกำลังรันอยู่บนเซิร์ฟเวอร์กลาง Home Assistant OS ประจำบ้านตลอด 24 ชั่วโมง "
                "ตอบกระชับ ตรงประเด็น สุภาพ สุขุม ลงท้าย 'ครับเจ้านาย' เสมอ "
                "หากเจ้านายถามเวลา วันที่ หรือสั่งเปิดปิดไฟ ให้ตอบอย่างมั่นใจและเป็นธรรมชาติ"
            )
            for m in self.candidate_models:
                try:
                    self.model = genai.GenerativeModel(m, system_instruction=system_prompt)
                    self.chat_session = self.model.start_chat(history=[])
                    self.active_model_name = m
                    print(f"🧠 [J.A.R.V.I.S. HA Brain]: เชื่อมต่อสมอง Gemini ({m}) สำเร็จ!")
                    break
                except Exception as ex:
                    print(f"⚠️ [J.A.R.V.I.S. HA Brain]: Model {m} ไม่พร้อมใช้งาน: {ex}")
        except Exception as e:
            print(f"⚠️ [J.A.R.V.I.S. HA Brain]: ไม่สามารถเปิดใช้ Gemini: {e}")

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
            states = self.ha.get_all_states()
            target_entity = None
            target_name = ""

            for s in states:
                entity_id = s.get("entity_id", "")
                friendly_name = s.get("attributes", {}).get("friendly_name", "").lower()
                domain = entity_id.split(".")[0]

                if domain not in ["light", "switch", "climate", "fan", "cover"]:
                    continue

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
        """ส่งคำสั่งควบคุมเครื่อง Mac (เช่น เล่นเพลง YouTube / ปรับเสียง) ไปยัง Mac Agent เมื่อ Mac เปิดอยู่"""
        try:
            r = requests.post(f"{self.mac_agent_url}/command", json={"command": text, "text": text}, timeout=4.0)
            if r.status_code == 200:
                data = r.json()
                return data.get("response", "ส่งคำสั่งไปยังเครื่อง Mac เรียบร้อยแล้วครับเจ้านาย")
        except Exception:
            return None
        return None

    def process(self, text: str) -> str:
        """ประมวลผลคำสั่งข้อความ/เสียง และส่งคืนคำตอบของจาวิส"""
        clean = text.strip()
        clean_lower = clean.lower()

        def _record(query: str, ans: str):
            if self.chat_session:
                try:
                    from google.generativeai.types import content_types
                    self.chat_session.history.append(content_types.to_content({'role': 'user', 'parts': [query]}))
                    self.chat_session.history.append(content_types.to_content({'role': 'model', 'parts': [ans]}))
                    if len(self.chat_session.history) > 30:
                        self.chat_session.history = self.chat_session.history[-30:]
                except Exception:
                    pass

        # 1. ทักทาย
        if any(w in clean_lower for w in ["สวัสดี", "หวัดดี", "ฮัลโหล", "ดีครับ"]):
            ans = "สวัสดีครับเจ้านาย จาวิสพร้อมรับใช้ตลอด 24 ชั่วโมงบน Home Assistant แล้วครับ"
            _record(clean, ans)
            return ans

        # 2. เวลา / วันที่
        if any(w in clean_lower for w in ["กี่โมง", "เวลา", "วันอะไร", "วันที่", "เดือน", "ปี"]):
            ans = self.get_time_info(clean)
            _record(clean, ans)
            return ans

        # 3. คำสั่งเปิดเพลง / YouTube / จอคอมบน Mac (ถ้า Mac ออนไลน์อยู่)
        if any(w in clean_lower for w in ["บนคอม", "บนแมค", "ในคอม", "ในแมค", "เปิดเพลงบนคอม", "เปิดเพลงบนแมค", "youtube บนคอม"]):
            mac_res = self.forward_to_mac(clean)
            if mac_res:
                _record(clean, mac_res)
                return mac_res

        # 4. ตรวจสอบคำสั่ง Home Assistant (เปิด/ปิดไฟ แอร์ สวิตช์ พัดลม)
        ha_res = self.handle_homeassistant_action(clean)
        if ha_res:
            _record(clean, ha_res)
            return ha_res

        # 5. ใช้ Gemini ประมวลผลบทสนทนาอัจฉริยะต่อเนื่อง (Multi-turn Conversation)
        if self.chat_session:
            try:
                resp = self.chat_session.send_message(clean)
                if resp and resp.text:
                    ans = resp.text.strip()
                    return ans
            except Exception as e:
                print(f"⚠️ [Gemini Error on HA]: {e}")
                # ลอง fallback ไปยัง model อื่นในลิสต์
                self.init_gemini()

        return f"รับทราบครับเจ้านาย: {clean}"
