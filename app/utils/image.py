import base64


def image_blob_to_base64_html(blob: bytes):
    return "data:image/png;charset=utf-8;base64, " + base64.b64encode(blob).decode("utf-8")
