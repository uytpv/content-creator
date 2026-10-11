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

def call_llm(system_prompt: str, user_content: str, provider: str, api_key: str, json_mode: bool = True) -> str:
    """Gọi LLM dựa trên provider (openai, gemini, claude, local/ollama)."""
    provider_clean = provider.strip().lower()
    
    if provider_clean == "openai":
        from openai import OpenAI
        client = OpenAI(api_key=api_key.strip())
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"} if json_mode else None,
            temperature=0.7
        )
        return completion.choices[0].message.content.strip()
        
    elif provider_clean == "gemini":
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key.strip()}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "contents": [
                {
                    "parts": [
                        {
                            "text": f"{system_prompt}\n\nYêu cầu kịch bản:\n{user_content}"
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.7,
                "responseMimeType": "application/json" if json_mode else "text/plain"
            }
        }
        
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        if response.status_code == 200:
            res_json = response.json()
            return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
        else:
            # Fallback sang v1
            url_v1 = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key.strip()}"
            payload_v1 = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": f"{system_prompt}\n\nYêu cầu kịch bản:\n{user_content}"
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7
                }
            }
            response = requests.post(url_v1, json=payload_v1, headers=headers, timeout=25)
            if response.status_code == 200:
                res_json = response.json()
                return res_json["candidates"][0]["content"]["parts"][0]["text"].strip()
            else:
                raise RuntimeError(f"Gemini API error: {response.text}")
                
    elif provider_clean == "claude":
        client = Anthropic(api_key=api_key.strip())
        message = client.messages.create(
            model="claude-3-5-sonnet-20240620",
            max_tokens=2000,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_content}
            ]
        )
        return message.content[0].text.strip()
        
    elif provider_clean == "local":
        model_name = api_key.strip()
        if not model_name or model_name == "Not Required" or model_name == "local" or model_name == "glm-5.2":
            # Auto-detect available models from Ollama to prevent 404 errors
            detected_model = None
            try:
                tags_resp = requests.get("http://localhost:11434/api/tags", timeout=3)
                if tags_resp.status_code == 200:
                    available_models = [m["name"] for m in tags_resp.json().get("models", [])]
                    # 1. Prefer GLM-5.2 variants
                    for m in available_models:
                        if "glm-5.2" in m:
                            detected_model = m
                            break
                    # 2. Fallback to GLM4 variants
                    if not detected_model:
                        for m in available_models:
                            if "glm4" in m:
                                detected_model = m
                                break
                    # 3. Fallback to the first available model
                    if not detected_model and available_models:
                        detected_model = available_models[0]
            except Exception:
                pass
                
            if detected_model:
                model_name = detected_model
            elif not model_name or model_name == "Not Required" or model_name == "local":
                model_name = "glm-5.2"
            
        url = "http://localhost:11434/api/chat"
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "format": "json" if json_mode else None,
            "stream": False,
            "options": {"temperature": 0.7}
        }
        
        try:
            # Tăng timeout lên 300 giây cho các dòng máy CPU chạy Ollama chậm
            response = requests.post(url, json=payload, timeout=300)
            if response.status_code != 200:
                raise RuntimeError(f"Ollama returned status {response.status_code}: {response.text}")
            res_json = response.json()
            return res_json["message"]["content"].strip()
        except Exception as e:
            raise RuntimeError(
                f"Không thể kết nối tới Ollama tại cổng 11434. Vui lòng bật Ollama trên máy của bạn "
                f"và tải sẵn model bằng lệnh: 'ollama run {model_name}'. Chi tiết lỗi: {e}"
            )
    else:
        raise ValueError(f"AI Provider không hợp lệ: {provider}")

def parse_json_from_text(text: str) -> dict:
    """Tách khối markdown ```json và parse thành dictionary."""
    text = text.strip()
    if text.startswith("```json"):
        text = text.split("```json", 1)[1].rsplit("```", 1)[0].strip()
    elif text.startswith("```"):
        text = text.split("```", 1)[1].rsplit("```", 1)[0].strip()
    return json.loads(text)

