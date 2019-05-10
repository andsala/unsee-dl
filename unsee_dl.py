import asyncio

from unsee import unsee_dl

if __name__ == '__main__':
    asyncio.get_event_loop().run_until_complete(unsee_dl.main())
