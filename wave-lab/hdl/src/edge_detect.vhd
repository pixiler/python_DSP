library IEEE;
use IEEE.STD_LOGIC_1164.all;

entity edge_detect is
  port (
    clk   : in std_logic;
    reset : in std_logic;

    signal_in     : in std_logic;
    edge_detected : out std_logic
  );
end entity edge_detect;

architecture rtl of edge_detect is

  signal signal_pre : std_logic;
begin

  process (clk, reset)
  begin
    if reset = '1' then

      signal_pre    <= '0';
      edge_detected <= '0';

    elsif rising_edge(clk) then
      signal_pre <= signal_in;
      if signal_pre = '1' and signal_in = '0' then
        edge_detected <= '1';
      else
        edge_detected <= '0';
      end if;

    end if;
  end process;

end architecture;
