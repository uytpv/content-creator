import os
import requests
import base64
import hashlib
from PIL import Image, ImageDraw

# Cấu hình địa chỉ API của máy GPU chạy Stable Diffusion WebUI
# Mặc định là localhost nếu chạy cùng máy, bạn có thể cấu hình IP mạng LAN (ví dụ: http://192.168.1.15:7860)
SD_API_URL = os.environ.get("SD_API_URL", "http://localhost:7860")

def generate_placeholder_image(prompt, style_preset, output_path):
    """
    Sinh ảnh nháp (placeholder) tuyệt đẹp khi máy GPU offline.
    Màu nền được băm (hash) từ prompt để đảm bảo mỗi phân cảnh có màu sắc nhất quán.
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    
    # Tạo mã màu RGB ngẫu nhiên nhưng cố định theo nội dung prompt
    h = hashlib.md5(prompt.encode('utf-8')).hexdigest()
    r = int(h[0:2], 16) % 120 + 30  # Giới hạn tông màu tối/ấm
    g = int(h[2:4], 16) % 120 + 30
    b = int(h[4:6], 16) % 120 + 30
    background_color = (r, g, b)
    
    img = Image.new('RGB', (1920, 1080), color=background_color)
    draw = ImageDraw.Draw(img)
    
    # Vẽ khung viền trang trí
    draw.rectangle([40, 40, 1880, 1040], outline=(255, 255, 255), width=8)
    draw.rectangle([55, 55, 1865, 1025], outline=(255, 255, 255, 128), width=2)
    
    # Nhãn góc trên
    draw.text((100, 100), "AI CONTENT FACTORY - OFFLINE PLACEHOLDER", fill=(200, 200, 200))
    draw.text((100, 150), f"Style Preset: {style_preset.upper()}", fill=(235, 196, 84)) # Màu vàng cam
    
    # Xuống dòng tự động cho prompt dài
    words = prompt.split(' ')
    lines = []
    current_line = []
    for word in words:
        current_line.append(word)
        if len(' '.join(current_line)) > 55:
            lines.append(' '.join(current_line[:-1]))
            current_line = [word]
    lines.append(' '.join(current_line))
    
    # Vẽ prompt text ở giữa ảnh
    y_offset = 350
    for line in lines:
        draw.text((100, y_offset), line, fill=(255, 255, 255))
        y_offset += 70
        
    img.save(output_path)
    print(f"Generated fallback placeholder image: {output_path}")

def generate_image(prompt, style_preset, output_path):
    """
    Gửi request tới API của Stable Diffusion WebUI để vẽ hình ảnh.
    Nếu không kết nối được (máy GPU tắt), tự động chuyển sang vẽ ảnh nháp để tránh gián đoạn pipeline.
    """
    # Gộp prompt với phong cách định hình
    full_prompt = f"{prompt}, {style_preset}" if style_preset else prompt
    negative_prompt = "nsfw, low quality, worst quality, bad anatomy, deformed, texts, watermark, logo, bad proportions"
    
    payload = {
        "prompt": full_prompt,
        "negative_prompt": negative_prompt,
        "steps": 20,
        "width": 1920,
        "height": 1080,
        "cfg_scale": 7.0,
        "sampler_name": "Euler a"
    }
    
    api_endpoint = f"{SD_API_URL.rstrip('/')}/sdapi/v1/txt2img"
    
    print(f"Requesting SD image from Local GPU API ({SD_API_URL})...")
    try:
        # Đặt timeout ngắn (3.5 giây) để không làm treo hệ thống nếu máy GPU kia không hoạt động
        response = requests.post(api_endpoint, json=payload, timeout=3.5)
        
        if response.status_code == 200:
            data = response.json()
            # Giải mã base64 của ảnh đầu tiên trong mảng trả về
            img_b64 = data["images"][0]
            img_data = base64.b64decode(img_b64)
            
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            with open(output_path, "wb") as f:
                f.write(img_data)
            print(f"Successfully generated SD image and saved to: {output_path}")
            return True
        else:
            print(f"[Warning] SD WebUI API returned status code {response.status_code}.")
            
    except requests.exceptions.RequestException as e:
        print(f"[Warning] Failed to connect to Local GPU API at {SD_API_URL} ({e}).")
        
    # Cơ chế dự phòng
    generate_placeholder_image(prompt, style_preset, output_path)
    return False

# Thử nghiệm độc lập
if __name__ == "__main__":
    generate_image("A cute orange cat wearing a crown sitting on a golden throne", "cinematic painting", "src/mock_assets/test_sd_image.png")
