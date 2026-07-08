# -*- coding: utf-8 -*-
"""
八字命盤網頁 App
填生辰 → 線上排盤 → 下載 PDF
作者：顏宏達
"""
from flask import Flask, render_template, request, send_file, jsonify
import io
from bazi import BaziChart
from pdf_report import build_pdf
from glossary import GLOSSARY, plain_reading
from topic import analyze_topic, topic_choices

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/analyze", methods=["POST"])
def analyze():
    """回傳排盤結果 JSON（給網頁即時顯示）"""
    try:
        data = request.get_json()
        year = int(data["year"])
        month = int(data["month"])
        day = int(data["day"])
        hour = data.get("hour")
        hour = int(hour) if hour not in (None, "", "unknown") else None

        ln_from = int(data.get("ln_from") or year + 33)
        ln_to = int(data.get("ln_to") or ln_from + 10)

        c = BaziChart(year, month, day, hour)
        a = c.full_analysis(ln_from, ln_to)
        a["reading"] = plain_reading(a)
        a["glossary"] = GLOSSARY
        a["topic_choices"] = topic_choices()

        # 若指定了想問的主題，做針對性分析
        topic_key = data.get("topic")
        if topic_key:
            a["topic_result"] = analyze_topic(c, topic_key, ln_from, ln_to)

        return jsonify({"ok": True, "data": a})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/pdf", methods=["POST"])
def pdf():
    """產生並下載 PDF"""
    try:
        data = request.get_json()
        year = int(data["year"])
        month = int(data["month"])
        day = int(data["day"])
        hour = data.get("hour")
        hour = int(hour) if hour not in (None, "", "unknown") else None

        ln_from = int(data.get("ln_from") or year + 33)
        ln_to = int(data.get("ln_to") or ln_from + 10)

        c = BaziChart(year, month, day, hour)
        a = c.full_analysis(ln_from, ln_to)

        topic_key = data.get("topic")
        topic_result = analyze_topic(c, topic_key, ln_from, ln_to) if topic_key else None
        pdf_bytes = build_pdf(a, topic_result)

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"bazi_{year}{month:02d}{day:02d}.pdf",
        )
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
