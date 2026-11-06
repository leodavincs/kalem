#!/usr/bin/env python3
"""istemler.json + kareler -> istemler.md ve istemler.html (kopyala düğmeli).

Kullanım:
  python3 motorlar/referans/html_yap.py <proje klasörü>

Claude'un yazdığı <proje>/istemler.json şu biçimde olmalı:
{
  "video": "dosya adı", "ozet": "Türkçe tek cümle", "stil": "ortak görsel stil (İngilizce)",
  "sahneler": [{
     "no": 1, "sure": 4.0,
     "aciklama": "Türkçe kısa açıklama",
     "kamera": "...", "isik": "...", "konu": "...", "doku_renk": "...", "gecis": "...",
     "istem": "tam İngilizce istem (tek başına çalışır)"
  }]
}
Karelerin yolu <proje>/sahneler.json içinden alınır.
"""
import html
import json
import sys
from pathlib import Path

ALANLAR = [("kamera", "Kamera"), ("isik", "Işık"), ("konu", "Konu / hareket"),
           ("doku_renk", "Doku / renk"), ("gecis", "Geçiş")]


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    p = Path(sys.argv[1]).expanduser()
    ist = json.loads((p / "istemler.json").read_text(encoding="utf-8"))
    bul = json.loads((p / "sahneler.json").read_text(encoding="utf-8"))
    kareler = {s["no"]: s["kareler"] for s in bul["sahneler"]}
    zaman = {s["no"]: (s["baslangic"], s["bitis"]) for s in bul["sahneler"]}
    uyar = [s["no"] for s in bul["sahneler"] if s["no"] not in {x["no"] for x in ist["sahneler"]}]
    if uyar:
        print("UYARI: istemi olmayan sahneler:", uyar)

    # --- istemler.md
    md = [f"# İstemler: {ist.get('video', '')}", "", ist.get("ozet", ""), "",
          f"**Ortak stil:** {ist.get('stil', '')}", ""]
    for s in ist["sahneler"]:
        md += [f"## Sahne {s['no']} ({s['sure']} sn)", "", s.get("aciklama", ""), ""]
        for k, ad in ALANLAR:
            if s.get(k):
                md.append(f"- **{ad}:** {s[k]}")
        md += ["", "```", s["istem"], "```", ""]
    (p / "istemler.md").write_text("\n".join(md), encoding="utf-8")

    # --- istemler.html
    e = html.escape
    kartlar = []
    for s in ist["sahneler"]:
        b, t = zaman.get(s["no"], (0, 0))
        imgs = "".join(f'<img src="{e(k)}" alt="sahne {s["no"]} karesi">' for k in kareler.get(s["no"], []))
        satirlar = "".join(f"<tr><th>{ad}</th><td>{e(s[k])}</td></tr>" for k, ad in ALANLAR if s.get(k))
        kartlar.append(f"""<section class="kart">
<header><h2>Sahne {s['no']}</h2><span class="sure">{s['sure']} sn &middot; {b:.0f}-{t:.0f}. sn</span></header>
<div class="kareler">{imgs}</div>
<p class="acik">{e(s.get('aciklama', ''))}</p>
<table>{satirlar}</table>
<pre id="i{s['no']}">{e(s['istem'])}</pre>
<button onclick="kopyala({s['no']}, this)">Kopyala</button>
</section>""")
    tum = "\n\n".join(s["istem"] for s in ist["sahneler"])
    sayfa = f"""<!doctype html>
<html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>İstemler: {e(ist.get('video', ''))}</title>
<style>
:root{{--zemin:#f4efe3;--kart:#fffdf7;--yazi:#2b2620;--soluk:#7a7063;--vurgu:#8a2b1f;--cizgi:#d9cfba}}
@media(prefers-color-scheme:dark){{:root{{--zemin:#1d1a16;--kart:#27231e;--yazi:#eee6d6;--soluk:#a39886;--vurgu:#e08a73;--cizgi:#3d372f}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--zemin);color:var(--yazi);font:16px/1.5 Georgia,serif;padding:24px 16px}}
main{{max-width:860px;margin:auto}}h1{{font-size:1.5rem;margin:0 0 4px}}.ozet{{color:var(--soluk);margin:0 0 4px}}
.stil{{font-size:.9rem;margin:0 0 16px}}
.kart{{background:var(--kart);border:1px solid var(--cizgi);border-radius:8px;padding:16px;margin:0 0 16px}}
header{{display:flex;justify-content:space-between;align-items:baseline;gap:8px}}h2{{margin:0;font-size:1.15rem;color:var(--vurgu)}}
.sure{{color:var(--soluk);font-size:.85rem}}.kareler{{display:flex;gap:6px;margin:10px 0}}
.kareler img{{flex:1;min-width:0;width:33%;border-radius:4px;border:1px solid var(--cizgi)}}
.acik{{margin:6px 0}}table{{border-collapse:collapse;width:100%;font-size:.88rem;margin:8px 0}}
th{{text-align:left;color:var(--soluk);font-weight:normal;padding:2px 12px 2px 0;white-space:nowrap;vertical-align:top}}td{{padding:2px 0}}
pre{{white-space:pre-wrap;word-wrap:break-word;background:var(--zemin);border:1px solid var(--cizgi);border-radius:6px;padding:10px;font:13px/1.45 ui-monospace,Menlo,monospace;margin:8px 0}}
button{{background:var(--vurgu);color:#fff;border:0;border-radius:6px;padding:8px 16px;font:inherit;cursor:pointer}}
button.hepsi{{background:var(--yazi);color:var(--zemin);margin-bottom:16px}}
</style></head><body><main>
<h1>İstemler: {e(ist.get('video', ''))}</h1>
<p class="ozet">{e(ist.get('ozet', ''))}</p>
<p class="stil"><b>Ortak stil:</b> {e(ist.get('stil', ''))}</p>
<button class="hepsi" onclick="kopyala(0, this)">Hepsini kopyala</button>
{chr(10).join(kartlar)}
<p class="ozet">Bu istemler ilham içindir. Başkasının videosunu birebir kopyalama; referans al, kendi işini yap.</p>
<script type="text/plain" id="hepsi">{e(tum)}</script>
<script>
function kopyala(n, d){{
  var m = n===0 ? document.getElementById('hepsi').textContent : document.getElementById('i'+n).textContent;
  var bitti = function(){{ var o=d.textContent; d.textContent='Kopyalandı'; setTimeout(function(){{d.textContent=o}},1500) }};
  var yedek = function(){{ var t=document.createElement('textarea'); t.value=m; document.body.appendChild(t); t.select();
    try{{document.execCommand('copy'); bitti()}}catch(e){{}} document.body.removeChild(t) }};
  if(navigator.clipboard && navigator.clipboard.writeText) navigator.clipboard.writeText(m).then(bitti, yedek); else yedek();
}}
</script></main></body></html>"""
    (p / "istemler.html").write_text(sayfa, encoding="utf-8")
    print(f"yazıldı: {p/'istemler.md'} ve {p/'istemler.html'}")


if __name__ == "__main__":
    main()
