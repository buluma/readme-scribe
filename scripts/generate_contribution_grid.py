#!/usr/bin/env python3
"""Render GitHub's contribution calendar as a numbered SVG (standard library only)."""
import argparse
import calendar
import datetime
import html
import json
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request

QUERY = """query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar {
        totalContributions
        weeks { contributionDays { date weekday contributionCount contributionLevel } }
      }
    }
  }
}"""
COLORS = dict(zip(
    ['NONE', 'FIRST_QUARTILE', 'SECOND_QUARTILE', 'THIRD_QUARTILE', 'FOURTH_QUARTILE'],
    ['#161b22', '#0e4429', '#006d32', '#26a641', '#39d353']))


def fetch_calendar(login, token):
    request = urllib.request.Request(
        'https://api.github.com/graphql',
        data=json.dumps({'query': QUERY, 'variables': {'login': login}}).encode(),
        headers={'Authorization': f'Bearer {token}', 'Content-Type': 'application/json',
                 'User-Agent': 'readme-scribe-contribution-grid'})
    with urllib.request.urlopen(request, timeout=30) as response:
        return json.load(response)


def render(data, login):
    if data.get('errors'):
        raise ValueError('; '.join(error['message'] for error in data['errors']))
    user = data['data']['user']
    if user is None:
        raise ValueError(f'GitHub user {login!r} was not found')
    grid = user['contributionsCollection']['contributionCalendar']
    weeks = grid['weeks']
    # Grow cells for unusually large counts instead of clipping their labels.
    digits = max((len(str(d['contributionCount'])) for w in weeks for d in w['contributionDays']), default=1)
    cell = max(36, digits * 10 + 8)
    pitch, left, top = cell + 7, 62, 106
    width, height = left + len(weeks) * pitch + 20, top + 7 * pitch + 62
    escape = html.escape
    title = f"{login}: {grid['totalContributions']:,} contributions in the last year"
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" width="{width}" height="{height}" role="img" aria-labelledby="title desc">',
             f'<title id="title">{escape(title)}</title>',
             '<desc id="desc">Daily GitHub contributions. Brighter green indicates more contributions; each cell shows the daily count.</desc>',
             f'<rect width="{width}" height="{height}" rx="7" fill="#0d1117"/>',
             f'<path d="M7 3 H{width-7}" stroke="#39d353" stroke-width="3"/>',
             '<g font-family="Arial, sans-serif" font-size="14" fill="#919ba5">',
             '<circle cx="37" cy="38" r="5" fill="#39d353"/>',
             '<text x="50" y="44" fill="#58a6ff" font-size="18" font-weight="bold">Contributions</text>',
             f'<path d="M27 77 H{width-27}" stroke="#21262d"/>']
    previous_month = None
    for column, week in enumerate(weeks):
        days = week['contributionDays']
        if not days:
            continue
        date = datetime.date.fromisoformat(days[0]['date'])
        month = (date.year, date.month)
        x = left + column * pitch
        if month != previous_month:
            parts.append(f'<text x="{x}" y="94">{calendar.month_abbr[date.month]}</text>')
            previous_month = month
        for day in days:
            y = top + day['weekday'] * pitch
            count = day['contributionCount']
            color = COLORS[day['contributionLevel']]
            ink = '#0d1117' if day['contributionLevel'] in ('THIRD_QUARTILE', 'FOURTH_QUARTILE') else '#e6edf3'
            if count == 0:
                ink = '#59616b'
            parts.extend([f'<g><title>{escape(day["date"])}: {count} contributions</title>',
                          f'<rect x="{x}" y="{y}" width="{cell}" height="{cell}" rx="4" fill="{color}"/>',
                          f'<text x="{x+cell/2}" y="{y+cell/2}" text-anchor="middle" dominant-baseline="central" font-family="monospace" font-size="18" font-weight="bold" fill="{ink}">{count}</text></g>'])
    for row, label in [(1, 'Mon'), (3, 'Wed'), (5, 'Fri')]:
        parts.append(f'<text x="21" y="{top+row*pitch+cell/2}" dominant-baseline="central">{label}</text>')
    y = top + 7 * pitch + 16
    parts.append(f'<text x="62" y="{y+22}">Less</text>')
    for index, color in enumerate(COLORS.values()):
        parts.append(f'<rect x="{108+index*39}" y="{y}" width="33" height="33" rx="4" fill="{color}"/>')
    parts.extend([f'<text x="311" y="{y+22}">More</text>', '</g></svg>'])
    return '\n'.join(parts) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--user', default=os.environ.get('GITHUB_USER'))
    parser.add_argument('--input', type=Path, help='Read a saved GraphQL response instead of calling GitHub')
    parser.add_argument('--output', type=Path, default=Path('dist/contributions.svg'))
    args = parser.parse_args()
    if not args.user:
        parser.error('set GITHUB_USER or pass --user')
    token = os.environ.get('GH_TOKEN')
    if not args.input and not token:
        parser.error('set GH_TOKEN to query GitHub')
    try:
        data = json.loads(args.input.read_text()) if args.input else fetch_calendar(args.user, token)
        svg = render(data, args.user)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(svg)
    except (ValueError, KeyError, OSError, urllib.error.URLError) as error:
        print(f'Contribution grid generation failed: {error}', file=sys.stderr)
        return 1
    print(f'Generated {args.output}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
