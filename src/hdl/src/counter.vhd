
library IEEE;
use IEEE.STD_LOGIC_1164.all;
use ieee.numeric_std.all;

entity counter is
  generic (
    C_DATA_WIDTH : natural := 32
  );
  port (
    clk : in std_logic;
    rst : in std_logic;

    ena  : in std_logic;
    tick : out std_logic;

    count_out : out std_logic_vector(C_DATA_WIDTH - 1 downto 0)
  );
end entity counter;

architecture rtl of counter is

  constant count_lim : unsigned(C_DATA_WIDTH - 1 downto 0) := to_unsigned(2 ** C_DATA_WIDTH - 1, C_DATA_WIDTH);
  signal count       : unsigned(C_DATA_WIDTH - 1 downto 0);

begin

    count_out <= std_logic_vector(count);

  pr_count : process (clk) is
  begin
    if rising_edge(clk) then
      if rst = '1' then
        count <= (others => '0');
        tick  <= '0';
      else
        if ena = '1' then
          tick <= '0';
          if count = count_lim then
            tick  <= '1';
            count <= (others => '0');
          else
            count <= count + 1;
          end if;
        else
          tick <= '0';
        end if;

      end if;
    end if;
  end process pr_count;

end architecture rtl;