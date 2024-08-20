import cv2
import inspect
import numpy as np
from shapely.geometry import Polygon, LineString

from src import params

FRAME_SUBSTRACTION: int = 1
BACKGROUND_SUBSTRACTION: int = 2
ADAPTIVE_BACKGROUND_SUBSTRACTION: int = 3
GAUSSIAN_AVERAGE: int = 4

def _filter_contours(contours: tuple, min_contour_area: int) -> tuple:

    intercepted_contours = []

    polygon = Polygon(np.array(params.VOLLEYBALL_FIELD))
    polygon = polygon.buffer(100)

    for contour in contours:
        
        # Ignore small areas
        if cv2.contourArea(contour) < min_contour_area:
            continue
        
        # Ignore non-intersecting contours 
        if not polygon.intersects(LineString(contour.squeeze())):
            continue
        
        intercepted_contours.append(contour)

    return tuple(intercepted_contours)

def frame_substraction(mat: cv2.typing.MatLike | cv2.cuda.GpuMat | cv2.UMat, time_window: int = 1, reset: bool = False) -> tuple[np.ndarray, list[tuple]]:

    # Copy the original frame
    original_frame = mat.copy()

    # Store the previous frame
    function = eval(inspect.stack()[0][3])

    try:
        function.ref_frame
        function.time_window

    except:
        reset = True

    if reset:
        function.ref_frame = mat.copy()
        function.time_window = 0

    # Convert ref frame to gray and apply gaussian blur
    ref_frame = function.ref_frame
    ref_frame_gray = cv2.cvtColor(ref_frame, cv2.COLOR_BGR2GRAY)
    ref_frame_gray = cv2.GaussianBlur(ref_frame_gray, (15, 15), 0)

    # Convert current frame to gray and apply gaussian blur
    frame = mat.copy()
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_gray = cv2.GaussianBlur(frame_gray, (15, 15), 0)

    # Calculate abs difference between the two frames
    diff = cv2.absdiff(ref_frame_gray, frame_gray)

    # Apply a threshold to get the binary image
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    
    # Dilate the thresholded image to fill in holes
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Extract contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = _filter_contours(contours=contours, min_contour_area=6500)

    bounding_boxes = []

    # Draw bounding boxes around detected motion
    for contour in contours:

        x, y, w, h = cv2.boundingRect(contour)
        bounding_boxes.append((x, y, w, h))

        cv2.rectangle(original_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # Update based on specified window
    function.time_window = function.time_window + 1

    if function.time_window == time_window:
        function.ref_frame = frame
        function.time_window = 0

    return original_frame, bounding_boxes

def background_substraction(mat: cv2.typing.MatLike | cv2.cuda.GpuMat | cv2.UMat, background: cv2.typing.MatLike | cv2.cuda.GpuMat | cv2.UMat) -> tuple[np.ndarray, list[tuple]]:

    # Copy the original frame
    original_frame = mat.copy()

    # Convert background to gray and apply gaussian blur
    _background = background.copy()
    background_gray = cv2.cvtColor(_background, cv2.COLOR_BGR2GRAY)
    background_gray = cv2.GaussianBlur(background_gray, (15, 15), 0)
    
    # Convert frame to gray and apply gaussian blur
    frame = mat.copy()
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_gray = cv2.GaussianBlur(frame_gray, (15, 15), 0)
    
    #cv2.imwrite("blur.jpg", frame_gray)
    #exit(0)

    # Calculate abs difference between the two frames
    diff = cv2.absdiff(background_gray, frame_gray)

    # Apply a threshold to get the binary image
    _, thresh = cv2.threshold(diff, 13, 255, cv2.THRESH_BINARY)
    
    # Dilate the thresholded image to fill in holes
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Extract contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = _filter_contours(contours=contours, min_contour_area=4000)

    bounding_boxes = []

    # Draw bounding boxes around detected motion
    for contour in contours:

        x, y, w, h = cv2.boundingRect(contour)
        bounding_boxes.append((x, y, w, h))

        cv2.rectangle(original_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    return original_frame, bounding_boxes

def adaptive_background_substraction(mat: cv2.typing.MatLike | cv2.cuda.GpuMat | cv2.UMat, background: cv2.typing.MatLike | cv2.cuda.GpuMat | cv2.UMat, alpha: float, reset: bool = False) -> tuple[np.ndarray, list[tuple]]:

    # Check alpha
    assert alpha >= 0 and alpha <= 1, "Alpha must be a number in the interval [0, 1]"

    # Copy the original frame
    original_frame = mat.copy()

    # Store the background frame so we can update it
    function = eval(inspect.stack()[0][3])

    try:
        function.background
    
    except:
        reset = True

    if reset:
        function.background = background.copy()

    # Convert background to gray and apply gaussian blur
    background_gray = cv2.cvtColor(function.background, cv2.COLOR_BGR2GRAY)
    background_gray = cv2.GaussianBlur(background_gray, (15, 15), 0)

    # Convert frame to gray and apply gaussian blur
    frame = mat.copy()
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_gray = cv2.GaussianBlur(frame_gray, (15, 15), 0)

    # Calculate abs difference between the two frames
    diff = cv2.absdiff(background_gray, frame_gray)

    # Apply a threshold to get the binary image
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)
    
    # Dilate the thresholded image to fill in holes
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Extract contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = _filter_contours(contours=contours, min_contour_area=4000)

    bounding_boxes = []

    # Draw bounding boxes around detected motion
    for contour in contours:

        x, y, w, h = cv2.boundingRect(contour)
        bounding_boxes.append((x, y, w, h))

        cv2.rectangle(original_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    # Update background (adaption step)
    function.background = cv2.addWeighted(frame, alpha, function.background, 1 - alpha, 0)

    return original_frame, bounding_boxes

def gaussian_average(mat: cv2.typing.MatLike | cv2.cuda.GpuMat | cv2.UMat, background: cv2.typing.MatLike | cv2.cuda.GpuMat | cv2.UMat, alpha: float, reset: bool = False) -> tuple[np.ndarray, list[tuple]]:

    # Check alpha
    assert alpha >= 0 and alpha <= 1, "Alpha must be a number in the interval [0, 1]"

    # Copy the original frame
    original_frame = mat.copy()

    # Store the background frame so we can update it
    function = eval(inspect.stack()[0][3])

    try:
        function.background

    except:
        reset = True
    
    if reset:
        function.background = background.copy()

    # Convert background to gray and apply gaussian blur
    background_gray = cv2.cvtColor(function.background, cv2.COLOR_BGR2GRAY)
    background_gray = cv2.GaussianBlur(background_gray, (15, 15), 0).astype("float")

    # Convert frame to gray and apply gaussian blur
    frame = mat.copy()
    frame_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    frame_gray = cv2.GaussianBlur(frame_gray, (15, 15), 0)

    # Compute the weighted running average of the background
    cv2.accumulateWeighted(frame_gray, background_gray, alpha)

    # Compute the absolute difference between the current frame and the background
    diff = cv2.absdiff(frame_gray, cv2.convertScaleAbs(background_gray))

    # Apply a threshold to get the binary image
    _, thresh = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

    # Dilate the thresholded image to fill in holes
    thresh = cv2.dilate(thresh, None, iterations=2)

    # Extract contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    contours = _filter_contours(contours=contours, min_contour_area=4000)

    bounding_boxes = []

    # Draw bounding boxes around detected motion
    for contour in contours:

        x, y, w, h = cv2.boundingRect(contour)
        bounding_boxes.append((x, y, w, h))

        cv2.rectangle(original_frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
    
    return original_frame, bounding_boxes