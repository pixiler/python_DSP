--------------------------------------------------------------------------
-- tb_axis_skid_buffer_vc -- ayni DUT, bu kez VUnit AXI-Stream VC'leriyle
--
-- Elle yazilan tb_axis_skid_buffer.vhd'yi SILMEK icin degil, YANINA durmak
-- icin var. Isbolumu:
--
--   elle yazilan TB : cevrim seviyesi yapi
--                     (hangi kayit ne zaman dolar, sira, gecikme)
--   VC'li TB        : veri butunlugu + protokol uyumu
--                     (binlerce rastgele zamanlama senaryosu, bedava)
--
-- VC'ler el sikismalarin ZAMANLAMASINI kendileri uydurur; sen yalnizca
-- "su beat'leri gonder" ve "su beat'leri bekliyorum" dersin. Bu yuzden
-- cevrim sayan iddialar (tam hiz, skid ne zaman dolar) VC'lerle
-- ifade edilemez -- onlar elle yazilan TB'de kalir.
--
-- KURULUM: run.py tarafinda `vu.add_verification_components()` cagrilmali,
-- yoksa vunit_lib.axi_stream_pkg bulunamaz.
--------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;

library vunit_lib;
context vunit_lib.vunit_context;
context vunit_lib.com_context; -- `net` sinyali buradan gelir
use vunit_lib.axi_stream_pkg.all;
use vunit_lib.stream_master_pkg.all;
use vunit_lib.stream_slave_pkg.all;
use vunit_lib.sync_pkg.all;

entity tb_axis_skid_buffer_vc is
  generic (
    runner_cfg : string;
    -- Stall konfigurasyonu ELABORASYON zamaninda VC'nin icine gomulur.
    -- Bu yuzden calisma zamaninda degistirilemez; testten teste degismesi
    -- gerekiyorsa generic + add_config yolundan gecmek zorunda.
    -- (Katsayi paketi meselesindeki kuralin aynisi.)
    g_master_stall_prob : real := 0.0;
    g_slave_stall_prob  : real := 0.0
  );
end entity tb_axis_skid_buffer_vc;

architecture bench of tb_axis_skid_buffer_vc is

  constant C_PERIOD     : time     := 10 ns;
  constant C_DATA_WIDTH : positive := 8;
  constant C_BEATS      : positive := 64;

  ----------------------------------------------------------------------
  -- VC tanimlari
  ----------------------------------------------------------------------
  constant master_stall : stall_config_t := new_stall_config(
  stall_probability => g_master_stall_prob,
  min_stall_cycles  => 1,
  max_stall_cycles  => 4);

  constant slave_stall : stall_config_t := new_stall_config(
  stall_probability => g_slave_stall_prob,
  min_stall_cycles  => 1,
  max_stall_cycles  => 4);

  constant axis_master : axi_stream_master_t := new_axi_stream_master(
  data_length  => C_DATA_WIDTH,
  stall_config => master_stall);

  constant axis_slave : axi_stream_slave_t := new_axi_stream_slave(
  data_length  => C_DATA_WIDTH,
  stall_config => slave_stall);

  -- Iki protokol denetcisi: biri DUT'un girisini, digeri cikisini izler.
  -- Cikistaki onemli olan -- DUT'un tvalid/tdata kararliligini o denetler.
  constant pc_in : axi_stream_protocol_checker_t :=
  new_axi_stream_protocol_checker(
  data_length => C_DATA_WIDTH,
  logger      => get_logger("axis_pc_in"),
  max_waits   => 64);

  constant pc_out : axi_stream_protocol_checker_t :=
  new_axi_stream_protocol_checker(
  data_length => C_DATA_WIDTH,
  logger      => get_logger("axis_pc_out"),
  max_waits   => 64);

  ----------------------------------------------------------------------
  signal clk      : std_logic := '0';
  signal reset    : std_logic := '1';
  signal areset_n : std_logic; -- VC'ler aktif-dusuk reset ister

  signal s_axis_tvalid : std_logic;
  signal s_axis_tready : std_logic;
  signal s_axis_tdata  : std_logic_vector(C_DATA_WIDTH - 1 downto 0);
  signal s_axis_tlast  : std_logic;

  signal m_axis_tvalid : std_logic;
  signal m_axis_tready : std_logic;
  signal m_axis_tdata  : std_logic_vector(C_DATA_WIDTH - 1 downto 0);
  signal m_axis_tlast  : std_logic;

  function beat_value(i : natural) return std_logic_vector is
  begin
    return std_logic_vector(to_unsigned((3 * i + 5) mod 2 ** C_DATA_WIDTH, C_DATA_WIDTH));
  end function;

