import requests
import urllib.request
import os
from typing import List
import shutil
from dotenv import load_dotenv
# class to provide facilites to take an url-link, download the file
# store it on the harddrive, under a location that makes sense.
# Moreover, it should be able to retrieve those files in a way
# that they can be served over api, either individually or as a zip-file

load_dotenv()

def create_zip_folder(target_dir_path: str, output_filename: str):
    shutil.make_archive(output_filename, 'zip', target_dir_path)

def zip_and_stream(filenames: List[str], phone: str):
    """ untested https://stackoverflow.com/questions/61163024/return-multiple-files-from-fastapi """
    zip_subdir = ""
    zip_io = BytesIO()
    with zipfile.ZipFile(zip_io, mode='w', compression=zipfile.ZIP_DEFLATED) as temp_zip:
        for fpath in filenames:
            # Calculate path for file in zip
            fdir, fname = os.path.split(fpath)
            zip_path = os.path.join(zip_subdir, fname)
            # Add file, at correct path
            temp_zip.write((fpath, zip_path))
    return StreamingResponse(
        iter([zip_io.getvalue()]), 
        media_type="application/x-zip-compressed", 
        headers = { "Content-Disposition": f"attachment; filename={phone}_images.zip"}
    )


class ImageService():
    def __init__(self, root_dir = ""):
        self.root_dir = root_dir or "./"
        if not os.path.exists(self.root_dir):
            os.makedirs(self.root_dir)

    def _create_filepath(self, doc_name: str, phone_number: str):
        """ where to store a file, creating user folder if not there """
        user_folder = f"{self.root_dir}/{phone_number}"
        if not os.path.exists(user_folder):
            os.makedirs(user_folder)
        return user_folder + "/" + doc_name

    def fetch_and_store(self, image_url: str, doc_name: str, phone_number: str):
        filepath = self._create_filepath(doc_name, phone_number)

        img_data = requests.get(image_url).content
        with open(filepath, 'wb') as handler:
            handler.write(img_data)

        # urllib.request.urlretrieve(image_url, filepath)

        return filepath

    def load_image(self, doc_name: str, phone_number: str):
        filepath = self._create_filepath(doc_name, phone_number)
        with open(filepath, 'rb') as handler:
            raise NotImplementedError("TODO")

    def zip_folder(self, phone_number: str):
        target_dir_path = os.path.dirname(self._create_filepath("tmp", phone_number))
        output_filename = f"{self.root_dir}/{phone_number}_zipped"
        create_zip_folder(target_dir_path, output_filename)
        return output_filename + ".zip"

ROOT_DIR = '.' #os.getenv("IMAGE_ROOT_DIR")
image_service = ImageService(ROOT_DIR) 
