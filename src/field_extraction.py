import cv2
import numpy as np

from typing import Union
from enum import Enum

class Side(Enum):
    LEFT = 0
    RIGHT = -1

def extract(mat: Union[cv2.typing.MatLike, cv2.cuda.GpuMat, cv2.UMat], side: Side, line_color: tuple[int, int, int] = (177, 63, 22), tolerance: int = 8) -> tuple[np.ndarray, np.ndarray]:

    # Copy the image
    _mat = mat.copy()

    # Convert image to HSV
    hsv_image = cv2.cvtColor(_mat, cv2.COLOR_BGR2HSV)

    # Convert color to HSV
    color = np.uint8([[list(line_color)]])
    hsv_color = cv2.cvtColor(color, cv2.COLOR_BGR2HSV)

    # Define the range of colors you want to keep (shades of blue)
    lower_bound = np.array([hsv_color[0][0][0] - tolerance, 50, 50])
    upper_bound = np.array([hsv_color[0][0][0] + tolerance, 255, 255])

    # Threshold the HSV image to get only the desired colors
    mask = cv2.inRange(hsv_image, lower_bound, upper_bound)

    # Apply the mask in order to replace the other colors with black
    _mat[mask == False] = (0,0,0)

    # Find contours and keep the largest ones
    gray = cv2.cvtColor(_mat, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(src=gray, thresh=1, maxval=255, type=cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(image=thresh, mode=cv2.RETR_LIST, method=cv2.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv2.contourArea(c) >= 10000]

    # max for left frame, min for right frame
    function = "max" if side == Side.LEFT else "min"
    function = eval(function)

    best_contour = None

    # Extract the point according to the selected function
    for contour in contours:
        min_point = function(contour[:, 0, :], key=lambda x: x[0])

        if best_contour is None or function(best_contour[0], min_point[0]) == min_point[0]:
            best_contour = (min_point[0], contour)

    # Create a new mask and draw the extracted contour
    mask = np.zeros_like(_mat)
    mask = cv2.cvtColor(mask, cv2.COLOR_BGR2GRAY)
    cv2.drawContours(mask, [best_contour[1]], 0, (255, 255, 255), thickness=cv2.FILLED)

    # Extract the external contour
    _mat = mask

    # For the left frame use 0, for the right one use -1
    side_pts = []

    for y in range(0, _mat.shape[0]):

        if np.all(_mat[y, :] == 0):
            continue

        non_zero = cv2.findNonZero(_mat[y, :])
        
        pt = (non_zero[side.value][0][1], y)
        side_pts.append(pt)

    # Common for both left and right frames
    bottom = []

    for x in range(_mat.shape[1]-1, -1, -1):

        if np.all(_mat[:, x] == 0):
            continue
        
        non_zero = cv2.findNonZero(_mat[:, x])

        pt = (x, non_zero[-1][0][1])
        bottom.append(pt)

    # Reconstruct the rectangle area (in case of missing points)
    if side == Side.LEFT:

        for y in range(0, _mat.shape[0]):
            non_zero = cv2.findNonZero(_mat[y, :])

            if non_zero is None:
                continue

            mask[y, non_zero[0][0][1]:] = 255

    else:

        for y in range(0, _mat.shape[0]):
            non_zero = cv2.findNonZero(_mat[y, :])

            if non_zero is None:
                continue

            mask[y, :non_zero[-1][0][1]+1] = 255

    field = mat.copy()
    field[mask == False] = (0,0,0)

    return field, mask