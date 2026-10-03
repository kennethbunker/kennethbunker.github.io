#!/usr/bin/env python3
"""Builds /publications/ (index + one page per item) and /sitemap.xml.

Edit publications/_src/publications.json, then run from the repo root:
    python3 publications/_src/build.py

To host a PDF yourself, drop it in publications/pdf/<slug>.pdf and rebuild.
The PDF button and the Google Scholar citation_pdf_url tag are added automatically.
"""
import json, os, html, re, unicodedata, datetime, urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
PUBDIR = os.path.join(ROOT, "publications")
SITE = "https://kennethbunker.github.io"
BASE = SITE + "/publications/"
EMAIL = "kenneth.bunker@uss.cl"
RG_PROFILE = "https://www.researchgate.net/profile/Kenneth-Bunker"
ACADEMIA_PROFILE = "https://uss.academia.edu/KennethBunker"
SCHOLAR_PROFILE = "https://scholar.google.cl/citations?user=kFHaW6wAAAAJ&hl=en"
ORCID = "https://orcid.org/0000-0002-4579-6132"

E = lambda s: html.escape(str(s), quote=True) if s is not None else ""
data = json.load(open(os.path.join(os.path.dirname(__file__), "publications.json"), encoding="utf-8"))

SECTIONS = [
    ("book", "Book", "Libro"),
    ("article", "Peer-reviewed articles", None),
    ("chapter", "Book chapters", None),
    ("review", "Book reviews", None),
    ("dataset", "Datasets", None),
    ("ideas", "Policy briefs: Ideas, Democracy and Government Lab", None),
    ("report", "Reports", None),
    ("workingpaper", "Working papers and other publications", None),
]
TYPE_LABEL = {"book": "Book", "article": "Journal article", "chapter": "Book chapter", "review": "Book review",
              "dataset": "Dataset", "ideas": "Policy brief", "report": "Report", "workingpaper": "Working paper"}

# ---------- helpers ----------
def split_name(full):
    parts = full.split()
    return " ".join(parts[:-1]), parts[-1]

# Spanish double surnames we know about
DOUBLE = {"Cristóbal González Piucol": ("Cristóbal", "González Piucol"),
          "Sebastián Contreras Ubal": ("Sebastián", "Contreras Ubal"),
          "Miguel Ángel López": ("Miguel Ángel", "López"),
          "Gabriel L. Negretto": ("Gabriel L.", "Negretto"),
          "Isaí Emanuel Muñoz": ("Isaí Emanuel", "Muñoz"),
          "Jaime Fernando Abedrapo Rojas": ("Jaime Fernando", "Abedrapo Rojas")}
def name_parts(full):
    return DOUBLE.get(full) or split_name(full)

def initials(given):
    return " ".join(p[0] + "." for p in re.split(r"[\s]+", given) if p and p[0].isalpha())

def apa_authors(auth):
    xs = [f"{name_parts(a)[1]}, {initials(name_parts(a)[0])}" for a in auth]
    if len(xs) == 1: return xs[0]
    return ", ".join(xs[:-1]) + ", & " + xs[-1]

def bib_authors(auth):
    return " and ".join(f"{name_parts(a)[1]}, {name_parts(a)[0]}" for a in auth)

def first_last(p):
    if not p: return None, None
    m = re.match(r"^\s*([0-9A-Za-z]+)\s*-\s*([0-9A-Za-z]+)\s*$", p)
    return (m.group(1), m.group(2)) if m else (p, None)

def ascii_slug(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "", s)

def bibkey(e):
    w = [x for x in re.split(r"\W+", unicodedata.normalize("NFKD", e["title"]).encode("ascii","ignore").decode().lower())
         if x and x not in {"the","a","an","el","la","los","las","de","cual","como","que","a"}]
    return ascii_slug(name_parts(e["authors"][0])[1]) + str(e.get("year") or "forthcoming") + (w[0] if w else "")

def year_str(e):
    return str(e["year"]) if e.get("year") else "Forthcoming"

