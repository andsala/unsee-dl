from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse


class UnseeImage:

    def __init__(self, album_id, image_id=None, out_path='.', group_album=False):
        """
        :param album_id: album id
        :param image_id: image id
        :param out_path: output path
        :type out_path: str
        :param group_album: should images be grouped in folders per album
        :type group_album: bool
        """
        self.album_id = album_id
        self.image_id = image_id
        self.out_path = out_path
        self.group_album = group_album

    def write_file_from_blob(self, image_data):
        if not self.image_id:
            digest = sha256(image_data).hexdigest()
            self.image_id = '{}_{}'.format(self.album_id, digest[:16])

        file_basename = '{}.jpg'.format(self.image_id)
        out_file_path = self._get_output_file_path(file_basename)

        with out_file_path.open('wb') as file:
            file.write(image_data)

        return str(out_file_path)

    async def write_file_from_stream(self, stream, buffer_size=1024):
        """
        Download the image from a stream
        :param stream: source stream
        :type stream: aiohttp.StreamReader
        :param buffer_size: size of the chunk to read
        :type buffer_size: int
        :return: output file path
        :rtype: str
        """
        if not self.image_id:
            raise ValueError("image id not set")

        file_basename = '{}_{}.jpg'.format(self.album_id, self.image_id)
        out_file_path = self._get_output_file_path(file_basename)

        with out_file_path.open('wb') as file:
            while True:
                chunk = await stream.read(buffer_size)
                if not chunk:
                    break
                file.write(chunk)

        return str(out_file_path)

    def _get_output_file_path(self, file_basename):
        out_path = Path(self.out_path)
        if self.group_album:
            out_path = out_path.joinpath(self.album_id)

        out_path.mkdir(parents=True, exist_ok=True)

        return out_path.joinpath(file_basename)


def get_album_id_from_url(album_url):
    url = urlparse(album_url)
    if url.netloc in ('', 'unsee.cc'):  # old unsee.cc
        path = [path for path in url.path.split('/') if len(path) > 0]
        if len(path) < 1:
            return None
        return path[0]
    elif url.netloc in ('app.unsee.cc', 'beta-app.unsee.cc'):  # new frontend or beta
        return url.fragment
    return None


def is_beta_album_id(album_id):
    return len(album_id) > 8
