import pytest
from database.image_service import ImageService
import os
import tempfile
import shutil

TEST_DIR = "."
IMAGE_URL = "https://filemanager.gupshup.io/fm/wamedia/demobot1/4e735c4f-e010-4779-82bd-251cb5bfac59?fileName="

@pytest.fixture(scope="session")
def image_service():
    tempdir = tempfile.mkdtemp()

    yield ImageService(tempdir)

    shutil.rmtree(tempdir)

def test_fetch_and_store(image_service: ImageService):
    pathName = image_service.fetch_and_store(IMAGE_URL, "testDoc", "123")
    assert os.path.exists(pathName)

def test_zip_folder(image_service: ImageService):
    pathName = image_service.fetch_and_store(IMAGE_URL, "testDoc", "123")
    output_filename = image_service.zip_folder("123")
    assert os.path.exists(output_filename)




