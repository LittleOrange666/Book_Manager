import json
import os
import time

import requests
import tqdm


def main():
    book_path = input("Enter the path to the existing book directory: ").strip()
    codes_path = input("Enter the path to the existing directory that contains codes.json: ").strip()
    admin_key = input("Enter the admin key (leave blank if none): ").strip()
    with open(f"{codes_path}/codes.json", encoding="utf-8") as f:
        codes = json.load(f)
    with open(f"{book_path}/names.json", encoding="utf-8") as f:
        names = json.load(f)
    out = []
    rev_code = {v: k for k, v in codes.items()}
    for dirname, title in names.items():
        path = f"{book_path}/{dirname}"
        if not os.path.exists(path) or not os.path.isdir(path):
            print(f"Directory {dirname} does not exist, skipping.")
            continue
        source = ""
        uid = dirname
        if title in rev_code:
            source = rev_code[title]
            uid = "book_"+source.split("/")[-2]
        data = {
            "admin_key": admin_key,
            "title": title,
            "uid": uid,
            "dirname": dirname,
            "source": source
        }
        out.append(data)
    print(f"Loaded {len(out)} books to migrate.")
    url = f"http://localhost:5000/api/book"
    session = requests.Session()
    for data in tqdm.tqdm(out):
        resp = session.put(url, data=data)
        if resp.status_code != 200:
            print(f"Failed to migrate {data['title']} - {data['uid']}: {resp.text}")
        else:
            print(f"Successfully migrated {data['title']} - {data['uid']}")
        time.sleep(0.1)


if __name__ == "__main__":
    main()
