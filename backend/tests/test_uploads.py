import re
from io import BytesIO

import pytest
from PIL import Image

from app.config import get_config
from app.services.uploads import MAX_UPLOAD_BYTES

from .conftest import log_in


@pytest.fixture(autouse=True)
def upload_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(get_config(), "upload_dir", tmp_path)
    return tmp_path


@pytest.fixture
def fan(client, make_user):
    user = make_user("fan@example.com")
    log_in(client, "fan@example.com")
    return user


def image_bytes(fmt="PNG", size=(64, 48), **save):
    out = BytesIO()
    Image.new("RGB", size, (200, 30, 30)).save(out, fmt, **save)
    return out.getvalue()


def upload(client, data, name="logo.png"):
    return client.post("/api/uploads", content=data, headers={"X-Filename": name, "Content-Type": "application/octet-stream"})


def test_guest_cannot_upload(client):
    assert upload(client, image_bytes()).status_code == 401


def test_upload_is_reencoded_as_webp_under_a_random_name(client, fan, upload_dir):
    res = upload(client, image_bytes(), name="my logo.PNG")
    assert res.status_code == 201
    (stored,) = list(upload_dir.iterdir())
    assert re.fullmatch(r"[0-9a-f]{32}\.webp", stored.name)  # nothing of the client's filename
    assert Image.open(stored).format == "WEBP"
    assert res.json()["size_bytes"] == stored.stat().st_size
    served = client.get(f"/api/uploads/{res.json()['id']}")
    assert served.status_code == 200 and served.headers["content-type"] == "image/webp"
    assert served.headers["x-content-type-options"] == "nosniff" and served.content == stored.read_bytes()


def test_metadata_is_stripped_and_big_images_shrink(client, fan, upload_dir):
    exif = Image.Exif()
    exif[0x010E] = "SECRET-DESCRIPTION"
    exif[0x013B] = "SECRET-AUTHOR"
    assert upload(client, image_bytes("JPEG", (1600, 900), exif=exif), "photo.jpg").status_code == 201
    stored = next(upload_dir.iterdir())
    raw = stored.read_bytes()
    assert b"SECRET" not in raw and not Image.open(stored).getexif()
    assert max(Image.open(stored).size) == 512


def test_bytes_appended_to_an_image_do_not_survive(client, fan, upload_dir):
    payload = b"<?php system($_GET['c']); ?>MARKER-PAYLOAD"
    assert upload(client, image_bytes() + payload).status_code == 201
    raw = next(upload_dir.iterdir()).read_bytes()
    assert b"MARKER-PAYLOAD" not in raw and b"<?php" not in raw


def test_executable_renamed_to_png_is_rejected(client, fan, upload_dir, activity):
    exe = b"MZ\x90\x00\x03\x00\x00\x00" + b"\x00" * 200
    res = upload(client, exe, "logo.png")
    assert res.status_code == 422 and "not a valid image" in res.json()["detail"]
    assert list(upload_dir.iterdir()) == []
    assert activity.lines[-1][0] == "upload_rejected"


@pytest.mark.parametrize("name", ["logo.gif", "logo.svg", "logo.php", "logo", "logo.png.exe", ""])
def test_only_whitelisted_extensions_pass(client, fan, name):
    assert upload(client, image_bytes(), name).status_code == 422


def test_extension_must_match_the_real_format(client, fan):
    assert upload(client, image_bytes("PNG"), "logo.jpg").status_code == 422
    assert upload(client, image_bytes("GIF"), "logo.png").status_code == 422  # a format outside the whitelist
    assert upload(client, image_bytes("JPEG"), "logo.jpeg").status_code == 201
    assert upload(client, image_bytes("WEBP"), "logo.webp").status_code == 201


def test_broken_and_oversized_pixel_images_are_rejected(client, fan):
    assert upload(client, image_bytes()[:60], "logo.png").status_code == 422  # truncated
    huge = image_bytes("PNG", (6000, 6000))  # a few KB on the wire, 36 megapixels decoded
    assert len(huge) < MAX_UPLOAD_BYTES
    res = upload(client, huge)
    assert res.status_code == 422 and "too large" in res.json()["detail"]


def test_file_over_12_mb_is_refused_by_its_declared_length(client, fan):
    res = upload(client, b"\0" * (MAX_UPLOAD_BYTES + 1))
    assert res.status_code == 413 and res.json()["code"] == "too_large"


def test_file_over_12_mb_is_refused_without_a_length_header(client, fan):
    def chunks():  # no Content-Length: only the byte count while reading can catch this
        for _ in range(13):
            yield b"\0" * (1024 * 1024)

    res = client.post("/api/uploads", content=chunks(), headers={"X-Filename": "logo.png"})
    assert res.status_code == 413


def test_only_the_owner_can_fetch_an_upload(client, fan, make_user):
    upload_id = upload(client, image_bytes()).json()["id"]
    make_user("other@example.com")
    log_in(client, "other@example.com")
    assert client.get(f"/api/uploads/{upload_id}").status_code == 403
    assert client.get("/api/uploads/999999").status_code == 404
    client.post("/api/auth/logout")
    assert client.get(f"/api/uploads/{upload_id}").status_code == 401
