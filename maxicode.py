import subprocess
import os
import sys
import cv2
import numpy as np
from urllib.parse import quote

# -----------------------------
# CONFIG: Paths to ZXing JARs
# -----------------------------
JAVASE_JAR = "javase-3.5.0.jar"
CORE_JAR = "core-3.5.0.jar"
JCOMMANDER_JAR = "jcommander-1.82.jar"

# -----------------------------
# FUNCTION: Decode barcode
# -----------------------------
def decode_barcode(image_path):
    """Decodes a barcode using ZXing Java library."""
    if not os.path.exists(image_path):
        return f"Error: Image not found at {image_path}"

    for jar in [JAVASE_JAR, CORE_JAR, JCOMMANDER_JAR]:
        if not os.path.exists(jar):
            return f"Error: Required ZXing JAR not found: {jar}"

    image_abs = os.path.abspath(image_path)
    image_abs_forward = image_abs.replace("\\", "/")
    file_uri = f"file:///{quote(image_abs_forward)}"

    classpath = f"{JAVASE_JAR};{CORE_JAR};{JCOMMANDER_JAR}"  # Windows
    cmd = [
        "java", "-cp", classpath,
        "com.google.zxing.client.j2se.CommandLineRunner",
        file_uri
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        output = result.stdout.strip()

        # Parse Raw and Parsed results
        output_lines = output.splitlines()
        raw_result = ""
        parsed_result = ""
        points = []

        for i, line in enumerate(output_lines):
            if line.startswith("Raw result:"):
                # Take next non-empty line as raw result
                for j in range(i+1, len(output_lines)):
                    candidate = output_lines[j].strip()
                    if candidate:
                        raw_result = candidate
                        break
            if line.startswith("Parsed result:"):
                for j in range(i+1, len(output_lines)):
                    candidate = output_lines[j].strip()
                    if candidate:
                        parsed_result = candidate
                        break
            if line.startswith("  Point"):
                parts = line.split(":")[1].strip().replace("(", "").replace(")", "").split(",")
                points.append((int(float(parts[0])), int(float(parts[1]))))

        return {
            "raw": raw_result,
            "parsed": parsed_result,
            "points": points,
            "full_output": output
        }

    except subprocess.CalledProcessError as e:
        return f"Error running Java: {e.stderr}"

# -----------------------------
# FUNCTION: Draw bounding box
# -----------------------------
def draw_bounding_box(image_path, points, save_path="annotated_barcode.png"):
    """Draws a polygon around barcode points and saves the annotated image."""
    if not points or len(points) < 4:
        print("No bounding box points detected. Skipping drawing.")
        return

    image = cv2.imread(image_path)
    if image is None:
        print("Error: Unable to read image for drawing.")
        return

    points_array = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
    cv2.polylines(image, [points_array], isClosed=True, color=(0, 255, 0), thickness=2)
    cv2.imwrite(save_path, image)
    print(f"Annotated image saved as {save_path}")

    cv2.imshow("Detected Barcode", image)
    print("Press any key to close the window.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# -----------------------------
# MAIN
# -----------------------------
if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else "./images/maxi-code.png"
    decoded = decode_barcode(image_path)

    print("\n=== DECODED OUTPUT ===")
    if isinstance(decoded, dict):
        print(f"Raw result: {decoded['raw']}")
        print(f"Parsed result: {decoded['parsed']}")
        print("\nFull ZXing Output:")
        print(decoded['full_output'])

        # Draw bounding box if points exist
        draw_bounding_box(image_path, decoded['points'])
    else:
        print(decoded)
