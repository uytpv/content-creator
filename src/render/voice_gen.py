import asyncio
import os
import edge_tts

async def generate_voice_and_subtitles_async(text, voice_code, audio_output_path, retries=4, delay=2.0):
    """
    Gọi Edge-TTS để sinh giọng nói từ văn bản và trả về danh sách phụ đề từ SentenceBoundary.
    Có sẵn cơ chế retry nếu gặp lỗi kết nối hoặc giới hạn tần suất (rate limits).
    """
    for attempt in range(retries):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(audio_output_path)), exist_ok=True)
            communicate = edge_tts.Communicate(text, voice_code)
            subtitles = []
            
            with open(audio_output_path, "wb") as f:
                async for chunk in communicate.stream():
                    if chunk["type"] == "audio":
                        f.write(chunk["data"])
                    elif chunk["type"] == "SentenceBoundary":
                        start_sec = chunk["offset"] / 10000000.0
                        duration_sec = chunk["duration"] / 10000000.0
                        end_sec = start_sec + duration_sec
                        
                        subtitles.append({
                            "text": chunk["text"],
                            "start": max(0.0, start_sec - 0.05),
                            "end": end_sec + 0.15
                        })
            
            # Nếu nhận được phụ đề thành công (có âm thanh), trả về kết quả
            if subtitles:
                return subtitles
            else:
                raise edge_tts.exceptions.NoAudioReceived("No audio bytes received from stream")
                
        except (edge_tts.exceptions.NoAudioReceived, Exception) as e:
            if attempt < retries - 1:
                print(f"[Warning] Edge-TTS attempt {attempt + 1} failed: {e}. Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
            else:
                print(f"[Error] All {retries} attempts failed for text: '{text[:30]}...'")
                raise e

def generate_voice_and_subtitles(text, voice_code, audio_output_path):
    """Bọc đồng bộ để gọi từ các module khác."""
    return asyncio.run(generate_voice_and_subtitles_async(text, voice_code, audio_output_path))

# Thử nghiệm độc lập
if __name__ == "__main__":
    test_text = "Chào các bạn! Hôm nay chúng ta sẽ kiểm thử tính năng sinh giọng nói tiếng Việt tự động."
    test_voice = "vi-VN-HoaiMyNeural"
    subs = generate_voice_and_subtitles(test_text, test_voice, "src/mock_assets/test_tts.mp3")
    print("Kết quả phụ đề mẫu:")
    for s in subs:
        print(f"[{s['start']:.2f}s -> {s['end']:.2f}s]: {s['text']}")
