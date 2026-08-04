-- Transpoze yapida FIR filtre.
--
-- Sabit noktali konvansiyonlar (generate_vectors.py ile ayni olmali):
--     Format     : Q1.15 giris, Q1.15 cikis, Q2.30 akumulator
--     Yuvarlama  : round-half-up (acc + 2**(DISCARDED_BITS-1), sonra kaydir)
--     Tasma      : doygunluk (sarma degil)
--     Gecikme    : 1 saat cevrimi (valid_out, valid_in'in bir cevrim gecikmisi)
--
-- Not: grup gecikmesi (NUM_TAPS-1)/2 filtrenin matematiginden gelir ve
-- beklenen cikisin icinde zaten vardir; yukaridaki 1 cevrim ise bu
-- uygulamanin pipeline gecikmesidir. Ikisi ayri seylerdir.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

use work.fir_pkg.all;
use work.fir_coeffs_pkg.all;

entity fir_filter is
    generic (
        DATA_WIDTH : integer := 16;            -- Giris/cikis genisligi (Q1.15)
        COEF_WIDTH : integer := 16;            -- Katsayi genisligi (Q1.15)
        NUM_TAPS   : integer := FIR_NUM_TAPS;
        COEFFS     : coef_array_type(0 to FIR_NUM_TAPS - 1) := FIR_COEFFS
    );
    port (
        clk       : in  std_logic;
        rst       : in  std_logic;                                -- asenkron, aktif yuksek

        valid_in  : in  std_logic;
        x_in      : in  std_logic_vector(DATA_WIDTH - 1 downto 0);

        valid_out : out std_logic;
        y_out     : out std_logic_vector(DATA_WIDTH - 1 downto 0)
    );
end entity fir_filter;


architecture rtl of fir_filter is

    constant MULT_WIDTH     : integer := DATA_WIDTH + COEF_WIDTH;   -- 32, Q2.30
    constant IN_FRAC_BITS   : integer := DATA_WIDTH - 1;            -- 15
    constant COEF_FRAC_BITS : integer := COEF_WIDTH - 1;            -- 15
    constant MULT_FRAC_BITS : integer := IN_FRAC_BITS + COEF_FRAC_BITS;  -- 30
    constant OUT_FRAC_BITS  : integer := DATA_WIDTH - 1;            -- 15
    constant DISCARDED_BITS : integer := MULT_FRAC_BITS - OUT_FRAC_BITS; -- 15

    -- Kirpma yerine yuvarlama: atilacak kismin en anlamli bitine 1 ekle.
    -- Kirpma (dogrudan kaydirma) asagi yuvarlar ve ortalama -0,5 LSB
    -- sistematik negatif sapma yaratir.
    constant ROUND_ADDEND : integer := 2 ** (DISCARDED_BITS - 1);

    -- Yuvarlama toplamasi tasabilecegi icin bir bit genis calisilir.
    constant EXT_WIDTH : integer := MULT_WIDTH + 1;

    -- Doygunluk kontrolu: bu indeksin ustundeki tum bitler isaret biti ile
    -- ayni olmalidir, yoksa sonuc DATA_WIDTH'e sigmiyor demektir.
    constant SAT_MSB : integer := DISCARDED_BITS + DATA_WIDTH - 1;  -- 30

    constant OUT_MAX : integer := 2 ** (DATA_WIDTH - 1) - 1;        --  32767
    constant OUT_MIN : integer := -(2 ** (DATA_WIDTH - 1));         -- -32768

    type acc_array_type is array (0 to NUM_TAPS - 1) of signed(MULT_WIDTH - 1 downto 0);

    signal mult_res : acc_array_type;
    signal x_signed : signed(DATA_WIDTH - 1 downto 0);

    -- Baslangic degerleri: zaman 0'da 'U' okunmasin. Reset zaten sifirliyor,
    -- ama reset yayilmadan onceki ilk delta'da cikis katinin 'U' ile
    -- karsilastirma yapmasini (metavalue uyarisi) bu engelliyor. FPGA'de de
    -- kaydediciler yapilandirmada tanimli bir degerle baslar.
    signal acc_reg  : acc_array_type := (others => (others => '0'));
    signal valid_q  : std_logic := '0';

begin

    ---------------------------------------------------------------------------
    -- ELABORASYON ZAMANI KONTROLLERI
    ---------------------------------------------------------------------------
    -- max|acc| <= 2**(DATA_WIDTH-1) * sum|h| < 2**(MULT_WIDTH-1)
    -- ==> sum|h| < 2**(MULT_WIDTH - DATA_WIDTH)
    -- (Esitsizlik bu haliyle yazilir; 2**(MULT_WIDTH-1) VHDL integer'ina sigmaz.)
    assert sum_abs(COEFFS) < 2 ** (MULT_WIDTH - DATA_WIDTH)
        report "akumulator tasar: sum|h| = " & integer'image(sum_abs(COEFFS))
             & ", sinir = " & integer'image(2 ** (MULT_WIDTH - DATA_WIDTH))
        severity failure;

    assert max_abs(COEFFS) <= 2 ** (COEF_WIDTH - 1)
        report "katsayi COEF_WIDTH'e sigmiyor: max|h| = "
             & integer'image(max_abs(COEFFS))
        severity failure;

    assert COEFFS'length = NUM_TAPS
        report "COEFFS uzunlugu NUM_TAPS ile uyusmuyor"
        severity failure;

    ---------------------------------------------------------------------------
    -- CARPMA KATI (kombinasyonel)
    ---------------------------------------------------------------------------
    x_signed <= signed(x_in);

    gen_mults : for i in 0 to NUM_TAPS - 1 generate
        mult_res(i) <= x_signed * to_signed(COEFFS(i), COEF_WIDTH);
    end generate gen_mults;

    ---------------------------------------------------------------------------
    -- TRANSPOZE TOPLAMA HATTI
    ---------------------------------------------------------------------------
    accumulate : process(clk, rst)
    begin
        if rst = '1' then
            valid_q <= '0';
            for i in 0 to NUM_TAPS - 1 loop
                acc_reg(i) <= (others => '0');
            end loop;

        elsif rising_edge(clk) then
            valid_q <= valid_in;

            if valid_in = '1' then
                acc_reg(NUM_TAPS - 1) <= mult_res(NUM_TAPS - 1);

                for i in 0 to NUM_TAPS - 2 loop
                    acc_reg(i) <= mult_res(i) + acc_reg(i + 1);
                end loop;
            end if;
        end if;
    end process accumulate;

    ---------------------------------------------------------------------------
    -- YUVARLAMA + DOYGUNLUK + CIKIS
    ---------------------------------------------------------------------------
    output_stage : process(all)
        variable acc_ext : signed(EXT_WIDTH - 1 downto 0);
        variable guard   : signed(EXT_WIDTH - 1 downto SAT_MSB);
    begin
        acc_ext := resize(acc_reg(0), EXT_WIDTH)
                 + to_signed(ROUND_ADDEND, EXT_WIDTH);

        -- SAT_MSB ustundeki bitler ya hep '0' (=0) ya hep '1' (=-1) olmali
        guard := acc_ext(EXT_WIDTH - 1 downto SAT_MSB);

        if guard = 0 or guard = -1 then
            y_out <= std_logic_vector(acc_ext(SAT_MSB downto DISCARDED_BITS));
        elsif acc_ext(EXT_WIDTH - 1) = '0' then
            y_out <= std_logic_vector(to_signed(OUT_MAX, DATA_WIDTH));
        else
            y_out <= std_logic_vector(to_signed(OUT_MIN, DATA_WIDTH));
        end if;
    end process output_stage;

    valid_out <= valid_q;

end architecture rtl;