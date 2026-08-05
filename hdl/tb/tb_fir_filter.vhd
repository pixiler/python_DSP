-- FIR filtre testbench'i.
--
-- Zamanlama konvansiyonu: tum surme ve okuma islemleri yukselen kenardan
-- HOLD kadar sonra yapilir. Izleyici process dusen kenarda calisir, boylece
-- suren ve olcen kod ayni zaman adimini paylasmaz.
--
-- Hizalama: beklenen cikis nedensel bir referanstan uretildigi icin filtrenin
-- grup gecikmesi (NUM_TAPS-1)/2 zaten expected.csv'nin icindedir. Burada
-- yalnizca uygulamanin pipeline gecikmesi hizalanir ve bu da valid_out
-- izlenerek yapilir -- hicbir yerde cevrim sayisi sabitlenmez.

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;

use work.fir_coeffs_pkg.all;

entity tb_fir_filter is
  generic (
    runner_cfg      : string;
    -- Hangi katsayi setiyle kurulacak. add_config bu generic'i degistirerek
    -- ayni testbench'i farkli tap sayilariyla kosturur.
    config_id       : natural := FIR_DEFAULT_CONFIG;
    input_csv       : string;
    expected_csv    : string;
    input_dc_csv    : string;
    expected_dc_csv : string
  );
end entity tb_fir_filter;


architecture bench of tb_fir_filter is

  constant C_DATA_WIDTH : natural := 16;
  constant C_COEF_WIDTH : natural := 16;
  constant C_PERIOD     : time    := 10 ns;
  constant HOLD         : time    := 1 ns;   -- kenardan sonra okuma/surme gecikmesi

  constant DRAIN_CYCLES   : natural := 4;    -- besleme sonrasi bosaltma
  constant IDLE_CYCLES    : natural := 5;    -- valid dusukken beklenen sure
  constant MONITOR_CYCLES : natural := 5;    -- kac cevrim log basilacak

  constant Q15_MAX : integer := 2 ** (C_DATA_WIDTH - 1) - 1;

  signal clk : std_logic := '0';
  signal rst : std_logic := '1';

  signal valid_in : std_logic := '0';
  signal x_in     : std_logic_vector(C_DATA_WIDTH - 1 downto 0) := (others => '0');

  signal valid_out : std_logic;
  signal y_out     : std_logic_vector(C_DATA_WIDTH - 1 downto 0);

