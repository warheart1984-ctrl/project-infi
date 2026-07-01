"""Minimal ReportLab PDF builder from wolf1_v1.1.md. Requires: pip install reportlab pyyaml"""
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
import os
import yaml

BASE = os.path.dirname(__file__)
SRC = os.path.join(BASE, "..", "..", "src", "wolf1_v1.1.md")
OUT = os.path.join(BASE, "wolf1_v1.1.pdf")
CFG = os.path.join(BASE, "layout_config.yaml")


def main():
    with open(CFG) as f:
        cfg = yaml.safe_load(f)
    c = canvas.Canvas(OUT, pagesize=A4)
    width, height = A4
    x = cfg["margin"]["left"]
    y = height - cfg["margin"]["top"]

    with open(SRC, encoding="utf-8") as f:
        for line in f:
            text = line.rstrip()
            if text.startswith("# "):
                c.setFont("Helvetica-Bold", cfg["heading"]["h1"])
                text = text[2:]
            elif text.startswith("## "):
                c.setFont("Helvetica-Bold", cfg["heading"]["h2"])
                text = text[3:]
            elif text.startswith("### "):
                c.setFont("Helvetica-Bold", cfg["heading"]["h3"])
                text = text[4:]
            else:
                c.setFont("Helvetica", cfg["font"]["size"])
            if not text.strip():
                y -= 10
                continue
            if len(text) > 95:
                text = text[:92] + "..."
            c.drawString(x, y, text)
            y -= 14
            if y < cfg["margin"]["bottom"]:
                c.showPage()
                y = height - cfg["margin"]["top"]
    c.save()
    print("Wrote", OUT)


if __name__ == "__main__":
    main()
