from paddleocr import PPStructure
import shutil
import os

# 1. Try to load (it will likely fail based on user report)
print("Attempting to load PPStructure with orientation...")
try:
    p = PPStructure(image_orientation=True, show_log=True)
    print("SUCCESS: Model loaded.")
except Exception as e:
    print(f"FAILURE: {e}")
    # 2. If it fails, delete the cache
    cache_dir = os.path.expanduser('~/.paddleclas')
    if os.path.exists(cache_dir):
        print(f"Deleting corrupted cache: {cache_dir}")
        shutil.rmtree(cache_dir)
        print("Cache deleted. Retrying load (this will re-download model)...")
        try:
            p = PPStructure(image_orientation=True, show_log=True)
            print("SUCCESS: Model re-downloaded and loaded.")
        except Exception as e2:
            print(f"RETRY FAILURE: {e2}")
    else:
        print("Cache dir not found, strange.")
