# python_DSP

MATLAB'dan Python/NumPy'a geçiş ve VUnit ile VHDL testbench kurma
öğrenme programı. Plan ve haftalık görevler `docs/` altında.

## Klasör yapısı

```
python_DSP/
├── dsp/                    # Hafta 5'te kurulan DSP paketi (asıl kütüphane)
│   ├── signals.py          #   sine_wave, add_awgn
│   ├── filters.py          #   fir1, frequency_response, apply_filter, LowPassFilter
│   ├── analysis.py         #   fft, measure_delay, find_cutoff, snr_calculate
│   ├── resampling.py       #   up_sample, down_sample, interpolate, decimate
│   └── plotting.py         #   sadece çizim — içinde hesap yok
├── tests/                  # pytest test seti (40 test)
│   ├── conftest.py         #   ortak fixture'lar
│   └── helpers.py          #   rms, FS, FC
├── hdl/                    # Hafta 6 — VHDL kaynakları
│   ├── src/                #   counter.vhd, fir_filter.vhd
│   └── tb/                 #   tb_counter.vhd, tb_fir_filter.vhd
├── vectors/                # üretilen CSV test vektörleri (git'e girmez)
├── docs/                   # öğrenme planı + haftalık görev dosyaları
├── weeks/                  # Hafta 1-4 çalışma script'leri (arşiv)
│   └── data/               #   olcumler.txt, sonuclar.txt
├── generate_vectors.py     # dsp/ ile test vektörü üretir  → vectors/
├── run.py                  # VUnit giriş noktası  (≈ conftest.py)
└── pytest.ini
```

`dsp/` + `tests/` üretim kodu; `weeks/` haftalık ödevlerin bırakıldığı
hâli, yeni koda referans olmaz.

## Çalıştırma

Python testleri (kök dizinden):

```bash
pytest
```

Kapsam raporu:

```bash
pytest --cov=dsp --cov-report=term-missing
```

VUnit testleri:

```bash
python run.py -v
```

Test vektörlerini üret:

```bash
python generate_vectors.py
```

## Gereksinimler

- Python 3.11+, `numpy`, `scipy`, `matplotlib`, `pytest`, `pytest-cov`
- `vunit_hdl` (Hafta 6)
- Bir VHDL simülatörü: NVC veya GHDL — `PATH`'te olmalı (`nvc --version`)
