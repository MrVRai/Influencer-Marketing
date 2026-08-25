import os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

WIDTH = 1080
HEIGHT = 1350
BG_COLOR = (10, 14, 26)  # #0A0E1A
PRIMARY = (99, 102, 241)  # #6366F1
ACCENT = (236, 72, 153)  # #EC4899
CYAN = (6, 182, 212)     # #06B6D4
GREEN = (16, 185, 129)   # #10B981
RED = (244, 63, 94)      # #F43F5E
CARD_BG = (19, 27, 46)   # #131B2E
BORDER = (35, 47, 72)    # #232F48
TEXT_LIGHT = (248, 250, 252)
TEXT_MUTED = (148, 163, 184)
GOLD = (251, 191, 36)

# Fonts
FONT_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REGULAR = "C:/Windows/Fonts/segoeui.ttf"
FONT_SEMI = "C:/Windows/Fonts/segoeui.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def draw_header_bar(draw, slide_num, total_slides=5):
    # Top agency badge
    draw.text((60, 60), "CREATOR ORBIT", font=get_font(FONT_BOLD, 22), fill=PRIMARY)
    # Slide counter
    counter_text = f"0{slide_num} / 0{total_slides}"
    draw.text((WIDTH - 140, 60), counter_text, font=get_font(FONT_BOLD, 22), fill=TEXT_MUTED)

def draw_footer_bar(draw, text="SWIPE ➔"):
    # Bottom brand and swipe reminder
    draw.text((60, HEIGHT - 80), "@thecreatororbit", font=get_font(FONT_REGULAR, 22), fill=TEXT_MUTED)
    draw.text((WIDTH - 200, HEIGHT - 80), text, font=get_font(FONT_BOLD, 22), fill=PRIMARY)

def draw_card(draw, x1, y1, x2, y2, bg=CARD_BG, border=BORDER, radius=20):
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=bg, outline=border, width=2)

def draw_badge(draw, text, x, y, bg=(99, 102, 241, 60), border=PRIMARY, text_color=TEXT_LIGHT, font_size=20):
    font = get_font(FONT_BOLD, font_size)
    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0] + 36
    h = bbox[3] - bbox[1] + 20
    draw.rounded_rectangle([x, y, x + w, y + h], radius=h//2, fill=(25, 34, 58), outline=border, width=2)
    draw.text((x + 18, y + 10), text, font=font, fill=text_color)
    return w, h

def create_base_canvas():
    img = Image.new("RGBA", (WIDTH, HEIGHT), BG_COLOR)
    # Add subtle cosmic glow in corners
    glow = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)
    glow_draw.ellipse([-100, -100, 500, 500], fill=(79, 70, 229, 35))
    glow_draw.ellipse([WIDTH - 400, HEIGHT - 400, WIDTH + 100, HEIGHT + 100], fill=(236, 72, 153, 30))
    glow = glow.filter(ImageFilter.GaussianBlur(80))
    img = Image.alpha_composite(img, glow)
    return img

