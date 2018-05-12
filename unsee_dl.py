import sys
import argparse

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException


def get_web_driver():
    opts = Options()
    opts.set_headless(True)
    opts.set_preference("network.cookie.alwaysAcceptSessionCookies", True)
    opts.set_preference("network.cookie.cookieBehavior", 1)

    browser = webdriver.Firefox(firefox_options=opts, log_path='/tmp/geckodriver.log')
    browser.implicitly_wait(10)
    return browser


def unsee_download(driver, image_id, out_path='.'):
    driver.get("https://unsee.cc/{:s}/".format(image_id))

    canvas = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.XPATH, "//canvas[@class='image']"))
    )

    # Remove overlay elements
    driver.execute_script('''
        var chat = document.getElementById("chat");
        chat.parentNode.removeChild(chat);
        
        var report = document.getElementsByClassName("report");
        for (index = report.length - 1; index >= 0; index--) {
            report[index].parentNode.removeChild(report[index]);
        }
        
        var grid = document.getElementsByClassName("toggle_grid");
        for (index = grid.length - 1; index >= 0; index--) {
            grid[index].parentNode.removeChild(grid[index]);
        }
    ''')

    canvas.screenshot("{}/{}.png".format(out_path, image_id))


def main():
    parser = argparse.ArgumentParser(description="unsee.cc downloader")
    parser.add_argument('-o', '--out', action="store", dest="out_dir", type=str, default=".",
                        help="Output directory")
    parser.add_argument('ids', action="store", nargs='+',
                        help="unsee.cc IDs to download")
    args = parser.parse_args(sys.argv[1:])

    driver = None
    try:
        driver = get_web_driver()
    except WebDriverException as err:
        parser.error(err.msg)

    for image_id in args.ids:
        # noinspection PyBroadException
        try:
            print("Downloading {:s}... ".format(image_id), end='', flush=True)
            unsee_download(driver, image_id, args.out_dir)
            print("done", flush=True)
        except Exception:
            print("fail", flush=True)
    driver.quit()


if __name__ == '__main__':
    main()
