from PIL import Image, ImageDraw, ImageFont

# Create a 512x512 image with a light blue background
img = Image.new('RGB', (512, 512), color='#63b3ed')
d = ImageDraw.Draw(img)

# Draw a white circle in the middle
d.ellipse((100, 100, 412, 412), fill='white')

# Try to load a nice font, fallback to default if not found
try:
    font = ImageFont.truetype("arial.ttf", 250)
except:
    font = ImageFont.load_default()

# Draw a purple "J" in the center
d.text((200, 150), "J", fill='#7c3aed', font=font)

# Save the icon
img.save("app_icon.png")
print("✅ Icon saved as app_icon.png! Ready for RuStore!")