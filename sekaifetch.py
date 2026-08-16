import json
import urllib.request
import urllib.parse
import re
import sys
import os


NAME_ALIASES = {
    #n25
    "kanade": "Yoisaki_Kanade",
    "mafuyu": "Asahina_Mafuyu",
    "ena": "Shinonome_Ena",
    "mizuki": "Akiyama_Mizuki",
    #l/n
    "ichika": "Hoshino_Ichika",
    "saki": "Tenma_Saki",
    "honami": "Mochizuki_Honami",
    "shiho": "Hoshino_Shiho",
    #mmj
    "shizuku": "Hinomori_Shizuku",
    "minori": "Hanasato_Minori",
    "haruka": "Kiritani_Haruka",
    "airi": "Momoi_Airi",
    #vbs
    "an": "Shiraishi_An",
    "kohane": "Azusawa_Kohane",
    "akito": "Shinonome_Akito",
    "toya": "Aoyagi_Toya",
    #wxs
    "tsukasa": "Tenma_Tsukasa",
    "rui": "Kamishiro_Rui",
    "emu": "Otori_Emu",
    "nene": "Kusanagi_Nene",
}

def clean_wiki_syntax(text):
    text = re.sub(r'\{\{[^|}]+\|([^}]+)\}\}', r'\1', text)
    text = re.sub(r'\[\[(?:[^|]*\|)?([^\]]+)\]\]', r'\1', text)
    text = text.replace("<br>", ", ").replace("\n", " ")
    return re.sub(r'\s+', ' ', text).strip()

def extract_group_name(logo_text):
    match = re.search(r'link=([^\]|]+)', logo_text)
    if match:
        return match.group(1).strip()
    return clean_wiki_syntax(logo_text)

def hex_to_ansi(hex_str):
    hex_str = hex_str.strip().lstrip('#')
    if len(hex_str) != 6:
        return ""
    try:
        r = int(hex_str[0:2], 16)
        g = int(hex_str[2:4], 16)
        b = int(hex_str[4:6], 16)
        return f"\x1b[38;2;{r};{g};{b}m"
    except ValueError:
        return ""

def fetch_and_parse():
    if len(sys.argv) < 2:
        print("Usage: sekaifetch <full name/first name>")
        print("Example: sekaifetch kanade")
        print("Example: sekaifetch \"Yoisaki Kanade\"")
        return

    user_input = " ".join(sys.argv[1:]).strip()
    normalized_input = user_input.lower().replace(" ", "_")

    if normalized_input in NAME_ALIASES:
        page_title = NAME_ALIASES[normalized_input]
    else:
        page_title = "_".join(sys.argv[1:])

    ascii_filename = f"{page_title.lower()}.txt"

    subdomain = "projectsekai"
    url = f"https://{subdomain}.fandom.com/api.php"

    params = {
        "action": "query",
        "prop": "revisions",
        "titles": page_title,
        "rvslots": "*",
        "rvprop": "content",
        "format": "json"
    }

    full_url = f"{url}?{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": "SekaiFetch/1.0 (https://github.com/ivo9990/sekaifetch)"}

    try:
        req = urllib.request.Request(full_url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

        pages = data["query"]["pages"]
        page_id = list(pages.keys())[0]

        if page_id == "-1":
            print(f"error: page '{page_title.replace('_', ' ')}' could not be found.")
            return

        raw_wiki_content = pages[page_id]["revisions"][0]["slots"]["main"]["*"]
        page_name = pages[page_id]["title"]

        template_match = re.search(r'\{\{CharacterTemplate\s*\n(.*?)\n\}\}', raw_wiki_content, re.DOTALL)

        if template_match:
            template_body = template_match.group(1)
            rows = re.split(r'\n\|(?=\s*[a-zA-Z0-9_ ]+=)', "\n|" + template_body)

            info = {}
            for row in rows:
                if "=" in row:
                    key, val = row.split("=", 1)
                    info[key.replace("|", "").strip().lower()] = val.strip()

            char_hex = info.get("color", "")
            color_ansi = hex_to_ansi(char_hex)
            reset_ansi = "\x1b[0m" if color_ansi else ""

            group_logo_raw = info.get("grouplogo", "")
            group_name = extract_group_name(group_logo_raw) if group_logo_raw else clean_wiki_syntax(info.get("group", "Unknown"))

            school_raw = info.get("school2", info.get("school", ""))

            # mizuki patch
            school_clean = school_raw.split("|")[0].strip()

            height = info.get("height2", info.get("height", ""))

            dislikes_list = []
            if info.get("dislikes"):
                dislikes_list.append(info.get("dislikes"))
            if info.get("dislikes_food"):
                dislikes_list.append(info.get("dislikes_food"))
            combined_dislikes = ", ".join(dislikes_list)

            raw_text_lines = [
                f"{color_ansi}Name{reset_ansi}: {page_name}",
                f"{color_ansi}Group{reset_ansi}: {group_name}",
                f"{color_ansi}Gender{reset_ansi}: {clean_wiki_syntax(info.get('gender', ''))}",
                f"{color_ansi}Birthday{reset_ansi}: {clean_wiki_syntax(info.get('birthday', ''))}",
                f"{color_ansi}School{reset_ansi}: {clean_wiki_syntax(school_clean)}",
                f"{color_ansi}Dislikes{reset_ansi}: {clean_wiki_syntax(combined_dislikes)}",
                f"{color_ansi}Hobbies{reset_ansi}: {clean_wiki_syntax(info.get('hobbies', ''))}",
                f"{color_ansi}Height{reset_ansi}: {clean_wiki_syntax(height)}",
                f"{color_ansi}Talents{reset_ansi}: {clean_wiki_syntax(info.get('talents', ''))}",
                f"{color_ansi}Favorite food{reset_ansi}: {clean_wiki_syntax(info.get('likes_food', ''))}"
            ]

            if hasattr(sys, '_MEIPASS'):
                art_path = os.path.join(sys._MEIPASS, "ascii", ascii_filename)
            else:
                art_path = os.path.join("ascii", ascii_filename)

            ascii_lines = []
            if os.path.exists(art_path):
                with open(art_path, "r", encoding="utf-8") as f:
                    ascii_lines = [line.rstrip('\n') for line in f.readlines()]
            else:
                print(f"[oops: no ascii found at '{os.path.join('ascii', ascii_filename)}']\n")


            total_ascii_height = len(ascii_lines)
            total_text_height = len(raw_text_lines)
            max_lines = max(total_ascii_height, total_text_height)

            text_lines = []
            if total_ascii_height > total_text_height:
                top_padding = (total_ascii_height - total_text_height) // 2 - 2
                text_lines = [""] * top_padding + raw_text_lines
            else:
                text_lines = raw_text_lines


            ascii_width = 50

            print("")
            for i in range(max_lines):
                left_side = ascii_lines[i] if i < len(ascii_lines) else ""
                right_side = text_lines[i] if i < len(text_lines) else ""

                if left_side:
                    print(f"{left_side}\t{right_side}")
                elif right_side:
                    print(f"{' ' * ascii_width}\t{right_side}")
            print("")

        else:
            print("could not find the 'CharacterTemplate' layout block on wiki page.")

    except Exception as e:
        print(f"oops: {e}")

if __name__ == "__main__":
    fetch_and_parse()
