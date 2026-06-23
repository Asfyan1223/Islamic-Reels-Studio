import requests
import random

def get_quran_data(min_duration_sec=20, custom_surah=None, custom_ayah=None, reciter_code="ar.husary", video_mode="Arabic Voice + Bilingual (Urdu)"):
    # 🌟 We fetch up to 70s of text data, so audio_generator can strictly cut it off at 55s!
    BATCH_FETCH_LIMIT = 70 
    
    print(f"   > 📡 Connecting to Live API (Fetching text batch to calculate true audio duration)...")
    
    while True: 
        if custom_surah and custom_ayah:
            first_endpoint = f"{custom_surah}:{custom_ayah}"
            print(f"   > 🎯 Custom Request: Surah {custom_surah}, Ayah {custom_ayah}")
        else:
            first_endpoint = str(random.randint(1, 6200))
        
        def fetch_ayah(endpoint):
            fetch_reciter = "ar.husary" if reciter_code == "ar.yasseraddussary" else reciter_code
            url = f"http://api.alquran.cloud/v1/ayah/{endpoint}/editions/quran-uthmani,ur.jalandhry,en.sahih,{fetch_reciter}"
            try:
                res = requests.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()["data"]
                    surah_num = data[0]['surah']['number']
                    ayah_num = data[0]['numberInSurah']
                    
                    if reciter_code == "ar.yasseraddussary":
                        audio_url = f"https://everyayah.com/data/Yasser_Ad-Dussary_128kbps/{surah_num:03d}{ayah_num:03d}.mp3"
                    else:
                        audio_url = data[3]["audio"]
                        
                    return {
                        "arabic": data[0]["text"],
                        "urdu": data[1]["text"],
                        "english": data[2]["text"],
                        "audio_url": audio_url, 
                        "surah_name": data[2]['surah']['englishName'],
                        "surah_num": surah_num, 
                        "ayah_num": ayah_num,
                        "absolute_num": data[0]['number'] 
                    }
            except Exception as e:
                print(f"   > ❌ Error fetching Ayah: {e}")
            return None

        def estimate_duration(verse_data):
            dur = len(verse_data["arabic"].split()) * 1.0 
            if video_mode in ["Arabic + Urdu", "Arabic Voice + Bilingual (Urdu)"]:
                dur += len(verse_data["urdu"].split()) * 0.4
            elif video_mode == "Urdu Only":
                dur = len(verse_data["urdu"].split()) * 0.4
            elif video_mode == "Arabic Only":
                dur = len(verse_data["arabic"].split()) * 1.0
            return dur

        first_verse = fetch_ayah(first_endpoint)
        if not first_verse:
            print("   > ❌ Network Error. Failed to fetch verse.")
            return None
            
        verses_data = []
        total_estimated_duration = 0.0

        verses_data.append(first_verse)
        total_estimated_duration += estimate_duration(first_verse)
        
        current_absolute_num = first_verse["absolute_num"]
        surah_boundary_hit = False
        
        # We fetch extra so the true audio firewall can cut it down properly
        while total_estimated_duration < BATCH_FETCH_LIMIT:
            current_absolute_num += 1
            next_verse = fetch_ayah(str(current_absolute_num))
            
            if not next_verse:
                print("   > ⚠️ Reached end of Quran or API limit.")
                break 

            if next_verse["surah_name"] != first_verse["surah_name"]:
                print("   > ⚠️ Reached end of Surah. Building batch with what we have.")
                surah_boundary_hit = True
                break

            verses_data.append(next_verse)
            total_estimated_duration += estimate_duration(next_verse)

        if not (custom_surah and custom_ayah) and surah_boundary_hit and total_estimated_duration < (min_duration_sec - 5):
            print("   > 🔄 Random selection was too close to the end of the Surah. Retrying...")
            continue 

        break 

    print(f"   > 📜 Fetched text block. Moving to Audio Engine for True Duration Firewall.")

    # The audio engine will rebuild the reference, so we just return the raw verse list
    return {"reference": "PENDING", "verses": verses_data}
