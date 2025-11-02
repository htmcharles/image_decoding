from pdf417decoder import PDF417Decoder
from PIL import Image
import re

def decode_pdf417(image_path):
    # Open the image
    image = Image.open(image_path)
    decoder = PDF417Decoder(image)
    
    # Decode barcodes
    barcode_count = decoder.decode()
    if barcode_count > 0:
        for i, raw_bytes in enumerate(decoder.barcodes_data):
            # Decode raw bytes
            text = raw_bytes.decode('utf-8', errors='ignore')
            
            print(f"\n--- RAW PDF417 Barcode {i+1} ---")
            print(text)
            
            # --- Clean the text ---
            clean_text = re.sub(r'[^A-Za-z0-9\s]', '', text)        # Remove symbols
            clean_text = re.sub(r'[A-Za-z]{20,}', '', clean_text)   # Remove long junk sequences
            clean_text = re.sub(r'\s+', ' ', clean_text).strip()    # Normalize whitespace
            
            print("\n--- CLEANED TEXT ---")
            print(clean_text)

            # --- Extract likely fields ---
            name_match = re.search(r'\b([A-Z]{3,}[A-Z]*[a-z]+)\b', clean_text)
            id_match = re.search(r'\b\d{7,}\b', clean_text)
            year_match = re.search(r'\b(19|20)\d{2}\b', clean_text)
            date_match = re.search(r'\b\d{6}\b', clean_text)

            print("\n--- EXTRACTED DATA ---")
            if id_match:
                print("ID Number:", id_match.group(0))
            if year_match:
                print("Birth Year:", year_match.group(0))
            if name_match:
                print("Name:", name_match.group(1))
            if date_match:
                print("Possible Date (YYMMDD or similar):", date_match.group(0))
        return True
    else:
        print("No PDF417 barcodes detected.")
        return False


if __name__ == "__main__":
    image_path = "./images/encoded-image.jpg"  # replace with your image path
    decode_pdf417(image_path)
