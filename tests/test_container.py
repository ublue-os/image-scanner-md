from ublue_scanner.container import normalize_image


def test_normalize_image():
    assert ("docker.io", "test/test") == normalize_image("test/test")
    assert ("ghcr.io", "test/test") == normalize_image("ghcr.io/test/test")
    assert ("localhost", "test/test") == normalize_image("localhost/test/test")
    assert ("docker.io", "library/test") == normalize_image("test")
