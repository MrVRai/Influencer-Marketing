"""
Creator Discovery & Sponsorship Scraper — Streamlit Dashboard
=============================================================
A comprehensive tool for influencer marketing agencies to discover
YouTube & Instagram creators, analyze performance metrics, detect
past sponsorships, and manage campaign rosters.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

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
    get_language_name,
    SUPPORTED_LANGUAGES,
)
from core.sponsor_detector import SponsorDetector
from core.database import CreatorDatabase
from utils.exporter import DataExporter

# ─────────────────────────── Page Config ────────────────────────────
st.set_page_config(
    page_title="Creator Discovery Engine",
    page_icon="🔍",
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
    st.title("🔍 Creator Discovery")
    st.caption("Influencer Marketing Agency Tool")

    st.divider()

    # API status indicators
    st.subheader("🔌 API Status")
    if yt.api_available:
        st.success("✅ YouTube Data API — Connected")
    else:
        st.warning("⚠️ YouTube API — Using scraper fallback")

    if ig.api_available:
        st.success("✅ Instagram (Apify) — Connected")
    else:
        st.info("ℹ️ Instagram — Add APIFY_API_TOKEN to .env")

    st.divider()

    # Database stats
    st.subheader("📊 Database")
    all_creators = db.search_creators(limit=9999)
    all_campaigns = db.get_all_campaigns()
    col1, col2 = st.columns(2)
    col1.metric("Creators Saved", len(all_creators))
    col2.metric("Campaigns", len(all_campaigns))


# ─────────────────────────── Main Tabs ──────────────────────────────
tab1, tab2, tab3 = st.tabs([
    "🔎 Creator Discovery",
    "📊 Channel Deep-Dive",
    "📋 Campaign Roster & Export",
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
                results = []

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
                            if len(results) >= max_results:
                                break

                            progress.progress(
                                (idx + 1) / len(channels),
                                text=f"Analyzing: {channel.get('title', 'Unknown')} ({idx+1}/{len(channels)}) — Matched: {len(results)}/{max_results}",
                            )

                            channel_id = channel.get("channel_id", "")
                            if not channel_id:
                                continue

                            # Get details & recent videos
                            details = yt.get_channel_details(channel_id)
                            videos = yt.get_recent_videos(channel_id, max_results=15)

                            # Calculate metrics
                            median_views = calculate_median_views(videos)
                            engagement_rate = calculate_engagement_rate(videos)
                            consistency = calculate_consistency_score(videos)
                            content_lang = detect_content_language(videos)
                            sub_count = details.get("subscriber_count", 0)
                            creator_score = calculate_creator_score(
                                median_views, engagement_rate, consistency, sub_count,
                            )
                            cpm = estimate_cpm_rate(median_views, "youtube", "60s_midroll")

                            # Apply filters
                            if min_subs > 0 and sub_count < min_subs:
                                continue
                            if max_subs > 0 and sub_count > max_subs:
                                continue
                            if min_engagement > 0 and engagement_rate < min_engagement:
                                continue
                            if min_views_filter > 0 and median_views < min_views_filter:
                                continue
                            if language_filter != "All Languages":
                                lang_code = language_filter.split("(")[-1].rstrip(")")
                                if content_lang != lang_code:
                                    continue
                            if has_sponsor_yt:
                                has_sp = any(detector.detect_from_description(v.get('description', ''))['is_sponsored'] for v in videos)
                                if not has_sp:
                                    continue

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
                            }

                            # Save to DB
                            db.upsert_creator(creator_data)
                            creator_data["videos"] = videos
                            results.append(creator_data)

                        progress.empty()

                elif platform == "Instagram":
                    if not ig.api_available:
                        st.error("Instagram requires Apify API token. Add APIFY_API_TOKEN to your .env file.")
                    else:
                        fetch_pool = max(max_results * 5, 80)

                        if search_mode == "#️⃣ Hashtag":
                            # Hashtag search: single wide scrape
                            scrape_status = st.empty()
                            scrape_status.info("🔍 Round 1 — Scraping hashtag posts...")
                            profiles = ig.search_by_hashtag(clean_query, max_results=max_results, fetch_limit=fetch_pool)
                            scrape_status.empty()
                        else:
                            # Keyword search: multi-round query variation scraping
                            round_progress = st.progress(0, text="🔍 Starting multi-round Instagram scrape...")
                            round_status = st.empty()

                            def ig_round_callback(round_num, total_rounds, variant, found_so_far):
                                pct = round_num / total_rounds
                                round_progress.progress(
                                    pct,
                                    text=f"🔄 Round {round_num}/{total_rounds} — Searching '{variant}' | Candidates collected: {found_so_far}"
                                )
                                round_status.info(f"📡 Scraping variation **'{variant}'** (Round {round_num} of {total_rounds}) — {found_so_far} unique creators found so far")

                            profiles = ig.search_profiles(
                                clean_query,
                                max_results=max_results,
                                fetch_limit=fetch_pool,
                                progress_callback=ig_round_callback
                            )
                            round_progress.empty()
                            round_status.empty()

                        if not profiles:
                            st.warning(f"No Instagram creators returned by Apify for '{clean_query}'. Try a broader topic (e.g. 'fitness', 'beauty', 'tech') or a specific handle (e.g. '@mkbhd').")
                        else:
                            st.info(f"✅ Collected **{len(profiles)} unique candidate profiles** — now applying your filters...")
                            progress = st.progress(0, text="Analyzing profiles...")
                            all_unfiltered_creators = []
                            tier_counts = {"Mega (1M+)": 0, "Macro (500K-1M)": 0, "Mid-Tier (100K-500K)": 0, "Micro (10K-100K)": 0, "Nano (1K-10K)": 0}

                            for idx, profile in enumerate(profiles):
                                if len(results) >= max_results:
                                    break

                                progress.progress(
                                    (idx + 1) / len(profiles),
                                    text=f"Analyzing: @{profile.get('username', 'unknown')} ({idx+1}/{len(profiles)}) — Matched: {len(results)}/{max_results}",
                                )

                                username = profile.get("username", "")
                                if not username:
                                    continue

                                posts = profile.get("posts", [])
                                follower_count = profile.get("follower_count", 0)

                                if follower_count >= 1000000:
                                    tier_counts["Mega (1M+)"] += 1
                                elif follower_count >= 500000:
                                    tier_counts["Macro (500K-1M)"] += 1
                                elif follower_count >= 100000:
                                    tier_counts["Mid-Tier (100K-500K)"] += 1
                                elif follower_count >= 10000:
                                    tier_counts["Micro (10K-100K)"] += 1
                                else:
                                    tier_counts["Nano (1K-10K)"] += 1

                                # Build post metrics
                                post_metrics = [
                                    {
                                        "view_count": p.get("view_count", p.get("like_count", 0) * 10),
                                        "like_count": p.get("like_count", 0),
                                        "comment_count": p.get("comment_count", 0),
                                        "title": p.get("caption", "")[:50],
                                        "description": "",
                                    }
                                    for p in posts
                                ] if posts else [
                                    {
                                        "view_count": max(int(follower_count * 0.1), 100),
                                        "like_count": max(int(follower_count * 0.03), 10),
                                        "comment_count": max(int(follower_count * 0.002), 1),
                                        "title": profile.get("biography", "")[:50],
                                        "description": "",
                                    }
                                ]

                                median_views = calculate_median_views(post_metrics)
                                engagement_rate = calculate_engagement_rate(post_metrics)
                                consistency = calculate_consistency_score(post_metrics)
                                content_lang = detect_content_language(post_metrics)
                                creator_score = calculate_creator_score(
                                    median_views, engagement_rate, consistency, follower_count,
                                )
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
                                }

                                db.upsert_creator(creator_data)
                                creator_data["posts"] = posts
                                creator_data["videos"] = post_metrics
                                all_unfiltered_creators.append(creator_data)

                                # Apply Instagram Advanced Filters
                                if min_subs > 0 and follower_count < min_subs:
                                    continue
                                if max_subs > 0 and follower_count > max_subs:
                                    continue
                                if min_engagement > 0 and engagement_rate < min_engagement:
                                    continue
                                if min_posts > 0 and profile.get("post_count", len(posts)) < min_posts:
                                    continue
                                if language_filter != "All Languages":
                                    lang_code = language_filter.split("(")[-1].rstrip(")")
                                    if content_lang != "unknown" and content_lang != lang_code:
                                        continue
                                if verified_only and not profile.get("is_verified", False):
                                    continue
                                if must_have_email and not profile.get("bio_email"):
                                    continue
                                if collab_only and ig_sponsor_check["total_sponsored_posts"] == 0:
                                    continue

                                results.append(creator_data)

                            progress.empty()

                            st.session_state.all_scraped_creators = all_unfiltered_creators

                            if len(profiles) > 0 and len(results) == 0:
                                breakdown_str = ", ".join(f"{k}: {v}" for k, v in tier_counts.items() if v > 0)
                                st.warning(
                                    f"⚠️ Scraped **{len(profiles)}** Instagram creators, but none matched your active filters.\n\n"
                                    f"📊 **Follower Breakdown of Scraped Creators:** {breakdown_str}\n\n"
                                    f"💡 *Tip: Broad terms ('fitness') rank major celebrity/macro accounts on Instagram. For Micro/Nano creators, try specific queries like 'calisthenics coach', 'pilates trainer', or 'mobility drills'.*"
                                )

                st.session_state.search_results = results

    # ── Display Results ──
    results = st.session_state.search_results
    if not results and st.session_state.get("all_scraped_creators"):
        if st.button("🔓 Show All Scraped Creators Anyway (Bypass Filter)", type="secondary"):
            st.session_state.search_results = st.session_state.all_scraped_creators
            st.rerun()
    if results:
        st.success(f"Found **{len(results)}** creators matching your criteria")

        # Summary metrics row
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
# TAB 3: Campaign Roster & Export
# ═══════════════════════════════════════════════════════════════════
with tab3:
    st.header("Campaign Roster & Export")

    # ── Campaign Management ──
    mgmt_col1, mgmt_col2 = st.columns([2, 1])

    with mgmt_col1:
        new_campaign_name = st.text_input("Create New Campaign", placeholder="e.g. Q3 SaaS Launch")
    with mgmt_col2:
        st.write("")  # spacer
        st.write("")
        if st.button("➕ Create Campaign") and new_campaign_name:
            db.create_campaign(new_campaign_name)
            st.success(f"Campaign '{new_campaign_name}' created!")
            st.rerun()

    st.divider()

    # ── Existing Campaigns ──
    campaigns = db.get_all_campaigns()
    if campaigns:
        campaign_names = {c["campaign_name"]: c["id"] for c in campaigns}
        selected_campaign = st.selectbox(
            "Select Campaign",
            list(campaign_names.keys()),
        )

        if selected_campaign:
            campaign_id = campaign_names[selected_campaign]

            # Add creator to campaign
            st.subheader("Add Creators to Campaign")
            saved_creators = db.search_creators(limit=200)
            if saved_creators:
                creator_options = {
                    f"{c['name']} ({c['platform']})": c["id"] for c in saved_creators
                }
                add_col1, add_col2 = st.columns([3, 1])
                with add_col1:
                    selected_to_add = st.multiselect(
                        "Select creators to add",
                        list(creator_options.keys()),
                    )
                with add_col2:
                    st.write("")
                    st.write("")
                    if st.button("➕ Add to Campaign") and selected_to_add:
                        for name in selected_to_add:
                            creator_id = creator_options[name]
                            db.add_to_campaign(campaign_id, creator_id)
                        st.success(f"Added {len(selected_to_add)} creators to '{selected_campaign}'")
                        st.rerun()

            # Show campaign roster
            st.divider()
            st.subheader(f"📋 Roster: {selected_campaign}")
            roster = db.get_campaign_creators(campaign_id)

            if roster:
                roster_df = pd.DataFrame([
                    {
                        "Name": c["name"],
                        "Platform": c["platform"].title(),
                        "Subscribers": f"{c.get('subscriber_count', 0):,}",
                        "Median Views": f"{c.get('median_views', 0):,}",
                        "Engagement Rate": f"{c.get('engagement_rate', 0):.2f}%",
                        "Language": get_language_name(c.get("content_language", "unknown")),
                        "Est. Rate": f"${c.get('estimated_cpm_low', 0):,.0f} – ${c.get('estimated_cpm_high', 0):,.0f}",
                        "Score": c.get("creator_score", 0),
                        "Status": c.get("status", "shortlisted"),
                    }
                    for c in roster
                ])
                st.dataframe(roster_df, use_container_width=True, hide_index=True)

                # Export buttons
                st.divider()
                exp_col1, exp_col2, exp_col3 = st.columns(3)

                with exp_col1:
                    if st.button("📥 Export as CSV"):
                        filepath = exporter.export_campaign_roster(
                            selected_campaign, roster, format="csv",
                        )
                        st.success(f"Exported to: `{filepath}`")

                with exp_col2:
                    if st.button("📥 Export as Excel"):
                        filepath = exporter.export_campaign_roster(
                            selected_campaign, roster, format="excel",
                        )
                        st.success(f"Exported to: `{filepath}`")

                with exp_col3:
                    # Quick stats
                    total_reach = sum(c.get("median_views", 0) for c in roster)
                    avg_er = sum(c.get("engagement_rate", 0) for c in roster) / len(roster) if roster else 0
                    st.metric("Total Campaign Reach", f"{total_reach:,}")
                    st.metric("Avg Engagement Rate", f"{avg_er:.2f}%")
            else:
                st.info("No creators in this campaign yet. Add creators from the list above.")
    else:
        st.info("No campaigns created yet. Create your first campaign above!")

    # ── Saved Creators Database ──
    st.divider()
    st.subheader("🗄️ All Saved Creators")

    # Filters for saved data
    db_col1, db_col2, db_col3 = st.columns(3)
    with db_col1:
        db_platform = st.selectbox("Filter Platform", ["All", "YouTube", "Instagram"], key="db_plat")
    with db_col2:
        db_language = st.selectbox(
            "Filter Language",
            ["All"] + [f"{name} ({code})" for code, name in SUPPORTED_LANGUAGES.items()],
            key="db_lang",
        )
    with db_col3:
        db_sort = st.selectbox(
            "Sort By",
            ["Creator Score", "Subscribers", "Median Views", "Engagement Rate"],
            key="db_sort",
        )

    sort_map = {
        "Creator Score": "creator_score",
        "Subscribers": "subscriber_count",
        "Median Views": "median_views",
        "Engagement Rate": "engagement_rate",
    }

    query_params = {"sort_by": sort_map.get(db_sort, "creator_score"), "limit": 100}
    if db_platform != "All":
        query_params["platform"] = db_platform.lower()
    if db_language != "All":
        lang_code = db_language.split("(")[-1].rstrip(")")
        query_params["language"] = lang_code

    saved = db.search_creators(**query_params)

    if saved:
        saved_rows = []
        for c in saved:
            extra = c.get("extra_data") or {}
            if isinstance(extra, str):
                import json
                try:
                    extra = json.loads(extra)
                except Exception:
                    extra = {}
            if not isinstance(extra, dict):
                extra = {}

            saved_rows.append({
                "Name": c["name"],
                "Platform": c["platform"].title(),
                "Handle / ID": c["platform_id"],
                "Followers / Subs": c.get("subscriber_count", 0),
                "Median Views": c.get("median_views", 0),
                "ER (%)": f"{c.get('engagement_rate', 0):.2f}%",
                "Language": get_language_name(c.get("content_language", "unknown")),
                "Score": c.get("creator_score", 0),
                "Verified": "☑️ Yes" if extra.get("is_verified") else "No",
                "Contact Email": extra.get("bio_email") or "—",
                "Est. Rate": f"${c.get('estimated_cpm_low', 0):,.0f} – ${c.get('estimated_cpm_high', 0):,.0f}",
            })

        saved_df = pd.DataFrame(saved_rows)
        st.dataframe(saved_df, use_container_width=True, hide_index=True)
    else:
        st.info("No creators saved yet. Use the Discovery tab to search and save creators.")
