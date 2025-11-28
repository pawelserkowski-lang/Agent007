import cv2
import numpy as np
from PIL import Image

class VisionProcessor:
    @staticmethod
    def process_image(image_path, threshold_percent=6):
        img = cv2.imread(image_path)
        if img is None: return None, "Błąd pliku"
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        thresh_val = int(255 * (threshold_percent / 100.0))
        _, binary = cv2.threshold(gray, thresh_val, 255, cv2.THRESH_BINARY)
        kernel = np.ones((5,5), np.uint8)
        morphed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=2)
        morphed = cv2.morphologyEx(morphed, cv2.MORPH_OPEN, kernel, iterations=2)
        contours, _ = cv2.findContours(morphed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if not contours: return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB)), "Brak obiektu"
        c = max(contours, key=cv2.contourArea)
        x, y, w, h = cv2.boundingRect(c)
        cropped = img[y:y+h, x:x+w]
        return Image.fromarray(cv2.cvtColor(cropped, cv2.COLOR_BGR2RGB)), f"Wycięto: {w}x{h}"
