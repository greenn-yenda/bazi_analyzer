# -*- coding: utf-8 -*-
"""
主題針對性分析
使用者選「想問什麼」（母親/父親/事業/感情/財運/健康/學業/子女），
程式找出對應的「十神」，分析該十神在四柱的狀態，
並掃描流年中對它的沖／合，回報哪幾年要注意。
這就是「你的檔案會分析出母親星」背後的邏輯。
"""
from bazi import GAN_WUXING, ZHI_WUXING, ten_god, GAN, ZHI

# 天干五合、地支六沖六合
GAN_HE = {("甲","己"),("乙","庚"),("丙","辛"),("丁","壬"),("戊","癸")}
ZHI_CHONG = {("子","午"),("丑","未"),("寅","申"),("卯","酉"),("辰","戌"),("巳","亥")}
ZHI_HE = {("子","丑"),("寅","亥"),("卯","戌"),("辰","酉"),("巳","申"),("午","未")}

def _pin(a,b,s): return (a,b) in s or (b,a) in s

# ---------- 主題 → 對應十神 ----------
# 每個主題對應「哪些十神代表它」
TOPIC_MAP = {
    "career": {
        "label": "事業工作", "icon": "💼",
        "gods": ["正官", "七殺"],
        "desc": "官殺代表工作、事業、地位與壓力。",
        "plain_good": "工作上容易遇到升遷、被賦予重任、獲得肯定的機會。",
        "plain_bad": "工作壓力較大、責任變重，或有職務變動、與上司的磨合。",
    },
    "love": {
        "label": "感情姻緣", "icon": "❤️",
        "gods": ["正財", "偏財", "正官", "七殺"],
        "desc": "男命以財星為妻、女命以官殺為夫，看緣分的來去。",
        "plain_good": "感情容易有進展、桃花出現、關係升溫或穩定下來。",
        "plain_bad": "感情上有波折、聚少離多，或需要多花心思經營。",
    },
    "wealth": {
        "label": "財運金錢", "icon": "🪙",
        "gods": ["正財", "偏財"],
        "desc": "財星代表財富、正職與偏財收入。",
        "plain_good": "財路較順、有進帳機會、投資或副業有斬獲。",
        "plain_bad": "花費增加、財務需謹慎，或有意外支出、投資要保守。",
    },
    "mother": {
        "label": "母親長輩", "icon": "👩",
        "gods": ["正印", "偏印"],
        "desc": "印星代表母親、長輩與貴人庇護。",
        "plain_good": "與母親、長輩關係和順，或得到長輩、貴人的幫助。",
        "plain_bad": "母親或長輩相關的事務浮現，健康或關係上需多關心。",
    },
    "father": {
        "label": "父親", "icon": "👨",
        "gods": ["正財", "偏財"],
        "desc": "財星也代表父親。",
        "plain_good": "與父親關係和順，或父親方面有好消息。",
        "plain_bad": "父親相關事務浮現，健康或財務上需留意。",
    },
    "people": {
        "label": "人際人事", "icon": "🤝",
        "gods": ["比肩", "劫財"],
        "desc": "比劫代表兄弟、朋友、同事與競爭者。",
        "plain_good": "人緣好、有朋友相挺、合作順利、團隊氣氛佳。",
        "plain_bad": "人際上有競爭、意見不合，或合夥、金錢往來要小心。",
    },
    "helper": {
        "label": "貴人運", "icon": "🙏",
        "gods": ["正印", "偏印"],
        "desc": "印星代表貴人、提攜與庇護。",
        "plain_good": "容易遇到貴人相助、有人提攜、關鍵時刻有人幫忙。",
        "plain_bad": "貴人運較弱的時期，凡事多靠自己、主動求援。",
    },
    "talent": {
        "label": "才華表現", "icon": "🎨",
        "gods": ["食神", "傷官"],
        "desc": "食傷代表才華、創作、表達與子女。",
        "plain_good": "才華有發揮舞台、創意受肯定、表達力強、適合展現自己。",
        "plain_bad": "表現慾強但易衝動，言語上要收斂、避免鋒芒太露惹爭議。",
    },
    "health": {
        "label": "健康自身", "icon": "🧍",
        "gods": ["比肩", "劫財"],
        "desc": "比劫與日主代表自身、體力與精神狀態。",
        "plain_good": "精神體力較好、狀態穩定、行動力足。",
        "plain_bad": "自身狀態受衝擊，要注意健康、作息與情緒起伏。",
    },
    "study": {
        "label": "學業考試", "icon": "📚",
        "gods": ["正印", "偏印"],
        "desc": "印星代表學業、學識與文憑。",
        "plain_good": "讀書、考試、學習較順，適合進修、考證照。",
        "plain_bad": "學習上較容易分心或受阻，需更專注、有耐心。",
    },
}


