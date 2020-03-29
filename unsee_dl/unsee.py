from hashlib import sha256
from pathlib import Path


class UnseeImage:

    def __init__(self, album_id, image_id=None):
        self.album_id = album_id
        self.image_id = image_id

    def write_file_from_blob(self, image_data, out_path='.', group_album=False):
        if not self.image_id:
            digest = sha256(image_data).hexdigest()
            self.image_id = '{}_{}'.format(self.album_id, digest[:16])

        file_basename = '{}.jpg'.format(self.image_id)
        out_file_path = self._get_output_file_path(file_basename, out_path, group_album)

        with out_file_path.open('wb') as file:
            file.write(image_data)

        return str(out_file_path)

    async def write_file_from_stream(self, stream, out_path='.', group_album=False, buffer_size=1024):
        """
        Download the image from a stream
        :param stream: source stream
        :type stream: aiohttp.StreamReader
        :param out_path: output path
        :type out_path: str
        :param group_album: should images be grouped in folders per album
        :type group_album: bool
        :param buffer_size: size of the chunk to read
        :type buffer_size: int
        :return: output file path
        :rtype: str
        """
        if not self.image_id:
            raise ValueError("image id not set")

        file_basename = '{}_{}.jpg'.format(self.album_id, self.image_id)
        out_file_path = self._get_output_file_path(file_basename, out_path, group_album)

        with out_file_path.open('wb') as file:
            while True:
                chunk = await stream.read(buffer_size)
                if not chunk:
                    break
                file.write(chunk)

        return str(out_file_path)

    def _get_output_file_path(self, file_basename, out_path='.', group_album=False):
        out_path = Path(out_path)
        if group_album:
            out_path = out_path.joinpath(self.album_id)

        out_path.mkdir(parents=True, exist_ok=True)

        return out_path.joinpath(file_basename)
