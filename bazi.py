# -*- coding: utf-8 -*-
"""
八字排盤與分析核心引擎
- 排四柱（年月日時）
- 判斷日主強弱
- 推喜用神 / 忌神
- 排大運與流年
作者：顏宏達
"""
import sxtwl

# ---------- 基礎資料 ----------
GAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
ZHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

GAN_WUXING = {
    "甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土",
    "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水",
}
ZHI_WUXING = {
    "子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火",
    "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水",
}

# 陰陽
GAN_YINYANG = {
    "甲": "陽", "乙": "陰", "丙": "陽", "丁": "陰", "戊": "陽",
    "己": "陰", "庚": "陽", "辛": "陰", "壬": "陽", "癸": "陰",
}

# 地支藏干（主氣、中氣、餘氣）
ZHI_CANGGAN = {
    "子": ["癸"], "丑": ["己", "癸", "辛"], "寅": ["甲", "丙", "戊"],
    "卯": ["乙"], "辰": ["戊", "乙", "癸"], "巳": ["丙", "庚", "戊"],
    "午": ["丁", "己"], "未": ["己", "丁", "乙"], "申": ["庚", "壬", "戊"],
    "酉": ["辛"], "戌": ["戊", "辛", "丁"], "亥": ["壬", "甲"],
}

# 五行生剋
SHENG = {"木": "火", "火": "土", "土": "金", "金": "水", "水": "木"}  # 我生
KE = {"木": "土", "土": "水", "水": "火", "火": "金", "金": "木"}      # 我剋

# 十神計算：以日主為我
def ten_god(day_gan, other_gan):
    """回傳 other_gan 對 day_gan 的十神"""
    me = GAN_WUXING[day_gan]
    other = GAN_WUXING[other_gan]
    same_yy = GAN_YINYANG[day_gan] == GAN_YINYANG[other_gan]
    if me == other:
        return "比肩" if same_yy else "劫財"
    if SHENG[me] == other:  # 我生者
        return "食神" if same_yy else "傷官"
    if KE[me] == other:  # 我剋者
        return "偏財" if same_yy else "正財"
    if KE[other] == me:  # 剋我者
        return "七殺" if same_yy else "正官"
    if SHENG[other] == me:  # 生我者
        return "偏印" if same_yy else "正印"
    return "?"


# ---------- 天干五合 / 地支六沖六合 ----------
GAN_HE = {("甲", "己"), ("乙", "庚"), ("丙", "辛"), ("丁", "壬"), ("戊", "癸")}
ZHI_CHONG = {("子", "午"), ("丑", "未"), ("寅", "申"), ("卯", "酉"), ("辰", "戌"), ("巳", "亥")}
ZHI_HE = {("子", "丑"), ("寅", "亥"), ("卯", "戌"), ("辰", "酉"), ("巳", "申"), ("午", "未")}


def _pair_in(a, b, s):
    return (a, b) in s or (b, a) in s


