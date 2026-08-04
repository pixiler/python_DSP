-- OTOMATIK URETILDI — generate_vectors.py
-- Elle duzenlemeyin; degisiklikler bir sonraki calistirmada silinir.
--
-- Fs = 50000 Hz, kesim = 2000 Hz, tap = 17
-- Format Q1.15 (olcek 2**15), DC kazanci = 32769

library ieee;
use ieee.std_logic_1164.all;

use work.fir_pkg.all;

package fir_coeffs_pkg is

    constant FIR_NUM_TAPS : natural := 17;

    constant FIR_COEFFS : coef_array_type(0 to FIR_NUM_TAPS - 1) := (
        151,
        269,
        596,
        1156,
        1903,
        2727,
        3479,
        4006,
        4195,
        4006,
        3479,
        2727,
        1903,
        1156,
        596,
        269,
        151
    );

end package fir_coeffs_pkg;
