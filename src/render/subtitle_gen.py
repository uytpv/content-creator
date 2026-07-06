import os

def format_time(seconds):
    """Đổi số giây (ví dụ: 12.34) sang định dạng ASS: h:mm:ss.cc (h:phút:giây.phần trăm giây)."""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    c = int(round((seconds - int(seconds)) * 100))
    if c == 100:
        s += 1
        c = 0
        if s == 60:
            m += 1
            s = 0
            if m == 60:
                h += 1
                m = 0
    return f"{h}:{m:02d}:{s:02d}.{c:02d}"

def generate_ass(subtitles, output_path):
    """
    Tạo file phụ đề .ass từ danh sách subtitle dict.
    Format: [{'text': '...', 'start': 0.5, 'end': 2.0}]
    """
    # Đảm bảo thư mục đầu ra tồn tại
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Định nghĩa cấu trúc file .ass với kiểu dáng (Style) hiển thị chữ đẹp mắt
    # - Alignment=2: Căn lề chính giữa phía dưới
    # - MarginV=100: Đẩy phụ đề lên cao hơn mép dưới 100 pixel để không bị che khuất
    # - Outline=3, Shadow=0: Có viền đen rõ nét bao quanh chữ
    # - PrimaryColour=&H00FFFFFF: Màu trắng tinh khiết
    # - OutlineColour=&H00000000: Màu viền đen
    header = """[Script Info]
Title: Auto-generated Subtitles by AI Content Factory
ScriptType: v4.00+
WrapStyle: 0
PlayResX: 1920
PlayResY: 1080
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,65,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,-1,0,0,0,100,100,0,0,1,4,0,2,10,10,120,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(header)
        for sub in subtitles:
            start_str = format_time(sub['start'])
            end_str = format_time(sub['end'])
            # Hủy bỏ các ký tự xuống dòng (nếu có) để phụ đề cùng 1 hàng
            text_cleaned = sub['text'].replace('\n', ' ').strip()
            
            # Ghi dòng thoại
            dialogue_line = f"Dialogue: 0,{start_str},{end_str},Default,,0,0,0,,{text_cleaned}\n"
            f.write(dialogue_line)
            
    print(f"Generated ASS subtitle file: {output_path}")

# Thử nghiệm độc lập
if __name__ == "__main__":
    test_subs = [
        {"text": "Xin chào thế giới!", "start": 0.5, "end": 2.0},
        {"text": "Đây là demo phụ đề ASS.", "start": 2.5, "end": 5.0}
    ]
    generate_ass(test_subs, "src/mock_assets/test.ass")
