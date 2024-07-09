# Standard Library imports
from itertools import count

# External imports
import cv2
import numpy as np
from controller import Robot, Display

# Local imports
from scanner import get_warped_document, resize_and_letter_box, segment_by_color


TIME_STEP = 100
HSV_LOW_RANGE = np.array([27, 0, 66])
HSV_UP_RANGE = np.array([180, 38, 255])
SAVE_TO_DISK = False


def counter(_count=count(1)):
    """https://stackoverflow.com/a/54715096/1253729"""
    return next(_count)


def save_image(image):
    cv2.imwrite(f"image_{counter()}.jpg", image)


def initialize():
    robot = Robot()

    camera = robot.getDevice("camera")
    camera.enable(100)

    display = robot.getDevice("image display")

    return robot, camera, display


def webots_image_to_numpy(im, h, w):
    return np.frombuffer(im, dtype=np.uint8).reshape((h, w, 4))


def display_numpy_image(im, display, display_width, display_height):
    """Display a Numpy image in a Webots display"""

    display_image = display.imageNew(
        im.tobytes(), Display.BGRA, display_width, display_height
    )
    display.imagePaste(display_image, 0, 0, blend=False)
    display.imageDelete(display_image)


if __name__ == "__main__":
    robot, camera, display = initialize()

    camera_width = camera.getWidth()
    camera_height = camera.getHeight()

    display_width = display.getWidth()
    display_height = display.getHeight()

    print(f"Camera HxW: {camera_height}x{camera_width}")
    print(f"Display HxW: {display_height}x{display_width}")

    while robot.step(TIME_STEP) != -1:
        webots_im = camera.getImage()
        numpy_im = webots_image_to_numpy(webots_im, camera_height, camera_width)

        if SAVE_TO_DISK:
            save_image(cv2.cvtColor(numpy_im, cv2.COLOR_RGB2BGR))

        mask = segment_by_color(numpy_im, HSV_LOW_RANGE, HSV_UP_RANGE)

        try:
            document = get_warped_document(numpy_im, mask, debug=False)
            document = resize_and_letter_box(document, display_height, display_width)
        except ValueError as e:
            document = np.zeros((display_width, display_height, 4), dtype=np.uint8)
            document[:, :, 0] = 255
            print(e)

        display_numpy_image(document, display, display_width, display_height)

    robot.cleanup()
