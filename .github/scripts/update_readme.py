"""Rewrite the 'Recently Updated' table in README.md from the GitHub API."""
import json
import os
import re
import urllib.request

OWNER = os.environ.get("GITHUB_OWNER", "AmalkiFernando")
LIMIT = int(os.environ.get("REPO_LIMIT", "6"))
EXCLUDE = {OWNER.lower()} | {
    name.strip().lower() for name in os.environ.get("EXCLUDE_REPOS", "").split(",") if name.strip()
}
README = "README.md"
START, END = "<!-- RECENT-REPOS:START -->", "<!-- RECENT-REPOS:END -->"


def fetch_repos():
    url = f"https://api.github.com/users/{OWNER}/repos?per_page=100&sort=pushed"
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "readme-updater"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(url, headers=headers)) as resp:
        return json.load(resp)


def cell(text):
    return (text or "—").replace("|", "\\|").replace("\n", " ").strip()


def build_table(repos):
    repos = [r for r in repos if not r["archived"] and r["name"].lower() not in EXCLUDE]
    repos.sort(key=lambda r: r["pushed_at"], reverse=True)
    rows = ["| Repository | Description | Language | Last updated |", "| --- | --- | --- | --- |"]
    for r in repos[:LIMIT]:
        rows.append(
            f"| [**{r['name']}**]({r['html_url']}) | {cell(r['description'])} "
            f"| {cell(r['language'])} | {r['pushed_at'][:10]} |"
        )
    return "\n".join(rows)


def main():
    with open(README, encoding="utf-8", newline="") as f:
        content = f.read()
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
    if not pattern.search(content):
        raise SystemExit(f"Markers {START} / {END} not found in {README}")
    block = f"{START}\n{build_table(fetch_repos())}\n{END}"
    updated = pattern.sub(lambda _: block, content)
    if updated != content:
        with open(README, "w", encoding="utf-8", newline="") as f:
            f.write(updated)
        print("README.md updated")
    else:
        print("README.md already up to date")


if __name__ == "__main__":
    main()
