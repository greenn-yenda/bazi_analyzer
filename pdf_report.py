# -*- coding: utf-8 -*-
"""
八字命盤 PDF 報告產生器
使用 reportlab + Noto Sans CJK TC 繁體字型
"""
import io
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# 註冊繁體中文字型（Noto Sans CJK TC）
FONT_REG = "NotoTC"
FONT_BOLD = "NotoTCBold"
try:
    pdfmetrics.registerFont(TTFont(FONT_REG,
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", subfontIndex=1))
    pdfmetrics.registerFont(TTFont(FONT_BOLD,
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc", subfontIndex=1))
except Exception:
    # 後備：內建 CID 字型
    pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
    FONT_REG = FONT_BOLD = "STSong-Light"

# 顏色主題
INK = colors.HexColor("#1a1a2e")
ACCENT = colors.HexColor("#7c3aed")      # 紫
ACCENT2 = colors.HexColor("#0ea5e9")     # 藍
GOLD = colors.HexColor("#b8860b")
LIGHT = colors.HexColor("#f4f4f8")
GREY = colors.HexColor("#6b7280")

WX_COLOR = {
    "木": colors.HexColor("#16a34a"),
    "火": colors.HexColor("#dc2626"),
    "土": colors.HexColor("#b45309"),
    "金": colors.HexColor("#ca8a04"),
    "水": colors.HexColor("#0891b2"),
}


def _styles():
    ss = getSampleStyleSheet()
    ss.add(ParagraphStyle("TitleTC", fontName=FONT_BOLD, fontSize=22,
                          textColor=INK, leading=28, spaceAfter=4))
    ss.add(ParagraphStyle("SubTC", fontName=FONT_REG, fontSize=11,
                          textColor=GREY, leading=16, spaceAfter=2))
    ss.add(ParagraphStyle("H2TC", fontName=FONT_BOLD, fontSize=14,
                          textColor=ACCENT, leading=20, spaceBefore=14, spaceAfter=6))
    ss.add(ParagraphStyle("BodyTC", fontName=FONT_REG, fontSize=10.5,
                          textColor=INK, leading=16))
    ss.add(ParagraphStyle("SmallTC", fontName=FONT_REG, fontSize=8.5,
                          textColor=GREY, leading=12))
    ss.add(ParagraphStyle("CellTC", fontName=FONT_REG, fontSize=9.5,
                          textColor=INK, leading=13))
    ss.add(ParagraphStyle("NoteTC", fontName=FONT_REG, fontSize=9,
                          textColor=INK, leading=13))
    return ss


def build_pdf(analysis: dict, topic_result: dict = None) -> bytes:
    """吃 bazi.full_analysis() 的 dict，回傳 PDF bytes"""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=18*mm, bottomMargin=16*mm,
                            leftMargin=16*mm, rightMargin=16*mm)
    ss = _styles()
    story = []

    inp = analysis["input"]
    hour_txt = f"{inp['hour']}時" if inp["hour"] is not None else "時辰未知"

    # ---- 標題 ----
    story.append(Paragraph("八字命盤分析報告", ss["TitleTC"]))
    story.append(Paragraph(
        f"出生：西元 {inp['year']} 年 {inp['month']} 月 {inp['day']} 日 · {hour_txt}",
        ss["SubTC"]))
    dm = analysis["day_master"]
    dmwx = analysis["day_master_wx"]
    strong = "身強" if analysis["strength"]["is_strong"] else "身弱"
    story.append(Paragraph(
        f"日主：{dm}（{dmwx}）· {strong}", ss["SubTC"]))
    story.append(Spacer(1, 4))
    story.append(HRFlowable(width="100%", thickness=1.2, color=ACCENT))
    story.append(Spacer(1, 8))

    # ---- 四柱表 ----
    story.append(Paragraph("一、四柱命盤", ss["H2TC"]))
    pil = analysis["pillars"]
    header = [Paragraph(f"<b>{p[0]}</b>", ss["CellTC"]) for p in pil]
    gan_row = []
    zhi_row = []
    for name, g, z in pil:
        gcolor = WX_COLOR.get(_gan_wx(g), INK)
        zcolor = WX_COLOR.get(_zhi_wx(z), INK)
        gan_row.append(Paragraph(
            f'<font size=18 color="{gcolor.hexval()}"><b>{g}</b></font>', ss["CellTC"]))
        zhi_row.append(Paragraph(
            f'<font size=18 color="{zcolor.hexval()}"><b>{z}</b></font>', ss["CellTC"]))
    # 十神列
    tg = {t["pillar"]: t for t in analysis["ten_gods"]}
    god_row = []
    for name, g, z in pil:
        gg = tg[name]["gan_god"]
        god_row.append(Paragraph(gg, ss["SmallTC"]))

    data = [header, god_row, gan_row, zhi_row]
    col_w = (doc.width) / len(pil)
    t = Table(data, colWidths=[col_w]*len(pil))
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LINEBELOW", (0, 0), (-1, 0), 0.5, colors.HexColor("#d1d5db")),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
    ]))
    story.append(t)
    story.append(Spacer(1, 6))

    # ---- 五行分布 + 喜忌 ----
    story.append(Paragraph("二、五行分布與喜用神", ss["H2TC"]))
    wx = analysis["wuxing_count"]
    yj = analysis["yong_ji"]
    # 五行 bar
    maxv = max(wx.values()) or 1
    bar_rows = []
    for k in ["木", "火", "土", "金", "水"]:
        v = wx[k]
        barlen = int((v / maxv) * 100)
        bar = Paragraph(
            f'<font color="{WX_COLOR[k].hexval()}">{"█"*max(1,barlen//8)}</font> {v}',
            ss["CellTC"])
        label = Paragraph(
            f'<font color="{WX_COLOR[k].hexval()}"><b>{k}</b></font>', ss["CellTC"])
        bar_rows.append([label, bar])
    wt = Table(bar_rows, colWidths=[20*mm, doc.width-20*mm])
    wt.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    story.append(wt)
    story.append(Spacer(1, 6))

    yong_str = "、".join(yj["yong"])
    ji_str = "、".join(yj["ji"])
    story.append(Paragraph(
        f'<b>喜用神：</b><font color="{ACCENT2.hexval()}"><b>{yong_str}</b></font>'
        f'　　<b>忌神：</b><font color="{colors.HexColor("#dc2626").hexval()}">{ji_str}</font>',
        ss["BodyTC"]))
    st = analysis["strength"]
    explain = (f'日主 {dm}（{dmwx}）幫身力量佔 {int(st["ratio"]*100)}%，'
               f'{"月令得氣，" if st["deling"] else "月令不得氣，"}'
               f'判定為「{strong}」。'
               f'{"身強者，喜洩剋耗（食傷、財、官殺）。" if st["is_strong"] else "身弱者，喜幫扶（比劫、印星），需金水相生。"}')
    story.append(Paragraph(explain, ss["NoteTC"]))
    story.append(Spacer(1, 10))

    # ---- 白話解讀 ----
    try:
        from glossary import plain_reading
        reading = plain_reading(analysis)
        story.append(Paragraph("● 白話解讀", ss["H2TC"]))
        for p in reading:
            is_note = p.startswith("＊")
            st_name = "SmallTC" if is_note else "BodyTC"
            para = Paragraph(p, ss[st_name])
            # 用淡框包起來
            box = Table([[para]], colWidths=[doc.width])
            box.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#faf9fc")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e2f0")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 7),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                ("LINEBEFORE", (0, 0), (0, -1), 2.5,
                 GOLD if is_note else ACCENT),
            ]))
            story.append(box)
            story.append(Spacer(1, 5))
        story.append(Spacer(1, 4))
    except Exception:
        pass

    # ---- 大運 ----
    story.append(Paragraph("三、大運排列", ss["H2TC"]))
    dy = analysis["da_yun"]
    dir_txt = "順排" if dy["forward"] else "逆排"
    story.append(Paragraph(f"（{dir_txt}，起運約 {dy['list'][0]['age']} 歲；實務起運以節氣為準，此為約略值）",
                           ss["SmallTC"]))
    dydata = [[Paragraph("<b>大運</b>", ss["CellTC"]),
               Paragraph("<b>干支</b>", ss["CellTC"]),
               Paragraph("<b>十神</b>", ss["CellTC"]),
               Paragraph("<b>五行</b>", ss["CellTC"]),
               Paragraph("<b>起始年齡</b>", ss["CellTC"]),
               Paragraph("<b>西元</b>", ss["CellTC"])]]
    for i, d in enumerate(dy["list"], 1):
        dydata.append([
            Paragraph(f"第{i}運", ss["CellTC"]),
            Paragraph(f'{d["gan"]}{d["zhi"]}', ss["CellTC"]),
            Paragraph(d["gan_god"], ss["CellTC"]),
            Paragraph(d["wuxing"], ss["CellTC"]),
            Paragraph(f'{d["age"]}歲', ss["CellTC"]),
            Paragraph(f'{d["year"]}', ss["CellTC"]),
        ])
    dyt = Table(dydata, colWidths=[doc.width*w for w in (.16,.16,.18,.16,.18,.16)])
    dyt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
    ]))
    story.append(dyt)
    story.append(Spacer(1, 6))

    # ---- 流年逐年表 ----
    ln = analysis["liu_nian"]
    y0, y1 = ln[0]["year"], ln[-1]["year"]
    story.append(Paragraph(f"四、流年逐年分析（{y0}–{y1}）", ss["H2TC"]))
    story.append(Paragraph("🔴重 · 🟡注意 · 🟢順 · ✅喜用 · 平＝平穩", ss["SmallTC"]))
    lndata = [[Paragraph("<b>西元</b>", ss["CellTC"]),
               Paragraph("<b>干支</b>", ss["CellTC"]),
               Paragraph("<b>年齡</b>", ss["CellTC"]),
               Paragraph("<b>評級</b>", ss["CellTC"]),
               Paragraph("<b>重點</b>", ss["CellTC"])]]
    for r in ln:
        lndata.append([
            Paragraph(str(r["year"]), ss["CellTC"]),
            Paragraph(r["ganzhi"], ss["CellTC"]),
            Paragraph(f'{r["age"]}歲', ss["CellTC"]),
            Paragraph(r["level"], ss["CellTC"]),
            Paragraph(r["notes"], ss["CellTC"]),
        ])
    lnt = Table(lndata, colWidths=[doc.width*w for w in (.13,.12,.11,.18,.46)])
    lnt.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
        ("ALIGN", (0, 0), (-2, -1), "CENTER"),
        ("ALIGN", (-1, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#d1d5db")),
        ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
    ]))
    story.append(lnt)
    story.append(Spacer(1, 10))

    # ---- 主題針對性分析 ----
    if topic_result and topic_result.get("found") is not None:
        tr = topic_result
        story.append(Paragraph(f"五、針對性分析：{tr['icon']} {tr['label']}", ss["H2TC"]))
        story.append(Paragraph(tr["desc"], ss["SmallTC"]))
        story.append(Spacer(1, 4))
        story.append(Paragraph(tr["summary"], ss["BodyTC"]))
        story.append(Spacer(1, 6))
        if tr.get("year_events"):
            tedata = [[Paragraph("<b>西元</b>", ss["CellTC"]),
                       Paragraph("<b>年齡</b>", ss["CellTC"]),
                       Paragraph("<b>吉凶</b>", ss["CellTC"]),
                       Paragraph("<b>可能發生的事</b>", ss["CellTC"])]]
            for e in tr["year_events"]:
                tedata.append([
                    Paragraph(str(e["year"]), ss["CellTC"]),
                    Paragraph(f'{e["age"]}歲', ss["CellTC"]),
                    Paragraph(e["level"], ss["CellTC"]),
                    Paragraph(e.get("plain", ""), ss["CellTC"]),
                ])
            tet = Table(tedata, colWidths=[doc.width*w for w in (.14,.12,.20,.54)])
            tet.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT),
                ("ALIGN", (0, 0), (-2, -1), "CENTER"),
                ("ALIGN", (-1, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("BOX", (0, 0), (-1, -1), 0.8, colors.HexColor("#d1d5db")),
                ("INNERGRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#e5e7eb")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fafafa")]),
            ]))
            story.append(tet)
        story.append(Spacer(1, 10))

    # ---- 頁尾聲明 ----
    story.append(HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#d1d5db")))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        "本報告由自製八字排盤程式自動產生，命理為傳統文化框架，僅供參考與自我省思，"
        "人生的選擇與努力才是根本。程式作者：顏宏達。",
        ss["SmallTC"]))

    doc.build(story)
    return buf.getvalue()


# 小工具：五行查詢（避免 import 循環）
_GAN_WX = {"甲":"木","乙":"木","丙":"火","丁":"火","戊":"土","己":"土","庚":"金","辛":"金","壬":"水","癸":"水"}
_ZHI_WX = {"子":"水","丑":"土","寅":"木","卯":"木","辰":"土","巳":"火","午":"火","未":"土","申":"金","酉":"金","戌":"土","亥":"水"}
def _gan_wx(g): return _GAN_WX.get(g, "")
def _zhi_wx(z): return _ZHI_WX.get(z, "")


if __name__ == "__main__":
    from bazi import BaziChart
    c = BaziChart(1991, 10, 20, 12)
    a = c.full_analysis(2025, 2035)
    pdf = build_pdf(a)
    with open("test_report.pdf", "wb") as f:
        f.write(pdf)
    print("PDF 產生成功，大小:", len(pdf), "bytes")
