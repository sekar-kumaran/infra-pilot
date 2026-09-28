import time
import random
import urllib.request
import urllib.error

url = "http://backend:8000/api/items"

def generate_traffic():
    while True:
        try:
            req = urllib.request.Request(url)
            urllib.request.urlopen(req)
            print("Request successful")
        except urllib.error.URLError as e:
            print(f"Request failed: {e}")
        time.sleep(random.uniform(0.1, 1.0))

if __name__ == "__main__":
    time.sleep(5) # wait for backend to start
    generate_traffic()
