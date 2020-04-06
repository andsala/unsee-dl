import logging

import aiohttp

from unsee_dl.unsee import UnseeImage

_GRAPHQL_URL = 'https://api.unsee.cc/graphql'


class Client:

    def __init__(self, session=None, out_path='.', group_album=True):
        """
        :param session: http session
        :type session: aiohttp.ClientSession
        :param out_path: output path
        :type out_path: str
        :param group_album: should images be grouped in folders per album
        :type group_album: bool
        """
        if session:
            self.session = session
        else:
            self.session = aiohttp.ClientSession()
        self.out_path = out_path
        self.group_album = group_album
        self.token = None

    async def __aenter__(self):
        self._did_enter_with = True
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session and self._did_enter_with:
            await self.session.close()

    async def anonymous_login(self):
        """
        Login with an anonymous token
        """
        gql_body = {
            'operationName': 'loginAnonymous',
            'variables': {},
            'query': """
    mutation loginAnonymous {
      login {
        ...AuthPayloadFragment
        __typename
      }
    }
    
    fragment AuthPayloadFragment on AuthPayload {
      token
      tokenRefresh
      __typename
    }"""
        }
        async with self.session.post('https://api.unsee.cc/graphql', json=gql_body) as response:
            content = await response.json()
            login_data = content['data']['login']
            self.token = login_data['token']

    async def download_album(self, album_id):
        """
        Download an album from unsee beta
        :param album_id: album id
        :type album_id: str
        """
        async for album_image in self._original_size_images(album_id):
            image = UnseeImage(album_id, album_image['id'], self.out_path, self.group_album)
            await self._download_and_save_image(image, album_image['url'])

    async def _original_size_images(self, album_id):
        """
        Get original size image for the album
        :param album_id: unsee album id
        :type album_id: str
        :return: generator with each image in album
        :rtype: Generator
        """
        headers = {
            'authorization': self.token
        }
        gql_body = {
            'operationName': 'getImages',
            'variables': {
                'filter': {
                    'chat': album_id
                },
                'pagination': {
                    'offset': 0
                }
            },
            'query': """
    query getImages($filter: ImageFilter!, $pagination: Pagination) {
    getImages(filter: $filter, pagination: $pagination) {
     id
     url
     __typename
    }
    }"""
        }
        async with self.session.post(_GRAPHQL_URL, json=gql_body, headers=headers) as response:
            content = await response.json()
            album_items = content['data']['getImages']

            if not album_items or len(album_items) <= 0:
                print(f"No images found in album {album_id}")
                return

            print('Found album {} with {} images.'.format(album_id, len(album_items)))

            for thumb in album_items:
                try:
                    # Get original size image
                    headers = {
                        'authorization': self.token
                    }
                    gql_body = {
                        'operationName': 'getImagesBig',
                        'variables': {
                            'filter': {
                                'chat': album_id,
                                'id': thumb['id']
                            }
                        },
                        'query': """
            query getImagesBig($filter: ImageFilter!) {
              getImages(filter: $filter) {
                id
                url(size: big)
                __typename
              }
            }"""
                    }
                    async with self.session.post(_GRAPHQL_URL, json=gql_body, headers=headers) as response:
                        image_big = await response.json()
                        image_big_items = image_big['data']['getImages']

                    for image_big in image_big_items:
                        yield image_big
                except Exception as ex:
                    logging.warning('Failed writing image from album {}'.format(album_id), exc_info=ex)

    async def _download_and_save_image(self, image, image_url):
        """
        Download and save the image
        :param image: unsee image
        :type image: UnseeImage
        :param image_url: image url
        :type image_url: str
        :return: saved image path
        :rtype: str
        """
        async with self.session.get(image_url) as response:
            image_path = await image.write_file_from_stream(response.content)
            logging.debug('Wrote image {}'.format(image_path))

        return image_path
