"""
Creator Orbit — Influencer Intelligence & CRM Platform
======================================================
Performance-driven creator partnerships for high-growth brands.
Co-Founders: Vedant Rai & Manya Jain
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os
import io

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.youtube_client import YouTubeClient
from core.instagram_client import InstagramClient
from core.metrics import (
    calculate_median_views,
    calculate_engagement_rate,
    calculate_consistency_score,
    estimate_cpm_rate,
    calculate_creator_score,
)
from core.language_detector import (
    detect_content_language,
    detect_ig_creator_language,
    get_language_name,
    SUPPORTED_LANGUAGES,
)
from core.sponsor_detector import SponsorDetector
from core.database import CreatorDatabase
from utils.exporter import DataExporter

# ─────────────────────────── Page Config ────────────────────────────
st.set_page_config(
    page_title="Creator Orbit — Influencer Intelligence & CRM",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────── Session State Init ─────────────────────
if "yt_client" not in st.session_state:
    st.session_state.yt_client = YouTubeClient()
if "ig_client" not in st.session_state:
    st.session_state.ig_client = InstagramClient()
if "sponsor_detector" not in st.session_state:
    st.session_state.sponsor_detector = SponsorDetector()
if "db" not in st.session_state:
    st.session_state.db = CreatorDatabase()
if "exporter" not in st.session_state:
    st.session_state.exporter = DataExporter()
if "search_results" not in st.session_state:
    st.session_state.search_results = []
if "selected_creator" not in st.session_state:
    st.session_state.selected_creator = None

yt = st.session_state.yt_client
ig = st.session_state.ig_client
detector = st.session_state.sponsor_detector
db = st.session_state.db
exporter = st.session_state.exporter

# ─────────────────────────── Sidebar ────────────────────────────────
with st.sidebar:
    st.markdown("## 🚀 **Creator Orbit**")
    st.caption("Performance Influencer Marketing Agency")
    st.caption("Co-Founders: **Vedant Rai** & **Manya Jain**")

    st.divider()

    # API status indicators
    st.subheader("🔌 Data Connectors")
    if yt.api_available:
        st.success("✅ YouTube Data API — Connected")
    else:
        st.warning("⚠️ YouTube — Scraper Mode Active")

    if ig.api_available:
        st.success("✅ Instagram (Apify) — Connected")
    else:
        st.info("ℹ️ Instagram — Add APIFY_API_TOKEN to .env")

    st.divider()

    # Database stats
    st.subheader("🗄️ Master CRM Intelligence")
    all_creators_count = len(db.search_creators(limit=99999))
    all_campaigns = db.get_all_campaigns()
    col1, col2 = st.columns(2)
    col1.metric("Vetted Creators", f"{all_creators_count:,}")
    col2.metric("Campaigns", len(all_campaigns))

    st.divider()
    st.caption("💼 *Creator Orbit Media © 2026*")


# ─────────────────────────── Main Tabs ──────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🔎 Live Discovery & Scraper",
    "📊 Channel Deep-Dive & Audit",
    "🗄️ Creator Orbit Master CRM & Rosters",
])


# ═══════════════════════════════════════════════════════════════════
# TAB 1: Creator Discovery
# ═══════════════════════════════════════════════════════════════════
with tab1:
    st.header("Discover Creators")

    # ── Search Controls ──
    mode_col, search_col1, search_col2, search_col3 = st.columns([1, 3, 1, 1])
    with mode_col:
        search_mode = st.selectbox("Search By", ["🔑 Keyword", "#️⃣ Hashtag"])
    with search_col1:
        if search_mode == "🔑 Keyword":
            search_query = st.text_input(
                "Search by keyword or niche",
                placeholder="e.g. 'beauty hindi', 'fitness coach', 'indian skincare', 'tech reviewer'",
            )
        else:
            search_query = st.text_input(
                "Search by hashtag",
                placeholder="e.g. 'indianbeautyblogger', 'makeuphindi', 'desibeauty', 'fitnessindia' (without #)",
            )
    with search_col2:
        platform = st.selectbox("Platform", ["YouTube", "Instagram"])
    with search_col3:
        max_results = st.slider("Max results", 5, 50, 20)

    # ── Platform-Specific Advanced Filters ──
    with st.expander("🔧 Advanced Filters", expanded=False):
        tier_options = [
            "All Tiers",
            "Nano (1K – 10K)",
            "Micro (10K – 100K)",
            "Mid-Tier (100K – 500K)",
            "Macro (500K – 1M)",
            "Mega / Celebrity (1M+)",
        ]

        if platform == "Instagram":
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                ig_tier = st.selectbox("Follower Tier", tier_options)
                st.caption("💡 1-word searches ('fitness') yield Mega/Macro accounts. Use niche terms ('fitness coach') for Micro/Nano.")
            with f_col2:
                # Set defaults based on tier
                tier_min_map = {"Nano (1K – 10K)": 1000, "Micro (10K – 100K)": 10000, "Mid-Tier (100K – 500K)": 100000, "Macro (500K – 1M)": 500000, "Mega / Celebrity (1M+)": 1000000}
                tier_max_map = {"Nano (1K – 10K)": 10000, "Micro (10K – 100K)": 100000, "Mid-Tier (100K – 500K)": 500000, "Macro (500K – 1M)": 1000000, "Mega / Celebrity (1M+)": 0}
                default_min = tier_min_map.get(ig_tier, 0)
                default_max = tier_max_map.get(ig_tier, 0)
                min_subs = st.number_input("Min Followers", min_value=0, value=default_min, step=1000)
            with f_col3:
                max_subs = st.number_input("Max Followers", min_value=0, value=default_max, step=1000, help="0 for no upper limit")
            with f_col4:
                min_engagement = st.number_input("Min Engagement Rate (%)", min_value=0.0, value=0.0, step=0.5)

            f2_col1, f2_col2, f2_col3, f2_col4 = st.columns(4)
            with f2_col1:
                language_options = ["All Languages"] + [
                    f"{name} ({code})" for code, name in SUPPORTED_LANGUAGES.items()
                ]
                language_filter = st.selectbox("Content Language", language_options)
            with f2_col2:
                min_posts = st.number_input("Min Total Posts", min_value=0, value=0, step=5)
            with f2_col3:
                st.write("")
                st.write("")
                must_have_email = st.checkbox("📧 Has Email in Bio", value=False)
            with f2_col4:
                st.write("")
                st.write("")
                verified_only = st.checkbox("☑️ Verified Only", value=False)

            collab_only = st.checkbox("🤝 Has Collab / Sponsored History (#ad, #collab, etc.)", value=False)
            min_views_filter = 0
            has_sponsor_yt = False

        else:  # YouTube
            f_col1, f_col2, f_col3, f_col4 = st.columns(4)
            with f_col1:
                yt_tier = st.selectbox("Subscriber Tier", tier_options)
            with f_col2:
                tier_min_map = {"Nano (1K – 10K)": 1000, "Micro (10K – 100K)": 10000, "Mid-Tier (100K – 500K)": 100000, "Macro (500K – 1M)": 500000, "Mega / Celebrity (1M+)": 1000000}
                tier_max_map = {"Nano (1K – 10K)": 10000, "Micro (10K – 100K)": 100000, "Mid-Tier (100K – 500K)": 500000, "Macro (500K – 1M)": 1000000, "Mega / Celebrity (1M+)": 0}
                default_min = tier_min_map.get(yt_tier, 0)
                default_max = tier_max_map.get(yt_tier, 0)
                min_subs = st.number_input("Min Subscribers", min_value=0, value=default_min, step=1000)
            with f_col3:
                max_subs = st.number_input("Max Subscribers", min_value=0, value=default_max, step=1000, help="0 for no upper limit")
            with f_col4:
                min_engagement = st.number_input("Min Engagement Rate (%)", min_value=0.0, value=0.0, step=0.5)

            f2_col1, f2_col2, f2_col3 = st.columns(3)
            with f2_col1:
                language_options = ["All Languages"] + [
                    f"{name} ({code})" for code, name in SUPPORTED_LANGUAGES.items()
                ]
                language_filter = st.selectbox("Content Language", language_options)
            with f2_col2:
                min_views_filter = st.number_input("Min Median Views", min_value=0, value=0, step=1000)
            with f2_col3:
                st.write("")
                st.write("")
                has_sponsor_yt = st.checkbox("🤝 Has Past Sponsors", value=False)

            must_have_email = False
            verified_only = False
            collab_only = False
            min_posts = 0

    # ── Search Button ──
    if st.button("🚀 Search Creators", type="primary", use_container_width=True):
        clean_query = search_query.strip().strip("'\"").strip()
        if not clean_query:
            st.warning("Please enter a search query.")
        else:
            with st.spinner(f"Searching {platform} for '{clean_query}'..."):
                all_creators = []

                if platform == "YouTube":
                    fetch_pool = min(max_results * 3, 50)
                    if search_mode == "#️⃣ Hashtag":
                        channels = yt.search_by_hashtag(clean_query, max_results=fetch_pool)
                    else:
                        channels = yt.search_channels(clean_query, max_results=fetch_pool)

                    if not channels:
                        st.warning("No creators found. Try a different search term.")
                    else:
                        progress = st.progress(0, text="Analyzing channels...")
                        for idx, channel in enumerate(channels):
                            progress.progress(
                                (idx + 1) / len(channels),
                                text=f"Analyzing: {channel.get('title', 'Unknown')} ({idx+1}/{len(channels)})",
                            )
                            channel_id = channel.get("channel_id", "")
                            if not channel_id:
                                continue
                            details = yt.get_channel_details(channel_id)
                            videos = yt.get_recent_videos(channel_id, max_results=15)
                            median_views = calculate_median_views(videos)
                            engagement_rate = calculate_engagement_rate(videos)
                            consistency = calculate_consistency_score(videos)
                            content_lang = detect_content_language(videos)
                            sub_count = details.get("subscriber_count", 0)
                            creator_score = calculate_creator_score(median_views, engagement_rate, consistency, sub_count)
                            cpm = estimate_cpm_rate(median_views, "youtube", "60s_midroll")
                            creator_data = {
                                "platform": "youtube",
                                "platform_id": channel_id,
                                "name": details.get("title", channel.get("title", "")),
                                "description": details.get("description", ""),
                                "subscriber_count": sub_count,
                                "median_views": median_views,
                                "engagement_rate": engagement_rate,
                                "consistency_score": consistency,
                                "creator_score": creator_score,
                                "content_language": content_lang,
                                "thumbnail_url": details.get("thumbnail_url", ""),
                                "country": details.get("country", ""),
                                "estimated_cpm_low": cpm["estimated_rate_low"],
                                "estimated_cpm_high": cpm["estimated_rate_high"],
                                "videos": videos,
                            }
                            db.upsert_creator(creator_data)
                            all_creators.append(creator_data)
                        progress.empty()

                elif platform == "Instagram":
                    if not ig.api_available:
                        st.error("Instagram requires Apify API token. Add APIFY_API_TOKEN to your .env file.")
                    else:
                        fetch_pool = max(max_results * 5, 80)
                        if search_mode == "#️⃣ Hashtag":
                            scrape_status = st.empty()
                            scrape_status.info("🔍 Scraping hashtag posts...")
                            profiles = ig.search_by_hashtag(clean_query, max_results=max_results, fetch_limit=fetch_pool)
                            scrape_status.empty()
                        else:
                            round_progress = st.progress(0, text="🔍 Starting multi-round Instagram scrape...")
                            round_status = st.empty()

                            def ig_round_callback(round_num, total_rounds, variant, found_so_far):
                                round_progress.progress(
                                    round_num / total_rounds,
                                    text=f"🔄 Round {round_num}/{total_rounds} — Searching '{variant}' | Found: {found_so_far} candidates"
                                )
                                round_status.info(f"📡 Scraping variation **'{variant}'** ({round_num}/{total_rounds}) — {found_so_far} unique profiles so far")

                            profiles = ig.search_profiles(
                                clean_query, max_results=max_results,
                                fetch_limit=fetch_pool, progress_callback=ig_round_callback
                            )
                            round_progress.empty()
                            round_status.empty()

                        if not profiles:
                            st.warning(f"No Instagram creators returned by Apify for '{clean_query}'. Try a different search term.")
                        else:
                            st.info(f"✅ Collected **{len(profiles)} candidate profiles** — building creator cards...")
                            progress = st.progress(0, text="Analyzing profiles...")
                            for idx, profile in enumerate(profiles):
                                progress.progress(
                                    (idx + 1) / len(profiles),
                                    text=f"Analyzing: @{profile.get('username', 'unknown')} ({idx+1}/{len(profiles)})",
                                )
                                username = profile.get("username", "")
                                if not username:
                                    continue
                                posts = profile.get("posts", [])
                                follower_count = profile.get("follower_count", 0)
                                post_metrics = [
                                    {
                                        "view_count": p.get("view_count", p.get("like_count", 0) * 10),
                                        "like_count": p.get("like_count", 0),
                                        "comment_count": p.get("comment_count", 0),
                                        "title": p.get("caption", ""),
                                        "description": "",
                                    }
                                    for p in posts
                                ] if posts else [
                                    {
                                        "view_count": max(int(follower_count * 0.1), 100),
                                        "like_count": max(int(follower_count * 0.03), 10),
                                        "comment_count": max(int(follower_count * 0.002), 1),
                                        "title": profile.get("biography", ""),
                                        "description": "",
                                    }
                                ]
                                median_views = calculate_median_views(post_metrics)
                                engagement_rate = calculate_engagement_rate(post_metrics)
                                consistency = calculate_consistency_score(post_metrics)
                                content_lang = detect_ig_creator_language(profile)
                                creator_score = calculate_creator_score(median_views, engagement_rate, consistency, follower_count)
                                cpm = estimate_cpm_rate(median_views, "instagram", "reel")
                                ig_sponsor_check = detector.detect_instagram_sponsors(posts)
                                extra_meta = {
                                    "bio_email": profile.get("bio_email"),
                                    "is_verified": profile.get("is_verified", False),
                                    "external_url": profile.get("external_url"),
                                    "post_count": profile.get("post_count", len(posts)),
                                    "following_count": profile.get("following_count", 0),
                                    "sponsored_posts_count": ig_sponsor_check["total_sponsored_posts"],
                                    "detected_brands": list(ig_sponsor_check["brand_frequency"].keys()),
                                }
                                creator_data = {
                                    "platform": "instagram",
                                    "platform_id": username,
                                    "name": profile.get("full_name", username) or username,
                                    "description": profile.get("biography", ""),
                                    "subscriber_count": follower_count,
                                    "median_views": median_views,
                                    "engagement_rate": engagement_rate,
                                    "consistency_score": consistency,
                                    "creator_score": creator_score,
                                    "content_language": content_lang,
                                    "thumbnail_url": profile.get("profile_pic_url", ""),
                                    "country": "",
                                    "estimated_cpm_low": cpm["estimated_rate_low"],
                                    "estimated_cpm_high": cpm["estimated_rate_high"],
                                    "extra_data": extra_meta,
                                    "bio_email": profile.get("bio_email"),
                                    "is_verified": profile.get("is_verified", False),
                                    "external_url": profile.get("external_url"),
                                    "sponsored_posts_count": ig_sponsor_check["total_sponsored_posts"],
                                    "detected_brands": list(ig_sponsor_check["brand_frequency"].keys()),
                                    "posts": posts,
                                    "videos": post_metrics,
                                }
                                db.upsert_creator(creator_data)
                                all_creators.append(creator_data)
                            progress.empty()

                # Store ALL scraped creators — filters applied at display time
                st.session_state.all_scraped_creators = all_creators
                st.session_state.search_results = all_creators

    # ── Display Results ──
    all_creators = st.session_state.get("all_scraped_creators", [])
    if all_creators:
        st.divider()
        total_scraped = len(all_creators)

        # ── Interactive filter bar (applied on top of already-fetched creators) ──
        st.markdown("### 🎛️ Filter Results")
        fc1, fc2, fc3, fc4, fc5 = st.columns([2, 2, 2, 2, 2])

        with fc1:
            display_tier_options = ["All Tiers", "Nano (1K–10K)", "Micro (10K–100K)", "Mid-Tier (100K–500K)", "Macro (500K–1M)", "Mega (1M+)"]
            disp_tier = st.selectbox("Follower Tier", display_tier_options, key="disp_tier")
        with fc2:
            lang_opts = ["All Languages"] + [f"{name} ({code})" for code, name in SUPPORTED_LANGUAGES.items()]
            disp_lang = st.selectbox("Content Language", lang_opts, key="disp_lang")
        with fc3:
            disp_min_er = st.number_input("Min Engagement %", min_value=0.0, value=0.0, step=0.5, key="disp_er")
        with fc4:
            disp_email = st.checkbox("📧 Has Email", key="disp_email")
            disp_verified = st.checkbox("☑️ Verified Only", key="disp_verified")
        with fc5:
            disp_collab = st.checkbox("🤝 Has Collabs", key="disp_collab")
            disp_sort = st.selectbox("Sort By", ["Creator Score", "Followers", "Engagement %", "Median Views"], key="disp_sort")

        # Apply filters to the fetched set
        tier_ranges = {
            "Nano (1K–10K)": (1000, 10000),
            "Micro (10K–100K)": (10000, 100000),
            "Mid-Tier (100K–500K)": (100000, 500000),
            "Macro (500K–1M)": (500000, 1000000),
            "Mega (1M+)": (1000000, float("inf")),
        }
        results = []
        for c in all_creators:
            subs = c.get("subscriber_count", 0)
            er = c.get("engagement_rate", 0.0)
            clang = c.get("content_language", "unknown")

            if disp_tier != "All Tiers":
                lo, hi = tier_ranges[disp_tier]
                if not (lo <= subs < hi):
                    continue
            if disp_lang != "All Languages":
                lcode = disp_lang.split("(")[-1].rstrip(")")
                if clang != lcode:
                    continue
            if disp_min_er > 0 and er < disp_min_er:
                continue
            if disp_email and not c.get("bio_email"):
                continue
            if disp_verified and not c.get("is_verified", False):
                continue
            if disp_collab and c.get("sponsored_posts_count", 0) == 0:
                continue
            results.append(c)

        # Sort
        sort_key = {
            "Creator Score": lambda x: x.get("creator_score", 0),
            "Followers": lambda x: x.get("subscriber_count", 0),
            "Engagement %": lambda x: x.get("engagement_rate", 0.0),
            "Median Views": lambda x: x.get("median_views", 0),
        }[disp_sort]
        results = sorted(results, key=sort_key, reverse=True)

        matched = len(results)
        if matched == 0:
            st.warning(
                f"⚠️ **{total_scraped} creators scraped, but 0 matched your current filters.**\n\n"
                f"Try relaxing: set **Follower Tier → All Tiers**, **Content Language → All Languages**, or uncheck optional filters."
            )
        else:
            st.success(f"Showing **{matched}** of {total_scraped} scraped creators — sorted by {disp_sort}")

        # Summary metrics row
        if results:
            m1, m2, m3, m4 = st.columns(4)
            avg_score = sum(r["creator_score"] for r in results) / len(results)
            avg_er = sum(r["engagement_rate"] for r in results) / len(results)
            avg_views = sum(r["median_views"] for r in results) / len(results)
            total_reach = sum(r["median_views"] for r in results)
            m1.metric("Avg Creator Score", f"{avg_score:.1f}/100")
            m2.metric("Avg Engagement Rate", f"{avg_er:.2f}%")
            m3.metric("Avg Median Views", f"{avg_views:,.0f}")
            m4.metric("Total Potential Reach", f"{total_reach:,.0f}")

        st.divider()

        # Results table
        for i, creator in enumerate(results):
            with st.container():
                col1, col2, col3, col4, col5 = st.columns([1, 3, 2, 2, 1])

                with col1:
                    thumbnail = creator.get("thumbnail_url", "")
                    if thumbnail:
                        st.image(thumbnail, width=80)
                    else:
                        st.write("📷")

                with col2:
                    platform_icon = "📺" if creator["platform"] == "youtube" else "📸"
                    verified_badge = " ☑️" if creator.get("is_verified") else ""
                    st.markdown(f"**{platform_icon} {creator['name']}{verified_badge}**")

                    if creator["platform"] == "instagram":
                        st.caption(f"@{creator.get('platform_id', '')}")

                    lang_name = get_language_name(creator.get("content_language", "unknown"))
                    metric_label = "subscribers" if creator["platform"] == "youtube" else "followers"
                    st.caption(
                        f"🌐 {lang_name} • "
                        f"👥 {creator['subscriber_count']:,} {metric_label} • "
                        f"📊 Score: {creator['creator_score']}/100"
                    )

                    # Dynamic Badges
                    badges = []
                    if creator.get("bio_email"):
                        badges.append(f"📧 `{creator['bio_email']}`")
                    if creator.get("external_url"):
                        badges.append(f"🔗 [Link in Bio]({creator['external_url']})")
                    if creator.get("sponsored_posts_count", 0) > 0:
                        badges.append(f"🤝 `{creator['sponsored_posts_count']} Collab(s)`")
                    if badges:
                        st.markdown(" • ".join(badges))

                    if creator.get("description"):
                        desc_text = creator["description"].strip()
                        st.caption(desc_text[:90] + ("..." if len(desc_text) > 90 else ""))

                with col3:
                    st.metric("Median Views", f"{creator['median_views']:,}")
                    st.caption(f"ER: {creator['engagement_rate']:.2f}%")

                with col4:
                    low = creator.get("estimated_cpm_low", 0)
                    high = creator.get("estimated_cpm_high", 0)
                    st.metric("Est. Rate", f"${low:,.0f} – ${high:,.0f}")
                    st.caption(f"Consistency: {creator['consistency_score']:.1f} CV")

                with col5:
                    if st.button("📊 Deep Dive", key=f"dive_{i}"):
                        st.session_state.selected_creator = creator
                        st.rerun()

                st.divider()


# ═══════════════════════════════════════════════════════════════════
# TAB 2: Channel Deep-Dive & Ad Tracker
# ═══════════════════════════════════════════════════════════════════
with tab2:
    st.header("Channel Deep-Dive & Sponsor Tracker")

    # Input for direct lookup
    lookup_col1, lookup_col2 = st.columns([3, 1])
    with lookup_col1:
        lookup_id = st.text_input(
            "Enter Channel ID or Username",
            placeholder="e.g. UCxxxxxx (YouTube) or @username (Instagram)",
        )
    with lookup_col2:
        lookup_platform = st.selectbox("Platform ", ["YouTube", "Instagram"], key="lookup_plat")

    creator = st.session_state.selected_creator

    if st.button("🔍 Analyze", type="primary") and lookup_id:
        with st.spinner("Fetching data..."):
            if lookup_platform == "YouTube":
                details = yt.get_channel_details(lookup_id)
                videos = yt.get_recent_videos(lookup_id, max_results=15)

                median_views = calculate_median_views(videos)
                engagement_rate = calculate_engagement_rate(videos)
                consistency = calculate_consistency_score(videos)
                content_lang = detect_content_language(videos)
                sub_count = details.get("subscriber_count", 0)
                creator_score_val = calculate_creator_score(
                    median_views, engagement_rate, consistency, sub_count,
                )
                cpm = estimate_cpm_rate(median_views, "youtube", "60s_midroll")

                creator = {
                    "platform": "youtube",
                    "platform_id": lookup_id,
                    "name": details.get("title", ""),
                    "description": details.get("description", ""),
                    "subscriber_count": sub_count,
                    "median_views": median_views,
                    "engagement_rate": engagement_rate,
                    "consistency_score": consistency,
                    "creator_score": creator_score_val,
                    "content_language": content_lang,
                    "thumbnail_url": details.get("thumbnail_url", ""),
                    "country": details.get("country", ""),
                    "estimated_cpm_low": cpm["estimated_rate_low"],
                    "estimated_cpm_high": cpm["estimated_rate_high"],
                    "videos": videos,
                }
                st.session_state.selected_creator = creator
            else:
                if not ig.api_available:
                    st.error("Instagram lookup requires Apify API token.")
                else:
                    profile = ig.get_profile_by_username(lookup_id)
                    if profile:
                        posts = profile.get("posts", [])
                        follower_count = profile.get("follower_count", 0)
                        post_metrics = [
                            {
                                "view_count": p.get("view_count", p.get("like_count", 0) * 10),
                                "like_count": p.get("like_count", 0),
                                "comment_count": p.get("comment_count", 0),
                                "title": p.get("caption", "")[:40] or "Instagram Post",
                                "description": "",
                            }
                            for p in posts
                        ] if posts else [
                            {
                                "view_count": max(int(follower_count * 0.1), 100),
                                "like_count": max(int(follower_count * 0.03), 10),
                                "comment_count": max(int(follower_count * 0.002), 1),
                                "title": profile.get("biography", "")[:40] or "Profile",
                                "description": "",
                            }
                        ]
                        median_views = calculate_median_views(post_metrics)
                        engagement_rate = calculate_engagement_rate(post_metrics)
                        consistency = calculate_consistency_score(post_metrics)
                        content_lang = detect_content_language(post_metrics)
                        creator_score_val = calculate_creator_score(
                            median_views, engagement_rate, consistency, follower_count,
                        )
                        cpm = estimate_cpm_rate(median_views, "instagram", "reel")
                        creator = {
                            "platform": "instagram",
                            "platform_id": profile.get("username", lookup_id),
                            "name": profile.get("full_name", lookup_id) or lookup_id,
                            "description": profile.get("biography", ""),
                            "subscriber_count": follower_count,
                            "median_views": median_views,
                            "engagement_rate": engagement_rate,
                            "consistency_score": consistency,
                            "creator_score": creator_score_val,
                            "content_language": content_lang,
                            "thumbnail_url": profile.get("profile_pic_url", ""),
                            "country": "",
                            "estimated_cpm_low": cpm["estimated_rate_low"],
                            "estimated_cpm_high": cpm["estimated_rate_high"],
                            "posts": posts,
                            "videos": post_metrics,
                        }
                        st.session_state.selected_creator = creator
                    else:
                        st.error(f"Could not find Instagram profile for '{lookup_id}'.")

    if creator:
        st.divider()

        # ── Creator Header ──
        h1, h2 = st.columns([1, 4])
        with h1:
            thumb = creator.get("thumbnail_url", "")
            if thumb:
                st.image(thumb, width=120)
        with h2:
            st.subheader(creator["name"])
            lang_name = get_language_name(creator.get("content_language", "unknown"))
            st.markdown(
                f"**Platform:** {'📺 YouTube' if creator['platform'] == 'youtube' else '📸 Instagram'} • "
                f"**Language:** {lang_name} • "
                f"**Country:** {creator.get('country', 'N/A')}"
            )

        # ── Key Metrics ──
        km1, km2, km3, km4, km5 = st.columns(5)
        km1.metric("Creator Score", f"{creator['creator_score']}/100")
        km2.metric("Subscribers", f"{creator['subscriber_count']:,}")
        km3.metric("Median Views", f"{creator['median_views']:,}")
        km4.metric("Engagement Rate", f"{creator['engagement_rate']:.2f}%")
        km5.metric("Consistency (CV)", f"{creator['consistency_score']:.1f}")

        st.divider()

        # ── View Distribution Chart ──
        videos = creator.get("videos", [])
        if videos:
            st.subheader("📈 View Distribution (Recent Content)")
            view_data = pd.DataFrame([
                {"Video": v.get("title", "")[:40], "Views": v.get("view_count", 0)}
                for v in videos
            ])
            fig = px.bar(
                view_data, x="Video", y="Views",
                color="Views",
                color_continuous_scale="Tealgrn",
            )
            fig.add_hline(
                y=creator["median_views"],
                line_dash="dash", line_color="red",
                annotation_text=f"Median: {creator['median_views']:,}",
            )
            fig.update_layout(xaxis_tickangle=-45, height=400)
            st.plotly_chart(fig, use_container_width=True)

        # ── Sponsorship Analysis (YouTube) ──
        if videos and creator["platform"] == "youtube":
            st.subheader("🔍 Sponsorship & Ad Detection")

            with st.spinner("Scanning descriptions & transcripts for sponsors..."):
                # Enrich videos with transcripts
                enriched_videos = []
                transcript_progress = st.progress(0, text="Fetching transcripts...")
                for idx, v in enumerate(videos[:10]):  # Limit to 10 for speed
                    transcript_progress.progress(
                        (idx + 1) / min(len(videos), 10),
                        text=f"Scanning transcript {idx+1}/{min(len(videos), 10)}...",
                    )
                    transcript = yt.get_video_transcript(v.get("video_id", ""))
                    enriched = {**v, "transcript": transcript}
                    enriched_videos.append(enriched)
                transcript_progress.empty()

                sponsor_analysis = detector.analyze_channel_sponsors(enriched_videos)

            # Display sponsor results
            sp1, sp2, sp3 = st.columns(3)
            sp1.metric(
                "Sponsored Videos",
                f"{sponsor_analysis['total_sponsored_videos']}/{len(enriched_videos)}",
            )
            sp2.metric("Sponsor Rate", f"{sponsor_analysis['sponsor_rate']:.1f}%")
            sp3.metric("Unique Brands", f"{len(sponsor_analysis['brand_frequency'])}")

            if sponsor_analysis["brand_frequency"]:
                st.markdown("**Detected Brands:**")
                brand_df = pd.DataFrame(
                    [
                        {"Brand": brand, "Mentions": count}
                        for brand, count in sorted(
                            sponsor_analysis["brand_frequency"].items(),
                            key=lambda x: x[1],
                            reverse=True,
                        )
                    ]
                )
                st.dataframe(brand_df, use_container_width=True, hide_index=True)

                # Save sponsors to DB
                db_creator = db.get_creator_by_platform_id(
                    creator["platform"], creator["platform_id"],
                )
                if db_creator:
                    for brand in sponsor_analysis["brand_frequency"]:
                        db.add_sponsor(db_creator["id"], brand, "auto-detected")

            if sponsor_analysis["all_promo_codes"]:
                st.markdown("**Promo Codes Found:** " + ", ".join(
                    f"`{code}`" for code in sponsor_analysis["all_promo_codes"]
                ))

            if sponsor_analysis["all_affiliate_links"]:
                st.markdown("**Affiliate Links:**")
                for link in sponsor_analysis["all_affiliate_links"]:
                    st.markdown(f"- `{link}`")

        # ── Sponsorship Analysis (Instagram) ──
        elif creator.get("platform") == "instagram" and creator.get("posts"):
            st.subheader("🔍 Sponsorship & Ad Detection")
            ig_sponsor_analysis = detector.detect_instagram_sponsors(creator["posts"])

            sp1, sp2, sp3 = st.columns(3)
            sp1.metric(
                "Sponsored Posts",
                f"{ig_sponsor_analysis['total_sponsored_posts']}/{len(creator['posts'])}",
            )
            sp2.metric("Sponsor Rate", f"{ig_sponsor_analysis['sponsor_rate']:.1f}%")
            sp3.metric("Unique Brands", f"{len(ig_sponsor_analysis['brand_frequency'])}")

            if ig_sponsor_analysis["sponsored_hashtags_found"]:
                st.markdown("**Sponsored Tags Found:** " + ", ".join(
                    f"`{tag}`" for tag in ig_sponsor_analysis["sponsored_hashtags_found"]
                ))

            if ig_sponsor_analysis["brand_frequency"]:
                st.markdown("**Detected Brands & Collabs:**")
                brand_df = pd.DataFrame(
                    [
                        {"Brand": brand, "Mentions": count}
                        for brand, count in sorted(
                            ig_sponsor_analysis["brand_frequency"].items(),
                            key=lambda x: x[1],
                            reverse=True,
                        )
                    ]
                )
                st.dataframe(brand_df, use_container_width=True, hide_index=True)

        # ── CPM Calculator ──
        st.divider()
        st.subheader("💰 Rate Calculator")
        calc_col1, calc_col2 = st.columns(2)
        with calc_col1:
            if creator["platform"] == "youtube":
                int_types = ["60s_midroll", "30s_preroll", "dedicated"]
            else:
                int_types = ["reel", "story", "post"]
            integration = st.selectbox("Integration Type", int_types)

        with calc_col2:
            agency_margin = st.slider("Agency Margin (%)", 10, 50, 20)

        cpm_data = estimate_cpm_rate(creator["median_views"], creator["platform"], integration)
        margin_mult = 1 + agency_margin / 100

        rate_col1, rate_col2, rate_col3 = st.columns(3)
        rate_col1.metric("Creator Rate (Low)", f"${cpm_data['estimated_rate_low']:,.0f}")
        rate_col2.metric("Creator Rate (High)", f"${cpm_data['estimated_rate_high']:,.0f}")
        rate_col3.metric(
            "Client Price (with margin)",
            f"${cpm_data['estimated_rate_low'] * margin_mult:,.0f} – "
            f"${cpm_data['estimated_rate_high'] * margin_mult:,.0f}",
        )


# ═══════════════════════════════════════════════════════════════════
# TAB 3: Creator Orbit Master CRM & Campaign Rosters
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.header("🗄️ Creator Orbit Master CRM")
    st.caption("Browse, search, and manage 3,000+ curated creators across India. Build customized client campaign rosters.")

    # ── Master Database Intelligence Stats ──
    all_raw_creators = db.search_creators(limit=99999)
    total_crm = len(all_raw_creators)

    email_count = 0
    phone_count = 0
    city_count = 0
    all_categories = set()

    for c in all_raw_creators:
        extra = c.get("extra_data") or {}
        if isinstance(extra, str):
            try:
                extra = json.loads(extra)
            except Exception:
                extra = {}
        if isinstance(extra, dict):
            if extra.get("bio_email"):
                email_count += 1
            if extra.get("phone"):
                phone_count += 1
            if extra.get("city"):
                city_count += 1
            for cat in extra.get("categories", []):
                if cat and str(cat).strip():
                    all_categories.add(str(cat).strip())

    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    stat_col1.metric("Total Creators in CRM", f"{total_crm:,}")
    stat_col2.metric("📧 Verified Emails", f"{email_count:,}")
    stat_col3.metric("📱 Direct Phone / WhatsApp", f"{phone_count:,}")
    stat_col4.metric("📍 Cities Covered", f"{city_count:,}")

    st.divider()

    # ── Search & Filter Controls ──
    st.subheader("🔍 Search & Filter Database")
    s_col1, s_col2, s_col3, s_col4 = st.columns([3, 2, 2, 2])

    with s_col1:
        crm_keyword = st.text_input(
            "Search Creators",
            placeholder="Search by name, handle, city (e.g. Mumbai, Delhi), email, niche...",
            key="crm_search_kw",
        )
    with s_col2:
        tier_opts = ["All Tiers", "Nano (1K–10K)", "Micro (10K–100K)", "Mid-Tier (100K–500K)", "Macro (500K–1M)", "Mega (1M+)"]
        crm_tier = st.selectbox("Follower Tier", tier_opts, key="crm_tier_sel")
    with s_col3:
        crm_platform = st.selectbox("Platform", ["All Platforms", "Instagram", "YouTube"], key="crm_plat_sel")
    with s_col4:
        crm_sort = st.selectbox(
            "Sort By",
            ["Followers (High to Low)", "Median Views", "Creator Score", "Engagement Rate"],
            key="crm_sort_sel",
        )

    f_chk1, f_chk2, f_chk3 = st.columns([2, 2, 6])
    with f_chk1:
        req_email = st.checkbox("📧 Has Email Only", value=False, key="crm_req_email")
    with f_chk2:
        req_phone = st.checkbox("📱 Has Phone / WhatsApp", value=False, key="crm_req_phone")

    # Fetch and filter
    tier_ranges = {
        "Nano (1K–10K)": (1000, 10000),
        "Micro (10K–100K)": (10000, 100000),
        "Mid-Tier (100K–500K)": (100000, 500000),
        "Macro (500K–1M)": (500000, 1000000),
        "Mega (1M+)": (1000000, float("inf")),
    }

    filtered_creators = []
    for c in all_raw_creators:
        extra = c.get("extra_data") or {}
        if isinstance(extra, str):
            try:
                extra = json.loads(extra)
            except Exception:
                extra = {}
        if not isinstance(extra, dict):
            extra = {}

        # Keyword match
        if crm_keyword:
            kw = crm_keyword.lower().strip()
            name_str = str(c.get("name", "")).lower()
            handle_str = str(c.get("platform_id", "")).lower()
            city_str = str(extra.get("city", "")).lower()
            state_str = str(extra.get("state", "")).lower()
            email_str = str(extra.get("bio_email", "")).lower()
            phone_str = str(extra.get("phone", "")).lower()
            cat_str = " ".join(str(cat).lower() for cat in extra.get("categories", []))

            if not (kw in name_str or kw in handle_str or kw in city_str or kw in state_str or kw in email_str or kw in phone_str or kw in cat_str):
                continue

        # Platform match
        if crm_platform != "All Platforms" and c.get("platform", "").lower() != crm_platform.lower():
            continue

        # Follower tier match
        subs = c.get("subscriber_count", 0)
        if crm_tier != "All Tiers":
            lo, hi = tier_ranges[crm_tier]
            if not (lo <= subs < hi):
                continue

        # Email & Phone checkboxes
        if req_email and not extra.get("bio_email"):
            continue
        if req_phone and not extra.get("phone"):
            continue

        filtered_creators.append((c, extra))

    # Sort
    sort_functions = {
        "Followers (High to Low)": lambda x: x[0].get("subscriber_count", 0),
        "Median Views": lambda x: x[0].get("median_views", 0),
        "Creator Score": lambda x: x[0].get("creator_score", 0),
        "Engagement Rate": lambda x: x[0].get("engagement_rate", 0),
    }
    filtered_creators = sorted(filtered_creators, key=sort_functions[crm_sort], reverse=True)

    st.markdown(f"Found **{len(filtered_creators):,}** matching creators")

    # ── Display Table ──
    table_rows = []
    for c, extra in filtered_creators[:200]:  # Limit preview to top 200 for fast UI rendering
        cats = ", ".join(extra.get("categories", []))
        table_rows.append({
            "Name": c.get("name") or c.get("platform_id"),
            "Handle": f"@{c.get('platform_id')}",
            "Platform": c.get("platform", "instagram").title(),
            "Followers": f"{c.get('subscriber_count', 0):,}",
            "Avg Views": f"{c.get('median_views', 0):,}",
            "Email": extra.get("bio_email") or "—",
            "Phone / WA": extra.get("phone") or "—",
            "City / State": f"{extra.get('city', '')} {extra.get('state', '')}".strip() or "—",
            "Commercials": extra.get("commercial_notes") or "—",
            "Niche / Tags": cats[:35] + ("..." if len(cats) > 35 else "") if cats else "—",
        })

    if table_rows:
        st.dataframe(pd.DataFrame(table_rows), use_container_width=True, hide_index=True)
    else:
        st.warning("No creators matched your current search filters. Try clearing the keyword or relaxing filters.")

    # ── Bulk Export Action ──
    st.divider()
    exp_col_a, exp_col_b = st.columns([3, 1])
    with exp_col_a:
        st.markdown(f"📥 **Export {len(filtered_creators):,} Filtered Creators to Excel**")
        st.caption("Exports all matching records with verified emails, phones, locations, and commercials.")
    with exp_col_b:
        if filtered_creators:
            # Build full export dataframe
            export_data = []
            for c, extra in filtered_creators:
                export_data.append({
                    "Creator Name": c.get("name"),
                    "Instagram Handle": f"@{c.get('platform_id')}",
                    "Followers": c.get("subscriber_count", 0),
                    "Estimated Avg Views": c.get("median_views", 0),
                    "Engagement Rate (%)": c.get("engagement_rate", 0),
                    "Contact Email": extra.get("bio_email", ""),
                    "Phone / WhatsApp": extra.get("phone", ""),
                    "City": extra.get("city", ""),
                    "State": extra.get("state", ""),
                    "Niche Categories": ", ".join(extra.get("categories", [])),
                    "Commercial Notes": extra.get("commercial_notes", ""),
                    "Source Sheet": ", ".join(extra.get("source_sheets", [])),
                })
            df_exp = pd.DataFrame(export_data)

            # Excel bytes in memory
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_exp.to_excel(writer, index=False, sheet_name='Creator Orbit CRM')
            buffer.seek(0)

            st.download_button(
                label="📥 Download Excel (.xlsx)",
                data=buffer,
                file_name="Creator_Orbit_CRM_Export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
                type="primary"
            )

    # ── Campaign Rosters & Client Pitch Builder ──
    st.divider()
    st.subheader("📋 Campaign Rosters & Client Pitch Builder")

    c_mgmt1, c_mgmt2 = st.columns([3, 1])
    with c_mgmt1:
        new_campaign_name = st.text_input("Create a New Client Campaign", placeholder="e.g. Nykaa Skincare Q3, Minimalist Sunscreen Launch...")
    with c_mgmt2:
        st.write("")
        st.write("")
        if st.button("➕ Create Campaign", use_container_width=True) and new_campaign_name:
            db.create_campaign(new_campaign_name)
            st.success(f"Campaign '{new_campaign_name}' created!")
            st.rerun()

    existing_campaigns = db.get_all_campaigns()
    if existing_campaigns:
        camp_names = {c["campaign_name"]: c["id"] for c in existing_campaigns}
        active_camp = st.selectbox("Select Active Campaign", list(camp_names.keys()))

        if active_camp:
            camp_id = camp_names[active_camp]

            # Add creator multi-select
            st.markdown(f"**Add Creators to '{active_camp}'**")
            all_options = {f"{c.get('name')} (@{c.get('platform_id')}) - {c.get('subscriber_count',0):,} followers": c["id"] for c in all_raw_creators[:500]}
            
            sel_add1, sel_add2 = st.columns([4, 1])
            with sel_add1:
                chosen_creators = st.multiselect("Pick creators to add to this campaign", list(all_options.keys()))
            with sel_add2:
                st.write("")
                st.write("")
                if st.button("➕ Add Selected", use_container_width=True) and chosen_creators:
                    for item in chosen_creators:
                        c_id = all_options[item]
                        db.add_to_campaign(camp_id, c_id)
                    st.success(f"Added {len(chosen_creators)} creators to '{active_camp}'!")
                    st.rerun()

            # Display Campaign Roster
            roster = db.get_campaign_creators(camp_id)
            if roster:
                st.markdown(f"### 📋 Roster for **{active_camp}** ({len(roster)} creators)")
                
                r_rows = []
                for c in roster:
                    ex = c.get("extra_data") or {}
                    if isinstance(ex, str):
                        try:
                            ex = json.loads(ex)
                        except Exception:
                            ex = {}
                    if not isinstance(ex, dict):
                        ex = {}

                    r_rows.append({
                        "Name": c.get("name"),
                        "Handle": f"@{c.get('platform_id')}",
                        "Followers": f"{c.get('subscriber_count', 0):,}",
                        "Median Views": f"{c.get('median_views', 0):,}",
                        "Contact Email": ex.get("bio_email") or "—",
                        "Phone / WhatsApp": ex.get("phone") or "—",
                        "Location": f"{ex.get('city', '')} {ex.get('state', '')}".strip() or "—",
                        "Est. Rate": f"${c.get('estimated_cpm_low', 0):,.0f} – ${c.get('estimated_cpm_high', 0):,.0f}",
                        "Status": c.get("status", "shortlisted").title(),
                    })

                st.dataframe(pd.DataFrame(r_rows), use_container_width=True, hide_index=True)

                r_m1, r_m2 = st.columns(2)
                tot_views = sum(c.get("median_views", 0) for c in roster)
                r_m1.metric("Total Expected Campaign Reach", f"{tot_views:,} views")
                r_m2.metric("Total Creators in Roster", len(roster))

                # Export Roster
                if st.button("📤 Export Branded Client Media Plan (.xlsx)", type="primary"):
                    fpath = exporter.export_campaign_roster(active_camp, roster, format="excel")
                    st.success(f"Branded Campaign Roster saved to: `{fpath}`")
            else:
                st.info(f"No creators in '{active_camp}' yet. Select creators above and click 'Add Selected'.")