def _find_god_positions(chart, target_gods):
    """在四柱中找出屬於 target_gods 的天干位置與其地支"""
    dm = chart.day_master
    positions = []
    pillars = [
        ("年", chart.year_gan, chart.year_zhi),
        ("月", chart.month_gan, chart.month_zhi),
        ("日", chart.day_gan, chart.day_zhi),
    ]
    if chart.hour_gan:
        pillars.append(("時", chart.hour_gan, chart.hour_zhi))
    for pname, g, z in pillars:
        if g == dm:
            god = "日主"
        else:
            god = ten_god(dm, g)
        if god in target_gods:
            positions.append({"pillar": pname, "gan": g, "zhi": z, "god": god})
    return positions


def analyze_topic(chart, topic_key, ln_from, ln_to):
    """
    針對某主題分析：
    1. 找出代表該主題的十神在命盤哪個位置
    2. 判斷該十神五行是喜用還是忌神
    3. 掃描流年，找出對這顆星「沖」或「合」的年份
    """
    topic = TOPIC_MAP.get(topic_key)
    if not topic:
        return None

    dm = chart.day_master
    positions = _find_god_positions(chart, topic["gods"])

    # 喜忌判斷
    yj = chart.yong_ji()
    yong = set(yj["yong"])

    result = {
        "topic_key": topic_key,
        "label": topic["label"],
        "icon": topic["icon"],
        "desc": topic["desc"],
        "found": len(positions) > 0,
        "positions": positions,
        "summary": "",
        "year_events": [],
    }

    # 若命盤中沒有這顆星（例如八字裡沒有官殺）
    if not positions:
        result["summary"] = (
            f"你的命盤裡沒有明顯的「{('、'.join(topic['gods']))}」透干"
            f"（代表{topic['label']}的星）。這在命理上代表這個面向的能量較隱性，"
            f"不一定是壞事，可能表示這方面較平淡、或需從地支藏干細看。"
        )
        return result

    # 有這顆星：分析它的狀態
    star_wx = [GAN_WUXING[p["gan"]] for p in positions]
    is_fav = any(w in yong for w in star_wx)
    pos_txt = "、".join(f"{p['pillar']}柱的{p['gan']}" for p in positions)

    if is_fav:
        fav_txt = f"這個面向對你整體是「助力」，只要好好把握，容易有好的發展。"
    else:
        fav_txt = f"這個面向對你來說要多花點心思經營，屬於需要用心的地方，但用心就有回報。"
    result["summary"] = (
        f"在你的命盤裡，代表「{topic['label']}」的能量落在 {pos_txt}。{fav_txt} "
        f"下面列出未來哪些年份，這個面向會特別有動靜——"
        f"「順利年」代表有好的機會或轉機，「變動年」代表容易有變化、要多留意。"
    )

    # 掃描流年，找對「這顆星的天干/地支」的沖合
    star_gans = [p["gan"] for p in positions]
    star_zhis = [p["zhi"] for p in positions]
    for yr in range(ln_from, ln_to + 1):
        g = GAN[(yr - 4) % 10]
        z = ZHI[(yr - 4) % 12]
        events = []
        # 流年天干合到星的天干
        for sg in star_gans:
            if _pin(g, sg, GAN_HE):
                events.append(f"流年{g}合星干{sg}")
        # 流年地支沖/合星所在的地支
        for sz in star_zhis:
            if _pin(z, sz, ZHI_CHONG):
                events.append(f"流年{z}沖星支{sz}")
            elif _pin(z, sz, ZHI_HE):
                events.append(f"流年{z}合星支{sz}")
        if events:
            kind = "沖" if any("沖" in e for e in events) else "合"
            plain = topic["plain_bad"] if kind == "沖" else topic["plain_good"]
            result["year_events"].append({
                "year": yr,
                "ganzhi": g + z,
                "age": yr - chart.year,
                "kind": kind,
                "level": "🔴 變動年" if kind == "沖" else "🟢 順利年",
                "detail": "、".join(events),
                "plain": plain,
            })

    if not result["year_events"]:
        result["summary"] += f"（在 {ln_from}–{ln_to} 這段期間，沒有直接沖合到這顆星，相對平穩。）"

    return result


# 給前端用的主題清單
def topic_choices():
    return [{"key": k, "label": v["label"], "icon": v["icon"]}
            for k, v in TOPIC_MAP.items()]


if __name__ == "__main__":
    from bazi import BaziChart
    c = BaziChart(1991, 10, 20, 12)
    print("=== 測試：問母親 ===")
    r = analyze_topic(c, "mother", 2010, 2035)
    print("找到星:", r["positions"])
    print("摘要:", r["summary"])
    print("流年事件:")
    for e in r["year_events"]:
        print(f"  {e['year']} {e['ganzhi']} {e['level']} - {e['detail']}")