def venue_html(e):
    t = e["type"]
    if t in ("article", "review"):
        s = f"<em>{E(e['journal'])}</em>"
        if e.get("volume"): s += f" {E(e['volume'])}"
        if e.get("issue"): s += f"({E(e['issue'])})"
        if e.get("pages"): s += f": {E(e['pages'])}"
        if e.get("article_number"): s += f", article {E(e['article_number'])}"
        if e.get("status"): s += f" ({E(e['status'])})"
        return s
    if t == "chapter":
        s = f"In <em>{E(e['book_title'])}</em>"
        if e.get("editors"): s += f", edited by {E(', '.join(e['editors']))}"
        if e.get("pages"): s += f", pp. {E(e['pages'])}"
        if e.get("publisher"): s += f". {E(e['publisher'])}"
        return s
    if t == "book":
        return f"{E(e['publisher'])}, {E(e.get('pages_total',''))} pp."
    if t == "dataset":
        return E(e["publisher"]) + (f", version {E(e['version'])}" if e.get("version") else "")
    if t == "ideas":
        return f"<em>{E(e['series'])}</em> {E(e['number'])}" + (f": {E(e['pages'])}" if e.get("pages") else "")
    if t == "report":
        return f"{E(e['publisher'])}, {E(e['place'])}" + (f", {E(e['pages_total'])} pp." if e.get("pages_total") else "")
    if t == "workingpaper":
        return f"<em>{E(e['series'])}</em> {E(e['number'])}. {E(e['publisher'])}"
    return ""

def apa_citation(e):
    a = apa_authors(e["authors"])
    y = year_str(e).lower() if not e.get("year") else e["year"]
    t = e["title"]
    end = f" https://doi.org/{e['doi']}" if e.get("doi") else ""
    k = e["type"]
    if k in ("article", "review"):
        v = e["journal"]
        if e.get("volume"): v += f", {e['volume']}"
        if e.get("issue"): v += f"({e['issue']})" if e.get("volume") else f", {e['issue']}"
        if e.get("pages"): v += f", {e['pages'].replace('-', '–')}"
        if e.get("article_number"): v += f", {e['article_number']}"
        return f"{a} ({y}). {t}. {v}.{end}"
    if k == "chapter":
        ed = ""
        if e.get("editors"):
            ed = " In " + ", ".join(e["editors"]) + (" (Eds.)," if len(e["editors"]) > 1 else " (Ed.),")
        else:
            ed = " In"
        pp = f" (pp. {e['pages'].replace('-', '–')})" if e.get("pages") else ""
        pub = f" {e['publisher']}." if e.get("publisher") else ""
        return f"{a} ({y}). {t}.{ed} {e['book_title']}{pp}.{pub}{end}"
    if k == "book":
        return f"{a} ({y}). {t}. {e['publisher']}.{end}"
    if k == "dataset":
        return f"{a} ({y}). {t}" + (f" (Version {e['version']})" if e.get("version") else "") + f" [Data set]. {e['publisher']}.{end}"
    if k == "ideas":
        return f"{a} ({y}). {t} ({e['series']}, No. {e['number']}). {e['publisher']}.{end}"
    if k == "report":
        return f"{a} ({y}). {t}. {e['publisher']}."
    if k == "workingpaper":
        return f"{a} ({y}). {t} ({e['series']}, No. {e['number']}). {e['publisher']}."
    return f"{a} ({y}). {t}."

