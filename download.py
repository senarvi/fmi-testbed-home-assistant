#!/usr/bin/env python

import requests
from bs4 import BeautifulSoup
import re

TESTBED_URL = "https://testbed.fmi.fi/"


def download_latest_radar_image():
    # Fetch the webpage.
    response = requests.get(TESTBED_URL)
    if response.status_code != 200:
        print("Failed to fetch the radar page")
        return

    # Parse HTML to extract image URLs.
    soup = BeautifulSoup(response.text, "html.parser")
    script_tag = soup.find("script", string=lambda s: "anim_images_anim_anim" in str(s))

    if not script_tag:
        print("Could not find image URLs in the page")
        return

    # Extract the latest image URL (first in the array).
    script_text = script_tag.string
    image_urls = []

    # Extract URLs from the JavaScript array.
    pattern = r"var\s+anim_images_anim_anim\s+=\s+new\s+Array\s*\(([^)]*)\)"
    match = re.search(pattern, script_text, re.DOTALL)
    if not match:
        print("Could not parse the animation JavaScript")
        return
    array_content = match.group(1)
    image_urls = re.findall(r'["\'](.*?)["\']', array_content, re.DOTALL)
    print("Image URLs:")
    print("\n".join(image_urls))

    for line in []:  # script_text.split('\n'):
        if "anim_images_anim_anim" in line and "new Array(" in line:
            print("XXX", line)
            urls_part = line.split("new Array(")[1].split(")")[0]
            image_urls = [url.strip('"') for url in urls_part.split(",")]
            break

    if not image_urls:
        print("No radar images found")
        return

    latest_image_url = image_urls[0]  # First URL is the latest.

    # Download the image.
    image_response = requests.get(latest_image_url, stream=True)
    if image_response.status_code == 200:
        with open("download.png", "wb") as f:
            for chunk in image_response.iter_content(1024):
                f.write(chunk)
    else:
        print("Failed to download the radar image")


if __name__ == "__main__":
    download_latest_radar_image()
