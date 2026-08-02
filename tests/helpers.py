"""Helper utilities for signal-processing tests."""

import numpy as np

FS : float = 50e3
"""Sampling frequency used by the helper routines in hertz."""

FC : float = 1e3
"""Carrier frequency used by the helper routines in hertz."""


def rms(x: np.ndarray) -> float:
    """Return the root mean square (RMS) value of an array.

    Parameters
    ----------
    x : numpy.ndarray
        Input signal samples.

    Returns
    -------
    float
        The RMS value of the input samples.
    """
    return float(np.sqrt(np.mean(x**2)))