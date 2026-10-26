#!/usr/bin/env python3
"""Rebuild the Apps section of README.md from the public App Store listing (no keys needed).

Runs in GitHub Actions every day. Picks up new apps, new versions, release notes and ratings automatically.
Everything between <!-- APPS:START --> and <!-- APPS:END --> is regenerated; the rest of README.md is left alone.
"""
import datetime, html, json, re, urllib.request

DEVELOPER_ID = 6782245881  # "Peyton Greenwood" on the App Store
START, END = "<!-- APPS:START -->", "<!-- APPS:END -->"


def fetch():
    url = f"https://itunes.apple.com/lookup?id={DEVELOPER_ID}&entity=software&country=us&limit=200"
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    return [x for x in data.get("results", []) if x.get("wrapperType") == "software"]


def first_paragraph(text, limit=240):
    """First real sentence block: skips headings (all caps, ending in ? or :, or very short lines)."""
    lines = [l.strip(" •-\t") for l in (text or "").replace("\r", "").split("\n")]
    keep = [l for l in lines if len(l) >= 25 and not l.isupper() and not l.endswith(("?", ":"))]
    text = re.sub(r"\s+", " ", " · ".join(keep)).strip()
    return text if len(text) <= limit else text[:limit].rsplit(" ", 1)[0] + "…"


def esc(t):
    return html.escape(t, quote=False)


def stars(app):
    r, n = app.get("averageUserRating"), app.get("userRatingCount") or 0
    return f"★ {r:.1f} ({n} ratings)" if r and n else "New"


def section(apps):
    apps.sort(key=lambda a: a.get("releaseDate", ""), reverse=True)
    out = [START, "", f"## My apps on the App Store ({len(apps)})", ""]
    for a in apps:
        url = a["trackViewUrl"].split("?")[0]
        updated = (a.get("currentVersionReleaseDate") or a.get("releaseDate") or "")[:10]
        notes = first_paragraph(a.get("releaseNotes"), 160)
        out += [
            "<table><tr>",
            f'<td width="96" valign="top"><a href="{url}"><img src="{a["artworkUrl512"]}" width="80" alt="{html.escape(a["trackName"])} icon"></a></td>',
            "<td valign=\"top\">",
            f'<b><a href="{url}">{esc(a["trackName"])}</a></b> · {esc(a.get("primaryGenreName", ""))} · {stars(a)}<br>',
            f"{esc(first_paragraph(a.get('description')))}<br>",
            f"<sub>Version {esc(a.get('version', ''))}, updated {updated}"
            + (f" · What's new: {esc(notes)}" if notes else "") + "</sub>",
            "</td></tr></table>",
            "",
        ]
    out += [f"<sub>App list refreshes automatically from the App Store · last checked {datetime.date.today():%B %Y}</sub>",
            "", END]
    return "\n".join(out)


def main():
    apps = fetch()
    if not apps:
        raise SystemExit("App Store lookup returned no apps; leaving README unchanged")
    readme = open("README.md").read()
    new = section(apps)
    readme = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda m: new, readme, flags=re.S) \
        if START in readme else readme.rstrip() + "\n\n" + new + "\n"
    open("README.md", "w").write(readme)
    print(f"{len(apps)} apps written")


if __name__ == "__main__":
    main()
