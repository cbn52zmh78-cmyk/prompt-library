#!/usr/bin/env python3
"""R6-D probe — NC, VA, MI, AZ reachable hosts."""
import io
import re
import ssl
import urllib.request

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 GroundTruth-R6D/1.0"

PROBES = [
    ("NC_90_21", "https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_90/GS_90-21.20.html"),
    ("NC_90_21_pdf", "https://www.ncleg.gov/EnactedLegislation/Statutes/PDF/BySection/Chapter_90/GS_90-21.20.pdf"),
    ("NC_75_61", "https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_75/GS_75-61.html"),
    ("NC_75_65", "https://www.ncleg.gov/EnactedLegislation/Statutes/HTML/BySection/Chapter_75/GS_75-65.html"),
    ("VA_32_1_127", "https://law.lis.virginia.gov/vacode/title32.1/chapter1/section32.1-127.1:03/"),
    ("VA_18_2_186", "https://law.lis.virginia.gov/vacode/title18.2/chapter8/section18.2-186.6/"),
    ("MI_333_26261", "https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-333-26261"),
    ("MI_445_63", "https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-445-63"),
    ("MI_445_72", "https://www.legislature.mi.gov/Laws/MCL?objectName=mcl-445-72"),
    ("AZ_32_3201", "https://www.azleg.gov/ars/32/03201.htm"),
    ("AZ_18_551", "https://www.azleg.gov/ars/18/00551.htm"),
    ("AZ_44_7501", "https://www.azleg.gov/ars/44/07501.htm"),
]


def fetch(url, n=120000):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read(n)


def pdf_text(data):
    import pypdf
    return "".join(p.extract_text() or "" for p in pypdf.PdfReader(io.BytesIO(data)).pages)


def main():
    for name, url in PROBES:
        try:
            st, ct, body = fetch(url)
            if "pdf" in ct.lower() or body[:4] == b"%PDF":
                t = pdf_text(body)
                print(f"{name}: {st} PDF len={len(t)}")
                print(t[:500])
            else:
                t = re.sub(r"\s+", " ", body.decode("utf-8", "replace"))
                print(f"{name}: {st} HTML len={len(t)}")
                for kw in ["disclosure", "breach", "confidential", "personal information", "authorization", "medical record", "health care"]:
                    if kw in t.lower():
                        i = t.lower().find(kw)
                        print(f"  {kw}: {t[max(0,i-40):i+120]}")
        except Exception as e:
            print(f"{name}: ERR {type(e).__name__} {e}")


if __name__ == "__main__":
    main()