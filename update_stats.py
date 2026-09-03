#!/usr/bin/env python3
import os
import sys
import json
import math
import re
import io
import urllib.request
from PIL import Image, ImageDraw, ImageFont, ImageFilter

USERNAME = "shari4444"
DISPLAY_NAME = "sharvari chaudhari"
OUTPUT_PATH = os.path.join("assets", "github-stats.gif")

# Image dimensions
WIDTH = 700
HEIGHT = 700

# Color Palette (Dark Theme matching user design)
BG_COLOR = (11, 12, 14, 255)            # Outside canvas background #0B0C0E
CARD_BG = (16, 17, 21, 255)             # Main Card background #101115
CARD_BORDER = (31, 34, 43, 255)         # Card border stroke #1F222B
TEXT_WHITE = (255, 255, 255, 255)       # Main white text
TEXT_MUTED = (138, 142, 155, 255)      # Muted grey text #8A8E9B
GREEN_ACCENT = (78, 190, 102, 255)      # Bright green value & fill #4EBE66
PROGRESS_TRACK = (34, 37, 46, 255)      # Dark progress track #22252E
DIVIDER_COLOR = (30, 33, 41, 255)       # Horizontal line #1E2129
ICON_BG = (22, 24, 30, 255)             # Icon background circle #16181E
ICON_BORDER = (38, 41, 52, 255)         # Icon circle border #262934


def get_font(font_size, bold=False):
    """Attempt to load system truetype fonts or fallback gracefully."""
    font_candidates = [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "Arial.ttf",
        "Helvetica.ttf"
    ]
    for font_path in font_candidates:
        if os.path.exists(font_path):
            try:
                index = 1 if (bold and font_path.endswith(".ttc")) else 0
                return ImageFont.truetype(font_path, font_size, index=index)
            except Exception:
                pass
    try:
        return ImageFont.load_default(size=font_size)
    except Exception:
        return ImageFont.load_default()


