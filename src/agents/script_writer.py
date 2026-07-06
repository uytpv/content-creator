import os
import json
import requests
from typing import List, Optional
from pydantic import BaseModel, Field
from anthropic import Anthropic

class ChartData(BaseModel):
    title: str = Field(description="Tiêu đề hiển thị trên biểu đồ, ví dụ: 'So sánh lực lượng quân sự (nghìn người)'")
    labels: List[str] = Field(description="Danh sách nhãn trục X (tối đa 4 nhãn, ví dụ: ['Pháp', 'Việt Minh'])")
    values: List[float] = Field(description="Danh sách số liệu trục Y tương ứng")

class SceneEffect(BaseModel):
    type: str = Field(description="Hiệu ứng chuyển động hình ảnh: 'zoom_in', 'zoom_out' hoặc 'static'")
    speed: float = Field(description="Tốc độ hiệu ứng zoompan, khuyên dùng từ 0.001 đến 0.0015")

class Scene(BaseModel):
    scene_id: str = Field(description="Mã phân cảnh, định dạng scene_1, scene_2, scene_3...")
    voice_text: str = Field(description="Đoạn thuyết minh nói bằng tiếng Việt (mỗi phân cảnh khoảng 1-2 câu ngắn gọn, súc tích, tối đa 30 từ)")
    visual_prompt: str = Field(description="Mô tả chi tiết hình ảnh minh họa cho phân cảnh bằng tiếng Anh để sinh ảnh tốt nhất, ví dụ: 'A majestic cat sitting on a throne, warm lighting'")
    effect: SceneEffect
    chart_data: Optional[ChartData] = Field(None, description="Điền thông tin nếu phân cảnh này có so sánh số liệu hoặc biểu đồ, nếu không cần thì để trống")

class VideoTimeline(BaseModel):
    project_title: str = Field(description="Tiêu đề chính của dự án video")
    voice_code: str = Field(description="Mã giọng đọc Edge-TTS tiếng Việt mặc định là 'vi-VN-HoaiMyNeural' (Nữ Nam Bộ) hoặc 'vi-VN-NamMinhNeural' (Nam Nam Bộ)")
    visual_style: str = Field(description="Phong cách mỹ thuật chung cho toàn bộ hình ảnh video, ví dụ: 'cinematic painting, oil canvas style, masterpiece'")
    scenes: List[Scene]

