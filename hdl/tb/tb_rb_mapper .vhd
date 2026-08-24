-- =====================================================================
-- tb_rb_mapper.vhd
--
-- rb_mapper icin VUnit testbench iskeleti.
--
-- Yapi:
--   test_runner : stimulus + beklenen degerleri kuyruga itme
--   monitor     : cikista el sikisan her beat'i kuyruktan cekip kontrol
--   clk_gen     : serbest kosan saat
--
-- Ornekleme kurali: handshake sinyalleri `wait until rising_edge(clk)`
-- sonrasinda, ARA GECIKMESIZ okunur. Bu anda sinyaller hala kenar
-- oncesi degerini tasir -- yani el sikismayi belirleyen degeri.
-- =====================================================================

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;

entity tb_rb_mapper is
    generic (
        runner_cfg   : string;
        DATA_WIDTH   : positive := 32;
        TUSER_WIDTH  : positive := 16;
        CONFIG_WIDTH : positive := 32
    );
end entity tb_rb_mapper;


architecture tb of tb_rb_mapper is

    constant CLK_PERIOD : time := 10 ns;

    signal clk   : std_logic := '0';
    signal rst_n : std_logic := '0';

    signal s_axi_config_tdata  : std_logic_vector(CONFIG_WIDTH-1 downto 0) := (others => '0');
    signal s_axi_config_tvalid : std_logic := '0';

    signal s_axis_tdata  : std_logic_vector(DATA_WIDTH-1 downto 0) := (others => '0');
    signal s_axis_tvalid : std_logic := '0';
    signal s_axis_tlast  : std_logic := '0';
    signal s_axis_tuser  : std_logic_vector(TUSER_WIDTH-1 downto 0) := (others => '0');
    signal s_axis_tready : std_logic;

    signal m_axis_tdata  : std_logic_vector(DATA_WIDTH-1 downto 0);
    signal m_axis_tvalid : std_logic;
    signal m_axis_tlast  : std_logic;
    signal m_axis_tuser  : std_logic_vector(TUSER_WIDTH-1 downto 0);
    signal m_axis_tready : std_logic := '1';

    -- Scoreboard: her beklenen beat icin sirayla
    --   slv  tdata
    --   int  sc
    --   int  sym
    --   bool tlast
    constant exp_queue : queue_t := new_queue;

    -- Vacuous test korumasi: hic beat gozlenmediyse test anlamsizdir.
    -- Yalnizca `monitor` process surer. Diger process'ler sadece okur.
    signal beat_count : natural := 0;

