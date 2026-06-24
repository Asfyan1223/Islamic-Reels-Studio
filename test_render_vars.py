import os
import json
import sys

app_data_dir = os.path.join(os.environ.get('APPDATA', ''), 'IslamicReelsStudio')
os.chdir(app_data_dir)

print("Cwd changed to:", os.getcwd())

with open("settings.json", "r") as f:
    master_settings = json.load(f)

for prof_name, settings in master_settings.items():
    print(f"\n=== Profile: {prof_name} ===")
    yt_p = bool(settings.get("enable_yt", True))
    insta_p = bool(settings.get("enable_ig", True))
    fb_p = bool(settings.get("enable_fb", True))
    
    print(f"Loaded toggles: enable_yt={yt_p}, enable_ig={insta_p}, enable_fb={fb_p}")
    
    # Simulate execute_render_and_upload logic
    prof_settings = settings.copy()
    
    ig_style = prof_settings.get("ig_video_style", "Cinematic (Reciter + Fast Cuts)")
    yt_style = prof_settings.get("yt_video_style", "Traditional (Static Loop)")
    
    enable_ig_fb = insta_p or fb_p
    enable_yt = yt_p
    
    print(f"enable_ig_fb={enable_ig_fb}, enable_yt={enable_yt}")
    print(f"ig_style={ig_style}, yt_style={yt_style}")
    print(f"Styles equal? {ig_style == yt_style}")
    
    ig_video_path = os.path.join("output", "instagram", f"reel_{prof_name}.mp4")
    yt_video_path = os.path.join("output", "youtube", f"reel_{prof_name}.mp4")
    
    print(f"ig_video_path exists? {os.path.exists(ig_video_path)} ({ig_video_path})")
    print(f"yt_video_path exists? {os.path.exists(yt_video_path)} ({yt_video_path})")
    
    generated_paths = {}
    if enable_ig_fb and enable_yt and (ig_style == yt_style):
        # optimization
        generated_paths['ig'] = ig_video_path
        generated_paths['yt'] = yt_video_path
    else:
        if enable_ig_fb:
            generated_paths['ig'] = ig_video_path
        if enable_yt:
            generated_paths['yt'] = yt_video_path
            
    print(f"generated_paths: {generated_paths}")
    
    # Check what would be uploaded
    if 'ig' in generated_paths:
        temp_set_ig = prof_settings.copy()
        temp_set_ig['enable_yt'] = False
        temp_set_ig['enable_ig'] = insta_p
        temp_set_ig['enable_fb'] = fb_p
        print(f"Instagram upload call would have settings:")
        print(f"  enable_ig={temp_set_ig.get('enable_ig')}, enable_fb={temp_set_ig.get('enable_fb')}, enable_yt={temp_set_ig.get('enable_yt')}")
        print(f"  ig_account_id={temp_set_ig.get('ig_account_id')}, fb_token is empty? {not temp_set_ig.get('fb_token')}")
    else:
        print("Instagram upload would NOT be called (not in generated_paths)")
        
    if 'yt' in generated_paths:
        temp_set_yt = prof_settings.copy()
        temp_set_yt['enable_fb'] = False
        temp_set_yt['enable_ig'] = False
        temp_set_yt['enable_yt'] = yt_p
        print(f"YouTube upload call would have settings:")
        print(f"  enable_ig={temp_set_yt.get('enable_ig')}, enable_fb={temp_set_yt.get('enable_fb')}, enable_yt={temp_set_yt.get('enable_yt')}")
