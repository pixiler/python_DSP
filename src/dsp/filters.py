import numpy as np
import scipy.signal as signal

def fir1(N: int, Wn: float) -> np.ndarray:
    """Design a low-pass FIR filter using the window method.

    Args:
        N (int): Filter order (number of taps).
        Wn (float): Normalized cutoff frequency (0 < Wn < 1).

    Returns:
        np.ndarray: 1-D array of filter coefficients (dtype float).
    """
    N = N + 1 if N % 2 == 0 else N  # Ensure N is odd for symmetry
    return signal.firwin(N, Wn)

def frequency_response(b: np.ndarray, a: np.ndarray | float = 1.0, worN: int = 1024, fs: float = 2.0) -> tuple[np.ndarray, np.ndarray]:
    """Compute the frequency response (w, H) of a digital filter.

    Wrapper around :func:`scipy.signal.freqz` that returns frequency bins and
    the complex frequency response as NumPy arrays.

    Args:
        b (np.ndarray): Numerator filter coefficients.
        a (np.ndarray | float): Denominator coefficients or 1.0 for FIR.
        worN (int): Number of frequency points.
        fs (float): Sampling frequency.

    Returns:
        tuple[np.ndarray, np.ndarray]: Frequencies and complex frequency response.
    """

    return signal.freqz(b, a, worN=worN, fs=fs)   # w, h

def apply_filter(input_signal: np.ndarray, b: np.ndarray, a: np.ndarray | float = 1.0) -> np.ndarray:
    """Apply a linear digital filter using :func:`scipy.signal.lfilter`.

    Args:
        input_signal (np.ndarray): Input signal samples.
        b (np.ndarray): Numerator filter coefficients.
        a (np.ndarray | float): Denominator coefficients or 1.0 for FIR.

    Returns:
        np.ndarray: Filtered output signal (same shape as input).
    """

    return signal.lfilter(b, a, input_signal)

def apply_filtfilt(input_signal: np.ndarray, b: np.ndarray, a: np.ndarray | float = 1.0) -> np.ndarray:
    """Apply zero-phase digital filtering using forward-backward filtering.

    Uses :func:`scipy.signal.filtfilt` to perform forward and backward filtering,
    which reduces phase distortion compared to a single forward filter pass.

    Args:
        input_signal (np.ndarray): Input signal samples.
        b (np.ndarray): Numerator filter coefficients.
        a (np.ndarray | float): Denominator coefficients or 1.0 for FIR.

    Returns:
        np.ndarray: Filtered output signal with reduced phase distortion.
    """

    return signal.filtfilt(b, a, input_signal)