def bibtex(e):
    k = e["type"]
    typ = {"article": "article", "review": "article", "chapter": "incollection", "book": "book",
           "dataset": "misc", "ideas": "techreport", "report": "techreport", "workingpaper": "techreport"}[k]
    f = [("author", bib_authors(e["authors"])), ("title", "{" + e["title"] + "}")]
    if k in ("article", "review"):
        f += [("journal", e["journal"]), ("volume", e.get("volume")), ("number", e.get("issue")),
              ("pages", (e.get("pages") or "").replace("-", "--") or None)]
        if e.get("article_number"): f.append(("eid", e["article_number"]))
    if k == "chapter":
        f += [("booktitle", e["book_title"]), ("editor", " and ".join(f"{name_parts(x)[1]}, {name_parts(x)[0]}" for x in e.get("editors", [])) or None),
              ("pages", (e.get("pages") or "").replace("-", "--") or None), ("publisher", e.get("publisher")), ("address", e.get("place"))]
    if k == "book":
        f += [("publisher", e["publisher"]), ("address", e.get("place")), ("isbn", (e.get("isbn") or "").split(" ")[0] or None)]
    if k == "dataset":
        f += [("publisher", e["publisher"]), ("version", e.get("version")), ("howpublished", "Data set")]
    if k in ("ideas", "workingpaper"):
        f += [("institution", e["publisher"]), ("type", e["series"]), ("number", e.get("number")), ("address", e.get("place"))]
    if k == "report":
        f += [("institution", e["publisher"]), ("address", e.get("place"))]
    f += [("year", e.get("year") or "forthcoming"), ("doi", e.get("doi")), ("url", BASE + e["slug"] + "/"),
          ("language", {"es": "spanish", "en": "english"}.get(e.get("language")))]
    if k == "review":
        f.append(("note", f"Review of {e['reviewed_title']}, by {e['reviewed_authors']}"))
    body = ",\n".join(f"  {n:<9}= {{{v}}}" for n, v in f if v not in (None, ""))
    return f"@{typ}{{{bibkey(e)},\n{body}\n}}"

def local_pdf(e):
    p = os.path.join(PUBDIR, "pdf", e["slug"] + ".pdf")
    return f"{BASE}pdf/{e['slug']}.pdf" if os.path.exists(p) else None

def links(e):
    """Return list of (label, url, cls)."""
    L = []
    q = re.sub(r"\s+", "+", e["title"])
    if e.get("doi"): L.append(("DOI", "https://doi.org/" + e["doi"], "doi"))
    elif e.get("url"): L.append(("Publisher", e["url"], "doi"))
    pdf = local_pdf(e) or e.get("pdf")
    if pdf: L.append(("PDF" + (" (submitted version)" if e.get("pdf_note") and not local_pdf(e) else ""), pdf, "pdf"))
    elif e.get("pdf_rg"): L.append(("PDF", e["researchgate"], "pdf"))
    else: L.append(("Request PDF", f"mailto:{EMAIL}?subject=" + re.sub(r"\s", "%20", "PDF request: " + e["title"]), "pdf req"))
    L.append(("ResearchGate", e.get("researchgate") or f"https://www.researchgate.net/search/publication?q={q}", "rg"))
    L.append(("Academia.edu", e.get("academia") or ACADEMIA_PROFILE, "ac"))
    L.append(("Google Scholar", "https://scholar.google.com/scholar?q=" + q, "gs"))
    return L

def btns(e, extra=""):
    s = "".join(f'<a class="pbtn {c}" href="{E(u)}" target="_blank" rel="noopener">{E(l)}</a>' for l, u, c in links(e))
    return f'<div class="pbtns">{extra}{s}</div>'

def authors_html(auth):
    return ", ".join(f"<strong>{E(a)}</strong>" if a == "Kenneth Bunker" else E(a) for a in auth)