class BaziChart:
    def __init__(self, year, month, day, hour=None):
        self.year = year
        self.month = month
        self.day = day
        self.hour = hour  # 0-23，可為 None（不知時辰）
        self._build()

    def _build(self):
        d = sxtwl.fromSolar(self.year, self.month, self.day)
        y = d.getYearGZ()
        m = d.getMonthGZ()
        day_gz = d.getDayGZ()

        self.year_gan, self.year_zhi = GAN[y.tg], ZHI[y.dz]
        self.month_gan, self.month_zhi = GAN[m.tg], ZHI[m.dz]
        self.day_gan, self.day_zhi = GAN[day_gz.tg], ZHI[day_gz.dz]

        if self.hour is not None:
            h = d.getHourGZ(self.hour)
            self.hour_gan, self.hour_zhi = GAN[h.tg], ZHI[h.dz]
        else:
            self.hour_gan, self.hour_zhi = None, None

        self.day_master = self.day_gan  # 日主

    # ---- 四柱列表 ----
    def pillars(self):
        p = [
            ("年柱", self.year_gan, self.year_zhi),
            ("月柱", self.month_gan, self.month_zhi),
            ("日柱", self.day_gan, self.day_zhi),
        ]
        if self.hour_gan:
            p.append(("時柱", self.hour_gan, self.hour_zhi))
        return p

    # ---- 五行統計 ----
    def wuxing_count(self):
        cnt = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        gans = [self.year_gan, self.month_gan, self.day_gan]
        zhis = [self.year_zhi, self.month_zhi, self.day_zhi]
        if self.hour_gan:
            gans.append(self.hour_gan)
            zhis.append(self.hour_zhi)
        for g in gans:
            cnt[GAN_WUXING[g]] += 1
        for z in zhis:
            # 地支主氣
            cnt[ZHI_WUXING[z]] += 1
            # 藏干（中餘氣各算半個力量，簡化為 +0.5）
            for i, cg in enumerate(ZHI_CANGGAN[z][1:], start=1):
                cnt[GAN_WUXING[cg]] += 0.5
        return {k: round(v, 1) for k, v in cnt.items()}

    # ---- 日主強弱判斷（簡化演算法） ----
    def strength(self):
        me = GAN_WUXING[self.day_master]
        cnt = self.wuxing_count()
        # 幫我 = 同類(比劫) + 生我(印)
        sheng_me = [k for k, v in SHENG.items() if v == me][0]  # 生我的五行
        help_score = cnt[me] + cnt[sheng_me]
        total = sum(cnt.values())
        ratio = help_score / total if total else 0

        # 月令加權：若月支五行幫我，額外加分
        month_wx = ZHI_WUXING[self.month_zhi]
        deling = month_wx == me or month_wx == sheng_me

        strong = ratio >= 0.5 or (ratio >= 0.42 and deling)
        return {
            "is_strong": strong,
            "ratio": round(ratio, 2),
            "help_score": round(help_score, 1),
            "total": round(total, 1),
            "deling": deling,
            "me": me,
            "sheng_me": sheng_me,
        }

    # ---- 喜用神 / 忌神 ----
    def yong_ji(self):
        s = self.strength()
        me = s["me"]
        sheng_me = s["sheng_me"]          # 生我（印）
        wo_sheng = SHENG[me]              # 我生（食傷）
        wo_ke = KE[me]                    # 我剋（財）
        ke_me = [k for k, v in KE.items() if v == me][0]  # 剋我（官殺）

        if s["is_strong"]:
            # 身強：喜洩、剋、耗 → 食傷、財、官殺
            yong = [wo_sheng, wo_ke, ke_me]
            ji = [me, sheng_me]
        else:
            # 身弱：喜幫、生 → 比劫、印
            yong = [me, sheng_me]
            ji = [wo_sheng, wo_ke, ke_me]
        # 去重保序
        yong = list(dict.fromkeys(yong))
        ji = list(dict.fromkeys(ji))
        return {"yong": yong, "ji": ji}

    # ---- 十神表 ----
    def ten_gods(self):
        res = []
        for name, g, z in self.pillars():
            tg = ten_god(self.day_master, g) if g != self.day_master else "日主"
            # 地支主氣十神
            main_cg = ZHI_CANGGAN[z][0]
            zg = ten_god(self.day_master, main_cg)
            res.append({"pillar": name, "gan": g, "gan_god": tg, "zhi": z, "zhi_god": zg})
        return res

    # ---- 大運排列 ----
    def da_yun(self, count=6):
        """
        簡化版大運：以月柱為基準，陽年男/陰年女順排，陰年男/陽年女逆排。
        這裡預設「男命」，起運歲數簡化為固定 8 歲起（實務應算節氣，這裡標註為約略）。
        """
        # 判斷順逆：以年干陰陽 + 性別（此工具預設男命）
        year_yy = GAN_YINYANG[self.year_gan]
        forward = (year_yy == "陽")  # 陽年男順排

        mg_idx = GAN.index(self.month_gan)
        mz_idx = ZHI.index(self.month_zhi)

        start_age = 8  # 簡化起運（實務需依節氣計算）
        luck = []
        for i in range(1, count + 1):
            if forward:
                g = GAN[(mg_idx + i) % 10]
                z = ZHI[(mz_idx + i) % 12]
            else:
                g = GAN[(mg_idx - i) % 10]
                z = ZHI[(mz_idx - i) % 12]
            age0 = start_age + (i - 1) * 10
            year0 = self.year + age0
            luck.append({
                "gan": g, "zhi": z,
                "gan_god": ten_god(self.day_master, g),
                "age": age0,
                "year": year0,
                "wuxing": GAN_WUXING[g] + ZHI_WUXING[z],
            })
        return {"forward": forward, "list": luck}

    # ---- 流年分析（判斷沖合） ----
    def liu_nian(self, from_year, to_year):
        yong_ji = self.yong_ji()
        yong = set(yong_ji["yong"])
        rows = []
        for yr in range(from_year, to_year + 1):
            g_idx = (yr - 4) % 10
            z_idx = (yr - 4) % 12
            g, z = GAN[g_idx], ZHI[z_idx]

            notes = []
            level = "平"  # 平穩

            # 天干與日主：沖(剋)或合
            if _pair_in(g, self.day_gan, GAN_HE):
                notes.append(f"{g}與日主{self.day_gan}相合")
            # 地支對四柱地支的沖
            chong_targets = []
            for pname, pz in [("年", self.year_zhi), ("月", self.month_zhi),
                              ("日", self.day_zhi)] + ([("時", self.hour_zhi)] if self.hour_zhi else []):
                if _pair_in(z, pz, ZHI_CHONG):
                    chong_targets.append(f"{z}沖{pname}支{pz}")
                elif _pair_in(z, pz, ZHI_HE):
                    notes.append(f"{z}合{pname}支{pz}")
            if chong_targets:
                notes.extend(chong_targets)

            # 五行對喜忌
            year_wx = {GAN_WUXING[g], ZHI_WUXING[z]}
            fav = bool(year_wx & yong)

            # 評級邏輯
            n_chong = len(chong_targets)
            has_he = any("合" in n for n in notes)
            if n_chong >= 2:
                level = "🔴 重"
            elif n_chong == 1:
                level = "🟡 注意"
            if has_he and n_chong == 0:
                level = "🟢 順"
            if fav and level == "平":
                level = "✅ 喜用"

            rows.append({
                "year": yr,
                "ganzhi": g + z,
                "age": yr - self.year,
                "level": level,
                "fav": fav,
                "notes": "、".join(notes) if notes else "平穩",
            })
        return rows

    # ---- 產出完整分析 dict ----
    def full_analysis(self, ln_from=None, ln_to=None):
        s = self.strength()
        yj = self.yong_ji()
        if ln_from is None:
            ln_from = self.year + 30
        if ln_to is None:
            ln_to = ln_from + 10
        return {
            "input": {"year": self.year, "month": self.month, "day": self.day,
                      "hour": self.hour},
            "pillars": self.pillars(),
            "day_master": self.day_master,
            "day_master_wx": GAN_WUXING[self.day_master],
            "wuxing_count": self.wuxing_count(),
            "strength": s,
            "yong_ji": yj,
            "ten_gods": self.ten_gods(),
            "da_yun": self.da_yun(),
            "liu_nian": self.liu_nian(ln_from, ln_to),
        }


if __name__ == "__main__":
    # 測試：用你的八字 1991-10-20 午時(12)
    c = BaziChart(1991, 10, 20, 12)
    import json
    a = c.full_analysis(2025, 2035)
    print("四柱:", a["pillars"])
    print("日主:", a["day_master"], a["day_master_wx"])
    print("五行:", a["wuxing_count"])
    print("強弱:", a["strength"])
    print("喜忌:", a["yong_ji"])
    print("大運順逆:", a["da_yun"]["forward"])
    for ln in a["liu_nian"][:5]:
        print(ln)
