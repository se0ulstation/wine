#!/usr/bin/env python3
"""web/dashboard.template.html + data/cellar.json → web/dashboard.html"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
tpl = (ROOT / "web" / "dashboard.template.html").read_text()
data = json.loads((ROOT / "data" / "cellar.json").read_text())
out = ROOT / "web" / "dashboard.html"
out.write_text(tpl.replace("/*__DATA__*/", json.dumps(data, ensure_ascii=False)))
print(f"{out.relative_to(ROOT)}: {sum(b.get('qty',1) for b in data['bottles'])}병")
