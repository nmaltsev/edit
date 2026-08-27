def extract_image_data(path):
    """
    Extract basic information and EXIF metadata from a JPEG, PNG, or GIF image.

    Returns:
        dict: {
            "file_type": str,
            "width": int,
            "height": int,
            "exif": dict
        }

    Raises:
        ValueError: If the extension is unsupported or the file is invalid.
        OSError: If the file cannot be opened.
    """
    import struct

    extension = path.rsplit(".", 1)[-1].lower()

    if extension not in ("jpeg", "jpg", "png", "gif"):
        raise ValueError(
            f"Unsupported image type: .{extension}. "
            "Expected jpeg, png, or gif."
        )

    with open(path, "rb") as f:
        data = f.read()

    if extension in ("jpeg", "jpg"):
        width, height, exif = _parse_jpeg(data)
        file_type = "jpeg"

    elif extension == "png":
        width, height, exif = _parse_png(data)
        file_type = "png"

    else:  # GIF
        width, height, exif = _parse_gif(data)
        file_type = "gif"

    return {
        "file_type": file_type,
        "width": width,
        "height": height,
        "exif": exif,
    }


def _parse_png(data):
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Invalid PNG file")

    width, height = struct.unpack(">II", data[16:24])

    # PNG does not normally contain EXIF in the same form as JPEG.
    # EXIF can be stored in an eXIf chunk.
    exif = {}

    pos = 8
    while pos + 12 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        chunk_type = data[pos + 4:pos + 8]
        chunk_data = data[pos + 8:pos + 8 + length]

        if chunk_type == b"eXIf":
            exif = _parse_tiff_exif(chunk_data)
            break

        pos += 12 + length

    return width, height, exif


def _parse_gif(data):
    if data[:6] not in (b"GIF87a", b"GIF89a"):
        raise ValueError("Invalid GIF file")

    width, height = struct.unpack("<HH", data[6:10])

    # GIF has no standard EXIF structure.
    # Some files may contain application-specific metadata, but
    # there is no standard EXIF block to decode here.
    return width, height, {}


def _parse_jpeg(data):
    if data[:2] != b"\xff\xd8":
        raise ValueError("Invalid JPEG file")

    pos = 2
    exif = {}
    width = height = None

    while pos < len(data):
        # Find the beginning of a JPEG marker.
        if data[pos] != 0xFF:
            pos += 1
            continue

        while pos < len(data) and data[pos] == 0xFF:
            pos += 1

        if pos >= len(data):
            break

        marker = data[pos]
        pos += 1

        # End of image / start of scan.
        if marker in (0xD9, 0xDA):
            break

        # Standalone markers don't have a length.
        if marker in range(0xD0, 0xD8):
            continue

        if pos + 2 > len(data):
            break

        segment_length = struct.unpack(">H", data[pos:pos + 2])[0]

        if segment_length < 2 or pos + segment_length > len(data):
            raise ValueError("Invalid JPEG segment")

        segment = data[pos + 2:pos + segment_length]

        # APP1 can contain EXIF.
        if marker == 0xE1 and segment.startswith(b"Exif\x00\x00"):
            exif = _parse_tiff_exif(segment[6:])

        # SOF markers contain image dimensions.
        if marker in (
            0xC0, 0xC1, 0xC2, 0xC3,
            0xC5, 0xC6, 0xC7,
            0xC9, 0xCA, 0xCB,
            0xCD, 0xCE, 0xCF,
        ):
            if len(segment) >= 5:
                height, width = struct.unpack(">HH", segment[1:5])

        pos += segment_length

    if width is None or height is None:
        raise ValueError("Could not determine JPEG dimensions")

    return width, height, exif


