import json, os, sys, urllib.parse, datetime

src, out = sys.argv[1], sys.argv[2]

# Torah order; joined parashot sit right after their second part.
ORDER = ("בראשית|נח|לך-לך|וירא|חיי שרה|תולדות|ויצא|וישלח|וישב|מקץ|ויגש|ויחי|"
         "שמות|וארא|בא|בשלח|יתרו|משפטים|תרומה|תצוה|כי תשא|ויקהל|פקודי|ויקהל-פקודי|"
         "ויקרא|צו|שמיני|תזריע|מצרע|תזריע-מצרע|אחרי מות|קדשים|אחרי מות-קדשים|אמור|בהר|בחקתי|בהר-בחקתי|"
         "במדבר|נשא|בהעלתך|שלח-לך|קורח|חקת|בלק|חקת-בלק|פינחס|מטות|מסעי|מטות-מסעי|"
         "דברים|ואתחנן|עקב|ראה|שופטים|כי-תצא|כי-תבוא|נצבים|וילך|נצבים-וילך|האזינו|וזאת הברכה").split("|")

def load(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)

def files(d):
    return {urllib.parse.unquote(os.path.splitext(n)[0]): os.path.join(d, n) for n in os.listdir(d)}

P, H = files(os.path.join(src, "parashot")), files(os.path.join(src, "haftarot"))
assert set(P) == set(ORDER), (set(P) ^ set(ORDER))
assert set(H) <= set(ORDER), set(H) - set(ORDER)

os.makedirs(os.path.join(out, "p"), exist_ok=True)
os.makedirs(os.path.join(out, "h"), exist_ok=True)

def dump(obj, path):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, separators=(",", ":"))

# parasha: [aliya][pasuk] = [perek, pasuk, textWithTeamim, targum, [[dibur, perush]...], isMaftir(0/1)]
for i, name in enumerate(ORDER):
    al = load(P[name])
    if len(al) != 7: print("note: %d aliyot in #%d" % (len(al), i))
    dump([[[p["Perek"], p["Id"], p["TextTeamim"].strip(), (p["Targum"] or "").strip(),
            [[r["Name"] or "", r["Value"] or ""] for r in (p["Rashi"] or [])], 1 if p.get("IsMaftir") else 0]
           for p in a["Psukim"]] for a in al], os.path.join(out, "p", "%d.json" % i))

# haftara: [[book, [[perek, [[pasuk, text, before, after]...]]...]]...]
for name, path in H.items():
    h = load(path)
    dump([[b["Name"], [[pr["Name"], [[q["Name"], q["Text"].strip(), q.get("MessageBefore") or "", q.get("MessageAfter") or ""]
                                     for q in pr["Psukim"]]] for pr in b["Prakim"]]] for b in h["Books"]],
         os.path.join(out, "h", "%d.json" % ORDER.index(name)))

# calendar: Shabbat dates as days since 1970-01-01 -> parasha index (haftara == parasha in the source data)
cal = {"names": ORDER, "haft": sorted(ORDER.index(n) for n in H)}
for key, fn in (("il", "HebCal-Israel.json"), ("ch", "HebCal-NonIsrael.json")):
    rows = []
    for e in load(os.path.join(src, fn)):
        assert e["Haftara"] == e["Name"]
        d = datetime.date.fromisoformat(e["Date"][:10])
        rows.append([(d - datetime.date(1970, 1, 1)).days, ORDER.index(e["Name"])])
    rows.sort()
    cal[key] = rows
dump(cal, os.path.join(out, "cal.json"))
print("ok", len(ORDER), "parashot,", len(H), "haftarot,", len(cal["il"]), len(cal["ch"]), "weeks")
