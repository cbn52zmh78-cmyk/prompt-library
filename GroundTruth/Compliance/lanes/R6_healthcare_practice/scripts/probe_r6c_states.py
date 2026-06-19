#!/usr/bin/env python3
"""R6-C state source probe — public .gov only."""
import io
import re
import ssl
import urllib.request

CTX = ssl.create_default_context()
UA = "Mozilla/5.0 GroundTruth-R6C/1.0"


def fetch(url, n=200000):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=40, context=CTX) as r:
        return r.status, r.headers.get("Content-Type", ""), r.read(n)


def pdf_text(data):
    import pypdf

    return "".join(p.extract_text() or "" for p in pypdf.PdfReader(io.BytesIO(data)).pages)


def main():
    probes = [
        ("PA_6155_PDF", "https://www.palegis.us/statutes/consolidated/view-statute?txtType=PDF&ttl=42&div=00.&chpt=61&sctn=55&subsctn=0"),
        ("PA_BPINA_search", "https://www.palegis.us/statutes/consolidated/statute-search?search=breach+personal+information"),
        ("IL_ilcs_asp", "https://www.ilga.gov/legislation/ilcs/ilcs.asp"),
        ("IL_JCAR_815", "https://www.ilga.gov/agencies/JCAR/entirepart?titlepart=08150530"),
        ("NJ_26_5C", "https://lis.njleg.state.nj.us/nxt/gateway.dll?f=templates&fn=default.htm&vid=Publish:10.1048/Enu&d=statutes/26%5f5C-7.htm"),
        ("GA_dph_privacy", "https://dph.georgia.gov/programs/healthcare-associated-infections"),
        ("GA_consumer", "https://consumer.georgia.gov/consumer-services/identity-theft"),
        ("OH_3701_74", "https://codes.ohio.gov/ohio-revised-code/section-3701.74"),
        ("OH_1349_19", "https://codes.ohio.gov/ohio-revised-code/section-1349.19"),
    ]
    for name, url in probes:
        try:
            st, ct, body = fetch(url)
            if "pdf" in ct.lower() or body[:4] == b"%PDF":
                t = pdf_text(body)
                print(f"{name}: {st} PDF chars={len(t)}")
                print(t[:600])
            else:
                t = re.sub(r"\s+", " ", body.decode("utf-8", "replace"))
                print(f"{name}: {st} HTML chars={len(t)}")
                for kw in ["815 ILCS", "740 ILCS", "26:5C", "31-33", "6155", "breach", "BPINA", "3701.74"]:
                    if kw.lower() in t.lower():
                        i = t.lower().find(kw.lower())
                        print(f"  HIT {kw}: {t[max(0,i-40):i+120]}")
        except Exception as e:
            print(f"{name}: ERR {type(e).__name__} {e}")

    # scan PA title 73 chapters for breach
    import pypdf

    for chpt in range(1, 60):
        url = f"https://www.palegis.us/statutes/consolidated/view-statute?txtType=PDF&ttl=73&div=00.&chpt={chpt}&sctn=1&subsctn=0"
        try:
            st, ct, body = fetch(url, 150000)
            if body[:4] != b"%PDF":
                continue
            t = pdf_text(body)
            if "breach of the security" in t.lower() or "breach of personal information" in t.lower():
                print(f"PA_BREACH_CHPT={chpt} len={len(t)}")
                print(t[:1200])
        except Exception:
            pass


if __name__ == "__main__":
    main()