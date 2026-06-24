import os
import json
import glob
import sys

print("=== DIAGNOSING ENVIRONMENT STATE ===")
print("Current Cwd:", os.getcwd())

app_data_dir = os.path.join(os.environ.get('APPDATA', ''), 'IslamicReelsStudio')
print("Expected App Data Dir:", app_data_dir)

# Check settings.json in Cwd and in AppData
local_settings_path = "settings.json"
appdata_settings_path = os.path.join(app_data_dir, "settings.json")

print("\n--- Settings Files ---")
if os.path.exists(local_settings_path):
    print(f"Local settings.json exists. Size: {os.path.getsize(local_settings_path)} bytes")
    try:
        with open(local_settings_path, "r") as f:
            data = json.load(f)
            print("Profiles in Local settings.json:", list(data.keys()))
            for p, s in data.items():
                print(f"  Profile '{p}': enable_ig={s.get('enable_ig')}, enable_fb={s.get('enable_fb')}, enable_yt={s.get('enable_yt')}, auto_upload={s.get('auto_upload')}")
    except Exception as e:
        print("  Error reading local settings:", e)
else:
    print("Local settings.json does NOT exist.")

if os.path.exists(appdata_settings_path):
    print(f"AppData settings.json exists. Size: {os.path.getsize(appdata_settings_path)} bytes")
    try:
        with open(appdata_settings_path, "r") as f:
            data = json.load(f)
            print("Profiles in AppData settings.json:", list(data.keys()))
            for p, s in data.items():
                print(f"  Profile '{p}': enable_ig={s.get('enable_ig')}, enable_fb={s.get('enable_fb')}, enable_yt={s.get('enable_yt')}, auto_upload={s.get('auto_upload')}")
    except Exception as e:
        print("  Error reading AppData settings:", e)
else:
    print("AppData settings.json does NOT exist.")

# Check last_rendered_video JSON files
print("\n--- Last Rendered Video JSON Files ---")
json_files = glob.glob("last_rendered_video_*.json") + glob.glob(os.path.join(app_data_dir, "last_rendered_video_*.json"))
for jf in json_files:
    print(f"File: {jf}")
    try:
        with open(jf, "r") as f:
            print("  Content:", f.read())
    except Exception as e:
        print("  Error reading:", e)

# Check output files
print("\n--- Output Directory Contents ---")
for root, dirs, files in os.walk("output"):
    for file in files:
        print(os.path.join(root, file))

for root, dirs, files in os.walk(os.path.join(app_data_dir, "output")):
    for file in files:
        print(os.path.join(root, file))

print("=== DIAGNOSIS COMPLETE ===")
