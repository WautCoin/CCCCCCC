"""
img_import.py — image import utilities for CCCCCCC.

Provides functions to load, validate, and inspect image files using
magic-byte detection.  No third-party dependencies are required.
Supported formats: PNG, JPEG, GIF, BMP, WEBP, TIFF.
"""

import os
import struct


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

SUPPORTED_TYPES = {"png", "jpeg", "gif", "bmp", "webp", "tiff"}


def import_image(path):
    """Load an image from *path* and return an :class:`ImageInfo` object.

    :param path: Path to the image file (str or os.PathLike).
    :raises FileNotFoundError: If *path* does not exist.
    :raises ValueError: If the file is not a recognised image format.
    :returns: :class:`ImageInfo`
    """
    path = os.fspath(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"No such file: {path!r}")

    image_type = _detect_type(path)
    if image_type is None:
        raise ValueError(f"Unrecognised image format for file: {path!r}")

    width, height = _read_dimensions(path, image_type)
    size = os.path.getsize(path)

    return ImageInfo(
        path=os.path.abspath(path),
        image_type=image_type,
        width=width,
        height=height,
        file_size=size,
    )


def is_image(path):
    """Return ``True`` if *path* points to a recognised image file."""
    try:
        return _detect_type(os.fspath(path)) is not None
    except OSError:
        return False


# ---------------------------------------------------------------------------
# Data class
# ---------------------------------------------------------------------------

class ImageInfo:
    """Holds metadata about an imported image."""

    __slots__ = ("path", "image_type", "width", "height", "file_size")

    def __init__(self, path, image_type, width, height, file_size):
        self.path = path
        self.image_type = image_type
        self.width = width
        self.height = height
        self.file_size = file_size

    def __repr__(self):
        return (
            f"ImageInfo(path={self.path!r}, type={self.image_type!r}, "
            f"width={self.width}, height={self.height}, "
            f"file_size={self.file_size})"
        )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _detect_type(path):
    """Return a lowercase type string or ``None`` using magic-byte detection."""
    try:
        with open(path, "rb") as fh:
            header = fh.read(16)
    except OSError:
        return None

    if header[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if header[:3] == b"\xff\xd8\xff":
        return "jpeg"
    if header[:6] in (b"GIF87a", b"GIF89a"):
        return "gif"
    if header[:2] == b"BM":
        return "bmp"
    # OS/2 bitmap variants share a common 2-byte signature prefix.
    if header[:2] in (b"BA", b"CI", b"CP", b"IC", b"PT"):
        return "bmp"
    if header[:4] == b"RIFF" and header[8:12] == b"WEBP":
        return "webp"
    if header[:4] in (b"MM\x00*", b"II*\x00", b"MM\x00+", b"II+\x00"):
        return "tiff"

    return None


def _read_dimensions(path, image_type):
    """Return (width, height) for common formats using only stdlib."""
    try:
        with open(path, "rb") as fh:
            data = fh.read(26)
    except OSError:
        return (None, None)

    if image_type == "png":
        if len(data) >= 24:
            w, h = struct.unpack(">II", data[16:24])
            return (w, h)

    elif image_type in ("jpeg", "jpg"):
        return _jpeg_dimensions(path)

    elif image_type == "gif":
        if len(data) >= 10:
            w, h = struct.unpack("<HH", data[6:10])
            return (w, h)

    elif image_type == "bmp":
        # BITMAPINFOHEADER: width at offset 18 (4 bytes), height at 22 (4 bytes)
        if len(data) >= 26:
            w, h = struct.unpack("<ii", data[18:26])
            return (abs(w), abs(h))

    elif image_type == "webp":
        return _webp_dimensions(path)

    return (None, None)


def _jpeg_dimensions(path):
    """Parse JPEG SOF markers to extract dimensions."""
    try:
        with open(path, "rb") as fh:
            fh.read(2)  # SOI marker
            while True:
                marker = fh.read(2)
                if len(marker) < 2:
                    break
                if marker[0] != 0xFF:
                    break
                code = marker[1]
                # SOF0–SOF3, SOF5–SOF7 markers contain image dimensions.
                if code in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7):
                    fh.read(3)  # length + precision
                    h, w = struct.unpack(">HH", fh.read(4))
                    return (w, h)
                length = struct.unpack(">H", fh.read(2))[0]
                fh.read(length - 2)
    except (OSError, struct.error):
        pass
    return (None, None)


def _webp_dimensions(path):
    """Extract dimensions from a WEBP file."""
    try:
        with open(path, "rb") as fh:
            fh.read(12)  # RIFF header
            chunk = fh.read(4)
            if chunk == b"VP8 ":
                fh.read(6)
                raw = fh.read(4)
                w = (struct.unpack("<H", raw[:2])[0] & 0x3FFF) + 1
                h = (struct.unpack("<H", raw[2:])[0] & 0x3FFF) + 1
                return (w, h)
            elif chunk == b"VP8L":
                fh.read(5)
                bits = struct.unpack("<I", fh.read(4))[0]
                w = (bits & 0x3FFF) + 1
                h = ((bits >> 14) & 0x3FFF) + 1
                return (w, h)
    except (OSError, struct.error):
        pass
    return (None, None)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _main():
    import sys

    if len(sys.argv) < 2:
        print("Usage: python img_import.py <image> [image ...]")
        sys.exit(1)

    any_error = False
    for arg in sys.argv[1:]:
        try:
            info = import_image(arg)
            dims = (
                f"{info.width}x{info.height}"
                if info.width is not None
                else "unknown dimensions"
            )
            print(f"{arg}: {info.image_type.upper()}  {dims}  {info.file_size} bytes")
        except (FileNotFoundError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            any_error = True

    sys.exit(1 if any_error else 0)


if __name__ == "__main__":
    _main()
