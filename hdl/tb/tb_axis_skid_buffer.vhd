--------------------------------------------------------------------------
-- tb_axis_skid_buffer -- AXI4-Stream skid buffer testbench'i
--
-- ORNEKLEME KONVANSIYONU (bu dosyanin en onemli kurali)
--
--   wait until rising_edge(clk);
--   <-- burada okunan degerler, kenarin GORDUGU (kenar oncesi) degerlerdir
--
--   El sikismalar ve transfer edilen payload BURADA okunur. "wait for 1 ns"
--   eklenirse kenarin SONUCU okunur ve bir cevrim ileri kayilir; o zaman
--   henuz gerceklesmemis bir transferi olmus saymis olursun.
--
--   Uyaran ise kenardan HEMEN SONRA surulur; atama bir delta sonra etkili
--   olur ve bir sonraki kenara kadar butun cevrim boyunca sabit kalir.
--
--   Dongu iskeleti:
--     1) bu cevrimin uyaranini sur
--     2) wait until rising_edge(clk)
--     3) el sikismalari degerlendir, check yap
--
-- MASTER TARAFI PROTOKOL KURALI
--   s_axis_tvalid '1' yapildiktan sonra, el sikisma tamamlanana kadar
--   ne geri cekilebilir ne de payload degistirilebilir. Kabarcik (bubble)
--   yalnizca beat'ler ARASINA konur. Testbench'in kendisi de protokole
--   uymak zorundadir; uymayan bir testbench DUT'u haksiz yere sucla.
--------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;
use ieee.numeric_std.all;
use ieee.math_real.all;

library vunit_lib;
context vunit_lib.vunit_context;

entity tb_axis_skid_buffer is
  generic (
    runner_cfg : string
  );
end entity tb_axis_skid_buffer;

architecture bench of tb_axis_skid_buffer is

  constant C_PERIOD     : time     := 10 ns;
  constant C_DATA_WIDTH : positive := 8;
  constant C_BEATS      : positive := 64;

  signal clk   : std_logic := '0';
  signal reset : std_logic := '1';

  signal s_axis_tvalid : std_logic := '0';
  signal s_axis_tready : std_logic;
  signal s_axis_tdata  : std_logic_vector(C_DATA_WIDTH - 1 downto 0) := (others => '0');
  signal s_axis_tlast  : std_logic := '0';

  signal m_axis_tvalid : std_logic;
  signal m_axis_tready : std_logic := '0';
  signal m_axis_tdata  : std_logic_vector(C_DATA_WIDTH - 1 downto 0);
  signal m_axis_tlast  : std_logic;

  -- i. beat'in tasidigi deger tek yerde tanimli: hem surucude hem
  -- kontrolde ayni fonksiyon kullanilir, ikisi ayrisamaz.
  -- 3*i+5 secildi: i = 1..64 icin degerler birbirinden farkli, boylece
  -- bir sira hatasi tesadufen ayni degere denk gelip gizlenemez.
  function beat_value(i : natural) return std_logic_vector is
  begin
    return std_logic_vector(to_unsigned((3 * i + 5) mod 2**C_DATA_WIDTH, C_DATA_WIDTH));
  end function;

  -- Son beat'te tlast '1', digerlerinde '0'.
  function beat_last(i : natural) return std_logic is
  begin
    if i = C_BEATS then
      return '1';
    else
      return '0';
    end if;
  end function;

