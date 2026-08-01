import numpy as np
from dsp.filters import fir1, apply_filter, apply_filtfilt, LowPassFilter
from dsp.analysis import measure_delay, snr_calculate
from dsp.signals import sine_wave, add_awgn
from helpers import rms, FS, FC 
import pytest 

def test_fir1_cift_dereceden_tek_sayida_katsayi_dondurur():
    h = fir1(64, 0.08)
    assert len(h) == 65

def test_apply_filter_cikis_uzunlugu_girise_esit(test_sinyali):
    h = fir1(64, 0.08)
    y = apply_filter(test_sinyali,h)
    assert len(y) == len(test_sinyali)

def test_group_delay_equal_tapin_bir_eksiginin_yarisidir(test_sinyali):
    
    h = fir1(64, 0.08)
    y = apply_filter(test_sinyali,h)
    assert measure_delay(y, test_sinyali, Fs=FS, fc=FC) == (len(h) - 1) / 2

def test_bant_disi_ton_en_az_40dB_bastirilir():
    s = sine_wave(10e3, 0.1, FS)
    h = fir1(64, 2e3/(FS/2))
    y = apply_filter(s, h)
    zayiflatma_db = 20 * np.log10(rms(y[100:]) / rms(s[100:]))
    assert zayiflatma_db <= -40

def test_bant_ici_ton_en_fazla_1dB_kaybeder():
    s = sine_wave(1e3, 0.1, FS)
    h = fir1(64, 2e3/(FS/2))
    y = apply_filter(s, h)
    zayiflatma_db = 20 * np.log10(rms(y[100:]) / rms(s[100:]))
    assert zayiflatma_db >= -1

def test_filtfilt_group_delay_zero(test_sinyali):
    h = fir1(64, 2e3/(FS/2))
    y = apply_filtfilt(test_sinyali, h)
    assert measure_delay(y, test_sinyali, Fs=FS, fc=FC) == 0

@pytest.mark.parametrize("Wn", [1.5, 1.0, 0.0, -0.2])
def test_fir1_gecersiz_Wn_icin_hata_verir(Wn):
    with pytest.raises(ValueError, match="Invalid cutoff frequency"):
        fir1(64, Wn)

def test_class_apply_filter_cikis_uzunlugu_girise_esit(test_sinyali):
    lpf = LowPassFilter(cutoff_hz=2000, fs=50_000, order=64, kind="fir")
    y = lpf.apply(test_sinyali)
    assert len(y) == len(test_sinyali)

def test_class_group_delay_tapin_bir_eksiginin_yarisi(test_sinyali):
    lpf = LowPassFilter(cutoff_hz=2000, fs=FS, order=64, kind="fir")
    y = lpf.apply(test_sinyali)
    olculen = measure_delay(y, test_sinyali, Fs=FS, fc=FC)
    assert olculen == lpf.group_delay_samples

def test_class_group_delay_IIR_ortalama_hesaplar(test_sinyali):
    lpf = LowPassFilter(cutoff_hz=2000, fs=FS, order=4, kind="iir")
    y = lpf.apply(test_sinyali)
    olculen = measure_delay(y, test_sinyali, Fs=FS, fc=FC)
    assert olculen == pytest.approx(lpf.group_delay_at(FC), abs=1.0)

def test_lowpassfilter_gecersiz_kind_icin_hata_verir():
    with pytest.raises(ValueError, match="kind"):
        LowPassFilter(cutoff_hz=2000, fs=FS, kind="bandpass")

def test_regresyon_fir_snr_iyilesmesi(test_sinyali, rng):
    _, noise = add_awgn(test_sinyali, 0.0, rng=rng)
    lpf = LowPassFilter(2000, FS, order=64, kind="fir")
    s_f = lpf.apply(test_sinyali)
    n_f = lpf.apply(noise)
    d = lpf.group_delay_samples
    iyilesme = snr_calculate(s_f[d:], n_f[d:])
    assert iyilesme == pytest.approx(11.2, abs=0.5)

def test_class_group_delay_filtfilt_uygulandiginda_sifir_olur(test_sinyali):
    lpf = LowPassFilter(cutoff_hz=2000, fs=FS, order=4, kind="iir")
    y = lpf.apply_zero_phase(test_sinyali)
    olculen = measure_delay(y, test_sinyali, Fs=FS, fc=FC)
    assert olculen == pytest.approx(0, abs=1.0)

def test_group_delay_samples_iir_icin_hata_verir():
    lpf = LowPassFilter(2000, FS, order=4, kind="iir")
    with pytest.raises(ValueError, match="group_delay_at"):
        lpf.group_delay_samples

def test_group_delay_at_fir_icin_hata_verir():
    lpf = LowPassFilter(2000, FS, order=64, kind="fir")
    with pytest.raises(ValueError, match="group_delay_samples"):
        lpf.group_delay_at(FC)
