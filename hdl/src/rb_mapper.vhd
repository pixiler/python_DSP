library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

entity rb_mapper is
    generic (
        DATA_WIDTH : positive := 32;
        TUSER_WIDTH : positive := 16;
        CONFIG_WIDTH : positive := 32
    );
    port (
        clk   : in  std_logic;
        rst_n : in  std_logic;

        ------------------------------------------------------------------
        -- Configuration AXI-Stream
        --
        -- Config format:
        --   [15:0]  = SC_COUNT
        --   [31:16] = SYM_COUNT
        ------------------------------------------------------------------
        s_axi_config_tdata  : in  std_logic_vector(CONFIG_WIDTH-1 downto 0);
        s_axi_config_tvalid : in  std_logic;

        ------------------------------------------------------------------
        -- AXI Stream Slave Input
        ------------------------------------------------------------------
        s_axis_tdata  : in  std_logic_vector(DATA_WIDTH-1 downto 0);
        s_axis_tvalid : in  std_logic;
        s_axis_tlast  : in  std_logic;
        s_axis_tuser  : in  std_logic_vector(TUSER_WIDTH-1 downto 0);

        ------------------------------------------------------------------
        -- AXI Stream Master Output
        ------------------------------------------------------------------
        m_axis_tdata  : out std_logic_vector(DATA_WIDTH-1 downto 0);
        m_axis_tvalid : out std_logic;
        m_axis_tlast  : out std_logic;
        m_axis_tuser  : out std_logic_vector(TUSER_WIDTH-1 downto 0);

        ------------------------------------------------------------------
        -- AXI Stream handshake
        ------------------------------------------------------------------
        s_axis_tready : out std_logic;
        m_axis_tready : in  std_logic
    );
end entity rb_mapper;


architecture rtl of rb_mapper is

    ----------------------------------------------------------------------
    -- Configuration registers
    ----------------------------------------------------------------------

    signal sc_count_reg  : unsigned(15 downto 0) := (others => '0');
    signal sym_count_reg : unsigned(15 downto 0) := (others => '0');

    ----------------------------------------------------------------------
    -- Current RB indices
    ----------------------------------------------------------------------

    signal sc_index  : unsigned(15 downto 0) := (others => '0');
    signal sym_index : unsigned(15 downto 0) := (others => '0');

    ----------------------------------------------------------------------
    -- Output register
    ----------------------------------------------------------------------

    signal out_tdata  : std_logic_vector(DATA_WIDTH-1 downto 0);
    signal out_tvalid : std_logic;
    signal out_tlast  : std_logic;
    signal out_tuser  : std_logic_vector(TUSER_WIDTH-1 downto 0);

    ----------------------------------------------------------------------
    -- Internal handshake
    ----------------------------------------------------------------------

    signal input_accept : std_logic;

begin

    ----------------------------------------------------------------------
    -- AXI Stream assignments
    ----------------------------------------------------------------------

    m_axis_tdata  <= out_tdata;
    m_axis_tvalid <= out_tvalid;
    m_axis_tlast  <= out_tlast;
    m_axis_tuser  <= out_tuser;

    ----------------------------------------------------------------------
    -- Input can be accepted when output register is empty
    -- or current output is being consumed.
    ----------------------------------------------------------------------

    s_axis_tready <= (not out_tvalid) or m_axis_tready;

    input_accept <= s_axis_tvalid and s_axis_tready;


    ----------------------------------------------------------------------
    -- Main process
    ----------------------------------------------------------------------

    process(clk)
        variable v_tuser : std_logic_vector(TUSER_WIDTH-1 downto 0);
    begin

        if rising_edge(clk) then

            if rst_n = '0' then

                sc_count_reg  <= (others => '0');
                sym_count_reg <= (others => '0');

                sc_index  <= (others => '0');
                sym_index <= (others => '0');

                out_tdata  <= (others => '0');
                out_tvalid <= '0';
                out_tlast  <= '0';
                out_tuser  <= (others => '0');

            else

                ------------------------------------------------------------------
                -- Configuration reception
                ------------------------------------------------------------------

                if s_axi_config_tvalid = '1' then

                    sc_count_reg  <= unsigned(s_axi_config_tdata(15 downto 0));
                    sym_count_reg <= unsigned(s_axi_config_tdata(31 downto 16));

                    -- Restart indexing whenever new configuration arrives
                    sc_index  <= (others => '0');
                    sym_index <= (others => '0');

                end if;


                ------------------------------------------------------------------
                -- Output register handling
                ------------------------------------------------------------------

                if m_axis_tready = '1' then
                    out_tvalid <= '0';
                end if;


                ------------------------------------------------------------------
                -- Accept new AXI Stream word
                ------------------------------------------------------------------

                if input_accept = '1' then

                    ------------------------------------------------------------------
                    -- Pass TDATA directly
                    ------------------------------------------------------------------

                    out_tdata  <= s_axis_tdata;
                    out_tvalid <= '1';

                    ------------------------------------------------------------------
                    -- Pass TLAST
                    ------------------------------------------------------------------

                    out_tlast <= s_axis_tlast;


                    ------------------------------------------------------------------
                    -- Generate TUSER
                    --
                    -- TUSER format:
                    --
                    -- [SC_INDEX]
                    -- [SYM_INDEX]
                    --
                    -- For TUSER_WIDTH=16:
                    --
                    -- bits  7:0 = SC index
                    -- bits 15:8 = SYM index
                    ------------------------------------------------------------------

                    if TUSER_WIDTH >= 16 then

                        v_tuser := (others => '0');

                        v_tuser(7 downto 0) :=
                            std_logic_vector(sc_index(7 downto 0));

                        v_tuser(15 downto 8) :=
                            std_logic_vector(sym_index(7 downto 0));

                        out_tuser <= v_tuser;

                    else

                        out_tuser <=
                            std_logic_vector(
                                resize(sc_index, TUSER_WIDTH)
                            );

                    end if;


                    ------------------------------------------------------------------
                    -- Increment resource-grid index
                    --
                    -- SC index changes first.
                    -- When SC_COUNT is reached, SC resets and SYM increments.
                    ------------------------------------------------------------------

                    if sc_count_reg /= 0 then

                        if sc_index = sc_count_reg - 1 then

                            sc_index <= (others => '0');

                            if sym_count_reg /= 0 then

                                if sym_index = sym_count_reg - 1 then
                                    sym_index <= (others => '0');
                                else
                                    sym_index <= sym_index + 1;
                                end if;

                            end if;

                        else

                            sc_index <= sc_index + 1;

                        end if;

                    end if;

                    ------------------------------------------------------------------
                    -- Optional packet termination handling
                    --
                    -- If TLAST is asserted, restart indexing for next packet.
                    ------------------------------------------------------------------

                    if s_axis_tlast = '1' then
                        sc_index  <= (others => '0');
                        sym_index <= (others => '0');
                    end if;

                end if;

            end if;

        end if;

    end process;

end architecture rtl;