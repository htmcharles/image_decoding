import cv2
import numpy as np
import sys

# Allow passing the image path via CLI, fallback to default
qr_image = sys.argv[1] if len(sys.argv) > 1 else "qrcode.png"

# Read the image
image = cv2.imread(qr_image)

if image is None:
    print(f"Error: Unable to read image '{qr_image}'")
    print("Please provide a valid image path.")
    sys.exit(1)

# Initialize QR code detector
detector = cv2.QRCodeDetector()

# Detect and decode the QR code
data, points, _ = detector.detectAndDecode(image)

if data:
    print("=" * 60)
    print("QR Code Decoder Output:")
    print("=" * 60)
    print(f"QR Code Data: {data}")
    print("=" * 60)
    
    # Draw polygon around the QR code
    if points is not None:
        points = points.astype(int)
        cv2.polylines(image, [points], True, (0, 255, 0), 2)
        
        # Annotate the decoded data beside the bounding box
        # Get the top-left point for text placement
        top_left = tuple(points[0][0])
        cv2.putText(image, data, (top_left[0], top_left[1] - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
    
    # Save decoded text to file
    with open("decoded_qrcode.txt", "w", encoding="utf-8") as f:
        f.write(data)
    print(f"Decoded text saved to: decoded_qrcode.txt")
    
    # Save annotated image
    annotated_image_path = "annotated_qrcode.png"
    cv2.imwrite(annotated_image_path, image)
    print(f"Annotated image saved as {annotated_image_path}")
    
    # Display the image
    cv2.imshow("QR Code with Annotation", image)
    print("Press any key to close the window.")
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print("=" * 60)
    print("No QR code detected.")
    print("=" * 60)
    print("Tips:")
    print("- Ensure the image is clear and the QR code is fully visible")
    print("- Try rotating the image if the QR code is at an angle")
    print("- Check if the image has sufficient contrast")
    sys.exit(1)