def render_slide_1(output_path, logo_path):
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    
    # Header & Footer
    draw_header_bar(draw, 1)
    draw_footer_bar(draw, "SWIPE ➔")
    
    # Centered Logo
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize((220, 220), Image.LANCZOS)
        
        # Circle mask
        mask = Image.new("L", (220, 220), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([0, 0, 220, 220], fill=255)
        
        logo_x = (WIDTH - 220) // 2
        logo_y = 260
        
        # Glow ring behind logo
        draw.ellipse([logo_x - 12, logo_y - 12, logo_x + 232, logo_y + 232], fill=(99, 102, 241, 40), outline=PRIMARY, width=4)
        img.paste(logo, (logo_x, logo_y), mask)
    
    # Category Pill
    draw_badge(draw, "OFFICIAL AGENCY LAUNCH", (WIDTH - 340) // 2, 540, text_color=TEXT_LIGHT, font_size=20)
    
    # Main Headline
    font_h1 = get_font(FONT_BOLD, 54)
    text_h1_1 = "ORBIT BEYOND"
    text_h1_2 = "ORDINARY."
    draw.text(((WIDTH - font_h1.getbbox(text_h1_1)[2]) // 2, 620), text_h1_1, font=font_h1, fill=TEXT_LIGHT)
    draw.text(((WIDTH - font_h1.getbbox(text_h1_2)[2]) // 2, 690), text_h1_2, font=font_h1, fill=PRIMARY)
    
    # Subhead
    font_sub = get_font(FONT_REGULAR, 26)
    sub_text1 = "Performance Creator Marketing"
    sub_text2 = "for Fast-Growing Indian D2C Brands"
    draw.text(((WIDTH - font_sub.getbbox(sub_text1)[2]) // 2, 800), sub_text1, font=font_sub, fill=TEXT_LIGHT)
    draw.text(((WIDTH - font_sub.getbbox(sub_text2)[2]) // 2, 840), sub_text2, font=font_sub, fill=TEXT_MUTED)
    
    # Pill Stats Banner
    draw_card(draw, 60, 930, WIDTH - 60, 1070, bg=CARD_BG, border=BORDER, radius=20)
    
    # 3 Mini Stats inside Card
    col_w = (WIDTH - 120) // 3
    
    stat1_val, stat1_lbl = "4,300+", "CREATOR ROSTER"
    stat2_val, stat2_lbl = "0%", "MIDDLEMEN MARKUP"
    stat3_val, stat3_lbl = "~15 DAYS", "TURNAROUND"
    
    font_stat_val = get_font(FONT_BOLD, 32)
    font_stat_lbl = get_font(FONT_BOLD, 14)
    
    # Col 1
    x1 = 60 + col_w * 0 + col_w // 2
    draw.text((x1 - font_stat_val.getbbox(stat1_val)[2] // 2, 960), stat1_val, font=font_stat_val, fill=PRIMARY)
    draw.text((x1 - font_stat_lbl.getbbox(stat1_lbl)[2] // 2, 1010), stat1_lbl, font=font_stat_lbl, fill=TEXT_MUTED)
    
    # Col 2
    x2 = 60 + col_w * 1 + col_w // 2
    draw.text((x2 - font_stat_val.getbbox(stat2_val)[2] // 2, 960), stat2_val, font=font_stat_val, fill=GREEN)
    draw.text((x2 - font_stat_lbl.getbbox(stat2_lbl)[2] // 2, 1010), stat2_lbl, font=font_stat_lbl, fill=TEXT_MUTED)
    
    # Col 3
    x3 = 60 + col_w * 2 + col_w // 2
    draw.text((x3 - font_stat_val.getbbox(stat3_val)[2] // 2, 960), stat3_val, font=font_stat_val, fill=CYAN)
    draw.text((x3 - font_stat_lbl.getbbox(stat3_lbl)[2] // 2, 1010), stat3_lbl, font=font_stat_lbl, fill=TEXT_MUTED)
    
    # Swipe CTA at bottom
    swipe_text = "Swipe to see how we're fixing creator marketing ➔"
    font_swipe = get_font(FONT_BOLD, 22)
    draw.text(((WIDTH - font_swipe.getbbox(swipe_text)[2]) // 2, 1140), swipe_text, font=font_swipe, fill=ACCENT)
    
    img.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"Saved: {output_path}")

def render_slide_2(output_path):
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    
    draw_header_bar(draw, 2)
    draw_footer_bar(draw, "THE SOLUTION ➔")
    
    # Tag
    draw_badge(draw, "THE PROBLEM WITH THE INDUSTRY", 60, 130, border=RED, text_color=RED)
    
    # Headline
    font_h = get_font(FONT_BOLD, 46)
    draw.text((60, 200), "Why Traditional Influencer", font=font_h, fill=TEXT_LIGHT)
    draw.text((60, 260), "Marketing Is Broken.", font=font_h, fill=RED)
    
    # 4 Pain Points
    pains = [
        ("HIDDEN AGENCY MARKUPS", "Brands pay 3x–5x inflated creator fees while creators get pennies. Zero transparency on actual costs.", RED),
        ("ENDLESS DM & SPREADSHEET CHAOS", "Spending 80+ hours hunting addresses, following up on drafts, and managing ghosted creators.", RED),
        ("VANITY METRICS & BOT ENGAGEMENT", "Paying for high follower counts with near-zero verified organic reach or buyer intent.", RED),
        ("OPERATIONAL & COURIER BOTTLENECK", "Managing manual dispatches, wrong sizes, lost tracking, and delayed reviews instead of growing.", RED)
    ]
    
    start_y = 360
    card_h = 160
    gap = 20
    
    for i, (title, desc, color) in enumerate(pains):
        y = start_y + i * (card_h + gap)
        draw_card(draw, 60, y, WIDTH - 60, y + card_h, bg=CARD_BG, border=BORDER, radius=18)
        
        # Icon / Cross
        draw.text((90, y + 25), "✕", font=get_font(FONT_BOLD, 26), fill=color)
        
        # Title
        draw.text((135, y + 25), title, font=get_font(FONT_BOLD, 22), fill=TEXT_LIGHT)
        
        # Desc (multiline wrapped)
        font_d = get_font(FONT_REGULAR, 19)
        # Simple wrap
        words = desc.split()
        lines = []
        cur_line = ""
        for w in words:
            test = cur_line + " " + w if cur_line else w
            if font_d.getbbox(test)[2] < (WIDTH - 240):
                cur_line = test
            else:
                lines.append(cur_line)
                cur_line = w
        if cur_line:
            lines.append(cur_line)
            
        for line_idx, line in enumerate(lines[:2]):
            draw.text((135, y + 68 + line_idx * 30), line, font=font_d, fill=TEXT_MUTED)
            
    # Bottom callout
    draw_card(draw, 60, 1100, WIDTH - 60, 1190, bg=(35, 20, 30), border=RED, radius=16)
    quote = "\"Influencer marketing shouldn't feel like a full-time operational nightmare.\""
    font_q = get_font(FONT_BOLD, 20)
    draw.text(((WIDTH - font_q.getbbox(quote)[2]) // 2, 1132), quote, font=font_q, fill=TEXT_LIGHT)
    
    img.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"Saved: {output_path}")

def render_slide_3(output_path):
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    
    draw_header_bar(draw, 3)
    draw_footer_bar(draw, "OUR PROGRAMS ➔")
    
    # Tag
    draw_badge(draw, "THE CREATOR ORBIT ADVANTAGE", 60, 130, border=PRIMARY, text_color=PRIMARY)
    
    # Headline
    font_h = get_font(FONT_BOLD, 46)
    draw.text((60, 200), "A Performance-First", font=font_h, fill=TEXT_LIGHT)
    draw.text((60, 260), "Creator Engine.", font=font_h, fill=PRIMARY)
    
    # 3 Main Pillars
    pillars = [
        ("4,300+ DIRECT CREATOR ROSTER", "Verified Indian creators in Beauty, Skincare, Fashion, Fitness & Lifestyle — no middlemen markups.", GREEN),
        ("FRICTIONLESS DISPATCH LOGISTICS", "We collect 100% verified addresses, phone numbers & variants. Your warehouse simply ships; we handle all tracking & drafts.", CYAN),
        ("THE ORBIT MATCH™ STANDARD", "5-pillar quality vetting framework guaranteeing 1.5%–2%+ organic reach, aesthetic hooks, and brand safety.", PRIMARY)
    ]
    
    start_y = 360
    card_h = 210
    gap = 25
    
    for i, (title, desc, color) in enumerate(pillars):
        y = start_y + i * (card_h + gap)
        draw_card(draw, 60, y, WIDTH - 60, y + card_h, bg=CARD_BG, border=BORDER, radius=20)
        
        # Checkmark Icon
        draw.rounded_rectangle([90, y + 25, 135, y + 70], radius=8, fill=color)
        draw.text((102, y + 30), "✓", font=get_font(FONT_BOLD, 26), fill=(10, 14, 26))
        
        # Title
        draw.text((155, y + 32), title, font=get_font(FONT_BOLD, 23), fill=TEXT_LIGHT)
        
        # Desc
        font_d = get_font(FONT_REGULAR, 20)
        words = desc.split()
        lines = []
        cur_line = ""
        for w in words:
            test = cur_line + " " + w if cur_line else w
            if font_d.getbbox(test)[2] < (WIDTH - 240):
                cur_line = test
            else:
                lines.append(cur_line)
                cur_line = w
        if cur_line:
            lines.append(cur_line)
            
        for line_idx, line in enumerate(lines[:3]):
            draw.text((90, y + 95 + line_idx * 32), line, font=font_d, fill=TEXT_MUTED)
            
    # Framework highlight
    draw_card(draw, 60, 1090, WIDTH - 60, 1190, bg=(20, 25, 50), border=PRIMARY, radius=16)
    fw_title = "THE ORBIT MATCH™ CORE"
    fw_items = "Originality • Relevance • Brand Safety • Ideal Audience • True Engagement"
    font_fwt = get_font(FONT_BOLD, 16)
    font_fwi = get_font(FONT_BOLD, 19)
    draw.text(((WIDTH - font_fwt.getbbox(fw_title)[2]) // 2, 1110), fw_title, font=font_fwt, fill=PRIMARY)
    draw.text(((WIDTH - font_fwi.getbbox(fw_items)[2]) // 2, 1140), fw_items, font=font_fwi, fill=TEXT_LIGHT)
    
    img.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"Saved: {output_path}")

def render_slide_4(output_path):
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    
    draw_header_bar(draw, 4)
    draw_footer_bar(draw, "GET STARTED ➔")
    
    # Tag
    draw_badge(draw, "HOW WE WORK WITH BRANDS", 60, 130, border=CYAN, text_color=CYAN)
    
    # Headline
    font_h = get_font(FONT_BOLD, 46)
    draw.text((60, 200), "Turnkey Campaign Models", font=font_h, fill=TEXT_LIGHT)
    draw.text((60, 260), "Built For Real ROI.", font=font_h, fill=CYAN)
    
    # 3 Service Packages
    services = [
        ("HIGH-VOLUME BARTER & SEEDING", "200 to 1,000+ creators across India. Generates 800K–5M+ authentic organic views and floods feeds with user reviews.", GREEN, "MOST POPULAR"),
        ("PERFORMANCE UGC CREATIVES", "High-retention hooks & unboxings crafted specifically for Meta & Instagram performance ad scaling.", PRIMARY, "FOR AD TEAMS"),
        ("CURATED PAID & WHITELISTED", "Handpicked top-converting creators with Meta partnership ad codes & full digital usage rights.", ACCENT, "SCALE MODEL")
    ]
    
    start_y = 360
    card_h = 210
    gap = 25
    
    for i, (title, desc, color, tag) in enumerate(services):
        y = start_y + i * (card_h + gap)
        draw_card(draw, 60, y, WIDTH - 60, y + card_h, bg=CARD_BG, border=BORDER, radius=20)
        
        # Tag Badge
        font_tb = get_font(FONT_BOLD, 13)
        t_w = font_tb.getbbox(tag)[2] + 24
        draw.rounded_rectangle([WIDTH - 90 - t_w, y + 22, WIDTH - 90, y + 54], radius=16, fill=color)
        draw.text((WIDTH - 78 - t_w, y + 28), tag, font=font_tb, fill=(10, 14, 26))
        
        # Number Badge
        draw.rounded_rectangle([90, y + 25, 135, y + 70], radius=8, fill=(25, 35, 60), outline=color, width=2)
        draw.text((104, y + 30), str(i + 1), font=get_font(FONT_BOLD, 24), fill=color)
        
        # Title
        draw.text((155, y + 34), title, font=get_font(FONT_BOLD, 21), fill=TEXT_LIGHT)
        
        # Desc
        font_d = get_font(FONT_REGULAR, 20)
        words = desc.split()
        lines = []
        cur_line = ""
        for w in words:
            test = cur_line + " " + w if cur_line else w
            if font_d.getbbox(test)[2] < (WIDTH - 200):
                cur_line = test
            else:
                lines.append(cur_line)
                cur_line = w
        if cur_line:
            lines.append(cur_line)
            
        for line_idx, line in enumerate(lines[:3]):
            draw.text((90, y + 95 + line_idx * 32), line, font=font_d, fill=TEXT_MUTED)
            
    # Guarantee callout
    draw_card(draw, 60, 1090, WIDTH - 60, 1190, bg=(15, 30, 40), border=GREEN, radius=16)
    guar_txt = "⚡ ~15-DAY CAMPAIGN TURNAROUND GUARANTEE"
    guar_sub = "From creator selection to first live deliverables."
    font_gt = get_font(FONT_BOLD, 20)
    font_gs = get_font(FONT_REGULAR, 17)
    draw.text(((WIDTH - font_gt.getbbox(guar_txt)[2]) // 2, 1115), guar_txt, font=font_gt, fill=GREEN)
    draw.text(((WIDTH - font_gs.getbbox(guar_sub)[2]) // 2, 1150), guar_sub, font=font_gs, fill=TEXT_LIGHT)
    
    img.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"Saved: {output_path}")

def render_slide_5(output_path, logo_path):
    img = create_base_canvas()
    draw = ImageDraw.Draw(img)
    
    draw_header_bar(draw, 5)
    draw_footer_bar(draw, "@thecreatororbit")
    
    # Tag
    draw_badge(draw, "LET'S WORK TOGETHER", (WIDTH - 280) // 2, 130, border=ACCENT, text_color=ACCENT)
    
    # Headline
    font_h = get_font(FONT_BOLD, 46)
    title1 = "Ready to Launch Your"
    title2 = "Next Creator Blitz?"
    draw.text(((WIDTH - font_h.getbbox(title1)[2]) // 2, 200), title1, font=font_h, fill=TEXT_LIGHT)
    draw.text(((WIDTH - font_h.getbbox(title2)[2]) // 2, 260), title2, font=font_h, fill=PRIMARY)
    
    # Main CTA Box
    draw_card(draw, 60, 360, WIDTH - 60, 780, bg=CARD_BG, border=PRIMARY, radius=24)
    
    # Small centered logo
    if os.path.exists(logo_path):
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize((100, 100), Image.LANCZOS)
        mask = Image.new("L", (100, 100), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse([0, 0, 100, 100], fill=255)
        img.paste(logo, ((WIDTH - 100) // 2, 400), mask)
        
    call_title = "Get a Custom 1-Page Creator Roster"
    call_sub = "Tailored specifically for your brand's niche & target audience."
    font_ct = get_font(FONT_BOLD, 26)
    font_cs = get_font(FONT_REGULAR, 20)
    draw.text(((WIDTH - font_ct.getbbox(call_title)[2]) // 2, 530), call_title, font=font_ct, fill=TEXT_LIGHT)
    draw.text(((WIDTH - font_cs.getbbox(call_sub)[2]) // 2, 575), call_sub, font=font_cs, fill=TEXT_MUTED)
    
    # Direct Action Pills
    p1 = "💬 Drop us a DM with \"ROSTER\""
    p2 = "🌐 Visit thecreatororbit.vercel.app"
    p3 = "✉️ thecreatororbit.media@gmail.com"
    font_p = get_font(FONT_BOLD, 21)
    
    draw.rounded_rectangle([100, 640, WIDTH - 100, 700], radius=14, fill=PRIMARY)
    draw.text(((WIDTH - font_p.getbbox(p1)[2]) // 2, 655), p1, font=font_p, fill=TEXT_LIGHT)
    
    draw.text(((WIDTH - font_p.getbbox(p2)[2]) // 2, 720), p2, font=font_p, fill=CYAN)
    
    # Founders Card
    draw_card(draw, 60, 830, WIDTH - 60, 1050, bg=(16, 22, 38), border=BORDER, radius=20)
    f_header = "MEET THE FOUNDERS"
    draw.text((100, 860), f_header, font=get_font(FONT_BOLD, 15), fill=TEXT_MUTED)
    
    f_names = "Vedant Rai & Manya Jain"
    f_roles = "Co-Founders | Creator Orbit"
    f_loc = "📍 New Delhi & Uttarakhand • Serving Brands Pan-India"
    
    draw.text((100, 895), f_names, font=get_font(FONT_BOLD, 30), fill=TEXT_LIGHT)
    draw.text((100, 945), f_roles, font=get_font(FONT_BOLD, 20), fill=PRIMARY)
    draw.text((100, 985), f_loc, font=get_font(FONT_REGULAR, 19), fill=TEXT_MUTED)
    
    # Final Tagline
    tagline = "🌌 ORBIT BEYOND ORDINARY"
    font_tag = get_font(FONT_BOLD, 24)
    draw.text(((WIDTH - font_tag.getbbox(tagline)[2]) // 2, 1120), tagline, font=font_tag, fill=ACCENT)
    
    img.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"Saved: {output_path}")

def main():
    logo_path = os.path.abspath("../branding/creator_orbit_official_logo.png")
    out_dir = os.path.abspath("../branding/launch_slides")
    os.makedirs(out_dir, exist_ok=True)
    
    print(f"Generating Instagram Launch Carousel in {out_dir}...")
    render_slide_1(os.path.join(out_dir, "slide_1_cover.png"), logo_path)
    render_slide_2(os.path.join(out_dir, "slide_2_problem.png"))
    render_slide_3(os.path.join(out_dir, "slide_3_solution.png"))
    render_slide_4(os.path.join(out_dir, "slide_4_programs.png"))
    render_slide_5(os.path.join(out_dir, "slide_5_cta.png"), logo_path)
    print("All 5 slides successfully generated!")

if __name__ == "__main__":
    main()