def generate_script_timeline(topic: str, provider: str, api_key: str, feedback: str = None) -> dict:
    """
    Sáng tác kịch bản JSON timeline dựa trên nhà cung cấp AI được chỉ định:
    'gemini', 'openai', 'claude', hoặc 'local' (Ollama).
    """
    system_prompt = (
        "Bạn là chuyên gia biên tập video và nhà sáng tạo nội dung viral chuyên nghiệp.\n"
        "Hãy viết kịch bản video tiếng Việt ngắn (khoảng 30-45 giây, gồm 4 phân cảnh) dựa trên chủ đề người dùng yêu cầu.\n"
        "Đối với mỗi phân cảnh, hãy cung cấp một mô tả hình ảnh cực kỳ chi tiết bằng tiếng Anh (visual_prompt) "
        "để sinh ảnh nghệ thuật chất lượng cao nhất.\n"
        "Nếu phân cảnh chứa số liệu so sánh hoặc thống kê, hãy bổ sung 'chart_data' (ví dụ: so sánh quân số chiến đấu, sự phát triển dân số).\n"
        "Hãy đảm bảo phân phối hiệu ứng chuyển động hình ảnh hợp lý (zoom_in / zoom_out)."
    )
    
    user_content = f"Hãy viết kịch bản về chủ đề: {topic}"
    if feedback:
        user_content += (
            f"\n\n[LƯU Ý ĐIỀU CHỈNH/VIẾT LẠI]: Người dùng không hài lòng với phiên bản trước và yêu cầu sửa đổi như sau:\n"
            f"\"{feedback}\"\n"
            f"Hãy điều chỉnh nội dung kịch bản chữ, thay đổi mô tả ảnh sinh (visual_prompt), thêm/bớt biểu đồ và chuyển cảnh để đáp ứng đúng yêu cầu này."
        )

    # Cấu trúc JSON chi tiết để hướng dẫn AI trả về định dạng chuẩn xác
    json_schema_desc = (
        "Bạn PHẢI trả về duy nhất một chuỗi JSON thuần túy biểu diễn kịch bản video theo cấu trúc sau (KHÔNG kèm lời chào hay ký tự viết thêm ngoài JSON):\n"
        "{\n"
        "  \"project_title\": \"Tiêu đề dự án\",\n"
        "  \"voice_code\": \"vi-VN-HoaiMyNeural\",\n"
        "  \"visual_style\": \"phong cách hình ảnh nghệ thuật, ví dụ: cinematic painting, realistic photographic\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"scene_id\": \"scene_1\",\n"
        "      \"voice_text\": \"Câu thuyết minh thuyết minh tiếng Việt (dưới 30 từ)\",\n"
        "      \"visual_prompt\": \"Mô tả hình ảnh chi tiết bằng tiếng Anh để sinh ảnh tốt nhất\",\n"
        "      \"effect\": {\n"
        "        \"type\": \"zoom_in\",\n"
        "        \"speed\": 0.001\n"
        "      },\n"
        "      \"chart_data\": null\n"
        "    }\n"
        "  ]\n"
        "}\n"
        "Lưu ý: Nếu phân cảnh cần hiển thị so sánh số liệu hoặc biểu đồ cột, hãy gán đối tượng vào trường 'chart_data' với cấu trúc:\n"
        "\"chart_data\": {\n"
        "  \"title\": \"Tiêu đề biểu đồ\",\n"
        "  \"labels\": [\"Nhãn A\", \"Nhãn B\"],\n"
        "  \"values\": [10.5, 20.0]\n"
        "}"
    )

    provider_clean = provider.strip().lower()
    
    if provider_clean == "openai":
        print("[Script Writer] Sử dụng OpenAI (GPT-4o-mini)...")
        from openai import OpenAI
        client = OpenAI(api_key=api_key.strip())
        
        completion = client.beta.chat.completions.parse(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            response_format=VideoTimeline,
            temperature=0.7
        )
        timeline_dict = completion.choices[0].message.parsed.model_dump()
        
    elif provider_clean == "gemini":
        print("[Script Writer] Sử dụng Google Gemini (Gemini 2.0 Flash) qua REST API v1beta...")
        # Sử dụng mô hình mới nhất gemini-2.0-flash được ủy quyền cho API key mới của bạn
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key.strip()}"
        
        full_prompt = (
            f"Bạn là AI chuyên về sinh dữ liệu có cấu trúc. Hãy tuân thủ hướng dẫn dưới đây và trả về một chuỗi JSON hợp lệ.\n\n"
            f"Chỉ dẫn kịch bản:\n{system_prompt}\n\n"
            f"Định dạng kịch bản bắt buộc:\n{json_schema_desc}\n\n"
            f"Chủ đề:\n{user_content}"
        )
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": full_prompt
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "responseMimeType": "application/json"
            }
        }
        
        headers = {"Content-Type": "application/json"}
        success = False
        text = ""
        
        # --- Stage 1: Gọi v1beta REST API kèm JSON Mode (Sử dụng gemini-2.0-flash) ---
        try:
            print("[Script Writer] Stage 1: Thử gọi Gemini 2.0 Flash v1beta với JSON Mode...")
            response = requests.post(url, json=payload, headers=headers, timeout=25)
            if response.status_code == 200:
                res_json = response.json()
                text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                success = True
                print("[Script Writer] Stage 1 thành công (JSON Mode v1beta).")
            else:
                print(f"[Script Writer] Stage 1 thất bại với mã lỗi {response.status_code}: {response.text}")
        except Exception as e:
            print(f"[Script Writer] Stage 1 lỗi kết nối: {e}")
            
        # --- Stage 2: Fallback sang v1 REST API dùng Text Mode thuần ---
        if not success:
            print("[Script Writer] Stage 2: Đang chuyển hướng gọi sang Gemini 2.0 Flash v1 (Text Mode) làm phương án dự phòng...")
            url_v1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key.strip()}"
            payload_v1 = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": full_prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7
                }
            }
            
            try:
                response = requests.post(url_v1, json=payload_v1, headers=headers, timeout=25)
                if response.status_code != 200:
                    raise RuntimeError(f"Gemini API v1 trả về mã lỗi {response.status_code}: {response.text}")
                    
                res_json = response.json()
                text = res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
                print("[Script Writer] Stage 2 thành công (Text Mode v1).")
            except Exception as e:
                raise RuntimeError(
                    f"Cả 2 phương thức kết nối tới Gemini API (v1beta JSON và v1 Text) dùng gemini-2.0-flash đều thất bại.\n"
                    f"Chi tiết lỗi REST v1: {e}"
                )
                
        # Giải mã và parse JSON từ text nhận được
        try:
            if text.startswith("```json"):
                text = text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
            elif text.startswith("```"):
                text = text.split("```", 1)[1].rsplit("```", 1)[0].strip()
                
            timeline_dict = json.loads(text)
        except Exception as e:
            raise RuntimeError(
                f"Đã nhận phản hồi từ Gemini API nhưng nội dung không đúng định dạng JSON.\n"
                f"Phản hồi thực tế: {text}\n"
                f"Chi tiết lỗi parse: {e}"
            )
        
    elif provider_clean == "claude":
        print("[Script Writer] Sử dụng Anthropic Claude (Claude 3.5 Sonnet)...")
        client = Anthropic(api_key=api_key.strip())
        
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            temperature=0.7,
            system=f"{system_prompt}\n\n{json_schema_desc}",
            messages=[
                {"role": "user", "content": user_content}
            ]
        )
        
        text = message.content[0].text.strip()
        if text.startswith("```json"):
            text = text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
        elif text.startswith("```"):
            text = text.split("```", 1)[1].rsplit("```", 1)[0].strip()
            
        timeline_dict = json.loads(text)
        
    elif provider_clean == "local":
        print("[Script Writer] Sử dụng Local LLM (Ollama)...")
        model_name = api_key.strip()
        if not model_name or model_name == "Not Required" or model_name == "local":
            model_name = "llama3"
            
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": f"{system_prompt}\n\n{json_schema_desc}"},
                {"role": "user", "content": user_content}
            ],
            "format": "json",
            "stream": False,
            "options": {"temperature": 0.7}
        }
        
        try:
            response = requests.post(url, json=payload, timeout=60)
            if response.status_code != 200:
                raise RuntimeError(f"Ollama returned status {response.status_code}: {response.text}")
                
            res_json = response.json()
            text = res_json["message"]["content"].strip()
            timeline_dict = json.loads(text)
        except Exception as e:
            raise RuntimeError(
                f"Không thể kết nối tới Ollama tại cổng 11434. Vui lòng bật Ollama trên máy của bạn "
                f"và tải sẵn model bằng lệnh: 'ollama run {model_name}'. Chi tiết lỗi: {e}"
            )
            
    else:
        raise ValueError(f"AI Provider không hợp lệ: {provider}")
        
    # Cấu hình nhạc nền mặc định
    timeline_dict["background_music"] = "src/mock_assets/music.wav"
    timeline_dict["music_volume"] = 0.06
    
    return timeline_dict