def generate_script_timeline(topic: str, provider: str, api_key: str, feedback: str = None) -> dict:
    """Sáng tác kịch bản ngắn (khoảng 30-45 giây, gồm 4 phân cảnh)."""
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

    json_schema_desc = (
        "Bạn PHẢI trả về duy nhất một chuỗi JSON thuần túy biểu diễn kịch bản video theo cấu trúc sau:\n"
        "{\n"
        "  \"project_title\": \"Tiêu đề dự án\",\n"
        "  \"voice_code\": \"vi-VN-HoaiMyNeural\",\n"
        "  \"visual_style\": \"phong cách hình ảnh nghệ thuật, ví dụ: cinematic painting, realistic photographic\",\n"
        "  \"scenes\": [\n"
        "    {\n"
        "      \"scene_id\": \"scene_1\",\n"
        "      \"voice_text\": \"Câu thuyết minh tiếng Việt (dưới 30 từ)\",\n"
        "      \"visual_prompt\": \"Mô tả hình ảnh chi tiết bằng tiếng Anh để sinh ảnh tốt nhất\",\n"
        "      \"effect\": {\n"
        "        \"type\": \"zoom_in\",\n"
        "        \"speed\": 0.001\n"
        "      },\n"
        "      \"chart_data\": null\n"
        "    }\n"
        "  ]\n"
        "}\n"
    )

    print("[Script Writer] Đang sinh kịch bản ngắn...")
    raw_response = call_llm(f"{system_prompt}\n\n{json_schema_desc}", user_content, provider, api_key, json_mode=True)
    timeline_dict = parse_json_from_text(raw_response)
    
    # Cấu hình nhạc nền mặc định
    timeline_dict["background_music"] = "src/mock_assets/music.wav"
    timeline_dict["music_volume"] = 0.06
    
    return timeline_dict

