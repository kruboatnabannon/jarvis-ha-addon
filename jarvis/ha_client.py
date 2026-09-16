"""
ha_client.py - โมดูลสื่อสารกับ Home Assistant Core API
รองรับทั้งการรันในฐานะ Local Add-on (ผ่าน SUPERVISOR_TOKEN) 
และการรันภายนอก (ผ่าน Long-Lived Access Token)
"""

import os
import requests

class HomeAssistantClient:
    def __init__(self, base_url: str = None, token: str = None):
        # หากรันเป็น Add-on ใน HAOS: Supervisor จะส่ง SUPERVISOR_TOKEN มาให้โดยอัตโนมัติ
        supervisor_token = os.getenv("SUPERVISOR_TOKEN")
        
        if supervisor_token:
            self.base_url = "http://supervisor/core/api"
            self.token = supervisor_token
            self.is_addon = True
        else:
            self.base_url = (base_url or os.getenv("HA_URL", "http://192.168.1.33:8123")).rstrip("/") + "/api"
            self.token = token or os.getenv("HA_TOKEN", "")
            self.is_addon = False

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }

    def is_connected(self) -> bool:
        """ตรวจสอบสถานะการเชื่อมต่อกับ Home Assistant Core"""
        try:
            r = requests.get(self.base_url, headers=self.headers, timeout=3.0)
            return r.status_code == 200
        except Exception:
            return False

    def get_all_states(self):
        """ดึงสถานะของอุปกรณ์ทั้งหมดในบ้าน"""
        try:
            r = requests.get(f"{self.base_url}/states", headers=self.headers, timeout=5.0)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"⚠️ [HA Client]: ไม่สามารถดึงสถานะอุปกรณ์: {e}")
        return []

    def get_entity_state(self, entity_id: str):
        """ดึงสถานะของอุปกรณ์เฉพาะตัว เช่น light.living_room"""
        try:
            r = requests.get(f"{self.base_url}/states/{entity_id}", headers=self.headers, timeout=3.0)
            if r.status_code == 200:
                return r.json()
        except Exception as e:
            print(f"⚠️ [HA Client]: ดึงสถานะ {entity_id} ไม่สำเร็จ: {e}")
        return None

    def call_service(self, domain: str, service: str, service_data: dict = None):
        """
        สั่งการทำงานของอุปกรณ์ใน Home Assistant
        เช่น domain='light', service='turn_on', service_data={'entity_id': 'light.bedroom'}
        """
        url = f"{self.base_url}/services/{domain}/{service}"
        try:
            r = requests.post(url, headers=self.headers, json=service_data or {}, timeout=5.0)
            if r.status_code in [200, 201]:
                return True, r.json()
            return False, f"HTTP Error {r.status_code}: {r.text}"
        except Exception as e:
            return False, str(e)

    def trigger_scene(self, scene_name: str):
        """สั่งเปิด Scene (ซีนบรรยากาศ) ในบ้าน"""
        return self.call_service("scene", "turn_on", {"entity_id": f"scene.{scene_name}"})

    def toggle_switch(self, entity_id: str):
        """สลับเปิด/ปิด สวิตช์หรือปลั๊ก"""
        domain = entity_id.split(".")[0] if "." in entity_id else "switch"
        return self.call_service(domain, "toggle", {"entity_id": entity_id})

    def set_climate_temperature(self, entity_id: str, temperature: float):
        """ปรับอุณหภูมิแอร์"""
        return self.call_service("climate", "set_temperature", {
            "entity_id": entity_id,
            "temperature": temperature
        })