# ---------- shared chrome ----------
HEAD_COMMON = """<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-XHPPDNKH57"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){dataLayer.push(arguments);}gtag('js',new Date());gtag('config','G-XHPPDNKH57');</script>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">
<link href="https://fonts.googleapis.com/css2?family=Inconsolata:wght@400;700&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@4.5.3/dist/css/bootstrap.min.css" integrity="sha384-TX8t27EcRE3e/ihU7zmQxVncDAy5uIKz4rEkgIXeMed4M0jlfIDPvg6uqKI2xXr2" crossorigin="anonymous">
<link rel="stylesheet" href="https://kennethbunker.github.io/sass/researcher.min.css">
<style>
.container.mt-5{max-width:100%;padding-left:0;padding-right:0}
.container.mt-5 .navbar-nav .btn{margin-right:.35rem!important;padding-left:.4rem;padding-right:.4rem}
.pub{padding:1.1rem 0;border-bottom:1px solid #eee;max-width:48rem}
.pub .ptitle{font-weight:700;font-size:1.05rem;line-height:1.35;margin-bottom:.3rem}
.pub .ptitle a{color:#222;text-decoration:none}.pub .ptitle a:hover{color:#0077cc;text-decoration:underline}
.pub .meta{font-size:.9rem;color:#444}
.pub .venue{font-size:.85rem;color:#777;margin-bottom:.15rem}
.pub .pbtns{margin-top:.5rem}
h2[id^=sec-]{margin-top:2.5rem!important;padding-bottom:.3rem;border-bottom:2px solid #222;max-width:48rem}
.pbtns{display:flex;flex-wrap:wrap;gap:.35rem;margin-top:.35rem}
.pbtn{display:inline-block;font-size:.78rem;line-height:1.2;padding:.18rem .5rem;border:1px solid #0077cc;border-radius:3px;color:#0077cc;text-decoration:none!important;background:#fff;cursor:pointer;font-family:inherit}
.pbtn:hover{background:#0077cc;color:#fff}
.pbtn.pdf{border-color:#b30000;color:#b30000}.pbtn.pdf:hover{background:#b30000;color:#fff}
.pbtn.req{border-style:dashed}
.pbtn.rg{border-color:#00b3a6;color:#008a80}.pbtn.rg:hover{background:#00b3a6;color:#fff}
.pbtn.ac{border-color:#41454a;color:#41454a}.pbtn.ac:hover{background:#41454a;color:#fff}
.pbtn.gs{border-color:#4285f4;color:#4285f4}.pbtn.gs:hover{background:#4285f4;color:#fff}
.pbtn.more{border-color:#333;color:#333}.pbtn.more:hover{background:#333;color:#fff}
pre.bib{background:#f6f6f6;border:1px solid #ddd;padding:.75rem;font-size:.8rem;white-space:pre-wrap;word-break:break-word}
.bibbox{display:none;margin-top:.5rem}
.bibbox.open{display:block}
.abstract{line-height:1.6;max-width:46rem}
.lbl{font-size:.75rem;letter-spacing:.08em;text-transform:uppercase;color:#777;margin:1.2rem 0 .3rem}
table.det td{padding:.15rem .8rem .15rem 0;vertical-align:top}
table.det td:first-child{font-weight:700;white-space:nowrap}
.tag{display:inline-block;font-size:.75rem;background:#eee;border-radius:3px;padding:.05rem .4rem;margin:0 .25rem .25rem 0}
#q{width:100%;max-width:420px;padding:.35rem .5rem;border:1px solid #ccc;border-radius:3px;font-family:inherit}
.toc a{margin-right:.8rem;white-space:nowrap}
.count{color:#777;font-weight:400;font-size:.8em}
</style>"""

NAV = """<div class="container mt-5">
<nav class="navbar navbar-expand-sm flex-column flex-sm-row text-nowrap p-0">
<a class="navbar-brand mx-0 mr-sm-auto" href="https://kennethbunker.github.io/">Kenneth Bunker</a>
<div class="navbar-nav flex-row flex-wrap justify-content-center">
<a class="btn btn-sm btn-outline-primary mr-2 mb-2" href="https://kennethbunker.github.io/">Home</a>
<a class="btn btn-sm btn-outline-primary mr-2 mb-2" href="https://kennethbunker.github.io/publications/">Publications</a>
<a class="btn btn-sm btn-outline-primary mr-2 mb-2" href="https://kennethbunker.github.io/press">In the Press</a>
<a class="btn btn-sm btn-outline-primary mr-2 mb-2" href="https://kennethbunker.github.io/prensa">Prensa</a>
<a class="btn btn-sm btn-outline-primary mr-2 mb-2" href="https://kennethbunker.github.io/columns">Columns</a>
<a class="btn btn-sm btn-outline-primary mr-2 mb-2" href="https://kennethbunker.github.io/theseus">Book</a>
<a class="btn btn-sm btn-outline-primary mr-2 mb-2" href="https://kennethbunker.github.io/interviews">Interviews</a>
<a class="btn btn-sm btn-outline-primary mr-2 mb-2" href="https://kennethbunker.github.io/covers">Covers</a>
<a class="btn btn-sm btn-outline-primary mr-2 mb-2" href="https://kennethbunker.github.io/contact">Projects</a>
</div>
</nav>
</div>
<hr>"""

