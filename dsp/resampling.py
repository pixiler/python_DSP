import numpy as np

from .filters import fir1, apply_filter

from dataclasses import dataclass

@dataclass
class InterpolationResult:
    """Result of signal interpolation.

    Attributes:
        signal: Filtered output signal at the new sampling rate.
        zero_stuffed: Intermediate signal after zero-insertion before filtering.
        fs: New sampling frequency (Hz).
        group_delay: Number of samples to discard from the output transient.
    """
    signal: np.ndarray       # filtered output signal
    zero_stuffed: np.ndarray # intermediate zero-stuffed signal
    fs: int                  # new sampling frequency
    group_delay: int         # number of transient output samples


def up_sample(signal: np.ndarray, factor: int) -> np.ndarray:
    """Insert zeros between samples to upsample a signal by an integer factor.

    Args:
        signal (np.ndarray): Input signal samples.
        factor (int): Integer upsampling factor.

    Returns:
        np.ndarray: Signal with zero-valued samples inserted between original samples.
    """
    upsampled_signal = np.zeros(len(signal) * factor)
    upsampled_signal[::factor] = signal
    return upsampled_signal


def down_sample(signal: np.ndarray, factor: int) -> np.ndarray:
    """Reduce the sample rate by selecting every nth sample.

    Args:
        signal (np.ndarray): Input signal samples.
        factor (int): Integer downsampling factor.

    Returns:
        np.ndarray: Downsampled signal containing every factor-th sample.
    """
    return signal[::factor]

def interpolate(signal: np.ndarray, Fs: int, factor: int) -> InterpolationResult:
    """Interpolate a signal by zero-stuffing and low-pass filtering.

    Args:
        signal (np.ndarray): Input signal samples.
        Fs (int): Original sampling frequency.
        factor (int): Interpolation factor.

    Returns:
        InterpolationResult: Result object containing the filtered interpolated signal,
            the zero-stuffed intermediate signal, the new sampling frequency, and
            the group delay introduced by the interpolation filter.
    """

    y_zs = up_sample(signal, factor)
    Fs_new = factor * Fs
    b_i = factor * fir1(64, (Fs/2) / (Fs_new / 2))
    y_up = apply_filter(y_zs, b_i)
    return InterpolationResult(
        signal=y_up,
        zero_stuffed=y_zs,
        fs=Fs_new,
        group_delay=(len(b_i) - 1) // 2,
    )

def decimate(signal: np.ndarray, Fs: int, factor: int) -> tuple[np.ndarray, np.ndarray, int]:
    """Decimate a signal by filtering and then downsampling.

    Args:
        signal (np.ndarray): Input signal samples.
        Fs (int): Original sampling frequency.
        factor (int): Decimation factor.

    Returns:
        tuple[np.ndarray, np.ndarray, int]: A tuple containing the downsampled signal,
            the filtered signal before decimation, and the new sampling frequency.
    """
    b_d = fir1(64, (Fs/(2*factor)) / (Fs / 2))
    y_filt = apply_filter(signal, b_d)
    y_ds = down_sample(y_filt, factor)
    Fs_new = Fs // factor
    return y_ds, y_filt, Fs_new