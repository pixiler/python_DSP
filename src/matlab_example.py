import numpy as np
import matplotlib.pyplot as plt
import scipy.signal as signal

def sine_wave(frequency: float, duration: float, sample_rate: int) -> np.ndarray:
    """
    Generates a sine wave signal.

    Args:
        frequency (float): Frequency of the sine wave in Hz.
        duration (float): Duration of the signal in seconds.
        sample_rate (int): Sampling rate in samples per second.

    Returns:
        np.ndarray: An array containing the generated sine wave samples.
    """
    
    t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)
    return np.sin(2 * np.pi * frequency * t)


def plot_signal(axes: plt.Axes, signal: np.ndarray, sample_rate: int, frequency: float, nSines: int) -> None:
    """
    Plots the given signal.

    Args:
        axes (plt.Axes): The axes on which to plot the signal.
        signal (np.ndarray): The signal to be plotted.
        sample_rate (int): Sampling rate in samples per second.
        frequency (float): Frequency of the sine wave in Hz.
        nSines (int): The number of sine waves to display.
    """
    t = np.arange(len(signal)) / sample_rate
    axes.plot(t, signal, '.-')
    axes.set_xlim(0, nSines/frequency)  # Show one period of the sine wave
    axes.set_title(f"Sine Wave Signal ({frequency} Hz)")
    axes.set_xlabel("Time [s]")
    axes.set_ylabel("Amplitude")
    axes.grid()

def fir1(N: int, Wn: float) -> np.ndarray:
    """
    Designs a low-pass FIR filter using the window method.

    Args:
        N (int): The order of the filter (number of taps).
        Wn (float): The normalized cutoff frequency (0 < Wn < 1).

    Returns:
        np.ndarray: The filter coefficients.
    """
    N = N + 1 if N % 2 == 0 else N  # Ensure N is odd for symmetry
    return signal.firwin(N, Wn)

def freqz(h: np.ndarray, worN: int, fs: int) -> tuple:
    """
    Computes the frequency response of a digital filter.

    Args:
        h (np.ndarray): The filter coefficients.
        worN (int): The number of frequency points to compute.
        fs (int): The sampling frequency.

    Returns:
        tuple: A tuple containing the frequencies and the frequency response.
    """
    w, h_freq = signal.freqz(h, worN=worN, fs=fs)

    mag_db = 20 * np.log10(np.abs(h_freq))

    cross_indices = np.diff(np.sign(mag_db - (-6)))  # Find the index where the magnitude response crosses -6 dB
    f_c = w[np.where(cross_indices)[0][0]] if np.any(cross_indices) else None # Find the cutoff frequency at -6 dB point
    
    plt.figure(figsize=(10, 6))
    plt.plot(w, mag_db, 'b')
    if f_c is not None:
        plt.axvline(f_c, color='r', linestyle='--', label=f'Cutoff Frequency: {f_c:.2f} Hz')
        plt.legend()
        plt.annotate(f'Cutoff Frequency: {f_c:.2f} Hz', xy=(f_c, -6), xytext=(f_c + 1000, -20),
                     arrowprops=dict(facecolor='black', shrink=0.05))
        plt.plot(f_c, -6, 'ro')  # Mark the cutoff frequency point
    plt.title("Frequency Response of the FIR Filter")
    plt.xlabel("Frequency [Hz]")
    plt.ylabel("Magnitude [dB]")
    plt.grid()
    plt.show()

    return w, h_freq

def fft(signal: np.ndarray, sample_rate: int) -> tuple:
    """
    Computes the Fast Fourier Transform (FFT) of a signal.

    Args:
        signal (np.ndarray): The input signal.
        sample_rate (int): The sampling rate in samples per second.

    Returns:
        tuple: A tuple containing the frequency bins and the FFT of the signal.
    """
    N = len(signal)
    f = np.arange(-N/2, N/2) * (sample_rate / N)  # Frequency bins
    fft_values = np.fft.fft(signal)
    fft_values = np.fft.fftshift(fft_values) / N  # Normalize and shift the FFT output
    return fft_values, f

def fir_filter(input_signal: np.ndarray, h: np.ndarray) -> np.ndarray:
    """
    Filters a signal using the given FIR filter coefficients.

    Args:
        input_signal (np.ndarray): The input signal to be filtered.
        h (np.ndarray): The FIR filter coefficients.

    Returns:
        np.ndarray: The filtered signal.
    """
    return signal.lfilter(h, 1.0, input_signal)

def plot_spectrum(axes: plt.Axes, signal: np.ndarray, sample_rate: int, label: str = None, xscale: str = 'linear') -> None:
    """
    Plots the magnitude spectrum of a signal.

    Args:
        axes (plt.Axes): The axes on which to plot the spectrum.
        signal (np.ndarray): The input signal.
        sample_rate (int): The sampling rate in samples per second.
        label (str, optional): The label for the plot.
        xscale (str, optional): xscale for the plot.
    """
    fft_values, f = fft(signal, sample_rate)
    magnitude = np.abs(fft_values)

    if xscale == 'log':
        axes.plot(f[len(f)//2+1:], magnitude[len(magnitude)//2+1:], label = label)
    else :
        axes.plot(f, magnitude, label = label)
    
    axes.legend()
    axes.set_title("Magnitude Spectrum")
    axes.set_xlabel("Frequency [Hz]")
    axes.set_ylabel("Magnitude")
    axes.set_xscale(xscale)
    
    axes.grid()

def main() -> None:

    fc_1 : float = 2e3
    fc_2 : float = 10e3
    Fs : int = 50e3
    t : float = 0.1

    print(f"fc_1: {fc_1}, fc_2: {fc_2}, Fs: {Fs}")
    sine_wave_samples_1 = sine_wave(fc_1, t, Fs)
    sine_wave_samples_2 = sine_wave(fc_2, t, Fs)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 10))
    plot_signal(ax1, sine_wave_samples_1, Fs, fc_1, 1)
    plot_signal(ax2, sine_wave_samples_2, Fs, fc_2, 1)

    sine_wave_samples_3 = sine_wave_samples_1 + sine_wave_samples_2
    plt.figure(figsize=(10, 6)) 
    ax3 = plt.axes()
    plot_signal(ax3, sine_wave_samples_3, Fs, fc_1, 5)
    plt.show()

    Wn : float = fc_1 / (Fs / 2)  # Normalized cutoff frequency
    N : int = 64  # Filter order
    h = fir1(N, Wn)
    freqz(h, 1024, Fs)

    sine_wave_samples_filtered = fir_filter(sine_wave_samples_3, h)
    plt.figure(figsize=(10, 6))
    plot_signal(plt.gca(), sine_wave_samples_filtered, Fs, fc_1, 5)
    plot_signal(plt.gca(), sine_wave_samples_1, Fs, fc_1, 5)
    plt.show()

    fig, axs = plt.subplots(2, 2, figsize=(12, 15))
    plot_spectrum(axs[0, 0], sine_wave_samples_filtered, Fs, label="Filtered Signal")
    plot_spectrum(axs[0, 1], sine_wave_samples_1, Fs, label="Original Signal")
    plot_spectrum(axs[1, 0], sine_wave_samples_2, Fs, label="High Frequency Signal")
    plot_spectrum(axs[1, 1], sine_wave_samples_3, Fs, label="Combined Signal")
    plt.show()

if __name__ == "__main__":
    main()
