-- FIR tasarimi icin ortak tip ve yardimci fonksiyonlar.
-- Elle yazilir; katsayi degerleri buraya girmez (bkz. fir_coeffs_pkg.vhd).

library ieee;
use ieee.std_logic_1164.all;

package fir_pkg is

    type coef_array_type is array (natural range <>) of integer;

    -- Katsayilarin mutlak toplami. Akumulator genisligi bundan turetilir:
    --     max|acc| <= max|x| * sum|h|
    function sum_abs(arr : coef_array_type) return natural;

    -- Dizideki en buyuk mutlak deger (katsayi genisligi dogrulamasi icin).
    function max_abs(arr : coef_array_type) return natural;

end package fir_pkg;


package body fir_pkg is

    function sum_abs(arr : coef_array_type) return natural is
        variable total : natural := 0;
    begin
        for i in arr'range loop
            total := total + abs(arr(i));
        end loop;
        return total;
    end function sum_abs;

    function max_abs(arr : coef_array_type) return natural is
        variable peak : natural := 0;
    begin
        for i in arr'range loop
            if abs(arr(i)) > peak then
                peak := abs(arr(i));
            end if;
        end loop;
        return peak;
    end function max_abs;

end package body fir_pkg;
