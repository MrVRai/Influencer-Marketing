import os
import sys
import math
import subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import random

# Output specs
WIDTH = 1080
HEIGHT = 1920
FPS = 30
DURATION_SEC = 10
TOTAL_FRAMES = FPS * DURATION_SEC

# Color Palette
BG_COLOR = (8, 12, 22)
PRIMARY = (99, 102, 241)        # #6366F1
PRIMARY_LIGHT = (165, 180, 252)  # #A5B4FC
ACCENT = (236, 72, 153)         # #EC4899
CYAN = (6, 182, 212)            # #06B6D4
GREEN = (16, 185, 129)          # #10B981
CARD_BG = (15, 22, 38)
CARD_BORDER = (28, 41, 68)
TEXT_WHITE = (255, 255, 255)
TEXT_MUTED = (148, 163, 184)

FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REGULAR = "C:/Windows/Fonts/segoeui.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_stars(draw, frame_idx, star_data):
    for x, y, size, speed, base_alpha in star_data:
        alpha = int(base_alpha + 60 * math.sin(frame_idx * speed))
        alpha = max(30, min(255, alpha))
        draw.ellipse([x, y, x + size, y + size], fill=(alpha, alpha, alpha))

def draw_orbit_ring(draw, cx, cy, rx, ry, angle_deg, color, width=3):
    rad = math.radians(angle_deg)
    cos_a = math.cos(rad)
    sin_a = math.sin(rad)
    
    points = []
    num_steps = 120
    for i in range(num_steps + 1):
        theta = 2 * math.pi * (i / num_steps)
        ex = rx * math.cos(theta)
        ey = ry * math.sin(theta)
        
        px = cx + (ex * cos_a - ey * sin_a)
        py = cy + (ex * sin_a + ey * cos_a)
        points.append((px, py))
        
    for i in range(len(points) - 1):
        draw.line([points[i], points[i+1]], fill=color, width=width)

