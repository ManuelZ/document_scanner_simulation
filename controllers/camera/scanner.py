# Standard Library imports
import argparse

# External imports
import numpy as np
import cv2
from imutils import resize


def get_box_width(top_left, top_right, bottom_right, bottom_left):
    """ """
    x1, y1 = top_left
    x2, y2 = top_right
    width1 = np.hypot(x2 - x1, y2 - y1)

    x1, y1 = bottom_left
    x2, y2 = bottom_right
    width2 = np.hypot(x2 - x1, y2 - y1)

    width = int(max(width1, width2))

    return width


def get_box_height(top_left, top_right, bottom_right, bottom_left):
    """ """
    x1, y1 = top_left
    x2, y2 = bottom_left
    height1 = np.hypot(x2 - x1, y2 - y1)

    x1, y1 = top_right
    x2, y2 = bottom_right
    height2 = np.hypot(x2 - x1, y2 - y1)

    height = int(max(height1, height2))

    return height


def identify_corners(approx_contour):
    """ """
    # First point will be top left, last point will be bottom right
    src_points = sorted(approx_contour, key=lambda p: p[0][0] + p[0][1])
    src_points = [p[0] for p in src_points]

    top_left, up1, up2, bottom_right = src_points

    # The bottom left point is the one with greater y value
    if up1[1] > top_left[1] and up1[0] < bottom_right[0]:
        bottom_left = up1
        top_right = up2
    else:
        bottom_left = up2
        top_right = up1

    return top_left, top_right, bottom_right, bottom_left


def resize_and_letter_box(image, rows, cols, channels=4):
    """
    Modified from: https://stackoverflow.com/a/53623469/1253729
    """
    image_rows, image_cols = image.shape[:2]
    row_ratio = rows / float(image_rows)
    col_ratio = cols / float(image_cols)
    ratio = min(row_ratio, col_ratio)
    image_resized = cv2.resize(image, dsize=(0, 0), fx=ratio, fy=ratio)
    letter_box = np.zeros((int(rows), int(cols), int(channels)), dtype=np.uint8)
    row_start = int((letter_box.shape[0] - image_resized.shape[0]) / 2)
    col_start = int((letter_box.shape[1] - image_resized.shape[1]) / 2)
    letter_box[
        row_start : row_start + image_resized.shape[0],
        col_start : col_start + image_resized.shape[1],
    ] = image_resized
    return letter_box


def validate_image_shape(width, height):
    """ """
    if width > height:
        ratio = width / height
    else:
        ratio = height / width

    if height < 250 or width < 250:
        raise ValueError(f"Detected label is too small: H{height}xW{width}")
    elif ratio > 3:
        raise ValueError("Detected label is too thin")


def segment_by_color(image, low_range, up_range):
    """Transform an image to the HSV colorspace to segment a region of interest"""
    if image.shape[2] == 4:
        image = cv2.cvtColor(image, cv2.COLOR_BGRA2BGR)
    im_hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(im_hsv, low_range, up_range)
    return mask


def get_warped_document(image, mask, debug=False):
    """ """

    contours, hierarchy = cv2.findContours(mask, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    # Keep top largest contours
    contours = sorted(contours, key=cv2.contourArea, reverse=True)[:3]

    # Loop to ensure the contour at hand has 4 vertices
    for i in range(len(contours)):
        contour = contours[i]

        # Approximate the contour by a simpler curve whose length deviates at a max of
        # 1% of the original length
        contour_length = cv2.arcLength(contour, closed=True)
        approx_contour = cv2.approxPolyDP(
            contour, epsilon=contour_length * 0.01, closed=True
        )

        # Stop if the approx contour has 4 vertices
        if len(approx_contour) == 4:
            break

    if debug:
        # Draw the found approximate contour
        cv2.drawContours(image, [approx_contour], 0, color=(0, 0, 255), thickness=10)
        cv2.imshow("Contours", resize(image, 540))
        cv2.waitKey(1)

    top_left, top_right, bottom_right, bottom_left = identify_corners(approx_contour)

    width = get_box_width(top_left, top_right, bottom_right, bottom_left)
    height = get_box_height(top_left, top_right, bottom_right, bottom_left)

    validate_image_shape(width, height)

    # Adjust corner points for *vertical* warping based on image orientation
    if height > width:
        src_points = [top_left, top_right, bottom_right, bottom_left]
    else:
        src_points = [top_right, bottom_right, bottom_left, top_left]
        width, height = height, width  # Swap width and height for a correct orientation

    src_points = np.array(src_points, dtype=np.float32)
    dst_points = np.array(
        [[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]],
        dtype="float32",
    )

    # Compute the perspective transform matrix and then apply it
    M = cv2.getPerspectiveTransform(src_points, dst_points)
    warped = cv2.warpPerspective(
        image, M, (width, height), borderMode=cv2.BORDER_CONSTANT
    )

    return warped


if __name__ == "__main__":

    ap = argparse.ArgumentParser()
    ap.add_argument(
        "-i", "--image", required=True, type=str, help="Filename of input image"
    )
    args = vars(ap.parse_args())

    image_path = args["image"]

    image = cv2.imread(image_path)
    mask = segment_by_color(image, np.array([27, 0, 66]), np.array([180, 38, 255]))
    warped = get_warped_document(image, mask)

    cv2.imshow("image", resize(image, 540))
    cv2.waitKey(0)

    cv2.imshow("warped", resize(warped, 540))
    cv2.waitKey(0)
