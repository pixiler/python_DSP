library IEEE;
use IEEE.STD_LOGIC_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;

entity tb_edge_detect is
  generic (runner_cfg : string);
end entity;

architecture bench of tb_edge_detect is

  constant C_PERIOD : time := 10 ns;
  signal clk        : std_logic;
  signal reset      : std_logic;

  signal signal_in     : std_logic;
  signal edge_detected : std_logic;
begin

  gen_clk : process
  begin
    loop
      clk <= '1';
      wait for C_PERIOD/2;
      clk <= '0';
      wait for C_PERIOD/2;
    end loop;
    wait;
  end process;

  DUT : entity work.edge_detect
    port map
    (
      clk   => clk,
      reset => reset,

      signal_in     => signal_in,
      edge_detected => edge_detected
    );

  main : process
    variable edge_count : natural;
  begin
    test_runner_setup(runner, runner_cfg);

    while test_suite loop
      -- Her testin ortak baslangici
      edge_count := 0;

      reset <= '1';
      wait until rising_edge(clk);
      wait for 1 ns;
      reset     <= '0';
      signal_in <= '0';

      if run("tek_cevrimlik_darbe_uretir") then

        signal_in <= '1';
        wait until rising_edge(clk);
        wait for 1 ns;
        signal_in <= '0';

        for i in 1 to 5 loop
          if edge_detected = '1' then
            edge_count := edge_count + 1;
          end if;
          wait until rising_edge(clk);
        end loop;

        check_equal(edge_count, 1, "tek cevrimlik darbe uretmedi");

      elsif run("arka_arkaya_kenar_kacirmaz") then

        signal_in <= '1';
        wait until rising_edge(clk);
        wait for 1 ns;
        signal_in <= '0';

        wait until rising_edge(clk);
        wait for 1 ns;

        check_equal(edge_detected, '1', "edge yakalanmadi");

        signal_in <= '1';
        wait until rising_edge(clk);
        wait for 1 ns;
        signal_in <= '0';
        wait until rising_edge(clk);
        wait for 1 ns;

        check_equal(edge_detected, '1', "arka arka edge yakalanmadi");
      end if;

    end loop;

    test_runner_cleanup(runner); -- VUNIT CLEANUP EKLEYIN
    wait;
  end process;

end architecture;