FOOT = f"""<hr>
<p class="small">Profiles: <a href="{SCHOLAR_PROFILE}">Google Scholar</a> / <a href="{ORCID}">ORCID</a> / <a href="{RG_PROFILE}">ResearchGate</a> / <a href="{ACADEMIA_PROFILE}">Academia.edu</a> / <a href="https://www.webofscience.com/wos/author/record/R-4439-2018">Web of Science</a> / <a href="https://kennethbunker.github.io/cv.pdf">CV</a></p>
</div></div>
<div id="footer" class="mb-5"><hr><div class="container text-center"><small>&copy; {datetime.date.today().year} Kenneth Bunker</small></div></div>
<script>
function tog(id,b){{var x=document.getElementById(id);x.classList.toggle('open');}}
function cp(id,b){{var t=document.getElementById(id).innerText;navigator.clipboard.writeText(t).then(function(){{var o=b.innerText;b.innerText='Copied';setTimeout(function(){{b.innerText=o}},1500)}});}}
</script>
</body></html>
"""

# ---------- metadata ----------
def meta_tags(e):
    m = []
    add = lambda n, v: v and m.append(f'<meta name="{n}" content="{E(v)}">')
    add("citation_title", e["title"])
    for a in e["authors"]:
        add("citation_author", f"{name_parts(a)[1]}, {name_parts(a)[0]}")
    if e.get("online_date"): add("citation_online_date", e["online_date"].replace("-", "/"))
    add("citation_publication_date", str(e["year"]) if e.get("year") else None)
    k = e["type"]
    if k in ("article", "review"):
        add("citation_journal_title", e["journal"])
        add("citation_volume", e.get("volume")); add("citation_issue", e.get("issue"))
        fp, lp = first_last(e.get("pages")); add("citation_firstpage", fp or e.get("article_number")); add("citation_lastpage", lp)
        for i in re.findall(r"\d{4}-\d{3}[\dX]", e.get("issn") or ""): add("citation_issn", i)
    if k == "chapter":
        add("citation_inbook_title", e["book_title"])
        fp, lp = first_last(e.get("pages")); add("citation_firstpage", fp); add("citation_lastpage", lp)
        for ed in e.get("editors", []): add("citation_editor", f"{name_parts(ed)[1]}, {name_parts(ed)[0]}")
    if k in ("chapter", "book"):
        for i in re.findall(r"97[89][-\d]{10,16}", e.get("isbn") or ""): add("citation_isbn", i)
    if k in ("ideas", "report", "workingpaper"):
        add("citation_technical_report_institution", e["publisher"])
        add("citation_technical_report_number", (e.get("series", "") + " " + e.get("number", "")).strip() or None)
    add("citation_publisher", e.get("publisher"))
    add("citation_doi", e.get("doi"))
    add("citation_language", e.get("language"))
    for kw in e.get("keywords") or []: add("citation_keywords", kw)
    add("citation_abstract_html_url", BASE + e["slug"] + "/")
    add("citation_pdf_url", local_pdf(e))
    add("dc.identifier", "doi:" + e["doi"] if e.get("doi") else None)
    return "\n".join(m)

