import requests
import os

print("Testing tmpfiles.org upload...")
test_file = "test_temp.txt"
with open(test_file, "w") as f:
    f.write("Hello, Meta Graph API testing!")

try:
    with open(test_file, "rb") as f:
        res = requests.post("https://tmpfiles.org/api/v1/upload", files={'file': f})
        print("Status Code:", res.status_code)
        json_res = res.json()
        print("Response:", json_res)
        url = json_res['data']['url']
        direct_url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
        print("Direct URL:", direct_url)
except Exception as e:
    print("Error:", e)
finally:
    if os.path.exists(test_file):
        os.remove(test_file)
