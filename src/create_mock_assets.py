import os
import wave
import struct
import math
from PIL import Image, ImageDraw

def create_mock_directories():
    os.makedirs("src/mock_assets", exist_ok=True)
    print("Created src/mock_assets directory.")

def write_beep_wav(filename, duration, freq=440, sample_rate=44100):
    """Tạo file âm thanh WAV với tần số cụ thể để làm mock voice/music."""
    with wave.open(filename, 'w') as wav:
        wav.setnchannels(1)  # Mono
        wav.setsampwidth(2)  # 16-bit (2 bytes)
        wav.setframerate(sample_rate)
        
        num_samples = int(duration * sample_rate)
        for i in range(num_samples):
            # Tạo sóng sin cơ bản với biên độ nhỏ (0.1) để đỡ chói tai
            val = int(32767 * 0.1 * math.sin(2 * math.pi * freq * i / sample_rate))
            wav.writeframesraw(struct.pack('<h', val))
    print(f"Created audio: {filename} ({duration}s)")

def write_whoosh_wav(filename, duration=0.8, sample_rate=44100):
    """Tạo âm thanh dạng frequency sweep (Whoosh transition) để làm SFX chuyển cảnh."""
    with wave.open(filename, 'w') as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        
        num_samples = int(duration * sample_rate)
        for i in range(num_samples):
            t = i / num_samples
            # Tần số quét từ 100Hz lên 800Hz
            freq = 150 + 650 * t
            # Biên độ hình quả chuông (fade in -> peak -> fade out)
            amplitude = math.sin(t * math.pi) * 0.15
            
            val = int(32767 * amplitude * math.sin(2 * math.pi * freq * i / sample_rate))
            wav.writeframesraw(struct.pack('<h', val))
    print(f"Created SFX transition: {filename} ({duration}s)")

def create_solid_image(filename, text, color):
    """Tạo ảnh PNG kích thước Full HD 1920x1080 với chữ minh họa."""
    img = Image.new('RGB', (1920, 1080), color=color)
    draw = ImageDraw.Draw(img)
    
    # Vẽ chữ đơn giản lên ảnh (dùng default font của Pillow)
    draw.text((100, 100), f"AI CONTENT FACTORY TEST", fill=(200, 200, 200))
    draw.text((100, 200), text, fill=(255, 255, 255))
    
    # Vẽ một vài hình vẽ để dễ nhận dạng hiệu ứng chuyển cảnh/zoom
    draw.rectangle([200, 400, 600, 800], outline=(255, 255, 255), width=5)
    draw.ellipse([1200, 400, 1600, 800], outline=(255, 255, 255), width=5)
    
    img.save(filename)
    print(f"Created image: {filename}")

def main():
    create_mock_directories()
    
    # Tạo các ảnh cho 4 Scene khác nhau với màu nền riêng biệt
    create_solid_image("src/mock_assets/scene1.png", "Scene 1: Introduction to Orange Cats", (30, 41, 59))  # Slate Blue
    create_solid_image("src/mock_assets/scene2.png", "Scene 2: History & Origin (Egypt)", (20, 83, 45))   # Forest Green
    create_solid_image("src/mock_assets/scene3.png", "Scene 3: Personality traits (Crazy Garfield)", (127, 29, 29)) # Deep Red
    create_solid_image("src/mock_assets/scene4.png", "Scene 4: Conclusion & Subscription", (88, 28, 135)) # Purple
    
    # Tạo các file âm thanh giọng nói (voiceover) cho từng cảnh với thời lượng khác nhau
    write_beep_wav("src/mock_assets/voice_scene1.wav", duration=6.0, freq=300)
    write_beep_wav("src/mock_assets/voice_scene2.wav", duration=8.0, freq=330)
    write_beep_wav("src/mock_assets/voice_scene3.wav", duration=7.0, freq=360)
    write_beep_wav("src/mock_assets/voice_scene4.wav", duration=5.0, freq=400)
    
    # Tạo file nhạc nền (background music) dài 30 giây với tần số thay đổi nhẹ nhàng
    write_beep_wav("src/mock_assets/music.wav", duration=30.0, freq=150)
    
    # Tạo âm thanh chuyển cảnh Whoosh
    write_whoosh_wav("src/mock_assets/whoosh.wav", duration=0.8)
    
    print("All mock assets created successfully!")

if __name__ == "__main__":
    main()