def fetch_github_stats():
    """Fetch public repository count, commit count, and avatar for GitHub user."""
    headers = {"User-Agent": "GitHub-Stats-Card-Generator"}
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    public_repos = 0
    avatar_url = None
    name = DISPLAY_NAME

    # User Profile Details
    try:
        user_url = f"https://api.github.com/users/{USERNAME}"
        req = urllib.request.Request(user_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            public_repos = data.get("public_repos", 0)
            avatar_url = data.get("avatar_url")
            if data.get("name"):
                name = data.get("name").lower()
    except Exception as e:
        print(f"Warning: Failed to fetch user profile ({e})", file=sys.stderr)

    # 1. Search Commits API
    total_commits = 0
    search_success = False
    try:
        headers_commit = dict(headers)
        headers_commit["Accept"] = "application/vnd.github+json"
        commit_url = f"https://api.github.com/search/commits?q=author:{USERNAME}"
        req_commit = urllib.request.Request(commit_url, headers=headers_commit)
        with urllib.request.urlopen(req_commit, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            total_commits = data.get("total_count", 0)
            search_success = True
    except Exception as e:
        print(f"Warning: Commit search API failed ({e}). Trying fallback repo commit counting...", file=sys.stderr)

    # 2. Fallback Commit Calculation across Repos if Search API failed or returned 0
    if not search_success or total_commits == 0:
        try:
            repos_url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner"
            req_repos = urllib.request.Request(repos_url, headers=headers)
            with urllib.request.urlopen(req_repos, timeout=15) as resp:
                repos = json.loads(resp.read().decode())
                calc_commits = 0
                for r in repos:
                    repo_name = r.get("name")
                    commits_url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/commits?author={USERNAME}&per_page=1"
                    req_c = urllib.request.Request(commits_url, headers=headers)
                    try:
                        with urllib.request.urlopen(req_c, timeout=10) as resp_c:
                            link_hdr = resp_c.headers.get("Link")
                            if link_hdr and 'rel="last"' in link_hdr:
                                match = re.search(r'page=(\d+)>; rel="last"', link_hdr)
                                count = int(match.group(1)) if match else len(json.loads(resp_c.read().decode()))
                            else:
                                count = len(json.loads(resp_c.read().decode()))
                            calc_commits += count
                    except Exception:
                        pass
                if calc_commits > 0:
                    total_commits = calc_commits
        except Exception as e:
            print(f"Warning: Fallback commit calculation failed ({e})", file=sys.stderr)

    # Download Avatar Image
    avatar_img = None
    if avatar_url:
        try:
            req_avatar = urllib.request.Request(avatar_url, headers=headers)
            with urllib.request.urlopen(req_avatar, timeout=10) as resp:
                avatar_bytes = resp.read()
                avatar_img = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        except Exception as e:
            print(f"Warning: Failed to download avatar ({e})", file=sys.stderr)

    return public_repos, total_commits, avatar_img, name


def create_avatar_icon(avatar_img, size=120):
    """Render square avatar container with white ambient glow and rounded corners."""
    container_size = size
    r = 24  # corner radius

    if avatar_img:
        img = avatar_img.resize((container_size, container_size), Image.Resampling.LANCZOS)
    else:
        # Fallback octocat placeholder box
        img = Image.new("RGBA", (container_size, container_size), (15, 15, 18, 255))
        draw_fallback = ImageDraw.Draw(img)
        draw_fallback.text((container_size // 3, container_size // 3), "GH", fill=(255, 255, 255, 255))

    # Mask to rounded square
    mask = Image.new("L", (container_size, container_size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle([0, 0, container_size, container_size], radius=r, fill=255)

    rounded_avatar = Image.new("RGBA", (container_size, container_size), (0, 0, 0, 0))
    rounded_avatar.paste(img, (0, 0), mask)

    # Ambient halo/glow
    glow_padding = 40
    total_w = container_size + glow_padding * 2
    total_h = container_size + glow_padding * 2
    glow_img = Image.new("RGBA", (total_w, total_h), (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow_img)
    glow_draw.rounded_rectangle(
        [glow_padding - 4, glow_padding - 4, glow_padding + container_size + 4, glow_padding + container_size + 4],
        radius=r + 4,
        fill=(255, 255, 255, 65)
    )
    glow_blur = glow_img.filter(ImageFilter.GaussianBlur(radius=16))

    # Composite rounded avatar onto center of glow
    glow_blur.paste(rounded_avatar, (glow_padding, glow_padding), rounded_avatar)
    return glow_blur, glow_padding


def render_frame(repos_val, commits_val, repos_ratio, commits_ratio, avatar_glow, glow_pad, name, fonts):
    """Render a single frame of the card animation."""
    font_title, font_code, font_val, font_sub = fonts

    img = Image.new("RGBA", (WIDTH, HEIGHT), BG_COLOR)
    draw = ImageDraw.Draw(img)

    # Card coordinates
    card_x1, card_y1 = 40, 40
    card_x2, card_y2 = 660, 660
    card_r = 32

    # Draw main dark card background & border
    draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=card_r, fill=CARD_BG, outline=CARD_BORDER, width=2)

    # 1. Avatar Header
    av_w, _ = avatar_glow.size
    av_x = (WIDTH - av_w) // 2
    av_y = card_y1 + 45 - glow_pad
    img.paste(avatar_glow, (av_x, av_y), avatar_glow)

    # 2. Name Text
    name_str = name if name else DISPLAY_NAME
    bbox = font_title.getbbox(name_str)
    name_w = bbox[2] - bbox[0]
    name_x = (WIDTH - name_w) // 2
    name_y = card_y1 + 195
    draw.text((name_x, name_y), name_str, font=font_title, fill=TEXT_WHITE)

    # 3. Horizontal Line Divider
    line_y = card_y1 + 255
    draw.line([(card_x1 + 35, line_y), (card_x2 - 35, line_y)], fill=DIVIDER_COLOR, width=2)

    # 4. Section 1: REPOSITORY
    sec1_y = line_y + 40
    icon_radius = 28
    icon1_cx, icon1_cy = card_x1 + 65, sec1_y + 30
    draw.ellipse([icon1_cx - icon_radius, icon1_cy - icon_radius, icon1_cx + icon_radius, icon1_cy + icon_radius],
                 fill=ICON_BG, outline=ICON_BORDER, width=2)

    # Vector monitor icon inside circle
    draw.rounded_rectangle([icon1_cx - 13, icon1_cy - 11, icon1_cx + 13, icon1_cy + 6], radius=3, outline=TEXT_WHITE, width=2)
    draw.line([(icon1_cx, icon1_cy + 6), (icon1_cx, icon1_cy + 11)], fill=TEXT_WHITE, width=2)
    draw.line([(icon1_cx - 8, icon1_cy + 11), (icon1_cx + 8, icon1_cy + 11)], fill=TEXT_WHITE, width=2)

    # Section 1 Labels
    content_x = card_x1 + 115
    draw.text((content_x, sec1_y), "REPOSITORY:", font=font_sub, fill=TEXT_MUTED)

    repo_prefix = "Repositories: "
    repo_num_str = f"{repos_val:,}"
    prefix_w = font_val.getbbox(repo_prefix)[2] - font_val.getbbox(repo_prefix)[0]
    draw.text((content_x, sec1_y + 22), repo_prefix, font=font_val, fill=TEXT_WHITE)
    draw.text((content_x + prefix_w, sec1_y + 22), repo_num_str, font=font_val, fill=GREEN_ACCENT)

    # Progress bar 1
    bar1_y1 = sec1_y + 65
    bar1_y2 = bar1_y1 + 16
    bar_x1 = content_x
    bar_x2 = card_x2 - 45
    bar_w = bar_x2 - bar_x1

    draw.rounded_rectangle([bar_x1, bar1_y1, bar_x2, bar1_y2], radius=8, fill=PROGRESS_TRACK)
    fill1_w = int(bar_w * repos_ratio)
    if fill1_w > 16:
        draw.rounded_rectangle([bar_x1, bar1_y1, bar_x1 + fill1_w, bar1_y2], radius=8, fill=GREEN_ACCENT)
    elif fill1_w > 0:
        draw.rectangle([bar_x1, bar1_y1, bar_x1 + fill1_w, bar1_y2], fill=GREEN_ACCENT)

    # 5. Section 2: TOTAL COMMITS
    sec2_y = bar1_y2 + 45
    icon2_cx, icon2_cy = card_x1 + 65, sec2_y + 30
    draw.ellipse([icon2_cx - icon_radius, icon2_cy - icon_radius, icon2_cx + icon_radius, icon2_cy + icon_radius],
                 fill=ICON_BG, outline=ICON_BORDER, width=2)

    # </> Code icon centered inside circle
    code_str = "</>"
    c_bbox = font_code.getbbox(code_str)
    c_w = c_bbox[2] - c_bbox[0]
    c_h = c_bbox[3] - c_bbox[1]
    draw.text((icon2_cx - c_w // 2, icon2_cy - c_h // 2 - c_bbox[1]), code_str, font=font_code, fill=TEXT_WHITE)

    # Section 2 Labels
    draw.text((content_x, sec2_y), "TOTAL COMMITS:", font=font_sub, fill=TEXT_MUTED)

    commit_prefix = "Total Commits: "
    commit_num_str = f"{commits_val:,}"
    c_prefix_w = font_val.getbbox(commit_prefix)[2] - font_val.getbbox(commit_prefix)[0]
    draw.text((content_x, sec2_y + 22), commit_prefix, font=font_val, fill=TEXT_WHITE)
    draw.text((content_x + c_prefix_w, sec2_y + 22), commit_num_str, font=font_val, fill=GREEN_ACCENT)

    # Progress bar 2
    bar2_y1 = sec2_y + 65
    bar2_y2 = bar2_y1 + 16
    draw.rounded_rectangle([bar_x1, bar2_y1, bar_x2, bar2_y2], radius=8, fill=PROGRESS_TRACK)
    fill2_w = int(bar_w * commits_ratio)
    if fill2_w > 16:
        draw.rounded_rectangle([bar_x1, bar2_y1, bar_x1 + fill2_w, bar2_y2], radius=8, fill=GREEN_ACCENT)
    elif fill2_w > 0:
        draw.rectangle([bar_x1, bar2_y1, bar_x1 + fill2_w, bar2_y2], fill=GREEN_ACCENT)

    return img


def ease_out_cubic(t):
    """Cubic ease-out curve for natural visual smoothing."""
    return 1.0 - math.pow(1.0 - t, 3)


def main():
    print(f"Fetching GitHub stats for user: {USERNAME}...")
    public_repos, total_commits, avatar_img, name = fetch_github_stats()
    print(f"Fetched stats -> Repositories: {public_repos}, Total Commits: {total_commits}")

    # Load fonts
    font_title = get_font(34, bold=True)
    font_code = get_font(18, bold=True)
    font_val = get_font(24, bold=True)
    font_sub = get_font(14, bold=True)
    fonts = (font_title, font_code, font_val, font_sub)

    # Avatar glow asset
    avatar_glow, glow_pad = create_avatar_icon(avatar_img, size=125)

    # Target progress ratios for full stats fill (~75-80% bar length matching UI reference design)
    target_repo_ratio = 0.76
    target_commit_ratio = 0.78

    NUM_ANIM_FRAMES = 30
    frames = []
    durations = []

    print("Rendering animation frames...")
    for i in range(NUM_ANIM_FRAMES):
        t = i / float(NUM_ANIM_FRAMES - 1)
        eased_t = ease_out_cubic(t)

        current_repos = int(round(public_repos * eased_t))
        current_commits = int(round(total_commits * eased_t))

        repos_ratio = target_repo_ratio * eased_t
        commits_ratio = target_commit_ratio * eased_t

        frame_img = render_frame(
            current_repos,
            current_commits,
            repos_ratio,
            commits_ratio,
            avatar_glow,
            glow_pad,
            name,
            fonts
        )
        frames.append(frame_img.convert("P", palette=Image.Palette.ADAPTIVE))

        if i == NUM_ANIM_FRAMES - 1:
            durations.append(3000)  # Hold 3 seconds on final state before looping
        else:
            durations.append(40)     # 40ms per frame count-up animation

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    print(f"Saving GIF to {OUTPUT_PATH}...")

    frames[0].save(
        OUTPUT_PATH,
        save_all=True,
        append_images=frames[1:],
        duration=durations,
        loop=0,
        disposal=2,
        optimize=True
    )

    print("Successfully generated animated stats GIF!")


if __name__ == "__main__":
    main()
