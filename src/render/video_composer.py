import os
import sys
import json
import subprocess
import imageio_ffmpeg
import re
import time
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
    
    # Calculate safe threads to prevent 100% CPU lockup
    cpu_count = os.cpu_count() or 4
    ffmpeg_threads = str(max(1, min(4, cpu_count - 1)))
    
    # Lower priority class on Windows to keep system responsive
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x00004000  # BELOW_NORMAL_PRIORITY_CLASS
    
    # Optimize zoompan to run at 960x540 instead of 1920x1080 (reduces pixels by 4x for zoompan filter), then scale to 1920x1080
    if effect_type == "zoom_in":
        z_expr = f"zoom+{speed}"
        zoompan_filter = f"zoompan=z='{z_expr}':d={num_frames}:s=960x540:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps},scale=1920:1080"
    elif effect_type == "zoom_out":
        z_expr = f"if(eq(on,1),1.15,zoom-{speed})"
        zoompan_filter = f"zoompan=z='{z_expr}':d={num_frames}:s=960x540:x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':fps={fps},scale=1920:1080"
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
            "-threads", ffmpeg_threads,
            "-loop", "1", "-i", image_path,
            "-i", voice_path,
            "-i", whoosh_path,
            "-filter_complex", f"{filter_str};{audio_filter}",
            "-map", "[v]",
            "-map", "[a]",
            "-c:v", "libx264",
            "-preset", "faster",
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
            "-threads", ffmpeg_threads,
            "-loop", "1", "-i", image_path,
            "-i", voice_path,
            "-filter_complex", filter_str,
            "-map", "[v]",
            "-map", "1:a",
            "-c:v", "libx264",
            "-preset", "faster",
            "-tune", "stillimage",
            "-c:a", "aac",
            "-b:a", "192k",
            "-pix_fmt", "yuv420p",
            "-t", f"{duration:.3f}",
            output_clip_path
        ]
    
    print(f"Rendering scene clip: {output_clip_path} (effect: {effect_type}, whoosh: {use_whoosh}, duration: {duration:.2f}s)...")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creationflags)
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
    
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x00004000  # BELOW_NORMAL_PRIORITY_CLASS
        
    print("Concatenating scenes into a unified video...")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creationflags)
    
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
    
    creationflags = 0
    if sys.platform == "win32":
        creationflags = 0x00004000  # BELOW_NORMAL_PRIORITY_CLASS
        
    print(f"Mixing background music (volume: {music_volume})...")
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=creationflags)
    if result.returncode != 0:
        print("[Error] Mixing background music!")
        print(result.stderr)
        raise RuntimeError(f"FFmpeg mix audio error: {result.stderr}")

