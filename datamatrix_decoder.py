import cv2
import numpy as np
import subprocess
import os
import sys
import shutil
from urllib.parse import quote

# Paths to required files
javase_jar = "javase-3.5.0.jar"
core_jar = "core-3.5.0.jar"
jcommander_jar = "jcommander-1.82.jar"

# Allow passing the image path via CLI, fallback to default
datamatrix_image = sys.argv[1] if len(sys.argv) > 1 else "datamatrix_image.jpg"

# Normalize paths for Docker and local Java
image_abs = os.path.abspath(datamatrix_image)
image_abs_forward = image_abs.replace("\\", "/")
image_name = os.path.basename(datamatrix_image)

# Validate required files
for file in [javase_jar, core_jar, jcommander_jar]:
    if not os.path.exists(file):
        print(f"Warning: {file} not found in current directory!")
        print("Please ensure you run this script from the Decoding folder.")

if not os.path.exists(datamatrix_image):
    print(f"Warning: Image file {datamatrix_image} not found!")
    print("Please provide the correct image path.")

def docker_command():
    # Docker command to detect the Data Matrix code and get its position
    return [
        "docker", "run", "--rm",
        "-v", f"{os.getcwd()}:/app",
        "openjdk:17",
        "java", "-cp",
        f"/app/{javase_jar}:/app/{core_jar}:/app/{jcommander_jar}",
        "com.google.zxing.client.j2se.CommandLineRunner",
        f"/app/{image_name}"
    ]

def local_java_command():
    # Local Java command (Windows uses ';' as classpath separator)
    classpath = f"{javase_jar};{core_jar};{jcommander_jar}"
    # Build a proper file URI to avoid ZXing URI parsing issues on Windows drive letters
    file_uri = f"file:///{quote(image_abs_forward)}"
    return [
        "java", "-cp", classpath,
        "com.google.zxing.client.j2se.CommandLineRunner",
        file_uri
    ]

def attempt_decode(current_image_path: str) -> str:
    """Run ZXing through Docker or local Java for the given image path.
    Returns the raw stdout from ZXing."""
    global image_abs, image_abs_forward, image_name

    # Update normalized paths for this candidate image
    image_abs = os.path.abspath(current_image_path)
    image_abs_forward = image_abs.replace("\\", "/")
    image_name = os.path.basename(current_image_path)

    out = ""
    ran = False

    if shutil.which("docker") is not None:
        try:
            result = subprocess.run(docker_command(), capture_output=True, text=True, check=True)
            out = result.stdout.strip()
            ran = True
        except Exception as e:
            print("Docker failed, attempting local Java fallback:", e)

    if not ran:
        if shutil.which("java") is None:
            print("Neither Docker nor Java is available. Install Docker Desktop or a JDK (Java 17).")
            sys.exit(1)
        try:
            result = subprocess.run(local_java_command(), capture_output=True, text=True, check=True)
            out = result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print("Local Java decoding failed:")
            print(e.stderr)
            sys.exit(1)

    return out

# Try original and rotated variants for robustness
candidates = [datamatrix_image]
try:
    img = cv2.imread(datamatrix_image)
    if img is not None:
        variants = {
            "datamatrix_rot90.jpg": cv2.rotate(img, cv2.ROTATE_90_CLOCKWISE),
            "datamatrix_rot270.jpg": cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE),
            "datamatrix_rot180.jpg": cv2.rotate(img, cv2.ROTATE_180),
        }
        for name, mat in variants.items():
            cv2.imwrite(name, mat)
            candidates.append(name)
except Exception:
    pass

output = ""
decoded_text = ""
for candidate in candidates:
    output = attempt_decode(candidate)
    if "No barcode found" not in output:
        # Extract the decoded text from ZXing output
        lines = output.splitlines()
        for line in lines:
            if line.strip() and not line.startswith("Raw") and not line.startswith("  Point") and not line.startswith("Parsed") and not line.startswith("Found"):
                # The decoded content is usually after the "Raw" line or the main line
                if decoded_text == "":
                    decoded_text = line.strip()
                elif line.strip() and not line.strip().startswith("Raw"):
                    # Sometimes the decoded text is on a separate line
                    potential_text = line.strip()
                    if len(potential_text) > 0 and not potential_text.startswith("("):
                        decoded_text = potential_text
        break

print("=" * 60)
print("Data Matrix Decoder Output:")
print("=" * 60)
print(output)
print("=" * 60)

if decoded_text:
    print(f"\nDecoded Text: {decoded_text}")
    # Save decoded text to file
    with open("decoded_datamatrix.txt", "w", encoding="utf-8") as f:
        f.write(decoded_text)
    print("Decoded text saved to: decoded_datamatrix.txt")
else:
    print("\nNo text could be extracted from the Data Matrix code.")
    # Try to parse output for any text
    if output:
        lines = output.splitlines()
        for line in lines:
            if "Raw result:" in line or "Parsed result:" in line:
                parts = line.split(":", 1)
                if len(parts) > 1:
                    decoded_text = parts[1].strip()
                    print(f"Extracted text: {decoded_text}")
                    with open("decoded_datamatrix.txt", "w", encoding="utf-8") as f:
                        f.write(decoded_text)
                    break

# Parse the ZXing output for barcode position
points = []
for line in output.splitlines():
    if line.startswith("  Point"):
        parts = line.split(":")[1].strip().replace("(", "").replace(")", "").split(",")
        points.append((int(float(parts[0])), int(float(parts[1]))))

# If points are found, draw a bounding polygon
if len(points) >= 4:
    # Load the image with OpenCV
    image = cv2.imread(datamatrix_image)
    if image is None:
        print("Error: Unable to read the image!")
    else:
        # Draw a polygon connecting the points
        points_array = np.array(points, dtype=np.int32).reshape((-1, 1, 2))
        print(f"\nDrawing polygon with points: {points}")

        cv2.polylines(image, [points_array], isClosed=True, color=(0, 255, 0), thickness=2)

        # Save and display the annotated image
        annotated_image_path = "annotated_datamatrix.png"
        cv2.imwrite(annotated_image_path, image)
        print(f"Annotated image saved as {annotated_image_path}")

        # Display the image
        cv2.imshow("Detected Data Matrix Code", image)
        print("Press any key to close the window.")
        cv2.waitKey(0)
        cv2.destroyAllWindows()
else:
    print("\nNo bounding box points detected.")

# Clean up rotation variants
for variant in ["datamatrix_rot90.jpg", "datamatrix_rot270.jpg", "datamatrix_rot180.jpg"]:
    if os.path.exists(variant):
        try:
            os.remove(variant)
        except:
            pass