def generate_long_script_timeline(topic: str, provider: str, api_key: str, feedback: str = None) -> dict:
    """Sáng tác kịch bản dài (khoảng 15-20 phút, gồm nhiều chương và phân cảnh)."""
    provider_clean = provider.strip().lower()
    # Tối ưu hóa số lượng chương và phân cảnh cho dòng máy cục bộ Ollama để tránh lỗi timeout
    num_chapters = 4 if provider_clean == "local" else 8
    num_scenes = 4 if provider_clean == "local" else 8

    # Giai đoạn 1: Sinh đề cương (Outline)
    outline_system = (
        "Bạn là chuyên gia biên kịch và thiết kế nội dung video chuyên nghiệp.\n"
        "Nhiệm vụ của bạn là lập dàn ý (outline) cho một video dài khoảng 15 phút về chủ đề được yêu cầu.\n"
        f"Dàn ý phải chia thành đúng {num_chapters} chương (chapters) mạch lạc, logic, dẫn dắt người xem từ mở đầu đến kết luận.\n"
        "Hãy trả về duy nhất chuỗi JSON có cấu trúc sau:\n"
        "{\n"
        "  \"project_title\": \"Tiêu đề dự án video\",\n"
        "  \"visual_style\": \"phong cách hình ảnh chung (ví dụ: cinematic painting, oil canvas)\",\n"
        "  \"chapters\": [\n"
        "    {\n"
        "      \"chapter_id\": \"chapter_1\",\n"
        "      \"title\": \"Tiêu đề chương 1\",\n"
        "      \"description\": \"Mô tả chi tiết luận điểm và nội dung cốt lõi của chương này\"\n"
        "    }\n"
        "  ]\n"
        "}\n"
    )
    
    user_content = f"Hãy tạo dàn ý chi tiết cho chủ đề: {topic}"
    if feedback:
        user_content += f"\n[Yêu cầu sửa đổi thêm từ người dùng]: {feedback}"
        
    print("[Script Writer] Khởi tạo sinh Đề cương (Outline) cho video dài...")
    outline_raw = call_llm(outline_system, user_content, provider, api_key, json_mode=True)
    outline = parse_json_from_text(outline_raw)
    
    project_title = outline.get("project_title", topic)
    visual_style = outline.get("visual_style", "cinematic painting")
    chapters = outline.get("chapters", [])
    
    print(f"[Script Writer] Đã tạo xong đề cương với {len(chapters)} chương.")
    
    consolidated_scenes = []
    previous_context = ""
    
    # Gán các chủ đề nhạc nền linh hoạt cho từng chương (quay vòng)
    music_themes = ["dramatic", "calm", "upbeat", "mysterious", "dramatic", "calm", "mysterious", "calm"]
    
    # Giai đoạn 2: Vòng lặp sinh phân cảnh từng chương
    for index, ch in enumerate(chapters):
        ch_id = ch["chapter_id"]
        ch_title = ch["title"]
        ch_desc = ch["description"]
        
        music_theme = music_themes[index % len(music_themes)]
        music_file = f"src/mock_assets/music_{music_theme}.wav"
        if not os.path.exists(music_file):
            music_file = "src/mock_assets/music.wav" # Fallback nhạc mặc định
            
        print(f"[Script Writer] Đang biên kịch Chương {index+1}/{len(chapters)}: {ch_title}...")
        
        chapter_system = (
            "Bạn là chuyên gia biên kịch video chuyên nghiệp.\n"
            f"Nhiệm vụ của bạn là viết chi tiết {num_scenes} phân cảnh (scenes) cho chương '{ch_title}' thuộc dự án video '{project_title}'.\n"
            f"Mô tả nội dung của chương này: '{ch_desc}'.\n"
            f"Phong cách hình ảnh chung: '{visual_style}'.\n"
            "Yêu cầu:\n"
            "1. Lời thoại (voice_text) viết bằng tiếng Việt tự nhiên, lôi cuốn, kể câu chuyện theo nội dung chương.\n"
            "2. Mỗi phân cảnh có 1-2 câu thuyết minh ngắn gọn, súc tích (khoảng 15-25 từ).\n"
            "3. Cung cấp mô tả hình ảnh bằng tiếng Anh (visual_prompt) chi tiết, giàu tính nghệ thuật để vẽ ảnh.\n"
            "4. Phân bổ hiệu ứng hình ảnh (zoom_in, zoom_out hoặc static) hợp lý.\n"
            "5. Nếu phân cảnh có so sánh số liệu hoặc thống kê, hãy bổ sung 'chart_data' (nếu không cần thì để null).\n"
            "Hãy trả về duy nhất một chuỗi JSON chứa danh sách các phân cảnh:\n"
            "{\n"
            "  \"scenes\": [\n"
            "    {\n"
            "      \"scene_id\": \"scene_placeholder\",\n"
            "      \"voice_text\": \"Lời thoại thuyết minh tiếng Việt\",\n"
            "      \"visual_prompt\": \"Detailed English image prompt\",\n"
            "      \"effect\": {\n"
            "        \"type\": \"zoom_in\",\n"
            "        \"speed\": 0.001\n"
            "      },\n"
            "      \"chart_data\": null\n"
            "    }\n"
            "  ]\n"
            "}\n"
        )
        
        ch_user_content = f"Hãy viết kịch bản chi tiết cho chương này."
        if previous_context:
            ch_user_content += f"\nLưu ý phân cảnh đầu tiên phải kết nối tự nhiên tiếp sau lời thoại này: '{previous_context}'"
            
        ch_scenes_raw = call_llm(chapter_system, ch_user_content, provider, api_key, json_mode=True)
        ch_data = parse_json_from_text(ch_scenes_raw)
        
        scenes = ch_data.get("scenes", [])
        for scene in scenes:
            scene["chapter_id"] = ch_id
            scene["chapter_title"] = ch_title
            scene["background_music"] = music_file
            scene["music_theme"] = music_theme
            consolidated_scenes.append(scene)
            
        if scenes:
            previous_context = scenes[-1]["voice_text"]
            
    # Giai đoạn 3: Đánh lại chỉ mục scene_id tuần tự
    for idx, scene in enumerate(consolidated_scenes):
        scene["scene_id"] = f"scene_{idx+1}"
        
    print(f"[Script Writer] Đã hoàn thành kịch bản dài gồm {len(consolidated_scenes)} phân cảnh.")
    
    return {
        "project_title": project_title,
        "voice_code": "vi-VN-HoaiMyNeural",
        "visual_style": visual_style,
        "scenes": consolidated_scenes,
        "background_music": "src/mock_assets/music.wav",
        "music_volume": 0.06
    }