begin

  clk      <= not clk after C_PERIOD / 2;
  areset_n <= not reset;

  ----------------------------------------------------------------------
  -- DUT
  ----------------------------------------------------------------------
  DUT : entity work.axis_skid_buffer
    generic map(
      DATA_WIDTH => C_DATA_WIDTH
    )
    port map(
      clk   => clk,
      reset => reset,

      s_axis_tvalid => s_axis_tvalid,
      s_axis_tready => s_axis_tready,
      s_axis_tdata  => s_axis_tdata,
      s_axis_tlast  => s_axis_tlast,

      m_axis_tvalid => m_axis_tvalid,
      m_axis_tready => m_axis_tready,
      m_axis_tdata  => m_axis_tdata,
      m_axis_tlast  => m_axis_tlast
    );

  ----------------------------------------------------------------------
  -- Verification Component'lar
  ----------------------------------------------------------------------
  vc_master : entity vunit_lib.axi_stream_master
    generic map(
      master => axis_master
    )
    port map(
      aclk     => clk,
      areset_n => areset_n,
      tvalid   => s_axis_tvalid,
      tready   => s_axis_tready,
      tdata    => s_axis_tdata,
      tlast    => s_axis_tlast
    );

  vc_slave : entity vunit_lib.axi_stream_slave
    generic map(
      slave => axis_slave
    )
    port map(
      aclk     => clk,
      areset_n => areset_n,
      tvalid   => m_axis_tvalid,
      tready   => m_axis_tready,
      tdata    => m_axis_tdata,
      tlast    => m_axis_tlast
    );

  vc_pc_in : entity vunit_lib.axi_stream_protocol_checker
    generic map(
      protocol_checker => pc_in
    )
    port map(
      aclk     => clk,
      areset_n => areset_n,
      tvalid   => s_axis_tvalid,
      tready   => s_axis_tready,
      tdata    => s_axis_tdata,
      tlast    => s_axis_tlast
    );

  vc_pc_out : entity vunit_lib.axi_stream_protocol_checker
    generic map(
      protocol_checker => pc_out
    )
    port map(
      aclk     => clk,
      areset_n => areset_n,
      tvalid   => m_axis_tvalid,
      tready   => m_axis_tready,
      tdata    => m_axis_tdata,
      tlast    => m_axis_tlast
    );

  ----------------------------------------------------------------------
  main : process
    variable t_start : time;
    variable t_end   : time;
  begin

    test_runner_setup(runner, runner_cfg);

    -- Ortak reset
    reset <= '1';
    wait until rising_edge(clk);
    wait until rising_edge(clk);
    reset <= '0';
    wait until rising_edge(clk);

    ------------------------------------------------------------------
    if run("veri_butunlugu") then
      -- Iddia: el sikismalarin zamanlamasi ne olursa olsun, transfer
      -- edilen dizi ayni. Ayni test kesintisiz ve agir stall'li
      -- konfigurasyonlarda kosar; beklenti dosyasi hic degismez.
      --
      -- push_axi_stream BLOKLAMAZ: 64 beat aninda kuyruga girer, VC
      -- onlari kendi uydurdugu zamanlamayla surer.
      for i in 1 to C_BEATS loop
        if i = C_BEATS then
          push_axi_stream(net, axis_master, beat_value(i), tlast => '1');
        else
          push_axi_stream(net, axis_master, beat_value(i), tlast => '0');
        end if;
      end loop;

      for i in 1 to C_BEATS loop
        if i = C_BEATS then
          check_axi_stream(net, axis_slave, beat_value(i), tlast => '1',
          msg                                                    => "beat " & integer'image(i));
        else
          check_axi_stream(net, axis_slave, beat_value(i), tlast => '0',
          msg                                                    => "beat " & integer'image(i));
        end if;
      end loop;

      ------------------------------------------------------------------
    elsif run("uc_paket_tlast_sinirlari") then
      -- tlast'in dogru beat'le birlikte tasindigini, paket sinirlarinin
      -- kaymadigini dogrular. Skid dolu haldeyken tlast'i tasiyan beat
      -- reg'e gecerken bayragin da onunla gitmesi gerekiyor.
      for p in 1 to 3 loop
        for i in 1 to 4 loop
          if i = 4 then
            push_axi_stream(net, axis_master, beat_value(p * 10 + i), tlast => '1');
          else
            push_axi_stream(net, axis_master, beat_value(p * 10 + i), tlast => '0');
          end if;
        end loop;
      end loop;

      for p in 1 to 3 loop
        for i in 1 to 4 loop
          if i = 4 then
            check_axi_stream(net, axis_slave, beat_value(p * 10 + i), tlast => '1',
            msg                                                             => "paket " & integer'image(p) & " son beat");
          else
            check_axi_stream(net, axis_slave, beat_value(p * 10 + i), tlast => '0',
            msg                                                             => "paket " & integer'image(p)
            & " beat " & integer'image(i));
          end if;
        end loop;
      end loop;

      ------------------------------------------------------------------
    elsif run("tam_hiz_zamanlamasi") then
      -- Bu teste add_config EKLENMEZ: varsayilan generic'lerle, yani
      -- stall olasiligi 0.0 ile kosar. Stall'siz VC'ler her cevrim bir
      -- beat surer, dolayisiyla gecen sure cevrim sayisi olarak
      -- olculebilir hale gelir.
      --
      -- %50 throughput'a dusuren bir hata (or. tek kayitli tasarim)
      -- burada ~2x sure olarak gorunur.
      t_start := now;

      for i in 1 to C_BEATS loop
        if i = C_BEATS then
          push_axi_stream(net, axis_master, beat_value(i), tlast => '1');
        else
          push_axi_stream(net, axis_master, beat_value(i), tlast => '0');
        end if;
      end loop;

      for i in 1 to C_BEATS loop
        if i = C_BEATS then
          check_axi_stream(net, axis_slave, beat_value(i), tlast => '1');
        else
          check_axi_stream(net, axis_slave, beat_value(i), tlast => '0');
        end if;
      end loop;

      t_end := now;

      -- C_BEATS cevrim + boru hatti gecikmesi + birkac cevrim tolerans
      check(t_end - t_start <= (C_BEATS + 5) * C_PERIOD,
      "tam hiz saglanmiyor: " & time'image(t_end - t_start)
      & " gecti, en fazla "
      & time'image((C_BEATS + 5) * C_PERIOD) & " olmaliydi");

    end if;

    -- VC'ler kuyruklarini bosaltsin, sonra kapat
    wait_until_idle(net, as_sync(axis_master));
    wait_until_idle(net, as_sync(axis_slave));

    test_runner_cleanup(runner);
  end process main;

  test_runner_watchdog(runner, 10 ms);

end architecture bench;