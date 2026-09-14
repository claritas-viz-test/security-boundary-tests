import unittest

from deep_tests.security_model import BoundaryViolation, normalize_relative_path, validate_outbound_url


class ClaritasDomainSecurityTests(unittest.TestCase):
    def test_renderer_asset_paths_reject_encoded_escape(self) -> None:
        for value in ("assets/%2e%2e/secrets.json", "meshes/%252E%252E/token", "%2e%2E/render.bin"):
            with self.subTest(value=value), self.assertRaises(BoundaryViolation):
                normalize_relative_path(value)

    def test_renderer_fetch_urls_reject_authority_confusion(self) -> None:
        allowed = {"viz.example.test"}
        for value in (
            "//viz.example.test/scene",
            "https://viz.example.test@attacker.invalid/scene",
            "https://attacker.invalid/viz.example.test/scene",
        ):
            with self.subTest(value=value), self.assertRaises(BoundaryViolation):
                validate_outbound_url(value, allowed)


if __name__ == "__main__":
    unittest.main()
