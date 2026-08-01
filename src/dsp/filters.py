import numpy as np
import scipy.signal as signal

class LowPassFilter:
    """Convenience wrapper for designing and using a low-pass filter.

    The class builds FIR or Butterworth coefficients from a cutoff frequency,
    applies them to signals, and exposes the filter response and delay.
    """

    def __init__(self, cutoff_hz, fs, order = 4, kind = "iir"):
        """Create a low-pass filter for the given sampling frequency.

        Args:
            cutoff_hz (float): Cutoff frequency in hertz.
            fs (float): Sampling frequency in hertz.
            order (int, optional): Filter order. Defaults to 4.
            kind (str, optional): Filter family, either "fir" or "iir".

        Raises:
            ValueError: If kind is not "fir" or "iir".
        """
        self.fs = fs
        self.kind = kind
        self.cutoff_hz = cutoff_hz
        wn = cutoff_hz / (fs/2)
        
        if kind == "fir":
            self.b, self.a = fir1(order, wn), 1.0
        elif kind == "iir":
            self.b, self.a = butter(order, wn)
        else:
            raise ValueError(f"kind 'fir' veya 'iir' olmali, verilen: {kind!r}")

    def apply(self, x: np.ndarray) -> np.ndarray:
        """Apply the configured filter to a signal.

        Args:
            x (np.ndarray): Input signal samples.

        Returns:
            np.ndarray: Filtered output signal with the same shape as the input.
        """
        return apply_filter(x, self.b , self.a) 

    def apply_zero_phase(self, x) -> np.ndarray:
        """Apply the filter with zero-phase distortion.

        Args:
            x (np.ndarray): Input signal samples.

        Returns:
            np.ndarray: Filtered signal using forward-backward filtering.
        """
        return apply_filtfilt(x, self.b , self.a)
       
    @property
    def group_delay_samples(self) -> int:
        """Return the nominal group delay of the FIR filter in samples.

        Returns:
            int: The estimated delay for FIR filters.

        Raises:
            ValueError: If the filter is an IIR filter, because its delay depends on frequency.
        """
        if self.kind == "fir":
            return (len(self.b) - 1) // 2
        else:
            raise ValueError(f"kind 'fir' olmali, 'iir' icin group_delay_at fonksiyonunu kullanin, verilen: {self.kind!r}")
        
    def group_delay_at(self, freq_hz: float) -> float:
        """Return the group delay at a specific frequency for an IIR filter.

        Args:
            freq_hz (float): Frequency in hertz at which the delay is requested.

        Returns:
            float: Interpolated group delay in samples.

        Raises:
            ValueError: If the filter is not an IIR filter.
        """
        if self.kind == "iir":
            w, gd = signal.group_delay((self.b, self.a), fs=self.fs)
            return float(np.interp(freq_hz, w, gd))
        else:
            raise ValueError(f"kind 'iir' olmali, 'fir' icin group_delay_samples fonksiyonunu kullanin, verilen: {self.kind!r}")
        
    def response(self, worN=1024) -> tuple[np.ndarray, np.ndarray]:
        """Return the frequency response of the configured filter.

        Args:
            worN (int, optional): Number of frequency points to evaluate. Defaults to 1024.

        Returns:
            tuple[np.ndarray, np.ndarray]: Frequency values and complex response values.
        """
        return frequency_response(self.b, self.a, worN=worN, fs=self.fs)


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

def butter(N: int, Wn: float) -> tuple[np.ndarray, np.ndarray]:
    """Design a Butterworth filter.

    Args:
        N: Filter order.
        Wn: Normalized cutoff frequency (0 < Wn < 1).

    Returns:
        Tuple of filter numerator and denominator coefficients.
    """
    
    return signal.butter(N, Wn)

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