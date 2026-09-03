#!/usr/bin/env python3
"""
generate-profile-svg.py
Generates an animated, futuristic SVG profile banner for GitHub user 'shari4444'.
Fetches live statistics (public repos, total commit count) via GitHub REST API.
Does NOT require external dependencies (uses standard library urllib, json, xml.etree).
"""

import os
import sys
import json
import re
import urllib.request
import xml.etree.ElementTree as ET

USERNAME = "shari4444"
DISPLAY_NAME = "SHARI4444"
TAGLINE = "BUILD • CREATE • SHIP"
OUTPUT_PATH = os.path.join("assets", "profile-animation.svg")


def fetch_github_stats():
    """Fetch user profile statistics and calculate total commits."""
    headers = {"User-Agent": "GitHub-Profile-SVG-Generator"}
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    public_repos = 0
    total_commits = 0

    # 1. Fetch User Profile for public_repos
    try:
        user_url = f"https://api.github.com/users/{USERNAME}"
        req = urllib.request.Request(user_url, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            public_repos = data.get("public_repos", 0)
    except Exception as e:
        print(f"Warning: Failed to fetch user profile ({e})", file=sys.stderr)

    # 2. Fetch Total Commits via Search API
    search_success = False
    try:
        headers_commit = dict(headers)
        headers_commit["Accept"] = "application/vnd.github+json"
        commit_url = f"https://api.github.com/search/commits?q=author:{USERNAME}"
        req_commit = urllib.request.Request(commit_url, headers=headers_commit)
        with urllib.request.urlopen(req_commit, timeout=12) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            total_commits = data.get("total_count", 0)
            search_success = True
    except Exception as e:
        print(f"Warning: Commit search API failed ({e}). Trying fallback repo commit count...", file=sys.stderr)

    # 3. Fallback: Sum commits across public repositories
    if not search_success or total_commits == 0:
        try:
            repos_url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&type=owner"
            req_repos = urllib.request.Request(repos_url, headers=headers)
            with urllib.request.urlopen(req_repos, timeout=15) as resp:
                repos = json.loads(resp.read().decode("utf-8"))
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
                                count = int(match.group(1)) if match else len(json.loads(resp_c.read().decode("utf-8")))
                            else:
                                count = len(json.loads(resp_c.read().decode("utf-8")))
                            calc_commits += count
                    except Exception:
                        pass
                if calc_commits > 0:
                    total_commits = calc_commits
        except Exception as e:
            print(f"Warning: Fallback commit calculation failed ({e})", file=sys.stderr)

    return public_repos, total_commits


def generate_svg(public_repos, total_commits):
    """Build the SVG XML string with embedded CSS keyframe animations."""

    # Format numbers
    repo_str = f"{public_repos:,}" if public_repos > 0 else "0"
    commit_str = f"{total_commits:,}" if total_commits > 0 else "0"

    svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 950 320" width="100%" height="100%">
  <defs>
    <!-- Background Gradient -->
    <linearGradient id="bg-grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#090A0F"/>
      <stop offset="50%" stop-color="#0E1017"/>
      <stop offset="100%" stop-color="#141724"/>
    </linearGradient>

    <!-- Title Text Gradient -->
    <linearGradient id="title-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00F2FE"/>
      <stop offset="100%" stop-color="#4FACFE"/>
    </linearGradient>

    <!-- Stat Bar 1 Gradient -->
    <linearGradient id="bar1-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00F2FE"/>
      <stop offset="100%" stop-color="#00C6FF"/>
    </linearGradient>

    <!-- Stat Bar 2 Gradient -->
    <linearGradient id="bar2-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#00E676"/>
      <stop offset="100%" stop-color="#1DE9B6"/>
    </linearGradient>

    <!-- Stat Bar 3 Gradient -->
    <linearGradient id="bar3-grad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#7F56D9"/>
      <stop offset="100%" stop-color="#9E77ED"/>
    </linearGradient>

    <!-- Card Background Gradient -->
    <linearGradient id="card-grad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#121520" stop-opacity="0.9"/>
      <stop offset="100%" stop-color="#181C2B" stop-opacity="0.9"/>
    </linearGradient>

    <!-- Glow Filters -->
    <filter id="glow-cyan" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="6" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <style>
    @keyframes fadeIn {{
      0% {{ opacity: 0; transform: translateY(12px); }}
      100% {{ opacity: 1; transform: translateY(0); }}
    }}

    @keyframes pulseDot {{
      0%, 100% {{ opacity: 1; }}
      50% {{ opacity: 0.3; }}
    }}

    @keyframes scanLine {{
      0% {{ transform: translateX(-950px); }}
      100% {{ transform: translateX(950px); }}
    }}

    @keyframes expandBar1 {{
      0% {{ width: 0px; }}
      100% {{ width: 190px; }}
    }}

    @keyframes expandBar2 {{
      0% {{ width: 0px; }}
      100% {{ width: 210px; }}
    }}

    @keyframes expandBar3 {{
      0% {{ width: 0px; }}
      100% {{ width: 200px; }}
    }}

    .title-text {{
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      font-size: 38px;
      font-weight: 800;
      letter-spacing: 5px;
      fill: url(#title-grad);
      animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      filter: drop-shadow(0 0 10px rgba(0, 242, 254, 0.35));
    }}

    .tagline-text {{
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      font-size: 13px;
      font-weight: 600;
      letter-spacing: 7px;
      fill: #8A93A6;
      animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) 0.2s forwards;
      opacity: 0;
    }}

    .status-text {{
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 2px;
      fill: #00E676;
    }}

    .card {{
      animation: fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
      opacity: 0;
    }}

    .card-1 {{ animation-delay: 0.35s; }}
    .card-2 {{ animation-delay: 0.50s; }}
    .card-3 {{ animation-delay: 0.65s; }}

    .stat-label {{
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 2px;
      fill: #6C768D;
    }}

    .stat-value {{
      font-family: system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      font-size: 32px;
      font-weight: 800;
      fill: #FFFFFF;
    }}

    .bar-fill-1 {{ animation: expandBar1 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.6s forwards; }}
    .bar-fill-2 {{ animation: expandBar2 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.75s forwards; }}
    .bar-fill-3 {{ animation: expandBar3 1.2s cubic-bezier(0.16, 1, 0.3, 1) 0.9s forwards; }}

    .dot-pulse {{ animation: pulseDot 2s infinite ease-in-out; }}
    .scanner {{ animation: scanLine 4s infinite linear; }}
  </style>

  <!-- Main Background Outer Frame -->
  <rect width="950" height="320" rx="16" fill="url(#bg-grad)" stroke="#1F2538" stroke-width="2"/>

  <!-- Subtle Cyber Grid Patterns -->
  <g opacity="0.07" stroke="#FFFFFF" stroke-width="1">
    <line x1="0" y1="80" x2="950" y2="80"/>
    <line x1="0" y1="160" x2="950" y2="160"/>
    <line x1="0" y1="240" x2="950" y2="240"/>
    <line x1="237.5" y1="0" x2="237.5" y2="320"/>
    <line x1="475" y1="0" x2="475" y2="320"/>
    <line x1="712.5" y1="0" x2="712.5" y2="320"/>
  </g>

  <!-- Top Laser Scanner Line -->
  <g opacity="0.6">
    <line class="scanner" x1="0" y1="2" x2="200" y2="2" stroke="url(#title-grad)" stroke-width="2"/>
  </g>

  <!-- Header Content -->
  <g transform="translate(50, 45)">
    <!-- Title -->
    <text x="0" y="32" class="title-text">{DISPLAY_NAME}</text>
    <!-- Tagline -->
    <text x="0" y="58" class="tagline-text">{TAGLINE}</text>
  </g>

  <!-- Live Status Badge (Top Right) -->
  <g transform="translate(730, 45)">
    <rect width="170" height="34" rx="17" fill="#121624" stroke="#1F263B" stroke-width="1.5"/>
    <circle cx="24" cy="17" r="5" fill="#00E676" class="dot-pulse"/>
    <text x="38" y="21" class="status-text">ONLINE • ACTIVE</text>
  </g>

  <!-- Divider Line -->
  <line x1="50" y1="130" x2="900" y2="130" stroke="#1C2133" stroke-width="1.5"/>

  <!-- STATISTICS CARDS -->
  <g transform="translate(50, 155)">

    <!-- CARD 1: REPOSITORIES -->
    <g class="card card-1" transform="translate(0, 0)">
      <rect width="260" height="120" rx="12" fill="url(#card-grad)" stroke="#1F253A" stroke-width="1.5"/>
      <!-- Icon Badge -->
      <rect x="20" y="20" width="36" height="36" rx="8" fill="#181D2E" stroke="#252D45" stroke-width="1"/>
      <path d="M30 33 h16 v10 h-16 z M38 43 v4 M34 47 h8" stroke="#00F2FE" stroke-width="1.8" fill="none" stroke-linecap="round"/>

      <text x="68" y="34" class="stat-label">REPOSITORIES</text>
      <text x="68" y="47" font-family="system-ui" font-size="10" fill="#4E5870">PUBLIC REPOS</text>
      <text x="20" y="88" class="stat-value">{repo_str}</text>

      <!-- Progress Track & Fill -->
      <rect x="20" y="100" width="220" height="6" rx="3" fill="#141826"/>
      <rect class="bar-fill-1" x="20" y="100" width="0" height="6" rx="3" fill="url(#bar1-grad)"/>
    </g>

    <!-- CARD 2: COMMITS -->
    <g class="card card-2" transform="translate(295, 0)">
      <rect width="260" height="120" rx="12" fill="url(#card-grad)" stroke="#1F253A" stroke-width="1.5"/>
      <!-- Icon Badge -->
      <rect x="20" y="20" width="36" height="36" rx="8" fill="#181D2E" stroke="#252D45" stroke-width="1"/>
      <path d="M28 38 l5-5 -5-5 M48 38 l-5-5 5-5 M40 27 l-4 14" stroke="#00E676" stroke-width="1.8" fill="none" stroke-linecap="round"/>

      <text x="68" y="34" class="stat-label">COMMITS</text>
      <text x="68" y="47" font-family="system-ui" font-size="10" fill="#4E5870">TOTAL CONTRIBUTIONS</text>
      <text x="20" y="88" class="stat-value">{commit_str}</text>

      <!-- Progress Track & Fill -->
      <rect x="20" y="100" width="220" height="6" rx="3" fill="#141826"/>
      <rect class="bar-fill-2" x="20" y="100" width="0" height="6" rx="3" fill="url(#bar2-grad)"/>
    </g>

    <!-- CARD 3: ACTIVITY / PROFILE -->
    <g class="card card-3" transform="translate(590, 0)">
      <rect width="260" height="120" rx="12" fill="url(#card-grad)" stroke="#1F253A" stroke-width="1.5"/>
      <!-- Icon Badge -->
      <rect x="20" y="20" width="36" height="36" rx="8" fill="#181D2E" stroke="#252D45" stroke-width="1"/>
      <circle cx="38" cy="38" r="8" stroke="#9E77ED" stroke-width="1.8" fill="none"/>
      <path d="M38 34 v4 l3 2" stroke="#9E77ED" stroke-width="1.8" fill="none" stroke-linecap="round"/>

      <text x="68" y="34" class="stat-label">ACTIVITY</text>
      <text x="68" y="47" font-family="system-ui" font-size="10" fill="#4E5870">CONTRIBUTION RATE</text>
      <text x="20" y="88" class="stat-value" font-size="24" fill="#9E77ED">100% LIVE</text>

      <!-- Progress Track & Fill -->
      <rect x="20" y="100" width="220" height="6" rx="3" fill="#141826"/>
      <rect class="bar-fill-3" x="20" y="100" width="0" height="6" rx="3" fill="url(#bar3-grad)"/>
    </g>

  </g>
</svg>"""

    return svg_content


def main():
    print(f"Fetching GitHub statistics for user: '{USERNAME}'...")
    public_repos, total_commits = fetch_github_stats()
    print(f"Fetched -> Public Repositories: {public_repos}, Total Commits: {total_commits}")

    svg_code = generate_svg(public_repos, total_commits)

    # Validate SVG XML formatting
    try:
        ET.fromstring(svg_code)
        print("SVG XML structure successfully validated!")
    except ET.ParseError as pe:
        print(f"Error: Generated SVG contains invalid XML! ({pe})", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    # Write file
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(svg_code)

    print(f"Successfully saved generated SVG to '{OUTPUT_PATH}'!")


if __name__ == "__main__":
    main()