def jsonld(e):
    typ = {"article": "ScholarlyArticle", "review": "Review", "chapter": "Chapter", "book": "Book", "dataset": "Dataset",
           "ideas": "Report", "report": "Report", "workingpaper": "Report"}[e["type"]]
    d = {"@context": "https://schema.org", "@type": typ, "name": e["title"], "headline": e["title"][:110],
         "author": [{"@type": "Person", "name": a, **({"url": SITE, "sameAs": ORCID} if a == "Kenneth Bunker" else {})} for a in e["authors"]],
         "url": BASE + e["slug"] + "/", "inLanguage": e.get("language")}
    if e.get("year"): d["datePublished"] = str(e["year"])
    if e.get("doi"): d["identifier"] = {"@type": "PropertyValue", "propertyID": "DOI", "value": e["doi"]}; d["sameAs"] = "https://doi.org/" + e["doi"]
    if e.get("abstract"): d["abstract"] = e["abstract"]
    if e.get("keywords"): d["keywords"] = ", ".join(e["keywords"])
    if e.get("publisher"): d["publisher"] = {"@type": "Organization", "name": e["publisher"]}
    if e["type"] in ("article", "review"):
        d["isPartOf"] = {"@type": "Periodical", "name": e["journal"]}
        fp, lp = first_last(e.get("pages"))
        if fp: d["pageStart"] = fp
        if lp: d["pageEnd"] = lp
    if e["type"] == "chapter": d["isPartOf"] = {"@type": "Book", "name": e["book_title"]}
    if e["type"] == "review": d["itemReviewed"] = {"@type": "Book", "name": e["reviewed_title"], "author": e["reviewed_authors"]}
    if e["type"] == "dataset" and e.get("license"): d["license"] = "https://creativecommons.org/licenses/by/4.0/"
    if e["type"] == "book" and e.get("isbn"): d["isbn"] = e["isbn"].split(" ")[0]
    return json.dumps(d, ensure_ascii=False, indent=1)

def short_desc(e):
    if e.get("abstract"):
        s = re.sub(r"\s+", " ", e["abstract"])
        return s[:157].rsplit(" ", 1)[0] + "…" if len(s) > 160 else s
    return f"{TYPE_LABEL[e['type']]} by {', '.join(e['authors'])} ({year_str(e)})."

def detail_rows(e):
    r = [("Type", TYPE_LABEL[e["type"]]), ("Authors", ", ".join(e["authors"]))]
    k = e["type"]
    if k in ("article", "review"):
        r += [("Journal", e["journal"]), ("Volume", e.get("volume")), ("Issue", e.get("issue")), ("Pages", e.get("pages")),
              ("Article number", e.get("article_number")), ("Status", e.get("status"))]
    if k == "review": r += [("Book reviewed", f"{e['reviewed_title']}, by {e['reviewed_authors']}")]
    if k == "chapter": r += [("Book", e["book_title"]), ("Editors", ", ".join(e.get("editors") or []) or None), ("Pages", e.get("pages")), ("Status", e.get("status"))]
    if k in ("ideas", "workingpaper"): r += [("Series", e["series"]), ("Number", e.get("number")), ("Pages", e.get("pages"))]
    if k == "book": r += [("Pages", e.get("pages_total"))]
    if k == "report": r += [("Pages", e.get("pages_total"))]
    if k == "dataset": r += [("Version", e.get("version")), ("License", e.get("license"))]
    r += [("Year", year_str(e)), ("Published online", e.get("online_date")), ("Publisher", e.get("publisher")),
          ("Place", e.get("place")), ("ISSN", e.get("issn")), ("ISBN", e.get("isbn")),
          ("DOI", f'<a href="https://doi.org/{E(e["doi"])}">{E(e["doi"])}</a>' if e.get("doi") else None),
          ("Language", {"en": "English", "es": "Spanish"}.get(e.get("language")))]
    if e.get("url") and e["type"] in ("book", "dataset"): r.append(("Website", f'<a href="{E(e["url"])}">{E(e["url"])}</a>'))
    out = []
    for n, v in r:
        if v in (None, "", []): continue
        out.append(f"<tr><td>{n}</td><td>{v if n in ('DOI','Website') else E(v)}</td></tr>")
    return "\n".join(out)