def _parse_tiff_exif(data):
    """
    Minimal TIFF/EXIF parser.

    Supports the common EXIF TIFF types and recursively follows
    EXIF/GPS IFD pointers.
    """
    import struct

    if len(data) < 8:
        return {}

    byte_order = data[:2]

    if byte_order == b"II":
        endian = "<"
    elif byte_order == b"MM":
        endian = ">"
    else:
        return {}

    magic = struct.unpack_from(endian + "H", data, 2)[0]
    if magic != 42:
        return {}

    ifd_offset = struct.unpack_from(endian + "I", data, 4)[0]

    type_sizes = {
        1: 1,  # BYTE
        2: 1,  # ASCII
        3: 2,  # SHORT
        4: 4,  # LONG
        5: 8,  # RATIONAL
        7: 1,  # UNDEFINED
        9: 4,  # SLONG
        10: 8,  # SRATIONAL
    }

    # Common EXIF tag names.
    tag_names = {
        0x010E: "ImageDescription",
        0x010F: "Make",
        0x0110: "Model",
        0x0112: "Orientation",
        0x011A: "XResolution",
        0x011B: "YResolution",
        0x0128: "ResolutionUnit",
        0x0131: "Software",
        0x0132: "DateTime",
        0x013B: "Artist",
        0x8298: "Copyright",
        0x829A: "ExposureTime",
        0x829D: "FNumber",
        0x8827: "ISOSpeedRatings",
        0x9003: "DateTimeOriginal",
        0x9004: "CreateDate",
        0x9201: "ShutterSpeedValue",
        0x9202: "ApertureValue",
        0x9204: "ExposureCompensation",
        0x9207: "MeteringMode",
        0x9209: "Flash",
        0x920A: "FocalLength",
        0xA001: "ColorSpace",
        0xA002: "PixelXDimension",
        0xA003: "PixelYDimension",
        0xA434: "LensModel",
        0x8825: "GPSInfoIFD",
        0x8769: "ExifIFD",
    }

    def read_values(offset, tag_type, count):
        size = type_sizes.get(tag_type)
        if size is None:
            return None

        total_size = size * count

        if total_size <= 4:
            raw = data[offset:offset + 4][:total_size]
        else:
            if offset + total_size > len(data):
                return None
            raw = data[offset:offset + total_size]

        try:
            if tag_type == 1:
                return list(raw)

            if tag_type == 2:
                return raw.rstrip(b"\x00").decode("utf-8", errors="replace")

            if tag_type == 3:
                return list(struct.unpack(
                    endian + f"{count}H", raw
                ))

            if tag_type == 4:
                return list(struct.unpack(
                    endian + f"{count}I", raw
                ))

            if tag_type == 5:
                return [
                    struct.unpack_from(endian + "II", raw, i * 8)
                    for i in range(count)
                ]

            if tag_type == 7:
                return raw.hex()

            if tag_type == 9:
                return list(struct.unpack(
                    endian + f"{count}i", raw
                ))

            if tag_type == 10:
                return [
                    struct.unpack_from(endian + "ii", raw, i * 8)
                    for i in range(count)
                ]

        except (struct.error, IndexError):
            return None

        return None

    def simplify(value):
        if isinstance(value, list):
            if len(value) == 1:
                return simplify(value[0])
            return [simplify(v) for v in value]

        if isinstance(value, tuple) and len(value) == 2:
            numerator, denominator = value

            if denominator == 0:
                return None

            if numerator % denominator == 0:
                return numerator // denominator

            return numerator / denominator

        return value

    result = {}

    def parse_ifd(offset, visited=None):
        if visited is None:
            visited = set()

        if offset in visited or offset + 2 > len(data):
            return

        visited.add(offset)

        entry_count = struct.unpack_from(
            endian + "H", data, offset
        )[0]

        entries_start = offset + 2

        for i in range(entry_count):
            entry = entries_start + i * 12

            if entry + 12 > len(data):
                break

            tag, tag_type, count = struct.unpack_from(
                endian + "HHI", data, entry
            )

            value_field = entry + 8
            size = type_sizes.get(tag_type)

            if size is None:
                continue

            total_size = size * count

            if total_size <= 4:
                value_offset = value_field
            else:
                value_offset = struct.unpack_from(
                    endian + "I", data, value_field
                )[0]

            values = read_values(value_offset, tag_type, count)

            if values is not None:
                name = tag_names.get(tag, f"Tag_0x{tag:04X}")
                result[name] = simplify(values)

            # Follow EXIF and GPS IFD pointers.
            if tag in (0x8769, 0x8825) and values:
                pointer = values[0] if isinstance(values, list) else values
                if isinstance(pointer, int):
                    parse_ifd(pointer, visited)

    parse_ifd(ifd_offset)

    return result