def render_video():
    logo_path = os.path.abspath("../branding/creator_orbit_official_logo.png")
    out_video_path = os.path.abspath("../branding/creator_orbit_launch_video.mp4")
    
    # Load and prepare logo
    if os.path.exists(logo_path):
        raw_logo = Image.open(logo_path).convert("RGBA")
    else:
        raw_logo = Image.new("RGBA", (240, 240), PRIMARY)
        
    random.seed(42)
    stars = []
    for _ in range(120):
        sx = random.randint(0, WIDTH)
        sy = random.randint(0, HEIGHT)
        size = random.choice([2, 2, 3, 4])
        speed = random.uniform(0.04, 0.12)
        base_alpha = random.randint(70, 180)
        stars.append((sx, sy, size, speed, base_alpha))

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{WIDTH}x{HEIGHT}",
        "-pix_fmt", "rgba",
        "-r", str(FPS),
        "-i", "-",
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-preset", "medium",
        "-crf", "18",
        out_video_path
    ]

    print(f"Starting rendering of {TOTAL_FRAMES} frames ({DURATION_SEC}s @ {FPS}fps)...")
    process = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    for frame in range(TOTAL_FRAMES):
        t_sec = frame / FPS
        
        img = Image.new("RGBA", (WIDTH, HEIGHT), BG_COLOR)
        
        # Ambient cosmic background glows
        ambient = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
        adraw = ImageDraw.Draw(ambient)
        
        pulse = 0.5 + 0.5 * math.sin(frame * 0.08)
        adraw.ellipse([WIDTH//2 - 320, 400 - 150, WIDTH//2 + 320, 700 + 150], 
                      fill=(79, 70, 229, int(25 + 20 * pulse)))
        adraw.ellipse([WIDTH - 350, HEIGHT - 450, WIDTH + 200, HEIGHT + 100], 
                      fill=(236, 72, 153, 20))
        ambient = ambient.filter(ImageFilter.GaussianBlur(80))
        img = Image.alpha_composite(img, ambient)
        
        draw = ImageDraw.Draw(img)
        draw_stars(draw, frame, stars)
        
        # TOP HEADER
        draw.text((70, 80), "CREATOR ORBIT", font=get_font(FONT_BOLD, 22), fill=PRIMARY_LIGHT)
        draw.text((WIDTH - 260, 80), "OFFICIAL LAUNCH", font=get_font(FONT_BOLD, 20), fill=ACCENT)
        draw.line([(70, 125), (WIDTH - 70, 125)], fill=CARD_BORDER, width=2)
        
        # Center Logo Y
        logo_center_y = 560
        
        # Spinning 3D Orbital Rings
        angle1 = (frame * 2.2) % 360
        angle2 = (frame * -1.8 + 60) % 360
        angle3 = (frame * 1.2 + 120) % 360
        
        draw_orbit_ring(draw, WIDTH//2, logo_center_y, 190, 80, angle1, (99, 102, 241, 140), width=3)
        draw_orbit_ring(draw, WIDTH//2, logo_center_y, 220, 95, angle2, (236, 72, 153, 130), width=3)
        draw_orbit_ring(draw, WIDTH//2, logo_center_y, 240, 110, angle3, (6, 182, 212, 110), width=2)
        
        # Center Circular Logo
        logo_size = 200
        resized_logo = raw_logo.resize((logo_size, logo_size), Image.LANCZOS)
        mask = Image.new("L", (logo_size, logo_size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, logo_size, logo_size], fill=255)
        
        lx = (WIDTH - logo_size) // 2
        ly = logo_center_y - logo_size // 2
        
        draw.ellipse([lx - 12, ly - 12, lx + logo_size + 12, ly + logo_size + 12], 
                     outline=(99, 102, 241, int(120 + 80 * pulse)), width=3)
        draw.ellipse([lx - 6, ly - 6, lx + logo_size + 6, ly + logo_size + 6], 
                     outline=PRIMARY_LIGHT, width=2)
        img.paste(resized_logo, (lx, ly), mask)
        
        draw_orbit_ring(draw, WIDTH//2, logo_center_y, 190, 80, angle1 + 180, (165, 180, 252, 200), width=3)
        
        # DYNAMIC SCENES
        if t_sec < 3.2:
            font_t = get_font(FONT_BOLD, 22)
            ttxt = "ORBIT BEYOND ORDINARY"
            draw.text(((WIDTH - font_t.getbbox(ttxt)[2]) // 2, 730), ttxt, font=font_t, fill=ACCENT)
            
            font_h = get_font(FONT_BOLD, 52)
            h1 = "CREATOR ORBIT"
            draw.text(((WIDTH - font_h.getbbox(h1)[2]) // 2, 800), h1, font=font_h, fill=TEXT_WHITE)
            
            font_sub = get_font(FONT_REGULAR, 26)
            s1 = "Performance Creator Marketing"
            s2 = "for Fast-Growing Indian D2C Brands"
            draw.text(((WIDTH - font_sub.getbbox(s1)[2]) // 2, 880), s1, font=font_sub, fill=PRIMARY_LIGHT)
            draw.text(((WIDTH - font_sub.getbbox(s2)[2]) // 2, 925), s2, font=font_sub, fill=TEXT_MUTED)
            
            hy = 1050
            draw.rounded_rectangle([100, hy, WIDTH - 100, hy + 90], radius=16, fill=CARD_BG, outline=CARD_BORDER, width=2)
            hl1 = "100% Founder-Vetted Roster  •  0% Middlemen Markup"
            font_hl = get_font(FONT_BOLD, 22)
            draw.text(((WIDTH - font_hl.getbbox(hl1)[2]) // 2, hy + 30), hl1, font=font_hl, fill=TEXT_WHITE)

        elif t_sec < 6.8:
            font_lb = get_font(FONT_BOLD, 22)
            live_txt = "🚀 WE ARE OFFICIALLY LIVE"
            bw = font_lb.getbbox(live_txt)[2] + 40
            bx = (WIDTH - bw) // 2
            draw.rounded_rectangle([bx, 720, bx + bw, 765], radius=20, fill=(236, 72, 153, 40), outline=ACCENT, width=2)
            draw.text((bx + 20, 730), live_txt, font=font_lb, fill=TEXT_WHITE)
            
            font_h = get_font(FONT_BOLD, 46)
            draw.text(((WIDTH - font_h.getbbox("Scale Your D2C Brand")[2]) // 2, 800), "Scale Your D2C Brand", font=font_h, fill=TEXT_WHITE)
            draw.text(((WIDTH - font_h.getbbox("With Authentic Creator Reviews")[2]) // 2, 860), "With Authentic Creator Reviews", font=font_h, fill=PRIMARY_LIGHT)
            
            cards = [
                ("🎁", "Scalable Barter Seeding", "50 to 500+ creators per campaign with zero markup", GREEN),
                ("🛡️", "ORBIT MATCH™ Quality", "1.5%–2%+ verified organic reach & brand safety", CYAN),
                ("📦", "Turnkey Warehouse Logistics", "Phone-verified dispatch sheets direct to your team", PRIMARY_LIGHT)
            ]
            
            cy_start = 970
            for ci, (cicon, ctitle, cdesc, ccol) in enumerate(cards):
                cy = cy_start + ci * 115
                draw.rounded_rectangle([90, cy, WIDTH - 90, cy + 98], radius=16, fill=CARD_BG, outline=CARD_BORDER, width=2)
                draw.text((120, cy + 18), cicon, font=get_font(FONT_BOLD, 26), fill=ccol)
                draw.text((170, cy + 18), ctitle, font=get_font(FONT_BOLD, 22), fill=TEXT_WHITE)
                draw.text((170, cy + 52), cdesc, font=get_font(FONT_REGULAR, 17), fill=TEXT_MUTED)

        else:
            font_t = get_font(FONT_BOLD, 22)
            ttxt = "READY TO LAUNCH?"
            draw.text(((WIDTH - font_t.getbbox(ttxt)[2]) // 2, 725), ttxt, font=font_t, fill=ACCENT)
            
            font_h = get_font(FONT_BOLD, 46)
            c1 = "Get Your Custom 1-Page"
            c2 = "Creator Roster"
            draw.text(((WIDTH - font_h.getbbox(c1)[2]) // 2, 785), c1, font=font_h, fill=TEXT_WHITE)
            draw.text(((WIDTH - font_h.getbbox(c2)[2]) // 2, 845), c2, font=font_h, fill=PRIMARY_LIGHT)
            
            draw.rounded_rectangle([90, 940, WIDTH - 90, 1190], radius=22, fill=CARD_BG, outline=PRIMARY, width=2)
            
            draw.rounded_rectangle([120, 970, WIDTH - 120, 1035], radius=12, fill=(79, 70, 229, 60), outline=PRIMARY, width=1)
            dm_txt = "💬 Drop us a DM with \"ROSTER\" on @thecreatororbit"
            font_dm = get_font(FONT_BOLD, 20)
            draw.text(((WIDTH - font_dm.getbbox(dm_txt)[2]) // 2, 990), dm_txt, font=font_dm, fill=TEXT_WHITE)
            
            draw.rounded_rectangle([120, 1055, WIDTH - 120, 1120], radius=12, fill=(6, 182, 212, 30), outline=CYAN, width=1)
            web_txt = "🌐 Visit thecreatororbit.vercel.app"
            font_web = get_font(FONT_BOLD, 20)
            draw.text(((WIDTH - font_web.getbbox(web_txt)[2]) // 2, 1075), web_txt, font=font_web, fill=CYAN)
            
            mail_txt = "✉️ thecreatororbit.media@gmail.com"
            font_m = get_font(FONT_REGULAR, 18)
            draw.text(((WIDTH - font_m.getbbox(mail_txt)[2]) // 2, 1145), mail_txt, font=font_m, fill=TEXT_MUTED)

        # BOTTOM AGENCY CREDENTIALS CARD
        fy = 1580
        draw.rounded_rectangle([70, fy, WIDTH - 70, fy + 220], radius=20, fill=CARD_BG, outline=CARD_BORDER, width=2)
        
        draw.text((110, fy + 25), "AGENCY OPERATIONS", font=get_font(FONT_BOLD, 14), fill=PRIMARY_LIGHT)
        draw.text((110, fy + 55), "Founder-Led Creator Engine", font=get_font(FONT_BOLD, 30), fill=TEXT_WHITE)
        draw.text((110, fy + 105), "Creator Orbit Media | Pan-India Reach", font=get_font(FONT_BOLD, 18), fill=CYAN)
        draw.text((110, fy + 145), "📍 New Delhi & Uttarakhand  •  Serving Brands Pan-India", font=get_font(FONT_REGULAR, 18), fill=TEXT_MUTED)
        
        draw.text(((WIDTH - get_font(FONT_BOLD, 18).getbbox("🌌 ORBIT BEYOND ORDINARY")[2]) // 2, HEIGHT - 65),
                  "🌌 ORBIT BEYOND ORDINARY", font=get_font(FONT_BOLD, 18), fill=ACCENT)
        
        process.stdin.write(img.tobytes())
        
        if frame % 60 == 0:
            print(f"Rendered frame {frame}/{TOTAL_FRAMES} ({t_sec:.1f}s)...")

    process.stdin.close()
    process.wait()
    print(f"\nSUCCESS! Launch Reel Video saved at: {out_video_path}")

if __name__ == "__main__":
    render_video()
