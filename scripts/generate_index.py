import markdown
import glob
import os

os.chdir("reports")

content = ""
for f in sorted(glob.glob("market_review_*.md"), reverse=True)[:1]:
    content += open(f, encoding="utf-8").read() + "\n\n---\n\n"
for f in sorted(glob.glob("report_*.md"), reverse=True):
    content += open(f, encoding="utf-8").read() + "\n\n---\n\n"

html = markdown.markdown(content, extensions=["tables", "fenced_code"])

page = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>每日股票分析报告</title>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:'Noto Sans SC',sans-serif;background:#f0f4f8;color:#2d3748;line-height:1.8}
.header{background:linear-gradient(135deg,#1a365d,#2b6cb0);color:white;padding:32px 24px;text-align:center}
.header h1{font-size:1.8rem;font-weight:700;letter-spacing:2px}
.header p{opacity:0.8;margin-top:8px;font-size:0.9rem}
.container{max-width:960px;margin:32px auto;padding:0 16px}
.card{background:white;border-radius:12px;box-shadow:0 2px 12px rgba(0,0,0,0.08);padding:28px 32px;margin-bottom:24px}
h1,h2,h3{color:#1a365d;margin:20px 0 12px}
h1{font-size:1.5rem;border-bottom:3px solid #2b6cb0;padding-bottom:8px}
h2{font-size:1.2rem;border-left:4px solid #63b3ed;padding-left:10px}
h3{font-size:1rem;color:#2b6cb0}
p{margin:10px 0}
table{width:100%;border-collapse:collapse;margin:16px 0;font-size:0.9rem}
th{background:#2b6cb0;color:white;padding:10px 14px;text-align:left;font-weight:500}
td{padding:9px 14px;border-bottom:1px solid #e2e8f0}
tr:nth-child(even) td{background:#f7fafc}
tr:hover td{background:#ebf8ff;transition:background 0.2s}
code{background:#edf2f7;padding:2px 6px;border-radius:4px;font-size:0.85rem}
pre{background:#2d3748;color:#e2e8f0;padding:16px;border-radius:8px;overflow-x:auto;margin:16px 0}
hr{border:none;border-top:2px dashed #e2e8f0;margin:32px 0}
strong{color:#2b6cb0}
ul,ol{padding-left:20px;margin:10px 0}
li{margin:4px 0}
.footer{text-align:center;padding:24px;color:#718096;font-size:0.85rem}
@media(max-width:600px){.card{padding:16px}.header h1{font-size:1.3rem}}
</style>
</head>
<body>
<div class="header">
  <h1>📈 每日股票分析报告</h1>
  <p>AI 驱动的智能股票分析系统</p>
</div>
<div class="container">
  <div class="card">
""" + html + """
  </div>
</div>
<div class="footer">由 daily_stock_analysis 自动生成</div>
</body>
</html>"""

with open("index.html", "w", encoding="utf-8") as f:
    f.write(page)

print("index.html generated successfully")