begin

  gen_clk : process
  begin
    clk <= '1';
    wait for C_PERIOD / 2;
    clk <= '0';
    wait for C_PERIOD / 2;
  end process gen_clk;


  DUT : entity work.fir_filter
    generic map (
      DATA_WIDTH => C_DATA_WIDTH,
      COEF_WIDTH => C_COEF_WIDTH,
      NUM_TAPS   => FIR_TAP_COUNTS(config_id),
      -- Dolgu sifirlarini disarida birak: dilim gercek tap sayisi kadar.
      COEFFS     => FIR_COEFF_SETS(config_id)(0 to FIR_TAP_COUNTS(config_id) - 1)
    )
    port map (
      clk       => clk,
      rst       => rst,
      valid_in  => valid_in,
      x_in      => x_in,
      valid_out => valid_out,
      y_out     => y_out
    );


  main : process
    variable input_data    : integer_array_t;
    variable expected_data : integer_array_t;
    variable compared      : natural := 0;
    variable captured      : integer_array_t;
    variable y_prev        : std_logic_vector(C_DATA_WIDTH - 1 downto 0);

    -- Reset uygula ve besleme icin temiz bir baslangic noktasi birak.
    -- valid_in reset boyunca dusuk tutulur; aksi halde DUT reset'ten cikarken
    -- tanimsiz bir ornegi yutar ve bir karsilastirma sessizce kaybolur.
    procedure reset_dut is
    begin
      rst      <= '1';
      valid_in <= '0';
      x_in     <= (others => '0');
      wait until rising_edge(clk);
      wait for HOLD;

      rst <= '0';
      wait until rising_edge(clk);   -- reset birakildiktan sonra bir bos cevrim
      wait for HOLD;

      compared := 0;
      captured := new_1d(bit_width => C_DATA_WIDTH, is_signed => true);
    end procedure reset_dut;

    -- Bir ornegi karsilastir ve sayaci ilerlet.
    procedure check_next_output is
    begin
      check_equal(
        to_integer(signed(y_out)),
        get(expected_data, compared),
        "cikis beklenenden farkli, index=" & to_string(compared)
      );
      append(captured, to_integer(signed(y_out)));
      compared := compared + 1;
    end procedure check_next_output;

    -- input_data[first..last] arasini besle, her gecerli cikisi karsilastir.
    procedure feed_range(constant first, last : in natural) is
    begin
      for i in first to last loop
        x_in     <= std_logic_vector(to_signed(get(input_data, i), C_DATA_WIDTH));
        valid_in <= '1';
        wait until rising_edge(clk);
        wait for HOLD;

        if valid_out = '1' then
          check_next_output;
        end if;
      end loop;
    end procedure feed_range;

    -- Beslemeyi durdur ve pipeline'da kalmis ornekleri topla.
    -- Gecikme 1 cevrimken bir sey toplamaz; pipeline derinlesirse gerekir.
    procedure drain is
    begin
      valid_in <= '0';
      for i in 1 to DRAIN_CYCLES loop
        wait until rising_edge(clk);
        wait for HOLD;

        if valid_out = '1' then
          check_next_output;
        end if;
      end loop;
    end procedure drain;

    -- Testin gercekten olctugunun kaniti: eksik karsilastirma sessiz kalmasin.
    procedure check_all_compared is
    begin
      check_equal(
        compared,
        length(expected_data),
        "beklenen sayida ornek karsilastirilmadi"
      );
    end procedure check_all_compared;

  begin
    test_runner_setup(runner, runner_cfg);

    while test_suite loop

      if run("cikis_ile_beklenen_ayni") then
        -- Referans bit-birebir oldugu icin tolerans yok: yuvarlama modunu
        -- bozan her degisiklik burada kirmizi verir.
        input_data    := load_csv(input_csv,    bit_width => C_DATA_WIDTH);
        expected_data := load_csv(expected_csv, bit_width => C_DATA_WIDTH);

        reset_dut;
        feed_range(0, length(input_data) - 1);
        drain;
        check_all_compared;
        save_csv(captured, output_path(runner_cfg) & "output.csv");

      elsif run("valid_dusukken_filtre_durur") then
        input_data    := load_csv(input_csv,    bit_width => C_DATA_WIDTH);
        expected_data := load_csv(expected_csv, bit_width => C_DATA_WIDTH);

        reset_dut;
        feed_range(0, 10);

        -- Besleme kesilince cikis dondurulmali. x_in ayni kalir; DUT valid_in'i
        -- yok sayiyor olsaydi ayni ornegi tekrar tekrar isler ve cikis degisirdi.
        valid_in <= '0';
        y_prev   := y_out;
        for i in 1 to IDLE_CYCLES loop
          wait until rising_edge(clk);
          wait for HOLD;
          check_equal(valid_out, '0', "valid_in dusukken valid_out yukseldi");
        end loop;
        check_equal(y_out, y_prev, "valid_in dusukken cikis degisti");

        -- Kaldigi yerden devam: hizalama bozulmamis olmali.
        feed_range(11, length(input_data) - 1);
        drain;
        check_all_compared;

      elsif run("tam_olcek_dc_de_doyar") then
        -- Katsayi yuvarlamasi yuzunden DC kazanci 1'in bir tik ustunde
        -- (sum(h) = 32769). Tam olcek DC girisi bu yuzden cikista tasar ve
        -- doygunluk dalini calistirir -- yoksa o dal hic kosulmuyordu.
        input_data    := load_csv(input_dc_csv,    bit_width => C_DATA_WIDTH);
        expected_data := load_csv(expected_dc_csv, bit_width => C_DATA_WIDTH);

        reset_dut;
        feed_range(0, length(input_data) - 1);
        drain;
        check_all_compared;

        -- Sarma olsaydi cikis tepede aniden negatife donerdi.
        check_equal(
          to_integer(signed(y_out)),
          Q15_MAX,
          "tam olcek DC'de cikis doymadi (sarma olabilir)"
        );

      end if;
    end loop;

    test_runner_cleanup(runner);
  end process main;


  monitor : process
    variable cyc : natural := 0;
  begin
    wait until falling_edge(clk);

    if cyc < MONITOR_CYCLES then
      info("cyc=" & to_string(cyc) &
           " vi=" & to_string(valid_in) &
           " x="  & to_string(to_integer(signed(x_in))) &
           " vo=" & to_string(valid_out) &
           " y="  & to_string(to_integer(signed(y_out))));
    end if;

    cyc := cyc + 1;
  end process monitor;


  test_runner_watchdog(runner, 1 ms);

end architecture bench;