def compose_video(timeline_path, final_output_path, progress_callback=None):
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
    
    scenes = timeline.get("scenes", [])
    total_scenes = len(scenes)
    
    # Kiểm tra xem có chứa chương (chapters) hay không
    has_chapters = any("chapter_id" in scene for scene in scenes)
    
    clip_paths = {}
    temp_files = [] # Chỉ chứa các file trung gian thực sự cần xóa
    
    try:
        # 1. Sinh voice/ảnh và render clip cho từng phân cảnh (Scene Clips)
        for i, scene in enumerate(scenes):
            scene_id = scene["scene_id"]
            
            if progress_callback:
                percent = int((i / total_scenes) * 80)
                progress_callback(percent, f"Đang dựng phân cảnh {i+1}/{total_scenes}: {scene_id}")
                
            # Đường dẫn tệp tin âm thanh giọng nói và hình ảnh (Lưu trữ lâu dài)
            voice_path = f"src/mock_assets/{project_slug}_{scene_id}_voice.mp3"
            image_path = scene.get("visual_asset_path")
            
            # Khởi tạo đường dẫn tạm thời cho clip render phân cảnh và phụ đề
            ass_path = f"temp/{scene_id}.ass"
            clip_path = f"temp/{scene_id}.mp4"
            
            # Sinh giọng nói và mốc thời gian động (nếu chưa có file âm thanh)
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
            
            # Xử lý ảnh phân cảnh: Kiểm tra xem có chứa ChartData hay không
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
            
            # Tạo phụ đề ASS tạm
            generate_ass(subs_list, ass_path)
            temp_files.append(ass_path)
            
            # Render clip cho scene này (chèn whoosh từ scene thứ 2 trở đi)
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
            clip_paths[scene_id] = clip_path
            temp_files.append(clip_path)
            
            # Cooldown sleep to prevent system overheating (especially on laptops)
            time.sleep(1.5)
            
        # 2. Ghép nối và lồng nhạc nền
        if progress_callback:
            progress_callback(85, "Đang tiến hành ghép các phân cảnh và lồng nhạc nền...")
            
        if has_chapters:
            # Nhóm các phân cảnh theo từng chương
            chapters_order = []
            chapter_scenes = {}
            for scene in scenes:
                ch_id = scene.get("chapter_id", "general")
                if ch_id not in chapter_scenes:
                    chapters_order.append(ch_id)
                    chapter_scenes[ch_id] = []
                chapter_scenes[ch_id].append(scene)
                
            chapter_clips = []
            for ch_idx, ch_id in enumerate(chapters_order):
                ch_s_list = chapter_scenes[ch_id]
                ch_clip_paths = [clip_paths[s["scene_id"]] for s in ch_s_list]
                
                ch_unmixed = f"temp/chapter_{ch_id}_unmixed.mp4"
                ch_mixed = f"temp/chapter_{ch_id}_mixed.mp4"
                temp_files.extend([ch_unmixed, ch_mixed])
                
                # Ghép nối các phân cảnh của chương này
                print(f"Assembling scenes for chapter {ch_id}...")
                concat_clips(ffmpeg_exe, ch_clip_paths, ch_unmixed)
                
                # Lồng nhạc nền riêng cho chương này
                bg_music = ch_s_list[0].get("background_music")
                if bg_music and os.path.exists(bg_music):
                    music_volume = timeline.get("music_volume", 0.06)
                    mix_background_music(
                        ffmpeg_exe=ffmpeg_exe,
                        video_path=ch_unmixed,
                        music_path=bg_music,
                        music_volume=music_volume,
                        output_path=ch_mixed
                    )
                else:
                    shutil.copy(ch_unmixed, ch_mixed)
                chapter_clips.append(ch_mixed)
                
            # Ghép nối tất cả các chương thành video hoàn chỉnh
            print("Assembling chapters into final video...")
            concat_clips(ffmpeg_exe, chapter_clips, final_output_path)
        else:
            # Luồng ghép truyền thống (ghép toàn bộ rồi lồng 1 file nhạc nền duy nhất)
            concatenated_path = "temp/concatenated_no_music.mp4"
            temp_files.append(concatenated_path)
            concat_clips(ffmpeg_exe, list(clip_paths.values()), concatenated_path)
            
            bg_music = timeline.get("background_music")
            if bg_music and os.path.exists(bg_music):
                music_volume = timeline.get("music_volume", 0.06)
                mix_background_music(
                    ffmpeg_exe=ffmpeg_exe,
                    video_path=concatenated_path,
                    music_path=bg_music,
                    music_volume=music_volume,
                    output_path=final_output_path
                )
            else:
                print("No background music detected. Exporting direct video copy...")
                creationflags = 0
                if sys.platform == "win32":
                    creationflags = 0x00004000
                subprocess.run([ffmpeg_exe, "-y", "-i", concatenated_path, "-c", "copy", final_output_path], creationflags=creationflags)
                
        if progress_callback:
            progress_callback(100, "Hoàn tất dựng video!")
            
        print(f"\nVideo composed successfully! Output file: {final_output_path}")
        
        # Ghi đè lại file timeline để cập nhật đường dẫn chính xác đã sinh
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
