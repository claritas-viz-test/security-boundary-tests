"""Live plot-catalog boundary tests against data-viz-server.rs.

Skipped unless TARGET_API_URL or DATA_VIZ_URL is set so the deterministic
deep suite stays offline. These checks are fail-closed: CSS kits are a closed
allowlist, native exports ignore CSS, titles cannot inject markup, and
gallery stylesheet query params cannot become freeform URLs.
"""

from __future__ import annotations

import json
import os
import unittest
import urllib.error
import urllib.request

LIVE = (os.getenv("TARGET_API_URL") or os.getenv("DATA_VIZ_URL") or "").rstrip("/")
ROWS = [{"x": f"g{index}", "y": value} for index, value in enumerate([12.0, 18.0, 9.0, 22.0])]


def _call(method: str, path: str, payload=None):
    url = LIVE + path
    headers = {"Accept": "application/json"}
    data = None
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as err:
        return err.code, err.read().decode("utf-8")


@unittest.skipUnless(LIVE, "TARGET_API_URL / DATA_VIZ_URL is not set")
class PlotCatalogLiveBoundaries(unittest.TestCase):
    def test_stylesheet_urls_fail_closed_and_are_not_fetched(self) -> None:
        status, raw = _call(
            "POST",
            "/plots/render",
            {
                "mark": "bar-chart",
                "css": "https://evil.example/x.css",
                "x": "x",
                "y": "y",
                "rows": ROWS,
            },
        )
        self.assertEqual(status, 400)
        blob = raw.lower()
        self.assertTrue("css kit" in blob or "unsupported" in blob)
        self.assertNotIn("<link", blob)

    def test_title_cannot_inject_markup_into_svg(self) -> None:
        status, raw = _call(
            "POST",
            "/plots/render",
            {
                "mark": "bar-chart",
                "title": '<script>alert(1)</script> & "q"',
                "x": "x",
                "y": "y",
                "rows": ROWS,
            },
        )
        self.assertEqual(status, 200, raw[:400])
        body = json.loads(raw)
        svg = body.get("svg", "")
        self.assertIn("&lt;script", svg)
        self.assertNotIn("<script", svg.lower())
        self.assertNotIn("javascript:", svg.lower())

    def test_native_export_ignores_css_and_does_not_emit_html(self) -> None:
        status, raw = _call(
            "POST",
            "/plots/export",
            {
                "mark": "bar-chart",
                "target": "flutter",
                "css": "pico",
                "x": "x",
                "y": "y",
                "rows": ROWS,
            },
        )
        self.assertEqual(status, 200, raw[:400])
        body = json.loads(raw)
        self.assertEqual(body.get("surface"), "native")
        self.assertEqual(body.get("cssKit"), "none")
        self.assertIsNone(body.get("stylesheet"))
        dart = body.get("body", "")
        self.assertIn("CustomPainter", dart)
        self.assertNotIn("<svg", dart)
        self.assertNotIn("<html", dart.lower())
        self.assertNotIn("react", dart.lower())

    def test_gallery_rejects_freeform_stylesheet_urls(self) -> None:
        status, raw = _call("GET", "/plots/gallery?css=https://evil.example/x.css")
        self.assertEqual(status, 400)
        blob = raw.lower()
        self.assertTrue("css kit" in blob or "unsupported" in blob)
        self.assertNotIn('<link rel="stylesheet"', blob)

    def test_catalog_json_does_not_advertise_react(self) -> None:
        status, raw = _call("GET", "/plots")
        self.assertEqual(status, 200)
        body = json.loads(raw)
        notes = str(body.get("notes", "")).lower()
        self.assertIn("never react", notes)
        kits = {kit["id"] for kit in body.get("skins", {}).get("cssKits", [])}
        self.assertIn("pico", kits)
        self.assertNotIn("bootstrap", kits)


if __name__ == "__main__":
    unittest.main()
