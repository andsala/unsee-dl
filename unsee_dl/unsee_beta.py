import logging
from pprint import pprint

import aiohttp

from unsee_dl.unsee import UnseeImage

_GRAPHQL_URL = 'https://api.unsee.cc/graphql'


async def anonymous_login(session):
    """
    :param session: http session
    :type session: aiohttp.ClientSession
    :return: auth token
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
  user {
    ...UserFragment
    __typename
  }
  __typename
}

fragment UserFragment on User {
  id
  name
  role
  status
  created
  updated
  isEu
  email
  allowInvites
  targetedAds
  __typename
}"""
    }
    async with session.post('https://api.unsee.cc/graphql', json=gql_body) as response:
        content = await response.json()
        return content['data']['login']['token']


async def download_album(album_id, out_path='.', group_album=True):
    """
    Download an album from unsee beta
    :param album_id: album id
    :type album_id: str
    :param out_path: output path
    :type out_path: str
    :param group_album: should images be grouped in folders per album
    :type group_album: bool
    """
    async with aiohttp.ClientSession() as session:
        token = await anonymous_login(session)

        async for album_image in _original_size_images(session, token, album_id):
            image = UnseeImage(album_id, album_image['id'])
            await _download_and_save_image(session, image, album_image['url'], out_path, group_album)


async def _original_size_images(session, auth_token, album_id):
    """
    Get original size image for the album
    :param session: http session
    :type session: aiohttp.ClientSession
    :param auth_token: authorization token
    :type auth_token: str
    :param album_id: unsee album id
    :type album_id: str
    :return: generator with each image in album
    :rtype: Generator
    """
    headers = {
        'authorization': auth_token
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
    async with session.post(_GRAPHQL_URL, json=gql_body, headers=headers) as response:
        content = await response.json()
        album_items = content['data']['getImages']

        print('Found album {} with {} images.'.format(album_id, len(album_items)))

        for thumb in album_items:
            try:
                # Get original size image
                headers = {
                    'authorization': auth_token
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
                async with session.post(_GRAPHQL_URL, json=gql_body, headers=headers) as response:
                    image_big = await response.json()
                    image_big_items = image_big['data']['getImages']

                for image_big in image_big_items:
                    yield image_big
            except Exception as ex:
                logging.warning('Failed writing image from album {}'.format(album_id), exc_info=ex)


async def _download_and_save_image(session, image, image_url, out_path='.', group_album=True):
    """
    Download and save the image
    :param session: http session
    :type session: aiohttp.ClientSession
    :param image: unsee image
    :type image: UnseeImage
    :param image_url: image url
    :type image_url: str
    :param out_path: output path
    :type out_path: str
    :param group_album: should images be grouped in folders per album
    :type group_album: bool
    :return: saved image path
    :rtype: str
    """
    async with session.get(image_url) as response:
        image_path = await image.write_file_from_stream(response.content, out_path, group_album)
        logging.debug('Wrote image {}'.format(image_path))

    return image_path
