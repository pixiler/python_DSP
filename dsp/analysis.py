import numpy as np
from scipy.signal import correlate, correlation_lags

# Bin indeksinin tamsayidan sapma toleransi. Float aritmetigi disindaki her
# sapma koherent olmayan bir pencere demektir (tolerans tablosu: ozdeslikler).
_BIN_TOL = 1e-9

# Bir tonun "var" sayilmasi icin sinyalin RMS'ine gore alt sinir. FFT'de
# bulunmayan bir frekansin genligi tam sifir degil, yuvarlama artigi kadar
# cikar (~1e-16). Bu yuzden `== 0.0` karsilastirmasi ise yaramaz; esik
# sinyalin kendi olcegine gore konur. -180 dB, herhangi bir gercek
# bilesenin cok altinda.
_TONE_PRESENT_REL = 1e-9

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

def tone_amplitude(x: np.ndarray, fs: float, tone_hz: float) -> float:
    """Koherent orneklenmis bir sinyalde tek bir tonun tepe genligi.

    Genlik tek bir FFT bin'inden okunur: gercek bir sinusun enerjisi +f ve -f
    binleri arasinda esit bolundugu icin tepe genlik ``2*|X[k]|/N`` olur.

    Pencere koherent olmalidir, yani ``tone_hz`` tam bir bin merkezine
    dusmelidir (``tone_hz * N / fs`` tamsayi). Aksi halde enerji komsu binlere
    sizar ve okunan genlik gercektekinden dusuk cikar. Bu durum sessizce yanlis
    sonuc uretmemesi icin hata olarak bildirilir.

    Args:
        x: Zaman domeninde sinyal ornekleri (1-B).
        fs: Ornekleme frekansi (Hz).
        tone_hz: Genligi olculecek tonun frekansi (Hz).

    Returns:
        Tonun tepe genligi (giristeki birim neyse o).

    Raises:
        ValueError: Pencere bu ton icin koherent degilse, ya da ton DC veya
            Nyquist'e dusuyorsa (o binlerde 2 carpani gecersizdir).
    """
    x = np.asarray(x, dtype=np.float64)
    n = x.size

    k_exact = tone_hz * n / fs
    k = int(round(k_exact))

    if abs(k_exact - k) > _BIN_TOL:
        raise ValueError(
            f"koherent olmayan pencere: {tone_hz} Hz, fs={fs}, N={n} icin "
            f"bin {k_exact:.4f} (tamsayi olmali). Pencere uzunlugunu tonun tam "
            f"periyot sayisina esitleyin."
        )

    if k == 0 or 2 * k == n:
        raise ValueError(
            f"tone_amplitude DC ve Nyquist icin kullanilamaz (bin {k}, N={n}); "
            f"bu binlerde tek yanli genlik donusumu (2x) gecersizdir."
        )

    return float(2.0 * np.abs(np.fft.fft(x)[k]) / n)


def suppression_db(
    y: np.ndarray, x: np.ndarray, fs: float, tone_hz: float
) -> float:
    """Belirli bir tonda cikisin girise gore kazanci, dB cinsinden.

    Tum sinyalin RMS'i degil, **yalnizca hedef tondaki** bilesen olculur.
    Cok tonlu bir sinyalde toplam RMS orani tek bir tonun bastirilmasi hakkinda
    bilgi vermez; gecen bilesenler orani domine eder.

    Args:
        y: Cikis (bastirilmis) sinyal.
        x: Giris (referans) sinyal.
        fs: Ornekleme frekansi (Hz).
        tone_hz: Olculecek tonun frekansi (Hz).

    Returns:
        20*log10(|Y(f)| / |X(f)|). Zayiflatma negatif, kazanc pozitif cikar.
        Cikis bileseni tam olarak sifirsa ``-inf`` doner.

    Raises:
        ValueError: Diziler ayni uzunlukta degilse, giriste hedef ton yoksa
            veya pencere koherent degilse.
    """
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)

    if x.size != y.size:
        raise ValueError(
            f"giris ve cikis ayni pencerede olmali: len(x)={x.size}, "
            f"len(y)={y.size}"
        )

    taban = _TONE_PRESENT_REL * float(np.sqrt(np.mean(x**2)))

    amp_in = tone_amplitude(x, fs, tone_hz)
    if amp_in <= taban:
        raise ValueError(
            f"giriste {tone_hz} Hz bileseni yok (genlik {amp_in:.3e}, "
            f"taban {taban:.3e}); bastirma tanimsiz."
        )

    amp_out = tone_amplitude(y, fs, tone_hz)
    if amp_out == 0.0:
        return float("-inf")

    return float(20.0 * np.log10(amp_out / amp_in))

