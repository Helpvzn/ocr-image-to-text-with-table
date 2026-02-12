import sys
import os

# Ensure ocr_tool is in path
sys.path.append(os.path.join(os.getcwd(), 'ocr_tool'))

print("DEBUG: Importing LocalOCREngine...")
from local_ocr_engine import LocalOCREngine

import cv2
import numpy as np

print("DEBUG: Initializing Engine...")
try:
    engine = LocalOCREngine()
    print("DEBUG: Engine initialized. Configuration:")
    # print internal config if possible
except Exception as e:
    print(f"DEBUG: Engine Init Failed: {e}")
    sys.exit(1)

print("DEBUG: Creating dummy image...")
img = np.zeros((500, 500, 3), dtype=np.uint8)
cv2.putText(img, "Hello World", (50, 250), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)

print("DEBUG: Processing image...")
try:
    res = engine.process_image(img)
    print("DEBUG: Processing Complete!")
    print(f"DEBUG: Result keys: {res.keys()}")
except Exception as e:
    print(f"DEBUG: Processing Failed: {e}")
    import traceback
    traceback.print_exc()

print("DEBUG: Finished.")
