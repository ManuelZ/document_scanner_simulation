# Standard Library imports
from itertools import count

# External imports
import cv2
import numpy as np
from imutils import resize
from controller import Robot, Display

# Local imports
from scanner import get_warped_document, resize_and_letter_box


TIME_STEP = 100
HSV_LOW_RANGE = np.array([24, 0, 0])
HSV_UP_RANGE = np.array([180, 255, 255])


def initialize():
    robot = Robot()

    camera = robot.getDevice("camera")
    camera.enable(100)

    display = robot.getDevice("image display")

    return robot, camera, display


def numpy_to_bytes(im):
    _, buffer = cv2.imencode(".bmp", im)
    return buffer.tobytes()


def webots_image_to_numpy_rgb(im, h, w):
    im_array = np.frombuffer(im, dtype=np.uint8).reshape((h, w, 4))
    im_array = cv2.cvtColor(im_array, cv2.COLOR_BGRA2RGB)
    return im_array


def display_numpy_image(im, display, display_width, display_height):
    """Display RGB image in a Webots display"""
    display_image = numpy_to_bytes(im)
    display_image = display.imageNew(
        display_image, Display.RGB, display_width, display_height
    )
    display.imagePaste(display_image, 0, 0, blend=False)
    display.imageDelete(display_image)


def segment_by_color(image, low_range, up_range):
    """Transform an RGB image to the HSV colorspace to segment region of interest"""
    im_hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    mask = cv2.inRange(im_hsv, low_range, up_range)
    return cv2.bitwise_and(image, image, mask=mask)


def counter(_count=count(1)):
    """https://stackoverflow.com/a/54715096/1253729"""
    return next(_count)


def save_rgb_image(image):
    im = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    cv2.imwrite(f"image_{counter()}.jpg", im)


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
        numpy_im = webots_image_to_numpy_rgb(webots_im, camera_height, camera_width)
        segmented = segment_by_color(numpy_im, HSV_LOW_RANGE, HSV_UP_RANGE)

        try:
            document = get_warped_document(segmented)
            document = resize_and_letter_box(document, display_height, display_width)
        except ValueError:
            document = np.zeros((display_width, display_height, 3), dtype=np.uint8)

        display_numpy_image(document, display, display_width, display_height)

    robot.cleanup()
