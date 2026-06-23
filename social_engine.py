import os
import requests
import json
import time
import sys
from datetime import datetime, timezone
from PIL import Image

def get_meta_server_time():
    try:
        res = requests.get("https://worldtimeapi.org/api/timezone/Etc/UTC", timeout=5).json()
        utc_time_str = datetime.fromisoformat(res['datetime']).strftime('%Y-%m-%d %H:%M:%S UTC')
        return utc_time_str, int(res['unixtime'])
    except:
        return datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC'), int(time.time())

def check_server_status(settings):
    statuses = {
        "meta_time": get_meta_server_time()[0],
        "facebook": "❌ Disconnected / No Token",
        "youtube": "⚠️ Needs OAuth JSON"
    }
    
    if settings.get("fb_token"):
        try:
            res = requests.get(f"https://graph.facebook.com/v19.0/me?access_token={settings['fb_token']}", timeout=5).json()
            if "id" in res:
                statuses["facebook"] = f"✅ Connected as: {res.get('name', 'Valid Page')}"
            else:
                statuses["facebook"] = "⚠️ Invalid Token or Expired"
        except:
            statuses["facebook"] = "🌐 Network Error"
            
    if os.path.exists("client_secret.json"):
        statuses["youtube"] = "✅ OAuth File Found"
        
    return statuses

def build_caption(quran_data, cta_text="", reciter_name=""):
    urdu = "\n".join([v['urdu'] for v in quran_data['verses']])
    english = "\n".join([v['english'] for v in quran_data['verses']])
    reference = quran_data['reference'].split("| [BG:")[0].strip()

    caption = f"✨ {english}\n\n"
    caption += f"Urdu: {urdu} - 📖 {reference}\n\n"
    
    if reciter_name:
        clean_name = reciter_name.replace(" (Safe)", "").replace(" (High Copyright Risk)", "")
        caption += f"🎙️ Reciter: {clean_name}\n\n"
    else:
        caption += "\n"
        
    if cta_text:
        caption += f"👇 {cta_text}\n\n"

    caption += "#Quran #IslamicReels #QuranRecitation #Islam #Muslim #DailyAyah #QuranQuotes #Deen #Allah #Shorts"
    return caption

def get_temp_url(file_path):
    print("   > ☁️ Uploading to Temp Server for direct Meta Transfer...")
    try:
        with open(file_path, 'rb') as f:
            res = requests.post("https://tmpfiles.org/api/v1/upload", files={'file': f}).json()
            url = res['data']['url']
            direct_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
            return direct_url
    except Exception as e:
        print(f"   > ❌ Temp Server Error: {e}")
        return None

def upload_to_facebook(video_path, caption, page_id, token):
    print(f"   > 🌐 Uploading to Facebook Page: {page_id}...")
    url = f"https://graph.facebook.com/v19.0/{page_id}/videos"
    try:
        with open(video_path, 'rb') as video_file:
            payload = {'access_token': token, 'description': caption}
            files = {'source': video_file}
            res = requests.post(url, data=payload, files=files).json()
            if 'id' in res:
                print(f"   > ✅ FB Upload Success! Video ID: {res['id']}")
            else:
                print(f"   > ❌ FB Upload Error: {res}")
    except Exception as e:
        print(f"   > ❌ FB Exception: {e}")

