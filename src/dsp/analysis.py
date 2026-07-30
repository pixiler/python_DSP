import numpy as np
from scipy.signal import correlate, correlation_lags

def fft(signal: np.ndarray, sample_rate: int) -> tuple[np.ndarray, np.ndarray]:
    """
    Compute the Fast Fourier Transform (FFT) of a signal.

    Args:
        signal (np.ndarray): Input signal samples.
        sample_rate (int): Sampling rate in samples per second.

    Returns:
        tuple[np.ndarray, np.ndarray]: A tuple containing the shifted and normalized FFT values
            and the corresponding frequency bins.
    """
    N = len(signal)
    f = np.arange(-N/2, N/2) * (sample_rate / N)  # Frequency bins
    fft_values = np.fft.fft(signal)
    fft_values = np.fft.fftshift(fft_values) / N  # Normalize and shift the FFT output
    return fft_values, f

def measure_delay(delayed: np.ndarray, reference: np.ndarray, Fs: float, fc: float) -> int:
    """Estimate the delay between two signals using cross-correlation.

    Args:
        delayed (np.ndarray): Delayed version of the reference signal.
        reference (np.ndarray): Reference signal for delay estimation.
        Fs (float): Sampling frequency in Hz.
        fc (float): Frequency parameter used to limit the delay search range.

    Returns:
        int: Estimated delay in samples.
    """

    c = correlate(delayed, reference, mode='full')
    lags = correlation_lags(len(delayed), len(reference), mode='full')
    P = int(Fs / fc)
    mask = (lags >= 0) & (lags < P)
    return lags[mask][np.argmax(c[mask])]

def find_cutoff(w: np.ndarray, h: np.ndarray, level_db: float = -6.0)  -> float | None:
    """Find the cutoff frequency where the magnitude response crosses a dB level.

    Args:
        w (np.ndarray): Frequency values corresponding to the response samples.
        h (np.ndarray): Complex frequency response values.
        level_db (float): Reference magnitude level in decibels.

    Returns:
        float | None: The first frequency at which the magnitude response crosses
            the specified dB level, or None if no crossing is found.
    """
    mag_db = 20 * np.log10(np.abs(h))
    
    cross_indices = np.diff(np.sign(mag_db - level_db))  # Find the index where the magnitude response crosses level_db dB
    indices = np.where(cross_indices)[0]
    f_c = float(w[indices[0]]) if indices.size > 0 else None
    return f_c

def snr_calculate(signal: np.ndarray, noise: np.ndarray) -> float:
    """Calculate the signal-to-noise ratio (SNR) in decibels.

    Args:
        signal (np.ndarray): Signal samples.
        noise (np.ndarray): Noise samples.

    Returns:
        float: The computed SNR value in decibels.
    """

    return 10 * np.log10(np.mean(signal**2) / np.mean(noise**2))    