from utils.image import image_blob_to_base64_html

test_image_binary = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\n\x00\x00\x00\n\x08\x02\x00\x00\x00\x02PX\xea"
    b"\x00\x00\x00\x01sRGB\x00\xae\xce\x1c\xe9\x00\x00\x00\x04gAMA\x00\x00\xb1\x8f\x0b\xfca\x05\x00"
    b"\x00\x00\tpHYs\x00\x00\x0e\xc3\x00\x00\x0e\xc3\x01\xc7o\xa8d\x00\x00\x00\x13IDAT(Scx+\xa3\x82"
    b"\x07\x8dJcA2*\x00\x84\x7fu\x95D\x8d\x05\xf0\x00\x00\x00\x00IEND\xaeB`\x82"
)

test_image_html = (
    "data:image/png;charset=utf-8;base64, iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAIAAAACUFjqAAAAAXNSR0IArs4c6"
    "QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAATSURBVChTY3gro4IHjUpjQTIqAIR/dZVEjQXwAAAAAEl"
    "FTkSuQmCC"
)


def test_image_blob_to_base64_html():
    assert test_image_html == image_blob_to_base64_html(test_image_binary)
