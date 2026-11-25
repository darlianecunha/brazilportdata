"""Regression tests for the static home page of brazilportdata.com.

The site has no build step and no JavaScript, so the risk sits in the
hand-edited content of index.html: the hand-typed ANTAQ figures in the
"Brazil at a Glance" strip, the project cards, in-page anchors, SEO metadata
and the files that must agree with the canonical URL.

Run with:  python -m unittest discover -s tests -v
Standard library only.
"""

import json
import re
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
CANONICAL = "https://www.brazilportdata.com/"


class PageParser(HTMLParser):
    """Collects the elements the tests need in a single pass."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids = []
        self.links = []          # dicts of <a> attributes
        self.meta = {}           # name/property -> content
        self.link_tags = []      # dicts of <link> attributes
        self.jsonld = []
        self.imgs = []
        self._in_jsonld = False
        self._buf = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if "id" in a:
            self.ids.append(a["id"])
        if tag == "a":
            self.links.append(a)
        elif tag == "meta":
            key = a.get("name") or a.get("property")
            if key:
                self.meta[key] = a.get("content", "")
        elif tag == "link":
            self.link_tags.append(a)
        elif tag == "img":
            self.imgs.append(a)
        elif tag == "script" and a.get("type") == "application/ld+json":
            self._in_jsonld = True
            self._buf = []

    def handle_endtag(self, tag):
        if tag == "script" and self._in_jsonld:
            self.jsonld.append("".join(self._buf))
            self._in_jsonld = False

    def handle_data(self, data):
        if self._in_jsonld:
            self._buf.append(data)


def text_of(html_fragment):
    """Strip tags and decode entities from a fragment."""
    p = HTMLParser(convert_charrefs=True)
    out = []
    p.handle_data = out.append
    p.feed(html_fragment)
    p.close()
    return re.sub(r"\s+", " ", "".join(out)).strip()


def num(s):
    return float(s.replace(",", ""))


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.html = INDEX.read_text(encoding="utf-8")
        cls.page = PageParser()
        cls.page.feed(cls.html)
        cls.page.close()


class TestStructuredData(Base):
    def test_jsonld_parses_and_has_expected_entities(self):
        self.assertEqual(len(self.page.jsonld), 1)
        data = json.loads(self.page.jsonld[0])
        types = {node["@type"] for node in data["@graph"]}
        self.assertEqual(types, {"WebSite", "Person", "Organization"})

    def test_jsonld_references_resolve(self):
        data = json.loads(self.page.jsonld[0])
        ids = {node["@id"] for node in data["@graph"]}
        for node in data["@graph"]:
            for value in node.values():
                if isinstance(value, dict) and "@id" in value:
                    self.assertIn(value["@id"], ids)

    def test_jsonld_urls_match_canonical(self):
        data = json.loads(self.page.jsonld[0])
        for node in data["@graph"]:
            if node["@type"] in ("WebSite", "Organization"):
                self.assertEqual(node["url"], CANONICAL)


class TestMetadata(Base):
    def test_canonical_and_og_url(self):
        canon = [l["href"] for l in self.page.link_tags if l.get("rel") == "canonical"]
        self.assertEqual(canon, [CANONICAL])
        self.assertEqual(self.page.meta.get("og:url"), CANONICAL)

    def test_required_social_meta_present_and_non_empty(self):
        for key in ("description", "og:title", "og:description", "og:image",
                    "twitter:card", "twitter:title", "twitter:image"):
            self.assertTrue(self.page.meta.get(key), f"missing or empty: {key}")

    def test_description_lengths_fit_search_snippets(self):
        self.assertLessEqual(len(self.page.meta["description"]), 200)
        self.assertLessEqual(len(self.page.meta["og:description"]), 200)

    def test_social_images_exist_in_repo(self):
        for key in ("og:image", "twitter:image"):
            path = urlparse(self.page.meta[key]).path.lstrip("/")
            self.assertTrue((ROOT / path).is_file(), f"{key} -> {path} not in repo")

    def test_og_image_declared_size_matches_file(self):
        data = (ROOT / "og-image.png").read_bytes()
        self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
        width = int.from_bytes(data[16:20], "big")
        height = int.from_bytes(data[20:24], "big")
        self.assertEqual(str(width), self.page.meta["og:image:width"])
        self.assertEqual(str(height), self.page.meta["og:image:height"])

    def test_favicon_exists(self):
        icons = [l["href"] for l in self.page.link_tags if l.get("rel") == "icon"]
        self.assertTrue(icons)
        for href in icons:
            self.assertTrue((ROOT / href.lstrip("/")).is_file())


class TestLinks(Base):
    def test_ids_are_unique(self):
        dupes = {i for i in self.page.ids if self.page.ids.count(i) > 1}
        self.assertFalse(dupes, f"duplicate ids: {dupes}")

    def test_in_page_anchors_resolve(self):
        ids = set(self.page.ids)
        for a in self.page.links:
            href = a.get("href", "")
            if href.startswith("#"):
                self.assertIn(href[1:], ids, f"broken anchor {href}")

    def test_external_links_are_https(self):
        for a in self.page.links:
            href = a.get("href", "")
            if href.startswith(("#", "mailto:")):
                continue
            self.assertTrue(href.startswith("https://"), f"not https: {href}")
            self.assertTrue(urlparse(href).netloc, f"no host: {href}")

    def test_new_tab_links_use_noopener(self):
        for a in self.page.links:
            if a.get("target") == "_blank":
                self.assertIn("noopener", a.get("rel", ""), a.get("href"))

    def test_mailto_matches_structured_data_email(self):
        data = json.loads(self.page.jsonld[0])
        email = next(n["email"] for n in data["@graph"] if n["@type"] == "Person")
        mailtos = {a["href"][7:] for a in self.page.links
                   if a.get("href", "").startswith("mailto:")}
        self.assertEqual(mailtos, {email})

    def test_images_have_alt_text(self):
        for img in self.page.imgs:
            self.assertTrue(img.get("alt"), f"img without alt: {img.get('src')}")


class TestProjectCards(Base):
    def setUp(self):
        self.ranks = re.findall(r'<div class="rkb">(\d+)</div>', self.html)
        self.codes = re.findall(r'<div class="idp">([A-Z0-9]+)-(\d+)</div>', self.html)

    def test_cards_are_numbered_consecutively(self):
        expected = [f"{i:02d}" for i in range(1, len(self.ranks) + 1)]
        self.assertEqual(self.ranks, expected)

    def test_card_codes_match_card_numbers(self):
        self.assertEqual(len(self.codes), len(self.ranks))
        for (prefix, code), rank in zip(self.codes, self.ranks):
            self.assertEqual(int(code), int(rank), f"{prefix}-{code} on card {rank}")

    def test_card_codes_are_unique(self):
        prefixes = [p for p, _ in self.codes]
        self.assertEqual(len(prefixes), len(set(prefixes)))

    def test_every_card_has_a_cta_link(self):
        cards = re.split(r'<div class="sc[ "]', self.html)[1:]
        self.assertEqual(len(cards), len(self.ranks))
        for i, card in enumerate(cards, 1):
            self.assertRegex(card, r'href="https://', f"card {i:02d} has no link")

    def test_readme_card_count_matches_page(self):
        words = {"nine": 9, "ten": 10, "eleven": 11, "twelve": 12,
                 "thirteen": 13, "fourteen": 14, "fifteen": 15}
        readme = (ROOT / "README.md").read_text(encoding="utf-8").lower()
        m = re.search(r"\b(" + "|".join(words) + r"|\d+) project cards", readme)
        self.assertIsNotNone(m, "README no longer states the card count")
        stated = words.get(m.group(1)) or int(m.group(1))
        self.assertEqual(stated, len(self.ranks))


class TestGlanceFigures(Base):
    """Internal consistency of the hand-typed ANTAQ numbers."""

    def setUp(self):
        m = re.search(r'<section[^>]*id="glance".*?</section>', self.html, re.S)
        self.assertIsNotNone(m, "glance section missing")
        self.glance = m.group(0)
        self.kpis = {}
        for block in re.findall(r'<div class="kpi">(.*?)</div>\s*</div>', self.glance, re.S):
            lbl = text_of(re.search(r'kpi-lbl">(.*?)</div>', block, re.S).group(1))
            self.kpis[lbl] = text_of(block)
        rank_html = re.search(r'class="glance-rank">(.*?)</div>', self.glance, re.S).group(1)
        self.rank_text = text_of(rank_html)
        self.ranking = [(name.strip(), num(v)) for name, v in re.findall(
            r"<strong>([^<]+?)\s([\d.,]+)</strong>", rank_html)]
        self.ranking = [(text_of(n), v) for n, v in self.ranking]

    def kpi_value(self, label):
        m = re.match(r".*?([\d.,]+)", self.kpis[label][len(label):])
        return num(m.group(1))

    def test_six_kpis_present(self):
        self.assertEqual(len(self.kpis), 6, list(self.kpis))

    def test_ranking_is_in_descending_order(self):
        values = [v for _, v in self.ranking]
        self.assertGreaterEqual(len(values), 3)
        self.assertEqual(values, sorted(values, reverse=True))

    def test_largest_complex_kpi_matches_ranking(self):
        kpi = self.kpis["Largest port complex"]
        top_name, top_val = self.ranking[0]
        self.assertIn(top_name, kpi)
        self.assertIn(f"{top_val:.1f} Mt", kpi)
        second_name, second_val = self.ranking[1]
        self.assertIn(f"{second_name} {second_val:.1f} Mt", kpi)

    def test_complexes_do_not_exceed_national_total(self):
        total = self.kpi_value("Cargo handled 2025")
        self.assertLess(sum(v for _, v in self.ranking), total)

    def test_container_share_matches_tonnage(self):
        total = self.kpi_value("Cargo handled 2025")
        mt = num(re.search(r"([\d.,]+) Mt", self.kpis["Containers 2025"]).group(1))
        share = int(re.search(r"containers (\d+)%", self.rank_text).group(1))
        self.assertAlmostEqual(mt / total * 100, share, delta=0.6)

    def test_cargo_mix_shares_are_plausible(self):
        shares = [int(s) for s in re.findall(r"(\d+)%", self.rank_text.split("Cargo 2025:")[1])]
        self.assertTrue(shares)
        self.assertLessEqual(sum(shares), 100)
        self.assertEqual(shares, sorted(shares, reverse=True))

    def test_top_partner_share_is_below_total(self):
        kpi = self.kpis["Top export partner"]
        mt = num(re.search(r"([\d.,]+) Mt", kpi).group(1))
        share = int(re.search(r"(\d+)% of exports", kpi).group(1))
        implied_exports = mt / (share / 100)
        self.assertLess(implied_exports, self.kpi_value("Cargo handled 2025"))

    def test_strip_year_matches_kpi_labels(self):
        year = re.search(r"ANTAQ (\d{4})", text_of(self.glance)).group(1)
        for label in ("Cargo handled", "Containers", "Berthings"):
            self.assertIn(f"{label} {year}", self.kpis)

    def test_source_note_names_antaq_and_dates(self):
        note = text_of(re.search(r'class="glance-note">(.*?)</div>', self.glance, re.S).group(1))
        self.assertIn("ANTAQ", note)
        self.assertRegex(note, r"Data to \w+ \d{4}")
        self.assertRegex(note, r"extracted \d{1,2} \w+ \d{4}")

    def test_meta_description_period_matches_source_note(self):
        """The SEO description must not advertise an older range than the data."""
        note = text_of(re.search(r'class="glance-note">(.*?)</div>', self.glance, re.S).group(1))
        data_year = int(re.search(r"Data to \w+ (\d{4})", note).group(1))
        m = re.search(r"ANTAQ (\d{4})-(\d{4})", self.page.meta["description"])
        if m:
            self.assertGreaterEqual(int(m.group(2)), data_year,
                                    "meta description year range is behind the data")


class TestSiteFiles(Base):
    def test_cname_matches_canonical_host(self):
        cname = (ROOT / "CNAME").read_text().strip()
        self.assertEqual(cname, urlparse(CANONICAL).netloc)

    def test_sitemap_is_valid_and_lists_canonical(self):
        tree = ET.parse(ROOT / "sitemap.xml")
        ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
        locs = [e.text.strip() for e in tree.getroot().findall("s:url/s:loc", ns)]
        self.assertIn(CANONICAL, locs)
        for lastmod in tree.getroot().findall("s:url/s:lastmod", ns):
            self.assertRegex(lastmod.text.strip(), r"^\d{4}-\d{2}-\d{2}$")

    def test_robots_points_to_sitemap(self):
        robots = (ROOT / "robots.txt").read_text()
        self.assertIn(f"Sitemap: {CANONICAL}sitemap.xml", robots)
        self.assertNotRegex(robots, r"(?m)^Disallow:\s*/\s*$")


if __name__ == "__main__":
    unittest.main()