# ---------- item pages ----------
CITE_BTN = '<button class="pbtn more" onclick="tog(\'citebox\',this)">Cite</button>'
def item_page(e):
    url = BASE + e["slug"] + "/"
    t = e["title"]
    ab = ""
    if e.get("abstract"):
        lab = e.get("abstract_label") or ("Abstract" if e.get("language") != "es" or e.get("abstract_es") else "Resumen")
        ab += f'<p class="lbl">{lab}</p>\n<p class="abstract">{E(e["abstract"])}</p>'
    if e.get("abstract_es"):
        ab += f'<p class="lbl">Resumen</p>\n<p class="abstract" lang="es">{E(e["abstract_es"])}</p>'
    if e["type"] == "review":
        ab += f'<p><em>Review of</em> {E(e["reviewed_title"])}, by {E(e["reviewed_authors"])}.</p>'
    kw = ""
    if e.get("keywords"):
        kw = '<h3>Keywords</h3><p>' + "".join(f'<span class="tag">{E(k)}</span>' for k in e["keywords"]) + "</p>"
    alt = f'<p class="text-muted">English title: {E(e["title_en"])}</p>' if e.get("title_en") else ""
    bid = "bib"; cid = "cit"
    page = f"""<!DOCTYPE html>
<html lang="{E(e.get('language') or 'en')}"><head>
{HEAD_COMMON}
<title>{E(t)} | Kenneth Bunker</title>
<meta name="description" content="{E(short_desc(e))}">
<meta name="author" content="{E(', '.join(e['authors']))}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="article">
<meta property="og:title" content="{E(t)}">
<meta property="og:description" content="{E(short_desc(e))}">
<meta property="og:url" content="{url}">
<meta property="og:site_name" content="Kenneth Bunker">
<meta name="twitter:card" content="summary">
{meta_tags(e)}
<script type="application/ld+json">
{jsonld(e)}
</script>
</head>
<body>
{NAV}
<div id="content"><div class="container">
<p class="small"><a href="{BASE}">&larr; All publications</a></p>
<p class="text-muted small mb-1">{E(TYPE_LABEL[e['type']])} &middot; {E(year_str(e))}</p>
<h1 style="font-size:1.6rem">{E(t)}</h1>
{alt}
<p>{authors_html(e['authors'])}</p>
<p>{venue_html(e)}</p>
{btns(e, CITE_BTN)}
<div class="bibbox" id="citebox">
<p class="small" id="{cid}">{E(apa_citation(e))}</p>
<pre class="bib" id="{bid}">{E(bibtex(e))}</pre>
<div class="pbtns"><button class="pbtn more" onclick="cp('{cid}',this)">Copy citation</button><button class="pbtn more" onclick="cp('{bid}',this)">Copy BibTeX</button><a class="pbtn more" href="data:application/x-bibtex;charset=utf-8,{E(urllib.parse.quote(bibtex(e)))}" download="{bibkey(e)}.bib">Download .bib</a></div>
</div>
<div class="mt-4">{ab}</div>
{FOOT}"""
    d = os.path.join(PUBDIR, e["slug"])
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, "index.html"), "w", encoding="utf-8").write(page)