begin

  clk <= not clk after C_PERIOD / 2;

  DUT : entity work.axis_skid_buffer
    generic map (
      DATA_WIDTH => C_DATA_WIDTH
    )
    port map (
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

  ------------------------------------------------------------------------
  -- Surekli protokol denetcisi
  --
  -- Testlerden bagimsiz, her cevrimde kosar. Tek kural denetler:
  --   tvalid = '1' ve tready = '0' iken, bir sonraki cevrimde tvalid hala
  --   '1' olmali ve payload degismemis olmali.
  -- Bu, VUnit'in axi_stream_protocol_checker'inin yaptigi isin elle
  -- yazilmis en kucuk halidir.
  ------------------------------------------------------------------------
  protocol_checker : process
    variable prev_valid : std_logic := '0';
    variable prev_ready : std_logic := '0';
    variable prev_data  : std_logic_vector(C_DATA_WIDTH - 1 downto 0) := (others => '0');
    variable prev_last  : std_logic := '0';
  begin
    wait until rising_edge(clk);

    if reset = '1' then
      prev_valid := '0';
    else
      if prev_valid = '1' and prev_ready = '0' then
        check_equal(m_axis_tvalid, '1',
                    "PROTOKOL: el sikisma olmadan tvalid geri cekildi");
        check_equal(m_axis_tdata, prev_data,
                    "PROTOKOL: el sikisma beklenirken tdata degisti");
        check_equal(m_axis_tlast, prev_last,
                    "PROTOKOL: el sikisma beklenirken tlast degisti");
      end if;
      prev_valid := m_axis_tvalid;
    end if;

    prev_ready := m_axis_tready;
    prev_data  := m_axis_tdata;
    prev_last  := m_axis_tlast;
  end process protocol_checker;

  ------------------------------------------------------------------------
  -- Ana test sureci
  ------------------------------------------------------------------------
  main : process

    -- Rastgele sayi uretecinin durumu. Sabit tohum = tekrarlanabilir test.
    variable seed1 : positive := 20260818;
    variable seed2 : positive := 7;

    procedure rand_bool(prob : in real; result : out boolean) is
      variable r : real;
    begin
      uniform(seed1, seed2, r);
      result := r < prob;
    end procedure;

    variable tx_index      : natural;   -- gonderilecek sonraki beat
    variable rx_index      : natural;   -- beklenen sonraki beat
    variable tx_active     : boolean;   -- su an askida bir beat var mi
    variable cycle         : natural;   -- reset sonrasi kenar sayaci
    variable prev_rx_cycle : natural;
    variable do_it         : boolean;

  begin

    test_runner_setup(runner, runner_cfg);

    while test_suite loop

      -- ---- her testin ortak baslangici --------------------------------
      reset         <= '1';
      s_axis_tvalid <= '0';
      s_axis_tdata  <= (others => '0');
      s_axis_tlast  <= '0';
      m_axis_tready <= '0';

      tx_index      := 1;
      rx_index      := 1;
      tx_active     := false;
      cycle         := 0;
      prev_rx_cycle := 0;

      wait until rising_edge(clk);
      wait until rising_edge(clk);
      reset <= '0';          -- bir sonraki cevrimden itibaren serbest

      --------------------------------------------------------------------
      if run("kesintisiz_akista_tam_hiz") then
        -- Iddia: hic geri basinc yokken her cevrim bir beat girer ve
        -- her cevrim bir beat cikar. Cikista tek bir bosluk bile olmamali.
        m_axis_tready <= '1';

        while rx_index <= C_BEATS loop

          -- 1) uyaran
          if tx_index <= C_BEATS then
            s_axis_tdata  <= beat_value(tx_index);
            s_axis_tlast  <= beat_last(tx_index);
            s_axis_tvalid <= '1';
          else
            s_axis_tvalid <= '0';
          end if;

          -- 2) kenar
          wait until rising_edge(clk);
          cycle := cycle + 1;

          -- 3) degerlendirme (kenar oncesi degerler)
          if tx_index <= C_BEATS then
            -- skid hic dolmamali, dolayisiyla giris hic durmamali
            check_equal(s_axis_tready, '1',
                        "kesintisiz akista giris durdu (cevrim "
                        & integer'image(cycle) & ")");
            tx_index := tx_index + 1;
          end if;

          if m_axis_tvalid = '1' and m_axis_tready = '1' then
            check_equal(m_axis_tdata, beat_value(rx_index),
                        "beat " & integer'image(rx_index) & ": yanlis veri");
            check_equal(m_axis_tlast, beat_last(rx_index),
                        "beat " & integer'image(rx_index) & ": yanlis tlast");
            if rx_index > 1 then
              check_equal(cycle, prev_rx_cycle + 1,
                          "cikista bosluk var: tam hiz saglanmiyor (beat "
                          & integer'image(rx_index) & ")");
            end if;
            prev_rx_cycle := cycle;
            rx_index      := rx_index + 1;
          end if;

        end loop;

        s_axis_tvalid <= '0';

      --------------------------------------------------------------------
      elsif run("her_iki_kayit_doluyken_sira_korunur") then
        -- Yonlendirilmis test: iki kaydi da doldurup cikis sirasini
        -- dogrudan olcer. Skid'i dolduran tek test bu -- rastgele stall'a
        -- guvenmek yerine durumu elle kurmak, hatanin yerini de soyler.

        -- Cevrim 1: A gelir, cikis tikali
        s_axis_tdata  <= beat_value(1);
        s_axis_tlast  <= '0';
        s_axis_tvalid <= '1';
        m_axis_tready <= '0';
        wait until rising_edge(clk);
        check_equal(s_axis_tready, '1', "bos buffer girisi kabul etmeli");
        -- bu kenarda A -> reg

        -- Cevrim 2: B gelir. reg dolu ama skid bos oldugu icin giris hala acik.
        s_axis_tdata <= beat_value(2);
        s_axis_tlast <= '1';
        wait until rising_edge(clk);
        check_equal(s_axis_tready, '1',
                    "reg dolu / skid bos iken giris kabul edilmeli");
        check_equal(m_axis_tvalid, '1', "A cikista sunulmali");
        check_equal(m_axis_tdata, beat_value(1), "cikista once A gelmeli");
        -- bu kenarda B -> skid

        -- Cevrim 3: iki kayit da dolu. Giris DURMALI, cikis hala A olmali.
        s_axis_tvalid <= '0';
        m_axis_tready <= '1';
        wait until rising_edge(clk);
        check_equal(s_axis_tready, '0', "skid doluyken giris durmali");
        check_equal(m_axis_tvalid, '1', "A hala cikista olmali");
        check_equal(m_axis_tdata, beat_value(1),
                    "SIRA HATASI: A'dan once baska beat cikti");
        check_equal(m_axis_tlast, '0', "A'nin tlast'i '0' olmali");
        -- bu kenarda A transfer edildi, skid -> reg

        -- Cevrim 4: sira B'de
        wait until rising_edge(clk);
        check_equal(m_axis_tvalid, '1', "B cikista sunulmali");
        check_equal(m_axis_tdata, beat_value(2), "ikinci beat B olmali");
        check_equal(m_axis_tlast, '1', "tlast B ile birlikte tasinmali");
        check_equal(s_axis_tready, '1', "skid bosaldi, giris yeniden acilmali");
        -- bu kenarda B transfer edildi

        -- Cevrim 5: buffer bos
        wait until rising_edge(clk);
        check_equal(m_axis_tvalid, '0', "buffer bosaldiktan sonra tvalid dusmeli");

      --------------------------------------------------------------------
      elsif run("tvalid_asiliyken_payload_sabit_kalir") then
        -- Iddia: m_axis_tready dusuk kaldigi surece cikis kipirdamaz.
        -- Bu, protokolun master tarafina koydugu tek katı kural.

        s_axis_tdata  <= beat_value(1);
        s_axis_tlast  <= '1';
        s_axis_tvalid <= '1';
        m_axis_tready <= '0';
        wait until rising_edge(clk);
        -- bu kenarda beat reg'e girdi

        s_axis_tvalid <= '0';   -- el sikisma tamamlandi, birakmak serbest

        for i in 1 to 5 loop
          wait until rising_edge(clk);
          check_equal(m_axis_tvalid, '1',
                      "tready dusukken tvalid geri cekilemez (cevrim "
                      & integer'image(i) & ")");
          check_equal(m_axis_tdata, beat_value(1),
                      "tready dusukken payload degisemez (cevrim "
                      & integer'image(i) & ")");
          check_equal(m_axis_tlast, '1',
                      "tready dusukken tlast degisemez (cevrim "
                      & integer'image(i) & ")");
        end loop;

        m_axis_tready <= '1';
        wait until rising_edge(clk);
        check_equal(m_axis_tvalid, '1', "transfer aninda tvalid '1' olmali");
        -- bu kenarda transfer edildi

        wait until rising_edge(clk);
        check_equal(m_axis_tvalid, '0', "transferden sonra tvalid dusmeli");

      --------------------------------------------------------------------
      elsif run("geri_basinc_altinda_veri_kaybetmez") then
        -- Iddia: el sikismalarin ZAMANLAMASI ne olursa olsun, transfer
        -- edilen VERI DIZISI degismez. Protokolun varlik sebebi bu ayrim.
        -- Tohum sabit oldugu icin dusen bir kosu aynen tekrarlanabilir.

        while rx_index <= C_BEATS loop

          -- 1a) master: askidaki beat'e DOKUNULMAZ. Kabarcik yalnizca
          --     beat'ler arasina konur.
          if not tx_active and tx_index <= C_BEATS then
            rand_bool(0.75, do_it);
            if do_it then
              s_axis_tdata  <= beat_value(tx_index);
              s_axis_tlast  <= beat_last(tx_index);
              s_axis_tvalid <= '1';
              tx_active     := true;
            end if;
          end if;

          -- 1b) slave: tready serbestce indirilip kaldirilabilir.
          rand_bool(0.5, do_it);
          if do_it then
            m_axis_tready <= '1';
          else
            m_axis_tready <= '0';
          end if;

          -- 2) kenar
          wait until rising_edge(clk);
          cycle := cycle + 1;

          -- 3) degerlendirme
          if tx_active and s_axis_tready = '1' then
            tx_index      := tx_index + 1;
            tx_active     := false;
            s_axis_tvalid <= '0';
          end if;

          if m_axis_tvalid = '1' and m_axis_tready = '1' then
            check_equal(m_axis_tdata, beat_value(rx_index),
                        "beat " & integer'image(rx_index)
                        & ": veri kaybi veya sira bozulmasi");
            check_equal(m_axis_tlast, beat_last(rx_index),
                        "beat " & integer'image(rx_index) & ": yanlis tlast");
            rx_index := rx_index + 1;
          end if;

        end loop;

        check_equal(tx_index, C_BEATS + 1,
                    "gonderilen ve alinan beat sayisi tutmuyor");

        s_axis_tvalid <= '0';
        m_axis_tready <= '0';

      end if;

      -- Sonraki testin temiz baslamasi icin bir cevrim bosluk
      wait until rising_edge(clk);

    end loop;

    test_runner_cleanup(runner);
  end process main;

  test_runner_watchdog(runner, 1 ms);

end architecture bench;