from __future__ import annotations

import html
import json
import os
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen


USERNAME = os.environ.get("GITHUB_USERNAME", "Abhi190702")
ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "assets"
API_ROOT = "https://api.github.com"

LANGUAGE_COLORS = {
    "TypeScript": "#3178c6",
    "Rust": "#dea584",
    "JavaScript": "#f1e05a",
    "Python": "#3572A5",
    "CSS": "#563d7c",
    "HTML": "#e34c26",
    "Shell": "#89e051",
    "PowerShell": "#012456",
    "C++": "#f34b7d",
    "C": "#555555",
    "Java": "#b07219",
    "Dockerfile": "#384d54",
    "SCSS": "#c6538c",
}


def api_get(path_or_url: str) -> object:
    url = path_or_url if path_or_url.startswith("https://") else f"{API_ROOT}{path_or_url}"
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "Abhi190702-profile-assets",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = Request(url, headers=headers)
    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API request failed for {url}: {exc.code} {message}") from exc


def fetch_repos() -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        chunk = api_get(f"/users/{USERNAME}/repos?per_page=100&type=owner&sort=updated&page={page}")
        if not isinstance(chunk, list) or not chunk:
            return repos
        repos.extend(chunk)
        page += 1


def escape(value: object) -> str:
    return html.escape(str(value), quote=True)


def summary_svg(user: dict, repos: list[dict], own_repos: list[dict]) -> str:
    followers = int(user.get("followers") or 0)
    public_repos = int(user.get("public_repos") or len(own_repos))
    own_projects = len(own_repos)
    stars = sum(int(repo.get("stargazers_count") or 0) for repo in repos)

    cards = [
        ("Public repos", public_repos, "#58a6ff"),
        ("Own projects", own_projects, "#8bf5cf"),
        ("Stars", stars, "#ffcc66"),
        ("Followers", followers, "#d2a8ff"),
    ]

    blocks = []
    for index, (label, value, color) in enumerate(cards):
        x = 24 + index * 113
        width = 108 if index == 3 else 96
        blocks.append(
            f'''    <g transform="translate({x} 92)">
      <rect width="{width}" height="54" rx="10" fill="#161b22" stroke="#30363d"/>
      <text x="14" y="22" fill="{color}" font-size="22" font-weight="800">{escape(value)}</text>
      <text x="14" y="41" fill="#c9d1d9" font-size="12">{escape(label)}</text>
    </g>'''
        )

    return f'''<svg width="495" height="170" viewBox="0 0 495 170" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">GitHub activity summary for Abhijeet Ranjan</title>
  <desc id="desc">Automatically refreshed public profile summary card showing repositories, projects, stars, and followers.</desc>
  <defs>
    <linearGradient id="accent" x1="24" y1="0" x2="471" y2="0" gradientUnits="userSpaceOnUse">
      <stop stop-color="#00f5ff"/>
      <stop offset="0.52" stop-color="#8a2be2"/>
      <stop offset="1" stop-color="#ff6b35"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="493" height="168" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
  <rect x="24" y="22" width="447" height="4" rx="2" fill="url(#accent)"/>
  <text x="24" y="49" fill="#f0f6fc" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="700">GitHub Signal</text>
  <text x="24" y="70" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="12">Public profile snapshot, refreshed from GitHub</text>
  <g font-family="Segoe UI, Arial, sans-serif">
{chr(10).join(blocks)}
  </g>
</svg>
'''


def top_languages_svg(own_repos: list[dict]) -> str:
    totals: dict[str, int] = {}
    for repo in own_repos:
        languages_url = repo.get("languages_url")
        if not languages_url:
            continue
        languages = api_get(str(languages_url))
        if not isinstance(languages, dict):
            continue
        for language, size in languages.items():
            totals[language] = totals.get(language, 0) + int(size or 0)

    total_bytes = sum(totals.values())
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    top = ranked[:4]
    other_value = sum(value for _, value in ranked[4:])
    if other_value:
        top.append(("Other", other_value))

    if not total_bytes:
        top = [("No language data", 1)]
        total_bytes = 1

    bar_x = 24
    bar_y = 80
    bar_width = 447
    segments = []
    used_width = 0
    for index, (language, value) in enumerate(top):
        if index == len(top) - 1:
            width = bar_width - used_width
        else:
            width = max(1, round(bar_width * value / total_bytes))
        color = "#8b949e" if language == "Other" else LANGUAGE_COLORS.get(language, "#8b949e")
        segments.append(
            f'<rect x="{bar_x + used_width}" y="{bar_y}" width="{width}" height="14" fill="{color}"/>'
        )
        used_width += width

    legend = []
    for index, (language, value) in enumerate(top):
        x = 24 if index < 3 else 250
        y = 117 + (index if index < 3 else index - 3) * 22
        color = "#8b949e" if language == "Other" else LANGUAGE_COLORS.get(language, "#8b949e")
        percent = value / total_bytes * 100
        legend.append(
            f'''    <circle cx="{x + 6}" cy="{y}" r="5" fill="{color}"/>
    <text x="{x + 18}" y="{y + 4}" fill="#c9d1d9">{escape(language)} {percent:.1f}%</text>'''
        )

    return f'''<svg width="495" height="170" viewBox="0 0 495 170" fill="none" xmlns="http://www.w3.org/2000/svg" role="img" aria-labelledby="title desc">
  <title id="title">Top languages across Abhijeet Ranjan's own public repositories</title>
  <desc id="desc">Automatically refreshed language card built from own non-fork public repositories.</desc>
  <defs>
    <linearGradient id="glow" x1="24" y1="0" x2="471" y2="0" gradientUnits="userSpaceOnUse">
      <stop stop-color="#3178c6"/>
      <stop offset="0.55" stop-color="#00c7b7"/>
      <stop offset="1" stop-color="#f1e05a"/>
    </linearGradient>
  </defs>
  <rect x="1" y="1" width="493" height="168" rx="14" fill="#0d1117" stroke="#30363d" stroke-width="2"/>
  <text x="24" y="38" fill="#f0f6fc" font-family="Segoe UI, Arial, sans-serif" font-size="20" font-weight="700">Language Footprint</text>
  <text x="24" y="59" fill="#8b949e" font-family="Segoe UI, Arial, sans-serif" font-size="12">Own non-fork public repositories</text>
  <rect x="24" y="80" width="447" height="14" rx="7" fill="#161b22"/>
  <g clip-path="url(#barClip)">
    {chr(10).join(segments)}
  </g>
  <defs>
    <clipPath id="barClip"><rect x="24" y="80" width="447" height="14" rx="7"/></clipPath>
  </defs>
  <g font-family="Segoe UI, Arial, sans-serif" font-size="12">
{chr(10).join(legend)}
  </g>
</svg>
'''


def main() -> None:
    user = api_get(f"/users/{USERNAME}")
    repos = fetch_repos()
    own_repos = [repo for repo in repos if not repo.get("fork")]

    ASSETS.mkdir(exist_ok=True)
    (ASSETS / "github-summary.svg").write_text(summary_svg(user, repos, own_repos), encoding="utf-8")
    (ASSETS / "top-languages.svg").write_text(top_languages_svg(own_repos), encoding="utf-8")


if __name__ == "__main__":
    main()
