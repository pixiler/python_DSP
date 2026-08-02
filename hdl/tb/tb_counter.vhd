library IEEE;
use IEEE.STD_LOGIC_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;

entity tb_counter is
  generic (runner_cfg : string);
end entity;

architecture bench of tb_counter is
  constant C_DATA_WIDTH : natural := 4;
  constant C_PERIOD     : time    := 10 ns;

  constant MAX_COUNT : natural := 2 ** C_DATA_WIDTH - 1;

  signal clk : std_logic := '0';
  signal rst : std_logic := '1';

  signal ena  : std_logic := '0';
  signal tick : std_logic;

  signal count_out : std_logic_vector(C_DATA_WIDTH - 1 downto 0);

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

  DUT : entity work.counter
    generic map(
      C_DATA_WIDTH => C_DATA_WIDTH
    )
    port map
    (
      clk => clk,
      rst => rst,

      ena  => ena,
      tick => tick,

      count_out => count_out
    );

  main : process
    variable count_pre : natural;
  begin
    test_runner_setup(runner, runner_cfg);

    while test_suite loop
      -- her testin ortak baslangici
      rst <= '1';
      ena <= '0';
      wait until rising_edge(clk);
      wait for 1 ns;
      rst <= '0';

      if run("reset_sayaci_sifirlar") then
        ena <= '1';
        for i in 1 to 5 loop
          wait until rising_edge(clk);
        end loop;
        wait for 1 ns;
        -- once sayacin gercekten saydigini dogrula:
        -- yoksa asagidaki check hep gecer, test bir sey olcmez
        check_equal(unsigned(count_out), 5, "sayac bekledigi gibi saymadi");

        rst <= '1';
        wait until rising_edge(clk);
        wait for 1 ns;
        check_equal(unsigned(count_out), 0, "reset sonrasi sayac sifirlanmadi");

      elsif run("enable_dusukken_sayac_durur") then
        ena <= '1';
        for i in 1 to 5 loop
          wait until rising_edge(clk);
        end loop;
        wait for 1 ns;
        ena <= '0';
        count_pre := to_integer(unsigned(count_out));
        for i in 1 to 5 loop
          wait until rising_edge(clk);
        end loop;
        wait for 1 ns;

        check_equal(to_integer(unsigned(count_out)), count_pre, "enable dusukken sayac saymaya devam etti");

        ena <= '1';
        for i in 1 to 5 loop
          wait until rising_edge(clk);
        end loop;
        wait for 1 ns;

        check_equal(to_integer(unsigned(count_out)), count_pre + 5, "enable yuksekken sayac sayac devam etmiyor");

      elsif run("maksimumda_tick_uretir") then
        ena <= '1';
        for i in 1 to MAX_COUNT loop
          wait until rising_edge(clk);
          wait for 1 ns;
        end loop;
        check_equal(unsigned(count_out), MAX_COUNT, "sayac maksimuma ulasmadi");

        wait until rising_edge(clk);
        wait for 1 ns;

        check_equal(tick, '1', "maksimumda tick uretilmedi");
        check_equal(unsigned(count_out), 0, "maksimumdan sonra sayac sifirlanmadi");

        wait until rising_edge(clk);
        wait for 1 ns;
        check_equal(tick, '0', "tick yuksekte kalmaya devam ediyor");

      end if;
    end loop;

    test_runner_cleanup(runner);
  end process;

  test_runner_watchdog(runner, 1 ms);

end architecture bench;