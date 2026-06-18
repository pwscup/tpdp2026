import argparse
import html
import json
import os
import re
import sys
import urllib.request


EXPECTED_HEADERS = [
    "No",
    "文献タイトル",
    "発表元/掲載先",
    "Issue",
    "文献の状態",
    "コードの状態",
    "優先度",
    "分類",
    "ステータス",
    "詳細調査結果",
]


def fetch_issue_body(repo: str, issue_number: int, token: str) -> str:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/issues/{issue_number}",
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return payload["body"]


def split_markdown_row(line: str) -> list[str]:
    line = line.strip()
    if not line.startswith("|") or not line.endswith("|"):
        raise ValueError(f"Not a markdown table row: {line}")
    return [cell.strip() for cell in line.strip("|").split("|")]


def parse_issue_table(body: str) -> list[dict[str, str]]:
    lines = body.splitlines()
    rows: list[dict[str, str]] = []
    headers: list[str] | None = None

    for index, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        cells = split_markdown_row(line)
        if cells == EXPECTED_HEADERS:
            headers = cells
            continue
        if headers and re.match(r"^\|\s*-", line):
            continue
        if headers and cells and re.fullmatch(r"\d+", cells[0]):
            if len(cells) != len(headers):
                raise ValueError(
                    f"Unexpected column count at table row {index + 1}: "
                    f"expected {len(headers)}, got {len(cells)}"
                )
            rows.append(dict(zip(headers, cells)))

    if headers is None:
        raise ValueError("Issue table header was not found")
    if len(rows) != 29:
        raise ValueError(f"Expected 29 table rows, got {len(rows)}")
    return rows


def markdown_links_to_html(value: str) -> str:
    value = value.strip()
    if value in {"", "未作成"}:
        return '<span class="pending">未作成</span>'

    def replace_link(match: re.Match[str]) -> str:
        label = html.escape(match.group(1), quote=False)
        href = html.escape(match.group(2), quote=True)
        return f'<a href="{href}">{label}</a>'

    converted = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", replace_link, value)
    if converted != value:
        return converted
    if re.fullmatch(r"https?://\S+", value):
        href = html.escape(value, quote=True)
        text = html.escape(value, quote=False)
        return f'<a href="{href}">{text}</a>'
    return html.escape(value, quote=False)


def priority_html(value: str) -> str:
    escaped = html.escape(value, quote=False)
    if value == "高":
        return f'<span class="tag high">{escaped}</span>'
    return f'<span class="tag">{escaped}</span>'


def row_to_html(row: dict[str, str]) -> str:
    cells = [
        html.escape(row["No"], quote=False),
        html.escape(row["文献タイトル"], quote=False),
        html.escape(row["発表元/掲載先"], quote=False),
        markdown_links_to_html(row["Issue"]),
        html.escape(row["文献の状態"], quote=False),
        html.escape(row["コードの状態"], quote=False),
        priority_html(row["優先度"]),
        html.escape(row["分類"], quote=False),
        html.escape(row["ステータス"], quote=False),
        markdown_links_to_html(row["詳細調査結果"]),
    ]
    inner = "".join(f"<td>{cell}</td>" for cell in cells)
    return f"            <tr>{inner}</tr>"


def replace_tbody(index_html: str, rows: list[dict[str, str]]) -> str:
    table_pattern = re.compile(
        r'(<table id="papers-table">.*?<tbody>\n)(.*?)(\n\s*</tbody>)',
        re.DOTALL,
    )
    tbody = "\n".join(row_to_html(row) for row in rows)
    updated, count = table_pattern.subn(rf"\1{tbody}\3", index_html, count=1)
    if count != 1:
        raise ValueError("Could not locate papers-table tbody in site/index.html")
    return updated


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", default=os.environ.get("GITHUB_REPOSITORY", "pwscup/tpdp2026"))
    parser.add_argument("--issue", type=int, default=30)
    parser.add_argument("--index", default="site/index.html")
    args = parser.parse_args()

    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise ValueError("GH_TOKEN or GITHUB_TOKEN is required")

    body = fetch_issue_body(args.repo, args.issue, token)
    rows = parse_issue_table(body)

    with open(args.index, "r", encoding="utf-8") as handle:
        index_html = handle.read()
    updated = replace_tbody(index_html, rows)
    with open(args.index, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(updated)

    print(f"Synced {len(rows)} rows from issue #{args.issue}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
