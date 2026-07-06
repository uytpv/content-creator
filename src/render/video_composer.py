import os
import json
import subprocess
import imageio_ffmpeg
import re
from .subtitle_gen import generate_ass
from .voice_gen import generate_voice_and_subtitles
from .image_gen import generate_image
from .chart_gen import generate_chart_image

def escape_subtitle_path(path):
    """Format and escape subtitle file paths for FFmpeg on Windows."""
    abs_path = os.path.abspath(path)
    clean_path = abs_path.replace('\\', '/')
    if ':' in clean_path:
        parts = clean_path.split(':', 1)
        clean_path = parts[0] + '\\:' + parts[1]
    return clean_path

def slugify(value):
    """Chuyển đổi tiêu đề dự án thành tên thư mục/file hợp lệ."""
    value = re.sub(r'[^\w\s-]', '', value.lower())
    return re.sub(r'[-\s]+', '_', value).strip('_')

def render_scene_clip(ffmpeg_exe, image_path, voice_path, ass_path, duration, effect, output_clip_path, use_whoosh=False):
    """Render a single scene clip with zoompan visual effects, subtitles, and optional transition SFX."""
    fps = 25
    num_frames = int(duration * fps)
    
    effect_type = effect.get("type", "static")
    speed = effect.get("speed", 0.001)
    
    if effect_type == "zoom_in":
        z_expr = f"zoom+{speed}"
        zoompan_filter = f"zoompan=z='{z_expr}':d={num_frames}:s=1920x1080:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps}"
    elif effect_type == "zoom_out":
        z_expr = f"if(eq(on,1),1.15,zoom-{speed})"
        zoompan_filter = f"zoompan=z='{z_expr}':d={num_frames}:s=1920x1080:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps}"
    else:
        zoompan_filter = "scale=1920:1080"
        
    if ass_path and os.path.exists(ass_path):
        escaped_ass = escape_subtitle_path(ass_path)
        filter_str = f"[0:v]{zoompan_filter},subtitles='{escaped_ass}'[v]"
    else:
        filter_str = f"[0:v]{zoompan_filter}[v]"
        
    whoosh_path = "src/mock_assets/whoosh.wav"
    if use_whoosh and os.path.exists(whoosh_path):
        # Trộn âm thanh chuyển cảnh Whoosh cùng lúc với giọng thoại
        audio_filter = "[1:a][2:a]amix=inputs=2:duration=first[a]"
        cmd = [
            ffmpeg_exe, "-y",
            "-loop", "1", "-i", image_path,
            "-i", voice_path,
            "-i", whoosh_path,
            "-filter_complex", f"{filter_str};{audio_filter}",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", f"{duration:.3f}",
            output_clip_path
        ]
    else:
        cmd = [
            ffmpeg_exe, "-y",
            "-loop", "1", "-i", image_path,
            "-i", voice_path,
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", f"{duration:.3f}",
            output_clip_path
        ]
    
    print(f"Rendering scene clip: {output_clip_path} (effect: {effect_type}, whoosh: {use_whoosh}, duration: {duration:.2f}s)...")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"[Error] Rendering scene clip {output_clip_path}!")
        print(result.stderr)
        raise RuntimeError(f"FFmpeg error: {result.stderr}")

def concat_clips(ffmpeg_exe, clip_paths, output_path):
    """Concatenate multiple scene clips into a single video file."""
    list_file_path = "temp_concat_list.txt"
    with open(list_file_path, "w", encoding="utf-8") as f:
        for clip in clip_paths:
            abs_path = os.path.abspath(clip).replace('\\', '/')
            f.write(f"file '{abs_path}'\n")
            
    cmd = [
        ffmpeg_exe, "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", list_file_path,
        "-c", "copy",
        output_path
    ]
    
    print("Concatenating scenes into a unified video...")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    
    if os.path.exists(list_file_path):
        os.remove(list_file_path)
        
    if result.returncode != 0:
        print("[Error] Concatenating video clips!")
        print(result.stderr)
        raise RuntimeError(f"FFmpeg concat error: {result.stderr}")

def mix_background_music(ffmpeg_exe, video_path, music_path, music_volume, output_path):
    """Mix background music with active audio ducking volume control."""
    cmd = [
        ffmpeg_exe, "-y",
        "-i", video_path,
        "-i", music_path,
        "-filter_complex", f"[1:a]volume={music_volume}[bg];[0:a][bg]amix=inputs=2:duration=first[a]",
        "-map", "0:v",
        "-map", "[a]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        output_path
    ]
    
    print(f"Mixing background music (volume: {music_volume})...")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print("[Error] Mixing background music!")
        print(result.stderr)
        raise RuntimeError(f"FFmpeg mix audio error: {result.stderr}")