def upload_to_instagram(video_url, caption, ig_id=None, token=None, cover_url=None, thumbnail_path=None):
    if not video_url: return
    
    # Support client.clip_upload-like calls with positional/keyword parameters
    # If a local path is passed, host it temporarily
    if os.path.exists(video_url):
        print(f"   > 🌐 Local video path detected. Hosting for Meta Graph API...")
        video_url = get_temp_url(video_url)
        if not video_url:
            print("   > ❌ Error: Failed to generate temporary public URL for local video.")
            return

    # If the third parameter is a local file path passed positionally (for thumbnail_path)
    if ig_id and isinstance(ig_id, str) and (ig_id.endswith(".jpg") or ig_id.endswith(".png") or os.path.exists(ig_id)):
        thumbnail_path = ig_id
        ig_id = None

    # If local thumbnail_path is provided, stage it to get cover_url
    if thumbnail_path and os.path.exists(thumbnail_path):
        print(f"   > 🖼️ Staging custom thumbnail path: {thumbnail_path}")
        cover_url = get_temp_url(thumbnail_path)
        if cover_url:
            print(f"   > ✅ Staged custom thumbnail from path: {thumbnail_path}")

    # Load credentials if missing
    if not ig_id or not token:
        import json
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r") as f:
                    settings_data = json.load(f)
                    for profile_settings in settings_data.values():
                        if not ig_id and profile_settings.get("ig_account_id"):
                            ig_id = profile_settings.get("ig_account_id")
                        if not token and profile_settings.get("fb_token"):
                            token = profile_settings.get("fb_token")
            except Exception as e:
                print(f"   > ⚠️ Failed to load settings.json to resolve IG credentials: {e}")

    if not ig_id or not token:
        print("   > ❌ Instagram upload failed: Missing ig_account_id or fb_token credentials.")
        return

    print(f"   > 🌐 Connecting to Instagram: {ig_id}...")
    try:
        url = f"https://graph.facebook.com/v19.0/{ig_id}/media"
        payload = {'access_token': token, 'caption': caption, 'media_type': 'REELS', 'video_url': video_url}
        
        # Attach custom thumbnail to payload
        if cover_url:
            payload['cover_url'] = cover_url
            print(f"   > 🖼️ Attached custom thumbnail to IG payload.")
            
        res = requests.post(url, data=payload).json()
        
        if 'id' in res:
            container_id = res['id']
            print(f"   > 📦 IG Container Created. Waiting for Meta to verify file...")
            is_ready = False
            status_url = f"https://graph.facebook.com/v19.0/{container_id}?fields=status_code&access_token={token}"
            
            for attempt in range(12):
                print(f"   > ⏳ Polling IG Status (Attempt {attempt + 1}/12)...")
                time.sleep(10) 
                status_res = requests.get(status_url).json()
                status_code = status_res.get('status_code', '')
                if status_code == 'FINISHED':
                    print("   > 🟢 IG Processing Complete! Publishing now...")
                    is_ready = True
                    break
                elif status_code == 'ERROR':
                    print("   > ❌ IG Processing Failed. Meta rejected the file.")
                    return
            if not is_ready: return
            
            publish_url = f"https://graph.facebook.com/v19.0/{ig_id}/media_publish"
            publish_payload = {'creation_id': container_id, 'access_token': token}
            pub_res = requests.post(publish_url, data=publish_payload).json()
            if 'id' in pub_res: print(f"   > ✅ IG Reel Published Successfully!")
            else: print(f"   > ❌ IG Publish Error: {pub_res}")
        else:
            print(f"   > ❌ IG Container Error: {res}")
    except Exception as e:
        print(f"   > ❌ IG Exception: {e}")

def get_authenticated_youtube_service(token_path):
    if not token_path:
        print("   > ❌ YT Error: No token path provided!")
        return None

    try:
        from googleapiclient.discovery import build
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
    except ImportError:
        print("   > ❌ YT Error: Missing required Google Libraries!")
        return None

    SCOPES = ['https://www.googleapis.com/auth/youtube.upload', 'https://www.googleapis.com/auth/youtube.readonly']
    creds = None

    if os.path.exists(token_path):
        print("   > ✅ Existing token found. Attempting login...")
        try:
            creds = Credentials.from_authorized_user_file(token_path, SCOPES)
        except Exception:
            pass
    else:
        print("   > ⚠️ No token found in this vault. A browser window will open to authenticate.")
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token: 
            try:
                print("   > 🔄 Token expired. Refreshing automatically...")
                creds.refresh(Request())
            except Exception:
                creds = None
        
        if not creds:
            if not os.path.exists('client_secret.json'): 
                print("   > ❌ YT Error: Missing client_secret.json in main directory!")
                return None
            print("   > 🌍 Opening browser for Google Authentication...")
            flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
            creds = flow.run_local_server(port=0, prompt='select_account consent')
            
        # Ensure parent directory exists
        os.makedirs(os.path.dirname(os.path.abspath(token_path)), exist_ok=True)
        with open(token_path, 'w') as token_file:
            token_file.write(creds.to_json())
        print("   > 💾 New OAuth Token saved securely to profile vault.")

    try:
        youtube = build('youtube', 'v3', credentials=creds)
        return youtube
    except Exception as e:
        print(f"   > ❌ YT build service exception: {e}")
        return None

