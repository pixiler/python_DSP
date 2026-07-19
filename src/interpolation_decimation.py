from matlab_example import fir1, fir_filter, plot_signal, sine_wave, plot_spectrum, fft
import numpy as np
import matplotlib.pyplot as plt


def up_sample(signal: np.ndarray, factor: int) -> np.ndarray:
    """
    Upsamples the input signal by a given factor.

    Args:
        signal (np.ndarray): The input signal to be upsampled.
        factor (int): The upsampling factor.

    Returns:
        np.ndarray: The upsampled signal.
    """
    upsampled_signal = np.zeros(len(signal) * factor)
    upsampled_signal[::factor] = signal
    return upsampled_signal

def down_sample(signal: np.ndarray, factor: int) -> np.ndarray:
    """
    Downsamples the input signal by a given factor.

    Args:
        signal (np.ndarray): The input signal to be downsampled.
        factor (int): The downsampling factor.

    Returns:
        np.ndarray: The downsampled signal.
    """
    return signal[::factor]

def interpolate(signal: np.ndarray, Fs: int, factor: int) -> tuple[np.ndarray, np.ndarray, int]:
    """
    Interpolates the input signal by a given factor using zero-order hold.

    Args:
        signal (np.ndarray): The input signal to be interpolated.
        Fs (int): The original sampling frequency.
        factor (int): The interpolation factor.

    Returns:
        np.ndarray: The interpolated signal.
        np.ndarray: The upsampled signal.
        int: The new sampling frequency.
    """

    y_zs = up_sample(signal, factor)
    Fs_new = factor * Fs
    b_i = factor * fir1(64, (len(signal)/2) / (Fs_new / 2))
    y_up = fir_filter(y_zs, b_i)
    return y_up, y_zs, Fs_new

def decimate(signal: np.ndarray, Fs: int, factor: int) -> tuple[np.ndarray, np.ndarray, int]:
    """
    Decimates the input signal by a given factor using zero-order hold.

    Args:
        signal (np.ndarray): The input signal to be decimated.
        Fs (int): The original sampling frequency.
        factor (int): The decimation factor.

    Returns:
        np.ndarray: The downsampled signal.
        np.ndarray: The decimated signal.
        int: The new sampling frequency.
    """
    b_d = fir1(64, (Fs/(2*factor)) / (Fs / 2))
    y_filt = fir_filter(signal, b_d)
    y_ds = down_sample(y_filt, factor)
    Fs_new = Fs // factor
    return y_ds, y_filt, Fs_new

def main() -> None:
    m: int = 2
    fc : float = 2e3
    Fs : int = 50e3
    t : float = 0.1
    y1 = sine_wave(fc, t, Fs)
    plt.figure(figsize=(10, 4))
    plot_signal(plt.gca(), y1, Fs, fc, 1)
    plt.show()

    y_up, y_zs, Fs_new_up = interpolate(y1, Fs, m)
    y_ds, y_filt, Fs_new_dec = decimate(y1, Fs, m)

    fig, ax = plt.subplots(3, 1, figsize=(10, 4)) 
    plot_spectrum(ax[0], y1, Fs, label="Original Signal")
    plot_spectrum(ax[1], y_zs, Fs_new_up, label="Upsampled Signal")
    plot_spectrum(ax[2], y_up, Fs_new_up, label="Filtered Signal")
    plt.show()

    fig, ax = plt.subplots(3, 1, figsize=(10, 4)) 
    plot_spectrum(ax[0], y1, Fs, label="Original Signal")
    plot_spectrum(ax[1], y_filt, Fs, label="Decimated Signal")
    plot_spectrum(ax[2], y_ds, Fs_new_dec, label="Filtered Signal")
    plt.show()


if __name__ == "__main__":
    main()  