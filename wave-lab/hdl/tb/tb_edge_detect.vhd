-- tb_edge_detect.vhd
--
-- edge_detect modulu icin VUnit testbench'i.
--
-- Sartname tek yerde yasiyor: C_LATENCY. Tasarimin gecikmesi degisirse
-- yalnizca o sabit degisir, testlerin govdesi degil.

library ieee;
use ieee.std_logic_1164.all;

library vunit_lib;
context vunit_lib.vunit_context;

entity tb_edge_detect is
  generic (runner_cfg : string);
end entity;

architecture bench of tb_edge_detect is

  constant C_PERIOD : time := 10 ns;

  -- Uyaran saat kenarindan C_SETTLE sonra surulur, cikis C_SETTLE sonra
  -- okunur. Iki isi birden yapar:
  --   1) Uyaran ile ornekleme arasinda gercekci bir clock-to-out payi birakir.
  --   2) FST'de delta cycle kavrami olmadigi icin, ayni zaman damgasina
  --      yigilan gecisleri ayirir -- dalga formu okunabilir kalir.
  constant C_SETTLE : time := 1 ns;

  -- SARTNAME: signal_in dustukten sonra kacinci yukselen kenarda
  -- edge_detected '1' olur.
  constant C_LATENCY : natural := 1;

  -- Darbeden sonra kac cevrim gozlenecek (genislik dogrulamasi icin)
  constant C_OBSERVE_CYCLES : natural := 5;

  signal clk   : std_logic := '0';
  signal reset : std_logic := '1';

  signal signal_in     : std_logic := '0';
  signal edge_detected : std_logic;

begin

  clk <= not clk after C_PERIOD / 2;

  DUT : entity work.edge_detect
    port map (
      clk           => clk,
      reset         => reset,
      signal_in     => signal_in,
      edge_detected => edge_detected
    );

  -- Bir "wait until" hic tamamlanmazsa simulasyon sonsuza kadar donmesin.
  test_runner_watchdog(runner, 1 ms);

  main : process

    -- Bir yukselen kenar bekler, sonra sinyallerin oturmasini bekler.
    -- Bundan sonraki her okuma O KENARIN sonucudur; kenar oncesi degil.
    procedure next_cycle is
    begin
      wait until rising_edge(clk);
      wait for C_SETTLE;
    end procedure;

    -- n yukselen kenar bekler, oturma payi eklemez.
    procedure wait_cycles(n : natural) is
    begin
      for i in 1 to n loop
        wait until rising_edge(clk);
      end loop;
    end procedure;

  begin
    test_runner_setup(runner, runner_cfg);

    while test_suite loop

      -- Her testin ortak baslangici: sifirlanmis DUT, signal_in dusuk
      reset     <= '1';
      signal_in <= '0';
      next_cycle;
      reset <= '0';

      -----------------------------------------------------------------------
      if run("tek_cevrimlik_darbe_uretir") then
        -- Darbenin YERINI ve GENISLIGINI ayni dongude dogrular.
        -- Sayma yaklasimi ikisini de olcemiyordu: "toplam 1 darbe var"
        -- ifadesi, darbe yanlis cevrimde olsa bile dogru kalir.

        signal_in <= '1';
        next_cycle;                       -- signal_in '1' olarak orneklendi
        signal_in <= '0';                 -- dusen kenar burada

        for i in 1 to C_OBSERVE_CYCLES loop
          next_cycle;
          if i = C_LATENCY then
            check_equal(edge_detected, '1',
                        "darbe " & to_string(C_LATENCY) & ". cevrimde bekleniyordu");
          else
            check_equal(edge_detected, '0',
                        to_string(i) & ". cevrimde beklenmeyen darbe");
          end if;
        end loop;

      -----------------------------------------------------------------------
      elsif run("arka_arkaya_kenar_kacirmaz") then
        -- Bu detektor icin mumkun olan en yuksek hiz: signal_in bir cevrim
        -- yuksek, bir cevrim dusuk. Yani dusen kenarlar iki cevrimde bir.
        -- Aradaki '0' kontrolu olmadan, cikisi '1'de takili kalan bir DUT
        -- bu testi gecerdi.

        signal_in <= '1';
        next_cycle;
        signal_in <= '0';                 -- dusen kenar #1

        wait_cycles(C_LATENCY);
        wait for C_SETTLE;
        check_equal(edge_detected, '1', "ilk kenar yakalanmadi");

        signal_in <= '1';                 -- hemen geri yukari
        next_cycle;
        check_equal(edge_detected, '0', "darbe bir cevrimden uzun surdu");

        signal_in <= '0';                 -- dusen kenar #2
        wait_cycles(C_LATENCY);
        wait for C_SETTLE;
        check_equal(edge_detected, '1', "arka arkaya gelen ikinci kenar kacirildi");

      -----------------------------------------------------------------------
      elsif run("sabit_giriste_darbe_uretmez") then
        -- Negatif test. Hicbir dusen kenar yok; cikis hic kipirdamamali.

        signal_in <= '1';

        for i in 1 to C_OBSERVE_CYCLES loop
          next_cycle;
          check_equal(edge_detected, '0',
                      to_string(i) & ". cevrimde sahte darbe");
        end loop;

      end if;

    end loop;

    test_runner_cleanup(runner);
  end process;

end architecture;