# ---------- index ----------
def index_page():
    parts = []
    toc = []
    total = 0
    for key, heading, _ in SECTIONS:
        items = [e for e in data if e["type"] == key]
        if not items: continue
        total += len(items)
        sid = "sec-" + key
        toc.append(f'<a href="#{sid}">{E(heading.split(":")[0])}</a>')
        parts.append(f'<h2 id="{sid}" class="mt-4">{E(heading)} <span class="count">({len(items)})</span></h2>')
        if key == "ideas":
            parts.append('<p class="small"><em>Ideas</em> is the policy brief series of the Laboratorio Democracia y Gobierno, Facultad de Economía y Gobierno, Universidad San Sebastián. Full catalog at <a href="https://labdemgob.github.io/ideas/">labdemgob.github.io</a>.</p>')
        for e in items:
            bid = "b-" + e["slug"]
            more = f'<a class="pbtn more" href="{BASE}{e["slug"]}/">{"Abstract &amp; details" if e.get("abstract") else "Details"}</a>'
            bibb = f'<button class="pbtn more" onclick="tog(\'{bid}\',this)">BibTeX</button>'
            search = E((e["title"] + " " + " ".join(e["authors"]) + " " + year_str(e) + " " + (e.get("journal") or e.get("book_title") or e.get("series") or "")).lower())
            short = [(l, u, c) for l, u, c in links(e) if c.split()[0] in ("doi", "pdf")]
            sb = "".join(f'<a class="pbtn {c}" href="{E(u)}" target="_blank" rel="noopener">{E(l)}</a>' for l, u, c in short)
            parts.append(f"""<div class="pub" data-s="{search}">
<div class="ptitle"><a href="{BASE}{e['slug']}/">{E(e['title'])}</a></div>
<div class="meta">{authors_html(e['authors'])} &middot; {E(year_str(e))}</div>
<div class="venue">{venue_html(e).rstrip('.')}</div>
<div class="pbtns"><a class="pbtn more" href="{BASE}{e['slug']}/">{"Abstract" if e.get("abstract") else "Details"}</a>{sb}{bibb}</div>
<div class="bibbox" id="{bid}"><pre class="bib" id="{bid}-t">{E(bibtex(e))}</pre><button class="pbtn more" onclick="cp('{bid}-t',this)">Copy BibTeX</button></div>
</div>""")
    page = f"""<!DOCTYPE html>
<html lang="en"><head>
{HEAD_COMMON}
<title>Publications | Kenneth Bunker</title>
<meta name="description" content="Complete list of publications by Kenneth Bunker: peer-reviewed articles, book, book chapters, reviews, datasets and policy briefs on elections, party systems and political institutions in Chile and Latin America.">
<meta name="author" content="Kenneth Bunker">
<link rel="canonical" href="{BASE}">
<meta property="og:title" content="Publications | Kenneth Bunker">
<meta property="og:url" content="{BASE}">
<meta property="og:type" content="website">
<meta property="og:image" content="https://kennethbunker.github.io/img/me2.png">
</head>
<body>
{NAV}
<div id="content"><div class="container">
<h1 style="font-size:1.8rem">Publications</h1>
<p>{total} publications. Click a title for the abstract. Also on <a href="{SCHOLAR_PROFILE}">Google Scholar</a>, <a href="{ORCID}">ORCID</a>, <a href="{RG_PROFILE}">ResearchGate</a> and <a href="{ACADEMIA_PROFILE}">Academia.edu</a>.</p>
<p class="toc small">{''.join(toc)}</p>
<input id="q" type="search" placeholder="Filter by title, coauthor, journal or year" oninput="flt(this.value)">
{''.join(parts)}
<script>
function flt(v){{v=v.toLowerCase().trim();document.querySelectorAll('.pub').forEach(function(p){{p.style.display=!v||p.dataset.s.indexOf(v)>-1?'':'none'}});document.querySelectorAll('h2[id^=sec-]').forEach(function(h){{var n=h.nextElementSibling,any=false;while(n&&n.tagName!=='H2'){{if(n.classList&&n.classList.contains('pub')&&n.style.display!=='none')any=true;n=n.nextElementSibling}}h.style.display=any||!v?'':'none'}})}}
</script>
{FOOT}"""
    open(os.path.join(PUBDIR, "index.html"), "w", encoding="utf-8").write(page)
    return total

# ---------- sitemap ----------
def sitemap():
    today = datetime.date.today().isoformat()
    urls = [SITE + "/", BASE]
    for sub in ["theseus/", "press/", "prensa/", "columns/", "interviews/", "covers/", "contact/", "labdemgob/", "cpld/"]:
        if os.path.exists(os.path.join(ROOT, sub, "index.html")): urls.append(SITE + "/" + sub)
    urls += [BASE + e["slug"] + "/" for e in data]
    for f in sorted(os.listdir(os.path.join(PUBDIR, "pdf"))) if os.path.isdir(os.path.join(PUBDIR, "pdf")) else []:
        if f.endswith(".pdf"): urls.append(BASE + "pdf/" + f)
    xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    xml += "".join(f"  <url><loc>{E(u)}</loc><lastmod>{today}</lastmod></url>\n" for u in urls)
    xml += "</urlset>\n"
    open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8").write(xml)
    return len(urls)

if __name__ == "__main__":
    os.makedirs(os.path.join(PUBDIR, "pdf"), exist_ok=True)
    for e in data: item_page(e)
    n = index_page()
    u = sitemap()
    print(f"Built {n} publication pages + index; sitemap has {u} URLs.")
