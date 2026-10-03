"""One-off catalogue cleanup (Problem 10): real shop names, and the 3 placeholder products.

The original names were generated from file names ("Benjamin Franklin 1 4 Zip",
"Champion Reverse Weave Hoodie 1", "Ua Mens Tech L S 2 0"), and three products had a
placeholder description ("...Vision blocked; filename-based stub.") with no colors.

    ../.venv/bin/python fix_catalogue.py           preview every change
    ../.venv/bin/python fix_catalogue.py --apply   write them

Safe to re-run: names are always rebuilt from the ORIGINAL names, which are saved to
data/catalogue_original_names.json the first time. product_id never changes, so cards,
images, inventory and saved chats keep working.
"""

import json
import re
import sqlite3
import sys
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"
DB = DATA / "campus_customs.db"
ORIGINALS = DATA / "catalogue_original_names.json"

# Names the rules can't get right on their own.
NAME_OVERRIDES = {
    "2025-yale-vs-harvard-t-shirt": "2025 Yale vs. Harvard Game Tee",
    "basic-hoodie-big-yale": "Big Yale Basic Hoodie",
    "brooks-brothers-bomber-jacket-yale": "Brooks Brothers Yale Bomber Jacket",
    "brooks-brothers-double-knit-full-zip-hoodie-yale": "Brooks Brothers Yale Double-Knit Full-Zip Hoodie",
    "champion-full-zip-hood": "Champion Yale Full-Zip Hoodie",
    "champion-mens-triumph-raglan-crew": "Champion Men's Triumph Raglan Crewneck",
    "champion-reverse-weave-crewneck": "Champion Reverse Weave Crewneck",
    "champion-reverse-weave-hoodie-1": "Champion Reverse Weave Hoodie",
    "district-tri-blend-t-shirt-vintage-shield": "Vintage Shield Tri-Blend Tee",
    "district-vit-crewneck-vintage-bulldog": "Vintage Bulldog Crewneck",
    "district-vit-crewneck-vintage-standing-bulldog": "Vintage Standing Bulldog Crewneck",
    "district-vit-hoodie-vintage-bulldog": "Vintage Bulldog Hoodie",
    "district-vit-hoodie-vintage-sailor-bulldog": "Vintage Sailor Bulldog Hoodie",
    "dry-zone-long-sleeve": "Yale Bulldogs Dry Zone Long-Sleeve Tee",
    "hype-and-vice-yale-university-offside-crewneck": "Hype and Vice Yale Offside Crewneck",
    "hype-and-vice-yale-university-premium-crewneck": "Hype and Vice Yale Premium Crewneck",
    "poly-twill-crewneck-arched-yale": "Arched Yale Twill Crewneck",
    "squash-left-chest-tennis": "Squash Left-Chest Crewneck",
    "super-heavyweight-crewneck-arched-yale-crest": "Super Heavyweight Arched Yale Crewneck",
    "t-felt-y-heavyweight": "Felt Y Heavyweight Tee",
    "ua-gameday-double-knit-hood": "Under Armour Gameday Double-Knit Hoodie",
    "ua-mens-tech-l-s-2-0": "Under Armour Men's Tech 2.0 Long-Sleeve Tee",
    "yale-bowl-t-shirt": "Yale Bowl Ringer Tee",
    "yale-maplehouse-diana-mockneck": "MapleHouse Diana Bulldogs Mockneck",
}

# The 3 placeholder products, filled in from their photos.
RECORD_FIXES = {
    "benjamin-franklin-t-shirt": {
        "garment_type": "short-sleeve T-shirt",
        "description": "Heather gray short-sleeve tee with a large red-and-blue Benjamin Franklin College shield "
        "and the college name printed below it.",
        "colors": ["heather gray", "red", "navy blue"],
        "search_tags": ["Yale", "Benjamin Franklin College", "residential college", "college crest", "shield",
                        "gray T-shirt", "short sleeve", "Campus Customs"],
    },
    "berkeley-sweater-fleece-jacket": {
        "garment_type": "full-zip fleece jacket",
        "description": "Light heather gray sweater-fleece jacket with a full zip, stand-up collar, charcoal trim "
        "and a small red Berkeley College crest on the left chest.",
        "colors": ["light heather gray", "charcoal gray", "red"],
        "search_tags": ["Yale", "Berkeley College", "residential college", "fleece jacket", "full zip",
                        "sweater fleece", "left chest crest", "gray jacket", "Campus Customs"],
    },
    "timothy-dwight-college-crewneck": {
        "garment_type": "crewneck sweatshirt",
        "description": "Heather gray crewneck sweatshirt with ribbed cuffs and hem and a small red Timothy Dwight "
        "College crest on the left chest.",
        "colors": ["heather gray", "red", "white"],
        "search_tags": ["Yale", "Timothy Dwight College", "TD", "residential college", "crewneck", "sweatshirt",
                        "left chest crest", "gray sweatshirt", "Campus Customs"],
    },
}


def clean_name(product_id: str, name: str) -> str:
    if product_id in NAME_OVERRIDES:
        return NAME_OVERRIDES[product_id]
    n = f" {name} "
    n = n.replace(" 1 4 Zip ", " Quarter-Zip ")
    n = re.sub(r"^ Yale Sports (Hoodie|Crewneck|Creqneck|T Shirt) (.+) $", lambda m: f" Yale {m[2]} Sports {m[1]} ", n)
    n = re.sub(r"^ Tri Blend Sports (.+) T Shirt $", r" Yale \1 Tri-Blend Tee ", n)
    for a, b in [(" Tri Blend ", " Tri-Blend "), (" Creqneck ", " Crewneck "), (" T Shirt ", " Tee "), (" Left Chest ", " Left-Chest "),
                 (" Track Field ", " Track & Field "), (" Track And Field ", " Track & Field "),
                 (" Of ", " of "), (" And ", " and ")]:
        n = n.replace(a, b)
    return n.strip()


def main() -> None:
    apply = "--apply" in sys.argv
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT product_id, name FROM catalogue ORDER BY product_id").fetchall()
    if ORIGINALS.exists():
        originals = json.loads(ORIGINALS.read_text())
    else:
        originals = dict(rows)
        if apply:
            ORIGINALS.write_text(json.dumps(originals, indent=2))

    changes = 0
    for pid, current in rows:
        new = clean_name(pid, originals[pid])
        if new != current:
            changes += 1
            print(f"{originals[pid]:<52} -> {new}")
            if apply:
                conn.execute("UPDATE catalogue SET name = ? WHERE product_id = ?", (new, pid))
    for pid, fix in RECORD_FIXES.items():
        print(f"[record] {pid}: description/colors/tags/garment_type filled in")
        if apply:
            conn.execute(
                "UPDATE catalogue SET garment_type = ?, description = ?, colors = ?, search_tags = ? WHERE product_id = ?",
                (fix["garment_type"], fix["description"], json.dumps(fix["colors"]), json.dumps(fix["search_tags"]), pid),
            )
    if apply:
        conn.commit()
    print(f"\n{changes} names {'updated' if apply else 'would change'}; {len(RECORD_FIXES)} records "
          f"{'fixed' if apply else 'would be fixed'}.")


if __name__ == "__main__":
    main()
