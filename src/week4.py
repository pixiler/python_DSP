from typing import Tuple

import numpy as np
import scipy.signal as signal
import matplotlib.pyplot as plt

from week3 import add_awgn
from matlab_example import sine_wave, fir1, freqz, plot_signal, plot_spectrum
from interpolation_decimation import interpolate

def welch(axes: plt.Axes, x : np.ndarray, Fs : int, nperseg: int = None, label : str = None) -> None:
    """Plot the power spectral density of a signal using Welch's method.

    Args:
        axes: Plot axes where the PSD is drawn.
        x: Input signal samples.
        Fs: Sampling frequency in Hz.
        nperseg: Number of samples per segment for Welch's method. If None, the default is used.
        label: Optional curve label to show in the legend.

    Notes:
        Uses `scipy.signal.welch` to estimate the PSD and plots the result on a
        semilog-y scale.
    """

    f, Pxx_den = signal.welch(x, Fs, nperseg=nperseg)
    axes.semilogy(f, Pxx_den, label = label)
    axes.set_xlabel('frequency [Hz]')
    axes.set_ylabel('PSD [V**2/Hz]')
    axes.legend()

def measure_delay(delayed: np.ndarray, reference: np.ndarray, Fs: float, fc: float) -> int:
    """Estimate the delay between two signals using cross-correlation.

    Args:
        delayed: Delayed version of the reference signal.
        reference: Reference signal for delay estimation.
        Fs: Sampling frequency in Hz.
        fc: Frequency parameter used to limit the delay search range.

    Returns:
        Estimated delay in samples.
    """
    from scipy.signal import correlate, correlation_lags

    c = correlate(delayed, reference, mode='full')
    lags = correlation_lags(len(delayed), len(reference), mode='full')
    P = int(Fs / fc)
    mask = (lags >= 0) & (lags < P)
    return lags[mask][np.argmax(c[mask])]


def apply_filter(input_signal: np.ndarray, b: np.ndarray, a: np.ndarray | float = 1.0) -> np.ndarray:
    """Apply a linear digital filter to a signal.

    Args:
        input_signal: Input signal samples.
        b: Numerator filter coefficients.
        a: Denominator filter coefficients, or 1.0 for an FIR filter.

    Returns:
        Filtered output signal.
    """

    return signal.lfilter(b, a, input_signal)

def apply_filtfilt(input_signal: np.ndarray, b: np.ndarray, a: np.ndarray | float = 1.0) -> np.ndarray:
    """Apply a zero-phase digital filter to a signal using forward-backward filtering.

    Args:
        input_signal: Input signal samples.
        b: Numerator filter coefficients.
        a: Denominator filter coefficients, or 1.0 for an FIR filter.

    Returns:
        Filtered output signal with zero phase distortion.
    """

    return signal.filtfilt(b, a, input_signal)

def butter(N: int, Wn: float) -> Tuple[np.ndarray, np.ndarray]:
    """Design a Butterworth filter.

    Args:
        N: Filter order.
        Wn: Normalized cutoff frequency (0 < Wn < 1).

    Returns:
        Tuple of filter numerator and denominator coefficients.
    """
    

    return signal.butter(N, Wn)

