#!/usr/bin/env python3
"""Videoyu sahnelere böler, her sahneden kare çıkarır.

Kullanım:
  python3 motorlar/referans/sahne_bul.py <video> [--cikti klasör] [--esik 0.30] [--en-uzun 8] [--en-kisa 1]

Çıktı klasörü (varsayılan projeler/referans-<video adı>/):
  kareler/s01-a.jpg, s01-b.jpg, s01-c.jpg   (her sahnenin başı, ortası, sonu)
  sahneler.json                              (sahne no, başlangıç, bitiş, süre, kare yolları)

Yalnız ffmpeg gerekir. Hiçbir şey internete gitmez.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def sure(video):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        sys.exit("Video okunamadı: " + str(video))


def kesimler(video, esik):
    """Sert kesim anlarını (saniye) döndürür."""
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", str(video), "-an",
                        "-vf", f"select='gt(scene,{esik})',showinfo", "-f", "null", "-"],
                       capture_output=True, text=True)
    return [float(m) for m in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def sahnele(toplam, kesim, en_kisa, en_uzun):
    # çok yakın kesimleri birleştir
    sinirlar = [0.0]
    for t in sorted(kesim):
        if t - sinirlar[-1] >= en_kisa and toplam - t >= en_kisa:
            sinirlar.append(t)
    sinirlar.append(toplam)
    parcalar = []
    for a, b in zip(sinirlar, sinirlar[1:]):
        n = max(1, -(-int((b - a) * 1000) // int(en_uzun * 1000)))  # tavan bölme
        adim = (b - a) / n
        for i in range(n):
            parcalar.append((round(a + i * adim, 2), round(a + (i + 1) * adim, 2)))
    return parcalar


def kare_al(video, t, yol):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{t:.2f}",
                    "-i", str(video), "-frames:v", "1", "-vf", "scale=640:-2", "-q:v", "4", str(yol)],
                   check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--cikti")
    ap.add_argument("--esik", type=float, default=0.30, help="kesim hassasiyeti (düşük = daha çok sahne)")
    ap.add_argument("--en-uzun", type=float, default=8.0, help="bir sahne en çok kaç saniye (video modelleri ~8 sn üretir)")
    ap.add_argument("--en-kisa", type=float, default=1.0)
    a = ap.parse_args()

    video = Path(a.video).expanduser().resolve()
    if not video.exists():
        sys.exit("Video yok: " + str(video))
    kok = Path(__file__).resolve().parents[2]
    cikti = Path(a.cikti).expanduser() if a.cikti else kok / "projeler" / f"referans-{video.stem}"
    (cikti / "kareler").mkdir(parents=True, exist_ok=True)

    toplam = sure(video)
    kes = kesimler(video, a.esik)
    parcalar = sahnele(toplam, kes, a.en_kisa, a.en_uzun)

    sahneler = []
    for i, (b, s) in enumerate(parcalar, 1):
        d = s - b
        kareler = []
        for harf, oran in (("a", 0.1), ("b", 0.5), ("c", 0.9)):
            yol = cikti / "kareler" / f"s{i:02d}-{harf}.jpg"
            kare_al(video, b + d * oran, yol)
            kareler.append(f"kareler/{yol.name}")
        sahneler.append({"no": i, "baslangic": b, "bitis": s, "sure": round(d, 1), "kareler": kareler})

    (cikti / "sahneler.json").write_text(json.dumps(
        {"video": video.name, "toplam_sure": round(toplam, 1), "sahneler": sahneler},
        ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(sahneler)} sahne ({toplam:.0f} sn, {len(kes)} kesim bulundu) -> {cikti}")


if __name__ == "__main__":
    main()