def compose_video(timeline_path, final_output_path):
    """Core function to orchestrate the video composition process."""
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    with open(timeline_path, 'r', encoding='utf-8') as f:
        timeline = json.load(f)
        
    project_title = timeline.get("project_title", "Untitled")
    project_slug = slugify(project_title)
    print(f"Starting video composition: {project_title}")
    
    os.makedirs("temp", exist_ok=True)
    os.makedirs("src/mock_assets", exist_ok=True)
    os.makedirs(os.path.dirname(os.path.abspath(final_output_path)), exist_ok=True)
    
    voice_code = timeline.get("voice_code", "vi-VN-HoaiMyNeural")
    visual_style = timeline.get("visual_style", "cinematic painting")
    
    clip_paths = []
    temp_files = [] # Chỉ chứa các file trung gian thực sự cần xóa
    
    try:
        for i, scene in enumerate(timeline["scenes"]):
            scene_id = scene["scene_id"]
            
            # Đường dẫn tệp tin âm thanh giọng nói và hình ảnh (Lưu trữ lâu dài)
            voice_path = f"src/mock_assets/{project_slug}_{scene_id}_voice.mp3"
            image_path = scene.get("visual_asset_path")
            
            # Khởi tạo đường dẫn tạm thời cho clip render phân cảnh và phụ đề
            ass_path = f"temp/{scene_id}.ass"
            clip_path = f"temp/{scene_id}.mp4"
            
            # 1. Sinh giọng nói và mốc thời gian động (nếu chưa có file âm thanh)
            if not os.path.exists(voice_path):
                print(f"Generating TTS audio for scene {scene_id} using voice {voice_code}...")
                subs_list = generate_voice_and_subtitles(scene["voice_text"], voice_code, voice_path)
            else:
                print(f"Voice audio exists for {scene_id}. Regenerating subtitle metadata...")
                subs_list = generate_voice_and_subtitles(scene["voice_text"], voice_code, voice_path)
                
            if not subs_list:
                raise ValueError(f"Failed to generate voice or subtitles for scene {scene_id}")
                
            duration = subs_list[-1]["end"] + 0.5
            
            # Cập nhật đường dẫn âm thanh và phụ đề thực tế vào dict
            scene["voice_audio_path"] = voice_path
            scene["subtitles"] = subs_list
            
            # 2. Xử lý ảnh phân cảnh: Kiểm tra xem có chứa ChartData hay không
            chart_data = scene.get("chart_data")
            if chart_data:
                # Nếu có dữ liệu biểu đồ, tự động sinh ảnh biểu đồ Matplotlib làm ảnh nền
                image_path = f"src/mock_assets/{project_slug}_{scene_id}_chart.png"
                print(f"Scene {scene_id} contains chart data. Drawing Matplotlib chart...")
                generate_chart_image(chart_data, image_path)
            elif not image_path or not os.path.exists(image_path):
                image_path = f"src/mock_assets/{project_slug}_{scene_id}_img.png"
                prompt = scene.get("visual_prompt") or scene["voice_text"]
                print(f"Visual asset missing for scene {scene_id}. Generating image from prompt...")
                generate_image(prompt, visual_style, image_path)
                
            scene["visual_asset_path"] = image_path
            
            # 3. Tạo phụ đề ASS tạm
            generate_ass(subs_list, ass_path)
            temp_files.append(ass_path)
            
            # 4. Render clip cho scene này (chèn whoosh từ scene thứ 2 trở đi)
            render_scene_clip(
                ffmpeg_exe=ffmpeg_exe,
                image_path=image_path,
                voice_path=voice_path,
                ass_path=ass_path,
                duration=duration,
                effect=scene.get("effect", {}),
                output_clip_path=clip_path,
                use_whoosh=(i > 0)
            )
            clip_paths.append(clip_path)
            temp_files.append(clip_path)
            
        # 5. Ghép nối toàn bộ phân cảnh
        concatenated_path = "temp/concatenated_no_music.mp4"
        temp_files.append(concatenated_path)
        concat_clips(ffmpeg_exe, clip_paths, concatenated_path)
        
        # 6. Trộn nhạc nền
        bg_music = timeline.get("background_music")
        if bg_music and os.path.exists(bg_music):
            music_volume = timeline.get("music_volume", 0.1)
            mix_background_music(
                ffmpeg_exe=ffmpeg_exe,
                video_path=concatenated_path,
                music_path=bg_music,
                music_volume=music_volume,
                output_path=final_output_path
            )
        else:
            print("No background music detected. Exporting direct video copy...")
            subprocess.run([ffmpeg_exe, "-y", "-i", concatenated_path, "-c", "copy", final_output_path])
            
        print(f"\nVideo composed successfully! Output file: {final_output_path}")
        
        # Ghi đè lại file timeline_example.json để cập nhật đường dẫn chính xác đã sinh
        with open(timeline_path, 'w', encoding='utf-8') as f:
            json.dump(timeline, f, indent=2, ensure_ascii=False)
            
    finally:
        print("Cleaning up temporary render files...")
        for temp_file in temp_files:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception as e:
                    print(f"Could not remove temporary file {temp_file}: {e}")
        if os.path.exists("temp"):
            try:
                os.rmdir("temp")
            except Exception:
                pass
