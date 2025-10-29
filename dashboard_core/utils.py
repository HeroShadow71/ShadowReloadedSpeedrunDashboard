"""
Small utility helpers used throughout the dashboard.

This module contains formatting helpers, axis tick generation utilities and a
helper to embed local images as data-URIs.
"""
import math
import logging
import base64
import mimetypes
import os

import pandas as pd
import numpy as np


def format_time_seconds(t):
    """
    Convert a numeric time in seconds into a readable string.

    Returns a formatted string in one of the following formats:
    - `H:MM:SS.xx` if the duration includes hours
    - `M:SS.xx` if the duration includes minutes but no hours
    - `S.xx` if the duration is less than a minute

    :param t: Time in seconds.
    :return: Formatted time string or empty string.
    """
    try:
        if pd.isna(t):
            return ""
        t = float(t)
    except Exception:
        return ""
    
    # Convert to centiseconds for consistent rounding
    total_cs = int(round(t * 100))
    total_seconds = total_cs // 100
    frac = total_cs % 100
    
    # Decompose into hours, minutes, seconds
    s = total_seconds % 60
    m = (total_seconds // 60) % 60
    h = total_seconds // 3600
    
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}.{frac:02d}"
    
    elif m > 0:
        return f"{m}:{s:02d}.{frac:02d}"
    else:
        return f"{s}.{frac:02d}"
    

def generate_time_axis_ticks(values, target_ticks=7, candidates=None):
    """
    Generate axis tick positions and formatted labels for time values (in seconds)
    for use in plotting.

    Cleans input data, selects a suitable step size from candidate intervals,
    and formats tick labels depending on the time range:

    - `subminute`: seconds with two decimals (ex: "12.34")
    - `minutes`: minutes and seconds (ex: "3:12")
    - `hours`: hours, minutes, and seconds (ex: "1:05:30")

    :param values: Iterable of numeric values in seconds.
    :param target_ticks: Approximate number of ticks to produce.
    :param candidates: Optional sequence of candidate step sizes in seconds.
                       Defaults to [1, 2, 5, 10, 15, 30, 60, 300, 600].
    :return: Tuple of (tickvals, ticktext), where:
    
        - `tickvals` are the numeric tick positions;
        - `ticktext` are the corresponding formatted label strings
    """
    # Clean and filter input
    values = np.asarray(values, dtype=float)
    vals = values[np.isfinite(values)]
    if vals.size == 0:
        return [0.0], ["0:00"]

    y_min, y_max = vals.min(), vals.max()
    
    # Expand degenerate ranges slightly for plotting
    if math.isclose(y_min, y_max):
        span = max(1.0, y_max * 0.05)
        y_min = y_min - span
        y_max = y_max + span
        
    span = y_max - y_min
    raw_step = span / max(1, (target_ticks - 1))

    # Default candidate steps in seconds
    candidates = candidates or [0.1, 0.2, 0.5, 1, 2, 5, 10, 15, 30, 60, 300, 600]

    # Pick smallest candidate >= required step
    step = next(
        (c for c in candidates if c >= raw_step),
        math.ceil(raw_step / candidates[-1]) * candidates[-1]
    )

    # Compute tick positions covering range
    tick_start = math.floor(y_min / step) * step
    tick_end = math.ceil(y_max / step) * step
    tickvals = np.arange(tick_start, tick_end + step * 0.5, step)
    tickvals = np.round(tickvals, 2).tolist()

    # Select label format based on range
    max_sec = y_max
    if max_sec < 60:
        mode = "subminute"
    elif max_sec < 3600:
        mode = "minutes"
    else:
        mode = "hours"

    ticktext = [_fmt_tick(v, mode) for v in tickvals]
    return tickvals, ticktext


def _fmt_tick(sec, mode):
    """
    Format a number of seconds according to a display mode.

    :param sec: Time in seconds.
    :param mode: One of `subminute`, `minutes`, or `hours`.
    :return: Formatted tick label as a string.
    """
    sec = float(sec)
    if mode == "subminute":
        return f"{sec:.2f}"
    
    if mode == "minutes":
        m = int(sec // 60)
        s = int(round(sec % 60))
        return f"{m}:{s:02d}"
    
    h = int(sec // 3600)
    rem = int(round(sec % 3600))
    m = rem // 60
    s = rem % 60
    return f"{h}:{m:02d}:{s:02d}"


def load_image_as_base64(path):
    """
    Encode a local image file as a base64 data URI.

    Attempts to guess the MIME type from the filename extension,
    defaulting to `image/png` if unknown.

    :param path: Path to the local image file.
    :return: Data URI string containing base64-encoded image.
    """
    try:
        with open(path, "rb") as f:
            content = f.read()
        b64 = base64.b64encode(content).decode("utf-8")
    except FileNotFoundError:
        logging.error("Image file not found: %s", path)
        return ""
    
    # Guess MIME type from extension, fallback to PNG
    mime, _ = mimetypes.guess_type(path)
    if not mime:
        ext = os.path.splitext(path)[1].lower()
        if ext in (".jpg", ".jpeg"):
            mime = "image/jpeg"
        elif ext == ".gif":
            mime = "image/gif"
        else:
            mime = "image/png"
            
    return f"data:{mime};base64,{b64}"