begin

    ------------------------------------------------------------------
    -- Saat
    ------------------------------------------------------------------
    clk <= not clk after CLK_PERIOD / 2;

    test_runner_watchdog(runner, 1 ms);

    ------------------------------------------------------------------
    -- DUT
    ------------------------------------------------------------------
    dut : entity work.rb_mapper
        generic map (
            DATA_WIDTH   => DATA_WIDTH,
            TUSER_WIDTH  => TUSER_WIDTH,
            CONFIG_WIDTH => CONFIG_WIDTH
        )
        port map (
            clk                 => clk,
            rst_n               => rst_n,
            s_axi_config_tdata  => s_axi_config_tdata,
            s_axi_config_tvalid => s_axi_config_tvalid,
            s_axis_tdata        => s_axis_tdata,
            s_axis_tvalid       => s_axis_tvalid,
            s_axis_tlast        => s_axis_tlast,
            s_axis_tuser        => s_axis_tuser,
            m_axis_tdata        => m_axis_tdata,
            m_axis_tvalid       => m_axis_tvalid,
            m_axis_tlast        => m_axis_tlast,
            m_axis_tuser        => m_axis_tuser,
            s_axis_tready       => s_axis_tready,
            m_axis_tready       => m_axis_tready
        );

    ------------------------------------------------------------------
    -- Monitor: cikista el sikisan her beat kuyrukla karsilastirilir
    ------------------------------------------------------------------
    monitor : process
        variable exp_data : std_logic_vector(DATA_WIDTH-1 downto 0);
        variable exp_sc   : natural;
        variable exp_sym  : natural;
        variable exp_last : boolean;
    begin
        wait until rising_edge(clk);

        if rst_n = '1' and m_axis_tvalid = '1' and m_axis_tready = '1' then

            check_false(is_empty(exp_queue),
                "beklenmeyen cikis beat'i (kuyruk bos), beat #"
                & to_string(beat_count));

            exp_data := pop_std_ulogic_vector(exp_queue);
            exp_sc   := pop_integer(exp_queue);
            exp_sym  := pop_integer(exp_queue);
            exp_last := pop_boolean(exp_queue);

            check_equal(m_axis_tdata, exp_data,
                "beat #" & to_string(beat_count) & " tdata");

            check_equal(to_integer(unsigned(m_axis_tuser(7 downto 0))), exp_sc,
                "beat #" & to_string(beat_count) & " SC index");

            check_equal(to_integer(unsigned(m_axis_tuser(15 downto 8))), exp_sym,
                "beat #" & to_string(beat_count) & " SYM index");

            check_equal(m_axis_tlast, exp_last,
                "beat #" & to_string(beat_count) & " tlast");

            beat_count <= beat_count + 1;
        end if;
    end process monitor;

    ------------------------------------------------------------------
    -- Stimulus
    ------------------------------------------------------------------
    test_runner : process

        variable beats_at_start : natural;

        -- Tum prosedurler "bir yukselen kenardan hemen sonrayiz"
        -- varsayimiyla girer ve ayni durumda cikar.

        procedure wait_cycles(n : natural) is
        begin
            for i in 1 to n loop
                wait until rising_edge(clk);
            end loop;
        end procedure;

        procedure reset_dut is
        begin
            rst_n               <= '0';
            s_axis_tvalid       <= '0';
            s_axis_tlast        <= '0';
            s_axi_config_tvalid <= '0';
            m_axis_tready       <= '1';
            wait_cycles(4);
            rst_n <= '1';
            wait_cycles(1);
        end procedure;

        procedure write_config(sc_count : natural; sym_count : natural) is
        begin
            s_axi_config_tdata(15 downto 0)  <= std_logic_vector(to_unsigned(sc_count, 16));
            s_axi_config_tdata(31 downto 16) <= std_logic_vector(to_unsigned(sym_count, 16));
            s_axi_config_tvalid <= '1';
            wait until rising_edge(clk);      -- DUT bu kenarda ornekler
            s_axi_config_tvalid <= '0';
        end procedure;

        -- Beklenen beat'i scoreboard'a it
        procedure expect(data : natural; sc : natural; sym : natural; last : boolean) is
        begin
            push_std_ulogic_vector(exp_queue, std_logic_vector(to_unsigned(data, DATA_WIDTH)));
            push_integer(exp_queue, sc);
            push_integer(exp_queue, sym);
            push_boolean(exp_queue, last);
        end procedure;

        -- Bir beat gonder, el sikisma tamamlanana kadar bekle
        procedure send_beat(data : natural; last : boolean) is
        begin
            s_axis_tdata  <= std_logic_vector(to_unsigned(data, DATA_WIDTH));
            s_axis_tlast  <= '1' when last else '0';
            s_axis_tvalid <= '1';
            loop
                wait until rising_edge(clk);
                exit when s_axis_tready = '1';
            end loop;
            s_axis_tvalid <= '0';
            s_axis_tlast  <= '0';
        end procedure;

    begin
        test_runner_setup(runner, runner_cfg);

        while test_suite loop

            reset_dut;
            beats_at_start := beat_count;    -- (okuma, surme degil)
            --------------------------------------------------------------
            if run("config_sc4_sym2_tuser_sirasi") then
                -- SC_COUNT=4, SYM_COUNT=2 -> beklenen (sc,sym) dizisi
                -- ELLE yazildi. Bilerek: donanimla ayni dongu mantigini
                -- TB'de tekrar yazmak, ayni hatayi iki yerde yapmak demek.
                write_config(sc_count => 4, sym_count => 2);
                wait_cycles(1);

                expect(data => 16#100#, sc => 0, sym => 0, last => false);
                expect(data => 16#101#, sc => 1, sym => 0, last => false);
                expect(data => 16#102#, sc => 2, sym => 0, last => false);
                expect(data => 16#103#, sc => 3, sym => 0, last => false);
                expect(data => 16#104#, sc => 0, sym => 1, last => false);
                expect(data => 16#105#, sc => 1, sym => 1, last => false);
                expect(data => 16#106#, sc => 2, sym => 1, last => false);
                expect(data => 16#107#, sc => 3, sym => 1, last => false);
                expect(data => 16#108#, sc => 0, sym => 0, last => false);  -- sarma
                expect(data => 16#109#, sc => 1, sym => 0, last => false);

                for i in 0 to 9 loop
                    send_beat(data => 16#100# + i, last => false);
                end loop;

            --------------------------------------------------------------
            elsif run("config_yazilmadan_indeks_ilerlemez") then
                -- SC_COUNT reset'ten sonra 0. Kod `if sc_count_reg /= 0`
                -- ile korumali -> indeks hic artmaz, tuser hep 0.
                -- SORU: istenen davranis bu mu, yoksa config gelmeden
                -- veri kabul etmemek mi gerekir?

                for i in 0 to 9 loop
                    expect(data => 16#100# + i, sc => 0, sym => 0, last => false);
                end loop;

                for i in 0 to 9 loop
                    send_beat(data => 16#100# + i, last => false);
                end loop;

                -- report "TODO" severity note;

            --------------------------------------------------------------
            elsif run("tlast_indeksi_sifirlar") then
                -- SC_COUNT=4 ile 3 beat gonder, ucuncude tlast='1'.
                -- Sonraki paketin ilk beat'i (0,0) olmali.
                write_config(sc_count => 4, sym_count => 4);
                wait_cycles(1);

                expect(data => 16#100#, sc => 0, sym => 0, last => false);
                expect(data => 16#101#, sc => 1, sym => 0, last => false);
                expect(data => 16#102#, sc => 2, sym => 0, last => true);
                expect(data => 16#103#, sc => 0, sym => 0, last => false);  -- yeni paket

                send_beat(data => 16#100#, last => false);
                send_beat(data => 16#101#, last => false);
                send_beat(data => 16#102#, last => true);
                send_beat(data => 16#103#, last => false);

                -- report "TODO" severity note;

            --------------------------------------------------------------
            elsif run("yeniden_config_indeksi_sifirlar") then
                -- SC_COUNT=4 ile 3 beat, sonra SC_COUNT=2 yaz,
                -- sonra 3 beat daha. Indeksler sifirlandi mi?
                write_config(sc_count => 4, sym_count => 4);
                wait_cycles(1);

                expect(data => 16#100#, sc => 0, sym => 0, last => false);
                expect(data => 16#101#, sc => 1, sym => 0, last => false);
                expect(data => 16#102#, sc => 2, sym => 0, last => false);

                send_beat(data => 16#100# , last => false);
                send_beat(data => 16#101# , last => false);
                send_beat(data => 16#102# , last => false);

                write_config(sc_count => 2, sym_count => 4);
                wait_cycles(1);

                expect(data => 16#100# , sc => 0, sym => 0, last => false);

                send_beat(data => 16#100# , last => false);
                
                -- report "TODO" severity note;

            --------------------------------------------------------------
            elsif run("backpressure_indeksi_ilerletmez") then
                -- m_axis_tready'yi birkac cevrim '0' yap.
                -- Beat kabul EDILMEDIGI icin indeks ilerlememeli.

                write_config(sc_count => 4, sym_count => 2);
                wait_cycles(1);

                -- Beklentiler ONCE kuyruga: monitor her an pop edebilir.
                expect(data => 16#100#, sc => 0, sym => 0, last => false);
                expect(data => 16#101#, sc => 1, sym => 0, last => false);
                expect(data => 16#102#, sc => 2, sym => 0, last => false);

                -- Bes cevrim tikanikligi ONCEDEN planla; process bloke olmaz.
                m_axis_tready <= '0', '1' after 5 * CLK_PERIOD;

                send_beat(data => 16#100#, last => false);
                send_beat(data => 16#101#, last => false);
                send_beat(data => 16#102#, last => false);
                -- report "TODO" severity note;

            --------------------------------------------------------------
            elsif run("sc_count_1_her_beatte_sym_artar") then
                -- SC_COUNT=1 sinir durumu: sc hep 0, sym her beat'te artar.
                report "TODO" severity note;

            --------------------------------------------------------------
            elsif run("config_ve_beat_ayni_cevrimde") then
                -- config_tvalid ile input_accept ayni kenarda.
                -- Once tahmin et: sc_index ne olur?
                report "TODO" severity note;

            elsif run("tlast_sym_indeksini_de_sifirlar") then
                
                report "TODO" severity note;

            end if;

            --------------------------------------------------------------
            -- Her testin ortak son kontrolleri
            --------------------------------------------------------------
            wait_cycles(5);   -- pipeline'daki son beat'in cikmasi icin

            check(is_empty(exp_queue),
                "kuyrukta beklenen beat kaldi -- cikis eksik");
            check(beat_count > 0,
                "hicbir beat gozlenmedi -- test vacuous");

            wait_cycles(1);

        end loop;

        test_runner_cleanup(runner);
    end process test_runner;

end architecture tb;