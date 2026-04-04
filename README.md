# CCCCCCC

CCCCCCC is a public domain project. See the [LICENSE](LICENSE) for details.

## Image Import

`img_import.py` provides lightweight image import utilities that work with
the Python standard library (no third-party dependencies required).

### API

```python
from img_import import import_image, is_image

# Load metadata for a single image
info = import_image("photo.png")
print(info.image_type)   # e.g. "png"
print(info.width)        # pixel width
print(info.height)       # pixel height
print(info.file_size)    # bytes on disk
print(info.path)         # absolute path

# Quick check
is_image("photo.png")    # True / False
```

### CLI

```
python img_import.py photo.png banner.jpg
# photo.png: PNG  800x600  45321 bytes
# banner.jpg: JPEG  1920x1080  234567 bytes
```

Supported formats: PNG, JPEG, GIF, BMP, WEBP, TIFF.
