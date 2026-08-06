import json, urllib.parse

ILLEGAL = set('$#[]/.')  # characters Firebase forbids

def find_invalid(obj, path="root"):
    problems = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == "" or any(ch in ILLEGAL for ch in k):
                problems.append((path, k))
            problems.extend(find_invalid(v, path + "." + repr(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            problems.extend(find_invalid(v, f"{path}[{i}]"))
    return problems

def sanitize(obj):
    if isinstance(obj, dict):
        new = {}
        for k, v in obj.items():
            if k == "":
                nk = "_empty_"
            elif any(ch in ILLEGAL for ch in k):
                # simple replacement; use urllib.parse.quote_plus(k, safe='') to encode instead
                nk = "".join('_' if ch in ILLEGAL else ch for ch in k)
            else:
                nk = k
            new[nk] = sanitize(v)
        return new
    elif isinstance(obj, list):
        return [sanitize(x) for x in obj]
    else:
        return obj

# Configuration constants (no CLI args)
FILEPATH = r"C:\Users\vchikkay\Downloads\Millennium World School Hassan Dec 2025 (3).json"
FIX = True       # set True to write a sanitized copy
ENCODE = True    # set True to percent-encode offending keys when fixing

if __name__ == "__main__":
    filepath = FILEPATH
    data = json.load(open(filepath, "r", encoding="utf-8"))
    problems = find_invalid(data)
    if problems:
        print("Found invalid keys (path, key):")
        for pr in problems[:200]:
            print(pr)
        print(f"Total invalid entries: {len(problems)}")
    else:
        print("No invalid keys found.")

    if FIX:
        def sanitize_choice(obj):
            if isinstance(obj, dict):
                new = {}
                for k, v in obj.items():
                    if k == "":
                        nk = "_empty_"
                    elif any(ch in ILLEGAL for ch in k):
                        if ENCODE:
                            nk = urllib.parse.quote(k, safe='')
                        else:
                            nk = "".join('_' if ch in ILLEGAL else ch for ch in k)
                    else:
                        nk = k
                    new[nk] = sanitize_choice(v)
                return new
            elif isinstance(obj, list):
                return [sanitize_choice(x) for x in obj]
            else:
                return obj
        fixed = sanitize_choice(data)
        out = filepath + ".fixed.json"
        json.dump(fixed, open(out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
        print("Wrote sanitized copy to", out)