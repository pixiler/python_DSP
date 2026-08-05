
import pytest
import numpy as np
from dsp.analysis import fft, find_cutoff, tone_amplitude, suppression_db
from dsp.filters import LowPassFilter
from dsp.signals import sine_wave
from helpers import FS, FC, DURATION

def test_fft_tepesi_dogru_binde(test_sinyali):
    Y, f = fft(test_sinyali, FS)
    mag = np.abs(Y)
    pozitif = f >= 0
    delta_f = FS / len(test_sinyali)
    assert f[pozitif][np.argmax(mag[pozitif])] == pytest.approx(FC, abs=delta_f/2)
    

def test_fft_tepe_genligi_yarim(test_sinyali):
    Y, _ = fft(test_sinyali, FS)
    assert np.max(np.abs(Y)) == pytest.approx(0.5, rel=0.01)

def test_parseval_zaman_ve_frekans_gucu_esit(test_sinyali):
    Y, _ = fft(test_sinyali, FS)
    pwr_time = np.mean(test_sinyali**2)
    pwr_freq = np.sum(np.abs(Y)**2)
    assert pwr_time == pytest.approx(pwr_freq, rel=1e-9)

def test_fir_kesim_frekansi_minus_6db_noktasi():
    lpf = LowPassFilter(cutoff_hz=FC, fs=FS, order=64, kind="fir")
    worN : int = 1024
    w, h = lpf.response(worN= worN)
    cutoff = find_cutoff(w, h, level_db=-6.0)
    assert cutoff == pytest.approx(FC, abs=2*(FS/2)/worN)

def test_butter_kesim_frekansi_minus_3db_noktasi():
    lpf = LowPassFilter(cutoff_hz=FC, fs=FS, order=4, kind="iir")
    worN : int = 1024
    w, h = lpf.response(worN= worN)
    cutoff = find_cutoff(w, h, level_db=-3.0)
    assert cutoff == pytest.approx(FC, abs=2*(FS/2) / worN)

def iki_tonlu(a1: float, f1: float, a2: float, f2: float) -> np.ndarray:
    """Iki sinusun toplami; her ikisi de FS'te koherent."""
    return a1 * sine_wave(f1, DURATION, FS) + a2 * sine_wave(f2, DURATION, FS)
 
 
# --------------------------------------------------------------------------
# tone_amplitude
# --------------------------------------------------------------------------
 
@pytest.mark.parametrize("genlik", [0.1, 1.0, 3.5])
def test_tone_amplitude_saf_sinus_genligini_bulur(genlik):
    x = genlik * sine_wave(FC, DURATION, FS)
    assert tone_amplitude(x, FS, FC) == pytest.approx(genlik, rel=1e-9)
 
 
def test_tone_amplitude_iki_tonu_birbirinden_ayirir():
    """Asil kullanim: cok tonlu sinyalde her tonu ayri olcmek.
 
    RMS tabanli bir olcum bu testi gecemez -- toplam RMS iki tonun
    bilesenidir, tek bir tonun genligini vermez.
    """
    x = iki_tonlu(0.4, 1e3, 0.1, 10e3)
    assert tone_amplitude(x, FS, 1e3) == pytest.approx(0.4, rel=1e-9)
    assert tone_amplitude(x, FS, 10e3) == pytest.approx(0.1, rel=1e-9)
 
 
def test_tone_amplitude_bulunmayan_tonda_sifira_yakin():
    x = sine_wave(FC, DURATION, FS)
    assert tone_amplitude(x, FS, 10e3) == pytest.approx(0.0, abs=1e-12)
 
 
def test_tone_amplitude_koherent_olmayan_pencere_hata_verir():
    """Pencere tam periyot sayisi icermezse sessiz sapma yerine hata."""
    x = sine_wave(FC, DURATION, FS)[:483]  # 1 kHz -> bin 9,66
    with pytest.raises(ValueError, match="koherent olmayan pencere"):
        tone_amplitude(x, FS, FC)
 
 
@pytest.mark.parametrize("tone_hz", [0.0, FS / 2])
def test_tone_amplitude_dc_ve_nyquist_hata_verir(tone_hz):
    """Bu binlerde tek yanli genlik donusumundeki 2 carpani gecersiz."""
    x = sine_wave(FC, DURATION, FS)
    with pytest.raises(ValueError, match="DC ve Nyquist"):
        tone_amplitude(x, FS, tone_hz)
 
 
def test_tone_amplitude_gecikmeden_etkilenmez():
    """Genlik buyuklugu faza bagli degildir; hizalama gerekmez."""
    n = int(FS * DURATION)
    t = np.arange(n) / FS
    x = np.sin(2 * np.pi * FC * t)
    x_kaymis = np.sin(2 * np.pi * FC * t + 0.7)
    assert tone_amplitude(x_kaymis, FS, FC) == pytest.approx(
        tone_amplitude(x, FS, FC), rel=1e-9
    )
 
 
# --------------------------------------------------------------------------
# suppression_db
# --------------------------------------------------------------------------
 
def test_suppression_db_ayni_sinyalde_sifir_db():
    x = sine_wave(FC, DURATION, FS)
    assert suppression_db(x, x, FS, FC) == pytest.approx(0.0, abs=1e-9)
 
 
@pytest.mark.parametrize(
    "kazanc, beklenen_db", [(0.5, -6.0206), (0.1, -20.0), (2.0, 6.0206)]
)
def test_suppression_db_bilinen_kazanci_olcer(kazanc, beklenen_db):
    x = sine_wave(FC, DURATION, FS)
    assert suppression_db(kazanc * x, x, FS, FC) == pytest.approx(
        beklenen_db, abs=1e-4
    )
 
 
def test_suppression_db_sadece_hedef_tonu_olcer():
    """Kritik test: cok tonlu sinyalde yalnizca hedef ton dikkate alinmali.
 
    Giriste esit iki ton; cikista 10 kHz 100 kat bastirilmis, 1 kHz dokunulmamis.
    Toplam RMS orani ~-3 dB verirdi; dogru olcum 10 kHz'de -40 dB, 1 kHz'de 0 dB.
    """
    x = iki_tonlu(0.4, 1e3, 0.4, 10e3)
    y = iki_tonlu(0.4, 1e3, 0.004, 10e3)
 
    assert suppression_db(y, x, FS, 10e3) == pytest.approx(-40.0, abs=1e-6)
    assert suppression_db(y, x, FS, 1e3) == pytest.approx(0.0, abs=1e-9)
 
 
def test_suppression_db_sifir_giriste_hata_verir():
    """Giriste hedef ton yoksa oran tanimsiz; 0 dB dondurmek yalan olurdu."""
    x = sine_wave(FC, DURATION, FS)
    y = sine_wave(10e3, DURATION, FS)
    with pytest.raises(ValueError, match="bastirma tanimsiz"):
        suppression_db(y, x, FS, 10e3)
 
 
def test_suppression_db_uzunluk_uyusmazliginda_hata_verir():
    """Dilimleme hatasini yakalar: [skip:n] ile [skip:skip+n] karisimi."""
    x = sine_wave(FC, DURATION, FS)
    with pytest.raises(ValueError, match="ayni pencerede"):
        suppression_db(x[:-1], x, FS, FC)
 
 
def test_suppression_db_tam_bastirmada_eksi_sonsuz():
    x = sine_wave(FC, DURATION, FS)
    y = np.zeros_like(x)
    assert suppression_db(y, x, FS, FC) == float("-inf")