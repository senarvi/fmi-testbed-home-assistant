#!/usr/bin/env python

import requests
import re
import sys

TESTBED_URL = "https://testbed.fmi.fi/"


def download_latest_radar_image():
    # Fetch the webpage.
    response = requests.get(TESTBED_URL)
    if response.status_code != 200:
        print("Failed to fetch the radar animation page.")
        sys.exit(1)

    # Extract the image URLs from the HTML page.
    pattern = r"var\s+anim_images_anim_anim\s+=\s+new\s+Array\s*\(([^)]*)\)"
    match = re.search(pattern, response.text, re.DOTALL)
    if not match:
        print("Could not parse the animation JavaScript.")
        sys.exit(1)
    array_content = match.group(1)
    image_urls = re.findall(r'["\'](.*?)["\']', array_content, re.DOTALL)
    if not image_urls:
        print("No radar images found.")
        sys.exit(1)
    print("Image URLs:")
    print("\n".join(image_urls))

    # Download the latest image.
    latest_image_url = image_urls[0]
    image_response = requests.get(latest_image_url, stream=True)
    if image_response.status_code == 200:
        with open("download.png", "wb") as f:
            for chunk in image_response.iter_content(1024):
                f.write(chunk)
        print("Wrote download.png.")
    else:
        print("Failed to download the radar image.")
        sys.exit(1)


if __name__ == "__main__":
    download_latest_radar_image()
