import os
import datetime

app_data_dir = os.path.join(os.environ.get('APPDATA', ''), 'IslamicReelsStudio')
ig_file = os.path.join(app_data_dir, "output", "instagram", "reel_Main Page.mp4")
yt_file = os.path.join(app_data_dir, "output", "youtube", "reel_Main Page.mp4")

print("Current UTC Time:", datetime.datetime.now(datetime.timezone.utc))

for name, path in [("Instagram Video", ig_file), ("YouTube Video", yt_file)]:
    if os.path.exists(path):
        mtime = os.path.getmtime(path)
        mtime_utc = datetime.datetime.fromtimestamp(mtime, datetime.timezone.utc)
        print(f"{name} Mod Time (UTC): {mtime_utc}")
    else:
        print(f"{name} does NOT exist at {path}")