def upload_to_youtube(video_path, title, description, token_path):
    print(f"   > 🌐 Initiating YouTube Upload Module...")
    print(f"   > 🔐 Target Token Vault: {token_path}")
    
    youtube = get_authenticated_youtube_service(token_path)
    if not youtube:
        return

    try:
        try:
            channel_res = youtube.channels().list(part='snippet', mine=True).execute()
            if channel_res.get('items'):
                channel_name = channel_res['items'][0]['snippet']['title']
                print(f"   > 📺 VERIFIED CHANNEL LOGIN: Logged in as '{channel_name}'")
            else:
                print("   > 📺 VERIFIED CHANNEL LOGIN: Unknown Channel")
                
        except Exception as e:
            print(f"   > 🛑 FATAL AUTHENTICATION ERROR: Old or corrupted token detected!")
            print(f"   > 🗑️ Auto-deleting the bad token from: {token_path}")
            if os.path.exists(token_path):
                os.remove(token_path)
            print("   > ❌ UPLOAD ABORTED to prevent posting to the wrong channel.")
            print("   > 🔄 ACTION REQUIRED: Please click 'Manual Upload' again. The browser WILL open this time!")
            return 

        body = {
            'snippet': {
                'title': title,
                'description': description,
                'tags': ['Quran', 'IslamicReels', 'Shorts', 'Allah', 'Deen'],
                'categoryId': '22'
            },
            'status': {'privacyStatus': 'public', 'selfDeclaredMadeForKids': False}
        }
        from googleapiclient.http import MediaFileUpload
        import socket
        import time
        
        chunksize = 1024 * 1024  # 1MB chunk size
        media = MediaFileUpload(video_path, chunksize=chunksize, resumable=True)
        print("   > 🚀 Pushing video file to YouTube Servers...")
        request = youtube.videos().insert(part=','.join(body.keys()), body=body, media_body=media)
        
        response = None
        while response is None:
            try:
                status, response = request.next_chunk()
                if status:
                    print(f"      [+] YouTube Upload Progress: {int(status.progress() * 100)}%")
            except (ConnectionResetError, socket.error, Exception) as e:
                print(f"      [!] Network connection reset detected ({e}). Re-establishing connection in 30 seconds...")
                time.sleep(30)
                # Continue the chunk resume loop without resetting the entire file upload progress
                continue
                
        if response and 'id' in response:
            print(f"   > ✅ YT Upload Success! Video ID: {response['id']}")
        else:
            print("   > ❌ YT Upload Failed: No response ID received.")
        
    except Exception as e:
        print(f"   > ❌ YT Upload Exception: {e}")

def run_all_uploads(video_path, quran_data, settings, abort_check=None, thumbnail_path=None):
    if not os.path.exists(video_path): return
        
    reciter_name = settings.get("reciter_name", "Unknown Reciter")
    caption = build_caption(quran_data, settings.get("cta_text", ""), reciter_name)
    
    print("\n========================================")
    print(f"🚀 INITIATING SOCIAL MEDIA UPLOADS...")
    print(f"📡 Meta Server Time: {get_meta_server_time()[0]}")
    print("========================================")

    # Staging Engine
    thumb_url = None
    if thumbnail_path:
        print(f"   > 🖼️ Staging custom thumbnail path: {thumbnail_path}")
        thumb_url = get_temp_url(thumbnail_path)
    elif settings.get("auto_thumbnail", False):
        import glob, random
        thumb_folder = "reciter_photos"
        if os.path.exists(thumb_folder):
            photos = glob.glob(f"{thumb_folder}/*.jpg") + glob.glob(f"{thumb_folder}/*.png")
            if photos:
                selected_photo = random.choice(photos)
                print(f"   > 🖼️ Uploading Thumbnail: {os.path.basename(selected_photo)}")
                thumb_url = get_temp_url(selected_photo)
                if thumb_url: print("   > ✅ Thumbnail staged successfully.")
            else:
                print(f"   > ⚠️ Warning: '{thumb_folder}' is empty. Skipping custom thumbnail.")

    # 1. Facebook
    if abort_check and not abort_check(): return
    if settings.get("enable_fb", True):
        if settings.get("fb_token") and settings.get("fb_page_id"):
            upload_to_facebook(video_path, caption, settings["fb_page_id"], settings["fb_token"])
        else:
            print("   > ⏭️ Skipping Facebook (Missing Token or Page ID)")
    else:
        print("   > ⏭️ Skipping Facebook (Turned off in settings)")

    # 2. Instagram
    if abort_check and not abort_check(): return
    if settings.get("enable_ig", True):
        if settings.get("ig_account_id") and settings.get("fb_token"):
            direct_url = get_temp_url(video_path)
            upload_to_instagram(direct_url, caption, settings["ig_account_id"], settings["fb_token"], cover_url=thumb_url, thumbnail_path=thumbnail_path)
        else:
            print("   > ⏭️ Skipping Instagram (Missing Token or IG ID)")
    else:
        print("   > ⏭️ Skipping Instagram (Turned off in settings)")

    # 3. YouTube
    if abort_check and not abort_check(): return
    if settings.get("enable_yt", True):
        clean_yt_ref = quran_data['reference'].split("| [BG:")[0].strip()
        yt_title = f"Beautiful Quran Recitation - {clean_yt_ref} ✨"
        
        current_profile = settings.get("current_profile_name", "Main Page")
        if getattr(sys, 'frozen', False):
            install_dir = os.path.dirname(sys.executable)
        else:
            install_dir = os.path.dirname(os.path.abspath(__file__))
            
        profile_yt_token = os.path.join(install_dir, "credentials", current_profile, "token.json")
        
        upload_to_youtube(video_path, yt_title, caption, profile_yt_token)
    else:
        print("   > ⏭️ Skipping YouTube (Turned off in settings)")

    print("========================================")
