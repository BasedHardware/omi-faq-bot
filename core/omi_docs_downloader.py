import os
import re
import json
import requests
import hashlib
import frontmatter
from pathlib import Path


def _file_hash(path: str) -> str:
    with open(path, "rb") as f:
        return hashlib.sha1(f.read()).hexdigest()


def clean_mdx_text(raw: str) -> str:
    """Clean .mdx into structured plain text suitable for embeddings."""
    if raw.strip().startswith("---"):
        try:
            raw = frontmatter.loads(raw).content
        except Exception:
            raw = re.sub(r"^---.*?---", "", raw, flags=re.S)

    raw = re.sub(r"```[\s\S]*?```", "", raw)
    raw = re.sub(r"`([^`]*)`", r"\1", raw)
    raw = re.sub(
        r"<Accordion(?: title=\"([^\"]*)\")?>([\s\S]*?)<\/Accordion>",
        r"\nAccordion: \1\n\2\n",
        raw,
    )
    raw = re.sub(
        r"<Card(?: title=\"([^\"]*)\")?>([\s\S]*?)<\/Card>", r"\nCard: \1\n\2\n", raw
    )
    raw = re.sub(r"<[^>]+>", "", raw)
    raw = re.sub(r"\[([^\]]+)\]\((https?[^)]+)\)", r"\1 (\2)", raw)
    raw = re.sub(r"<(https?[^>]+)>", r"\1", raw)
    raw = re.sub(r"!\[([^\]]*)\]\([^)]+\)", r"Image: \1", raw)
    raw = re.sub(r"^#{1,6}\s*(.*)", r"\n\n\1:\n", raw, flags=re.M)
    raw = re.sub(r"^\s*[-*+]\s+", "• ", raw, flags=re.M)
    raw = re.sub(r"^\s*\d+\.\s+", "• ", raw, flags=re.M)
    raw = re.sub(
        r"^\|.*\|\n\|[-| :]*\|\n((?:\|.*\|\n?)*)",
        lambda m: "\n".join(
            [
                f"Row: {' '.join(row.strip().split('|')[1:-1])}"
                for row in m.group(1).strip().split("\n")
            ]
        )
        + "\n",
        raw,
        flags=re.M,
    )
    raw = re.sub(r"[*_#>]+", "", raw)
    raw = re.sub(r"\n{2,}", "\n\n", raw)
    raw = re.sub(r"\s{2,}", " ", raw)
    return raw.strip()


def _clean_all_docs(
    in_dir: str = "data/omi_docs", out_file: str = "data/clean_docs.json"
):
    in_path = Path(in_dir)
    if not in_path.exists():
        raise FileNotFoundError(f"{in_dir} not found.")

    all_docs = []
    for path in in_path.glob("*.mdx"):
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        clean = clean_mdx_text(raw)
        if not clean.strip():
            print(f"⚠️ Skipping empty file: {path.name}")
            continue

        all_docs.append({"filename": path.name, "clean_text": clean})
        print(f"✅ Cleaned {path.name} ({len(clean)} chars)")

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_docs, f, indent=2, ensure_ascii=False)

    print(f"\n🧾 Saved {len(all_docs)} cleaned docs → {out_file}")


def download_omi_docs(
    api_url: str = "https://api.github.com/repos/BasedHardware/omi/git/trees/main?recursive=1",
    raw_base_url: str = "https://raw.githubusercontent.com/BasedHardware/omi/main/",
    output_dir: str = "data/omi_docs",
    force_update: bool = False,
):
    """
    Download or update all .mdx docs from OMI (docs/doc and docs/onboarding),
    auto-renaming duplicates using their folder path.
    """
    os.makedirs(output_dir, exist_ok=True)
    response = requests.get(api_url)
    response.raise_for_status()
    tree = response.json().get("tree", [])

    updated, skipped = 0, 0

    for item in tree:
        if not (
            (
                item["path"].startswith("docs/doc/")
                or item["path"].startswith("docs/onboarding/")
            )
            and item["path"].endswith(".mdx")
        ):
            continue

        url = raw_base_url + item["path"]

        # 🔹 Generate safe unique filename with path context
        rel_path = item["path"].replace("docs/", "").replace("/", "__")
        filename = os.path.join(output_dir, rel_path)

        r = requests.get(url)
        r.raise_for_status()
        new_data = r.text

        if os.path.exists(filename) and not force_update:
            old_hash = _file_hash(filename)
            new_hash = hashlib.sha1(new_data.encode("utf-8")).hexdigest()
            if old_hash == new_hash:
                skipped += 1
                continue

        with open(filename, "w", encoding="utf-8") as f:
            f.write(new_data)
        updated += 1

    print(f"📥 Docs update complete: {updated} updated, {skipped} skipped.")

    # 🧹 Clean all docs into JSON after update
    _clean_all_docs(output_dir)
