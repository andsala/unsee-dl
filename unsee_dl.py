import asyncio

from unsee import unsee_dl


def main():
    asyncio.get_event_loop().run_until_complete(unsee_dl.main())


if __name__ == '__main__':
    main()
