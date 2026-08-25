import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH = 1080
HEIGHT = 1350

# Refined Luxury Dark Mode Palette
BG_MAIN = (8, 12, 22)         # #080C16
CARD_BG = (15, 22, 38)        # #0F1626
CARD_BORDER = (28, 41, 68)    # #1C2944
PRIMARY = (99, 102, 241)      # #6366F1 Electric Indigo
PRIMARY_LIGHT = (165, 180, 252) # #A5B4FC
ACCENT = (236, 72, 153)       # #EC4899 Pink
CYAN = (6, 182, 212)          # #06B6D4
GREEN = (16, 185, 129)        # #10B981
RED = (244, 63, 94)           # #F43F5E
TEXT_MAIN = (255, 255, 255)
TEXT_SUB = (203, 213, 225)    # #CBD5E1
TEXT_MUTED = (148, 163, 184)  # #94A3B8

FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REGULAR = "C:/Windows/Fonts/segoeui.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def create_canvas():
    img = Image.new("RGBA", (WIDTH, HEIGHT), BG_MAIN)
    # Subtle top & bottom ambient light
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    gdraw = ImageDraw.Draw(glow)
    gdraw.ellipse([WIDTH//2 - 350, -200, WIDTH//2 + 350, 300], fill=(79, 70, 229, 30))
    gdraw.ellipse([WIDTH - 300, HEIGHT - 300, WIDTH + 200, HEIGHT + 200], fill=(6, 182, 212, 20))
    glow = glow.filter(ImageFilter.GaussianBlur(100))
    return Image.alpha_composite(img, glow)

def draw_header(draw, slide_index, section_tag):
    # Top Bar: Agency Tag & Section
    draw.text((70, 65), "CREATOR ORBIT", font=get_font(FONT_BOLD, 19), fill=PRIMARY_LIGHT)
    draw.text((250, 65), f"|  {section_tag}", font=get_font(FONT_BOLD, 17), fill=TEXT_MUTED)
    
    # Counter Badge
    counter = f"0{slide_index} / 05"
    draw.text((WIDTH - 150, 65), counter, font=get_font(FONT_BOLD, 18), fill=TEXT_MUTED)
    
    # Thin divider line
    draw.line([(70, 105), (WIDTH - 70, 105)], fill=CARD_BORDER, width=1)

def draw_footer(draw, cta_text="SWIPE ➔"):
    # Thin divider line
    draw.line([(70, HEIGHT - 105), (WIDTH - 70, HEIGHT - 105)], fill=CARD_BORDER, width=1)
    
    # Bottom Bar
    draw.text((70, HEIGHT - 75), "@thecreatororbit", font=get_font(FONT_REGULAR, 20), fill=TEXT_MUTED)
    draw.text((WIDTH - 200, HEIGHT - 75), cta_text, font=get_font(FONT_BOLD, 20), fill=PRIMARY_LIGHT)

def render_slide_1(out_path, logo_path):
    img = create_canvas()
    draw = ImageDraw.Draw(img)
    draw_header(draw, 1, "OFFICIAL AGENCY LAUNCH")
    draw_footer(draw, "SWIPE ➔")
    
    # Centered Logo with double glow ring
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA").resize((180, 180), Image.LANCZOS)
        mask = Image.new("L", (180, 180), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, 180, 180], fill=255)
        
        lx = (WIDTH - 180) // 2
        ly = 200
        # Rings
        draw.ellipse([lx - 12, ly - 12, lx + 192, ly + 192], outline=(99, 102, 241, 60), width=2)
        draw.ellipse([lx - 6, ly - 6, lx + 186, ly + 186], outline=PRIMARY, width=3)
        img.paste(logo, (lx, ly), mask)
    
    # Agency Name
    font_name = get_font(FONT_BOLD, 24)
    name_txt = "CREATOR ORBIT"
    draw.text(((WIDTH - font_name.getbbox(name_txt)[2]) // 2, 420), name_txt, font=font_name, fill=PRIMARY_LIGHT)
    
    # Tagline
    font_tag = get_font(FONT_BOLD, 15)
    tag_txt = "ORBIT BEYOND ORDINARY"
    draw.text(((WIDTH - font_tag.getbbox(tag_txt)[2]) // 2, 460), tag_txt, font=font_tag, fill=ACCENT)
    
    # Main Headline
    font_h1 = get_font(FONT_BOLD, 48)
    line1 = "Performance Creator Marketing"
    line2 = "for High-Growth Indian D2C Brands"
    draw.text(((WIDTH - font_h1.getbbox(line1)[2]) // 2, 530), line1, font=font_h1, fill=TEXT_MAIN)
    draw.text(((WIDTH - font_h1.getbbox(line2)[2]) // 2, 595), line2, font=font_h1, fill=TEXT_MAIN)
    
    # Subheading
    font_sub = get_font(FONT_REGULAR, 21)
    sub1 = "Founder-curated creator seeding & authentic UGC campaigns"
    sub2 = "built specifically for high-growth Indian Beauty & Skincare brands."
    draw.text(((WIDTH - font_sub.getbbox(sub1)[2]) // 2, 690), sub1, font=font_sub, fill=TEXT_SUB)
    draw.text(((WIDTH - font_sub.getbbox(sub2)[2]) // 2, 725), sub2, font=font_sub, fill=TEXT_SUB)
    
    # 3 Stat Cards
    cw = (WIDTH - 140 - 30) // 3
    stats = [
        ("100%", "FOUNDER-VETTED ROSTER", PRIMARY),
        ("0%", "MIDDLEMEN MARKUP", GREEN),
        ("~15 DAYS", "CAMPAIGN TURNAROUND", CYAN)
    ]
    
    sy = 810
    for i, (val, lbl, col) in enumerate(stats):
        cx = 70 + i * (cw + 15)
        draw.rounded_rectangle([cx, sy, cx + cw, sy + 180], radius=16, fill=CARD_BG, outline=CARD_BORDER, width=2)
        
        # Stat Val
        font_v = get_font(FONT_BOLD, 36)
        draw.text((cx + (cw - font_v.getbbox(val)[2]) // 2, sy + 38), val, font=font_v, fill=col)
        
        # Stat Lbl
        font_l = get_font(FONT_BOLD, 13)
        words = lbl.split()
        if len(words) == 3:
            l1 = words[0] + " " + words[1]
            l2 = words[2]
            draw.text((cx + (cw - font_l.getbbox(l1)[2]) // 2, sy + 95), l1, font=font_l, fill=TEXT_MUTED)
            draw.text((cx + (cw - font_l.getbbox(l2)[2]) // 2, sy + 120), l2, font=font_l, fill=TEXT_MUTED)
        else:
            draw.text((cx + (cw - font_l.getbbox(lbl)[2]) // 2, sy + 105), lbl, font=font_l, fill=TEXT_MUTED)
            
    # Bottom Callout Banner
    draw.rounded_rectangle([70, 1030, WIDTH - 70, 1120], radius=14, fill=(18, 25, 45), outline=PRIMARY, width=1)
    call_txt = "🎁 Scalable Barter Seeding  •  ⚡ Performance UGC  •  💎 Paid Whitelisting"
    font_c = get_font(FONT_BOLD, 17)
    draw.text(((WIDTH - font_c.getbbox(call_txt)[2]) // 2, 1060), call_txt, font=font_c, fill=TEXT_SUB)
    
    img.convert("RGB").save(out_path, "PNG", quality=98)
    print(f"Saved: {out_path}")

def render_slide_2(out_path):
    img = create_canvas()
    draw = ImageDraw.Draw(img)
    draw_header(draw, 2, "THE INDUSTRY BOTTLENECK")
    draw_footer(draw, "OUR SOLUTION ➔")
    
    # Headline
    font_h = get_font(FONT_BOLD, 42)
    draw.text((70, 145), "Why Traditional Influencer", font=font_h, fill=TEXT_MAIN)
    draw.text((70, 200), "Marketing Burns D2C Budgets", font=font_h, fill=RED)
    
    # 4 Structured Pain Point Rows
    pains = [
        ("01", "HIDDEN AGENCY MARKUPS", "Brands pay 3x–5x inflated creator fees with zero transparency on true creator commercials. Budgets get drained on agency retainers instead of reach."),
        ("02", "ENDLESS DM & SPREADSHEET CHAOS", "Spending 80+ hours hunting addresses, tracking courier pincodes, and chasing ghosted creators for drafts."),
        ("03", "VANITY REACH & BOT ENGAGEMENT", "Paying top-tier fees for big follower counts with near-zero authentic organic engagement or verified buyer intent."),
        ("04", "LOGISTICS & DISPATCH FRICTION", "Wrong size variants, delayed couriers, and untracked parcels stalling crucial product launches and marketing calendars.")
    ]
    
    sy = 290
    card_h = 165
    gap = 18
    
    for i, (num, title, desc) in enumerate(pains):
        y = sy + i * (card_h + gap)
        draw.rounded_rectangle([70, y, WIDTH - 70, y + card_h], radius=16, fill=CARD_BG, outline=CARD_BORDER, width=2)
        
        # Red Tag
        draw.rounded_rectangle([95, y + 25, 140, y + 65], radius=8, fill=(45, 20, 30), outline=RED, width=1)
        draw.text((105, y + 32), num, font=get_font(FONT_BOLD, 17), fill=RED)
        
        # Title
        draw.text((155, y + 32), title, font=get_font(FONT_BOLD, 20), fill=TEXT_MAIN)
        
        # Desc
        font_d = get_font(FONT_REGULAR, 18)
        words = desc.split()
        lines = []
        cur = ""
        for w in words:
            t = cur + " " + w if cur else w
            if font_d.getbbox(t)[2] < (WIDTH - 210):
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        
        for li, line in enumerate(lines[:3]):
            draw.text((95, y + 80 + li * 26), line, font=font_d, fill=TEXT_MUTED)
            
    # Bottom callout box
    draw.rounded_rectangle([70, 1060, WIDTH - 70, 1140], radius=12, fill=(35, 18, 25), outline=RED, width=1)
    callout = "\"Influencer marketing shouldn't feel like a full-time operational headache.\""
    font_co = get_font(FONT_BOLD, 18)
    draw.text(((WIDTH - font_co.getbbox(callout)[2]) // 2, 1088), callout, font=font_co, fill=TEXT_SUB)
    
    img.convert("RGB").save(out_path, "PNG", quality=98)
    print(f"Saved: {out_path}")

def render_slide_3(out_path):
    img = create_canvas()
    draw = ImageDraw.Draw(img)
    draw_header(draw, 3, "THE CREATOR ORBIT ENGINE")
    draw_footer(draw, "OUR PROGRAMS ➔")
    
    # Headline
    font_h = get_font(FONT_BOLD, 42)
    draw.text((70, 145), "A Performance-First Infrastructure", font=font_h, fill=TEXT_MAIN)
    draw.text((70, 200), "Built For Predictable Creator ROI", font=font_h, fill=PRIMARY_LIGHT)
    
    # 3 Solution Pillars
    pillars = [
        ("🎯", "CURATED BEAUTY & SKINCARE NETWORK", "Direct-access, handpicked creators across Indian Beauty, Skincare & Lifestyle with zero middlemen markup.", PRIMARY),
        ("📦", "FRICTIONLESS DISPATCH LOGISTICS", "We provide 100% phone-verified addresses, names, and variants directly to your warehouse. Your team simply ships; we manage all follow-ups, QC & live link tracking.", CYAN),
        ("🛡️", "THE ORBIT MATCH™ VETTING STANDARD", "Our proprietary 5-pillar quality framework guaranteeing 1.5%–2.0%+ verified organic reach, aesthetic hooks, and strict brand safety.", GREEN)
    ]
    
    sy = 290
    card_h = 220
    gap = 22
    
    for i, (icon, title, desc, col) in enumerate(pillars):
        y = sy + i * (card_h + gap)
        draw.rounded_rectangle([70, y, WIDTH - 70, y + card_h], radius=18, fill=CARD_BG, outline=CARD_BORDER, width=2)
        
        # Icon Pill
        draw.rounded_rectangle([95, y + 24, 145, y + 70], radius=10, fill=(25, 35, 60), outline=col, width=2)
        draw.text((106, y + 30), icon, font=get_font(FONT_BOLD, 22), fill=col)
        
        # Title
        draw.text((160, y + 34), title, font=get_font(FONT_BOLD, 21), fill=TEXT_MAIN)
        
        # Desc
        font_d = get_font(FONT_REGULAR, 19)
        words = desc.split()
        lines = []
        cur = ""
        for w in words:
            t = cur + " " + w if cur else w
            if font_d.getbbox(t)[2] < (WIDTH - 210):
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        
        for li, line in enumerate(lines[:3]):
            draw.text((95, y + 90 + li * 28), line, font=font_d, fill=TEXT_MUTED)
            
    # ORBIT MATCH Framework Pill
    draw.rounded_rectangle([70, 1050, WIDTH - 70, 1140], radius=14, fill=(18, 26, 48), outline=PRIMARY, width=1)
    fw_lbl = "THE ORBIT MATCH™ STANDARD"
    fw_desc = "O — Originality  •  R — Relevance  •  B — Brand Safety  •  I — Ideal Audience  •  T — True Engagement"
    font_fl = get_font(FONT_BOLD, 14)
    font_fd = get_font(FONT_BOLD, 16)
    draw.text(((WIDTH - font_fl.getbbox(fw_lbl)[2]) // 2, 1065), fw_lbl, font=font_fl, fill=PRIMARY_LIGHT)
    draw.text(((WIDTH - font_fd.getbbox(fw_desc)[2]) // 2, 1098), fw_desc, font=font_fd, fill=TEXT_MAIN)
    
    img.convert("RGB").save(out_path, "PNG", quality=98)
    print(f"Saved: {out_path}")

def render_slide_4(out_path):
    img = create_canvas()
    draw = ImageDraw.Draw(img)
    draw_header(draw, 4, "OUR CAMPAIGN PROGRAMS")
    draw_footer(draw, "GET STARTED ➔")
    
    # Headline
    font_h = get_font(FONT_BOLD, 42)
    draw.text((70, 145), "Scalable Creator Programs", font=font_h, fill=TEXT_MAIN)
    draw.text((70, 200), "Tailored For Your Growth Stage", font=font_h, fill=CYAN)
    
    # 3 Service Packages
    programs = [
        ("01", "HIGH-VOLUME BARTER & SEEDING", "200, 500, or 1,000+ verified creators posting authentic reels & reviews. Generates 800K–5M+ organic views with zero creator fee markups.", GREEN, "MOST POPULAR"),
        ("02", "PERFORMANCE UGC VIDEO CREATIVES", "High-retention video hooks, unboxings, and 7-day routine formats crafted specifically for your Meta & Instagram ad library.", PRIMARY, "FOR PERFORMANCE TEAMS"),
        ("03", "CURATED PAID & WHITELISTED SCALE", "Handpicked high-converting creators with Meta partnership ad codes, dedicated deliverables, and guaranteed view reach.", ACCENT, "SCALE CAMPAIGNS")
    ]
    
    sy = 290
    card_h = 220
    gap = 22
    
    for i, (num, title, desc, col, badge) in enumerate(programs):
        y = sy + i * (card_h + gap)
        draw.rounded_rectangle([70, y, WIDTH - 70, y + card_h], radius=18, fill=CARD_BG, outline=CARD_BORDER, width=2)
        
        # Number Badge
        draw.rounded_rectangle([95, y + 24, 145, y + 70], radius=10, fill=(25, 35, 60), outline=col, width=2)
        draw.text((106, y + 30), num, font=get_font(FONT_BOLD, 22), fill=col)
        
        # Title
        draw.text((160, y + 34), title, font=get_font(FONT_BOLD, 20), fill=TEXT_MAIN)
        
        # Pill Tag on right
        font_b = get_font(FONT_BOLD, 12)
        bw = font_b.getbbox(badge)[2] + 20
        draw.rounded_rectangle([WIDTH - 95 - bw, y + 28, WIDTH - 95, y + 58], radius=12, fill=col)
        draw.text((WIDTH - 85 - bw, y + 35), badge, font=font_b, fill=(8, 12, 22))
        
        # Desc
        font_d = get_font(FONT_REGULAR, 19)
        words = desc.split()
        lines = []
        cur = ""
        for w in words:
            t = cur + " " + w if cur else w
            if font_d.getbbox(t)[2] < (WIDTH - 210):
                cur = t
            else:
                lines.append(cur)
                cur = w
        if cur: lines.append(cur)
        
        for li, line in enumerate(lines[:3]):
            draw.text((95, y + 90 + li * 28), line, font=font_d, fill=TEXT_MUTED)
            
    # Turnaround Guarantee Banner
    draw.rounded_rectangle([70, 1050, WIDTH - 70, 1140], radius=14, fill=(12, 30, 35), outline=GREEN, width=1)
    g_title = "⚡ ~15-DAY CAMPAIGN TURNAROUND GUARANTEE"
    g_desc = "From creator selection to dispatch sheet delivery and first live posts."
    font_gt = get_font(FONT_BOLD, 16)
    font_gd = get_font(FONT_REGULAR, 16)
    draw.text(((WIDTH - font_gt.getbbox(g_title)[2]) // 2, 1065), g_title, font=font_gt, fill=GREEN)
    draw.text(((WIDTH - font_gd.getbbox(g_desc)[2]) // 2, 1098), g_desc, font=font_gd, fill=TEXT_MAIN)
    
    img.convert("RGB").save(out_path, "PNG", quality=98)
    print(f"Saved: {out_path}")

def render_slide_5(out_path, logo_path):
    img = create_canvas()
    draw = ImageDraw.Draw(img)
    draw_header(draw, 5, "GET STARTED")
    draw_footer(draw, "@thecreatororbit")
    
    # Headline
    font_h = get_font(FONT_BOLD, 42)
    draw.text((70, 145), "Ready to Launch Your Next", font=font_h, fill=TEXT_MAIN)
    draw.text((70, 200), "High-ROI Creator Campaign?", font=font_h, fill=PRIMARY_LIGHT)
    
    # Main CTA Action Box
    draw.rounded_rectangle([70, 290, WIDTH - 70, 680], radius=22, fill=CARD_BG, outline=PRIMARY, width=2)
    
    # Subtitle
    font_ct = get_font(FONT_BOLD, 26)
    draw.text((105, 335), "Get a Custom 1-Page Creator Roster", font=font_ct, fill=TEXT_MAIN)
    font_cs = get_font(FONT_REGULAR, 18)
    draw.text((105, 375), "Tailored specifically for your brand's category, target cities & budget.", font=font_cs, fill=TEXT_MUTED)
    
    # 3 Direct Actions
    actions = [
        ("💬", "Direct DM", "Drop us a DM with \"ROSTER\" on Instagram @thecreatororbit"),
        ("🌐", "Live Website", "Visit thecreatororbit.vercel.app for packages & economics"),
        ("✉️", "Direct Email", "Reach us at thecreatororbit.media@gmail.com")
    ]
    
    for i, (icon, title, desc) in enumerate(actions):
        ay = 425 + i * 75
        draw.rounded_rectangle([105, ay, WIDTH - 105, ay + 62], radius=12, fill=(22, 31, 52), outline=CARD_BORDER, width=1)
        draw.text((125, ay + 16), icon, font=get_font(FONT_BOLD, 20), fill=PRIMARY)
        draw.text((165, ay + 13), title, font=get_font(FONT_BOLD, 17), fill=PRIMARY_LIGHT)
        draw.text((165, ay + 35), desc, font=get_font(FONT_REGULAR, 15), fill=TEXT_SUB)
        
    # Founders Section Card
    draw.rounded_rectangle([70, 715, WIDTH - 70, 990], radius=20, fill=CARD_BG, outline=CARD_BORDER, width=2)
    
    draw.text((105, 745), "MEET THE FOUNDERS", font=get_font(FONT_BOLD, 15), fill=PRIMARY_LIGHT)
    
    font_fn = get_font(FONT_BOLD, 30)
    draw.text((105, 780), "Vedant Rai & Manya Jain", font=font_fn, fill=TEXT_MAIN)
    
    font_fr = get_font(FONT_BOLD, 18)
    draw.text((105, 830), "Co-Founders | Creator Orbit", font=font_fr, fill=CYAN)
    
    font_fl = get_font(FONT_REGULAR, 18)
    draw.text((105, 870), "📍 New Delhi & Uttarakhand  •  Serving Fast-Growing D2C Brands Pan-India", font=font_fl, fill=TEXT_MUTED)
    
    draw.text((105, 915), "Selection Core: Audience Match • Content Quality • Engagement • Budget Fit • Relevance", font=get_font(FONT_REGULAR, 15), fill=TEXT_SUB)
    
    # Tagline Banner
    draw.rounded_rectangle([70, 1025, WIDTH - 70, 1115], radius=14, fill=(20, 26, 48), outline=PRIMARY, width=1)
    tag_txt = "🌌 ORBIT BEYOND ORDINARY"
    font_tb = get_font(FONT_BOLD, 22)
    draw.text(((WIDTH - font_tb.getbbox(tag_txt)[2]) // 2, 1055), tag_txt, font=font_tb, fill=ACCENT)
    
    img.convert("RGB").save(out_path, "PNG", quality=98)
    print(f"Saved: {out_path}")

def main():
    logo_path = os.path.abspath("../branding/creator_orbit_official_logo.png")
    out_dir = os.path.abspath("../branding/launch_slides")
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Generating Ultra-Realistic Agency Launch Carousel in {out_dir}...")
    render_slide_1(os.path.join(out_dir, "slide_1_cover.png"), logo_path)
    render_slide_2(os.path.join(out_dir, "slide_2_problem.png"))
    render_slide_3(os.path.join(out_dir, "slide_3_solution.png"))
    render_slide_4(os.path.join(out_dir, "slide_4_programs.png"))
    render_slide_5(os.path.join(out_dir, "slide_5_cta.png"), logo_path)
    print("All 5 refined realistic slides successfully generated!")

if __name__ == "__main__":
    main()
