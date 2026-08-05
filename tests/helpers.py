"""Helper utilities for signal-processing tests."""

import numpy as np

FS : float = 50e3
"""Sampling frequency used by the helper routines in hertz."""

FC : float = 1e3
"""Carrier frequency used by the helper routines in hertz."""

DURATION = 0.1

def rms(signal: np.ndarray) -> float:
    """Return the root mean square (RMS) value of an array.

    Parameters
    ----------
    signal : numpy.ndarray
        Input signal samples.

    Returns
    -------
    float
        The RMS value of the input samples.
    """
    return float(np.sqrt(np.mean(signal**2)))

# Eğer sinyallerde DC offset varsa:
def ac_rms(signal: np.ndarray) -> float:
    ac_signal = signal - np.mean(signal)
    return float(np.sqrt(np.mean(ac_signal**2)))