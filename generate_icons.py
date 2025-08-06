from PIL import Image
import os

# Path to original image
original_path = 'static/uploads/unnamed.png'

# Output directory
output_dir = 'static/icons'
os.makedirs(output_dir, exist_ok=True)

# Load original image
img = Image.open(original_path)

# Resize and save
sizes = [192, 512]
for size in sizes:
    resized = img.resize((size, size))
    output_path = os.path.join(output_dir, f'icon-{size}x{size}.png')
    resized.save(output_path)
    print(f"✅ Saved: {output_path}")