def main() -> None:
    """Execute the week 4 signal processing demonstration.

    This routine generates a noisy sine wave, designs FIR and IIR filters,
    evaluates frequency responses, and plots the results.
    """
    fc: float = 1e3  # Carrier frequency in Hz
    Fs: float = 50e3  # Sampling frequency in Hz
    t: float = 0.1  # Duration in seconds

    y = sine_wave(fc, t, Fs)
    snr_db: float = 0  # Desired SNR in dB
    noisy_signal, noise = add_awgn(y, snr_db)

    Wn : float = 2e3 / (Fs / 2)  # Normalized cutoff frequency
    N : int = 64  # Filter order
    h = fir1(N, Wn)
    b, a = butter(4, Wn)

    plt.figure(figsize=(12, 6))
    w, h_freq_fir = freqz(plt.gca(), h, worN=1024, fs=Fs, label='FIR')
    w, h_freq_iir = freqz(plt.gca(), b, a, 1024, Fs, label='IIR')

    mag_fir = 20 * np.log10(np.abs(h_freq_fir))
    mag_iir = 20 * np.log10(np.abs(h_freq_iir))

    for f_test in [4e3, 10e3, 20e3]:
        idx = np.argmin(np.abs(w - f_test))
        print(f"{f_test/1e3:.0f} kHz: FIR {mag_fir[idx]:.1f} dB, IIR {mag_iir[idx]:.1f} dB")

    y_fir = apply_filter(noisy_signal, h, 1.0)
    y_iir = apply_filter(noisy_signal, b, a)
    y_ff = apply_filtfilt(noisy_signal, b, a)

    s_fir = apply_filter(y, h, 1.0)
    s_iir = apply_filter(y, b, a)
    s_ff = apply_filtfilt(y,b, a)

    n_fir = apply_filter(noise, h, 1.0)
    n_iir = apply_filter(noise, b, a)
    n_ff = apply_filtfilt(noise, b, a)

    plt.figure()
    plot_signal(plt.gca(), y, Fs, fc, 5, label='Original signal')
    plot_signal(plt.gca(), y_fir, Fs, fc, 5, label='Noisy signal with linear FIR')
    plot_signal(plt.gca(), y_iir, Fs, fc, 5, label='Noisy signal with linear IIR')
    plot_signal(plt.gca(), y_ff, Fs, fc, 5, label='Noisy signal with twice filter IIR')

    print(f"Calculated SNR (dB): {10 * np.log10(np.mean(y**2) / np.mean(noise**2)):.2f} with original signal")
    print(f"Calculated SNR (dB): {10 * np.log10(np.mean(s_fir[200:]**2) / np.mean(n_fir[200:]**2)):.2f} with linear FIR")
    print(f"Calculated SNR (dB): {10 * np.log10(np.mean(s_iir[200:]**2) / np.mean(n_iir[200:]**2)):.2f} with linear IIR")
    print(f"Calculated SNR (dB): {10 * np.log10(np.mean(s_ff[200:]**2) / np.mean(n_ff[200:]**2)):.2f} with twice filter IIR")  


    print(f"group_delay (sample) : {measure_delay(s_fir, y, Fs, fc)} with FIR filter")
    print(f"group_delay (sample) : {measure_delay(s_iir, y, Fs, fc)} with IIR filter")
    print(f"group_delay (sample) : {measure_delay(s_ff, y, Fs, fc)} with twice filter IIR filter")

    plt.figure(figsize=(12, 8))
    for i, nperseg in enumerate([256, 512, 1024, 2048, 4096]):
        welch(plt.gca(), noisy_signal, Fs, nperseg=nperseg, label=f"nperseg = {nperseg}")

    plt.figure(figsize=(12, 8))
    welch(plt.gca(), y, Fs, nperseg=1024, label='Original signal')
    welch(plt.gca(), noisy_signal, Fs, nperseg=1024, label='Noisy signal')
    welch(plt.gca(), y_fir, Fs, nperseg=1024, label='Noisy signal with linear FIR')
    welch(plt.gca(), y_iir, Fs, nperseg=1024, label='Noisy signal with linear IIR')
    welch(plt.gca(), y_ff, Fs, nperseg=1024, label='Noisy signal with twice filter IIR')

    plt.figure(figsize=(12, 8))
    P = int(Fs / fc)
    err_fir = np.abs(s_fir[:-P] - s_fir[P:])
    env_fir = np.array([err_fir[i:i+P].max() for i in range(len(err_fir)-P)])
    err_iir = np.abs(s_iir[:-P] - s_iir[P:])
    env_iir = np.array([err_iir[i:i+P].max() for i in range(len(err_iir)-P)])
    err_ff = np.abs(s_ff[:-P] - s_ff[P:])
    env_ff = np.array([err_ff[i:i+P].max() for i in range(len(err_ff)-P)])
    plt.semilogy(env_fir, label= "linear FIR")
    plt.semilogy(env_iir, label= "linear IIR")
    plt.semilogy(env_ff, label="twice filter IIR")
    plt.xlim(0, 300)
    plt.legend()


    fig, ax = plt.subplots(2, 1, figsize=(12, 8))
    m: int = 2
    y_up, y_zs, Fs_new_up = interpolate(y, Fs, m)
    y_resample = signal.resample(y, 2*len(y))
    plot_spectrum(ax[0], y_up, Fs_new_up, label="interpolate signal")
    plot_spectrum(ax[1], y_resample, Fs_new_up, label="resample signal")

    d = measure_delay(y_up, y_resample, Fs_new_up, fc)
    pwr_diff = np.mean((y_up[d+200:] - y_resample[200:len(y_resample)-d]) ** 2)
    print(f"Power differens interpolate and resample {pwr_diff:.3e}")

if __name__ == "__main__":
    main()
    plt.show()