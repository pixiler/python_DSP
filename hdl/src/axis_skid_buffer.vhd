--------------------------------------------------------------------------
-- AXI4-Stream skid buffer (2 derinlik)
--
-- AMAC
--   valid/ready el sikismasini HER IKI yonde de kayitli hale getirmek:
--     s_axis_tready  <-- yalnizca skid_valid (kayit) uzerinden
--     m_axis_tvalid  <-- yalnizca reg_valid  (kayit) uzerinden
--   Boylece modulun girisi ile cikisi arasinda kombinasyonel yol kalmaz.
--   Iki fayda: (1) uzun zincirlerde ready yolu birikmez, (2) "slave
--   tready'yi tvalid'e bakarak kaldirabilir" izniyle birlesip
--   tvalid -> tready -> tvalid kombinasyonel dongusu olusturamaz.
--
-- NEDEN IKI KAYIT
--   m_axis_tready dustugu cevrimde s_axis_tready hala '1'dir; cunku
--   kayitli bir sinyale bagli, yani "duramam" haberi bir cevrim gecikir.
--   O cevrimde yukari akis bir beat daha gonderir ve AXI'ye gore o beat
--   KABUL EDILMIS sayilir. Onu koyacak bir yer gerekir: skid.
--   Bir sonraki cevrimde s_axis_tready = '0' oldugu icin ucuncu bir beat
--   gelemez. Bu yuzden iki kayit yeterli, ucuncusu gereksizdir.
--
-- SIRA KORUNUMU  (ilk denemede kaybedilen ozellik)
--   reg  : her zaman EN ESKI beat. Cikisa DOGRUDAN baglidir.
--   skid : bir sonraki beat. Yalnizca reg bosaldiginda reg'e tasinir.
--   Cikista mux YOKTUR. Cikis "skid doluysa skid, degilse reg" diye
--   secilseydi yeni beat eskisinden once cikardi -- veri kaybi olmadan
--   sira bozulurdu, ki bu sayim tabanli testlerin goremedigi bir hatadir.
--
-- KONVANSIYONLAR
--   reset : SENKRON (projenin geri kalaniyla ayni)
--   gecikme: 1 cevrim
--   veri yolu bos akista tam hiz (her cevrim bir beat)
--------------------------------------------------------------------------

library ieee;
use ieee.std_logic_1164.all;

entity axis_skid_buffer is
  generic (
    DATA_WIDTH : positive := 32
  );
  port (
    clk   : in std_logic;
    reset : in std_logic;

    -- Slave arayuzu (giris)
    s_axis_tvalid : in  std_logic;
    s_axis_tready : out std_logic;
    s_axis_tdata  : in  std_logic_vector(DATA_WIDTH - 1 downto 0);
    s_axis_tlast  : in  std_logic;

    -- Master arayuzu (cikis)
    m_axis_tvalid : out std_logic;
    m_axis_tready : in  std_logic;
    m_axis_tdata  : out std_logic_vector(DATA_WIDTH - 1 downto 0);
    m_axis_tlast  : out std_logic
  );
end entity axis_skid_buffer;

architecture rtl of axis_skid_buffer is

  -- Cikis kaydi: en eski beat burada durur.
  signal reg_data  : std_logic_vector(DATA_WIDTH - 1 downto 0) := (others => '0');
  signal reg_last  : std_logic := '0';
  signal reg_valid : std_logic := '0';

  -- Skid kaydi: fren mesafesinde yakalanan beat.
  signal skid_data  : std_logic_vector(DATA_WIDTH - 1 downto 0) := (others => '0');
  signal skid_last  : std_logic := '0';
  signal skid_valid : std_logic := '0';

begin

  ------------------------------------------------------------------------
  -- Kombinasyonel cikislar
  --
  -- Ikisi de YALNIZCA kayitlara bakar. Ne s_axis_tvalid ne m_axis_tready
  -- bu ifadelerde gecer -- sartname 1 boyle saglanir.
  ------------------------------------------------------------------------
  s_axis_tready <= not skid_valid;

  m_axis_tvalid <= reg_valid;
  m_axis_tdata  <= reg_data;
  m_axis_tlast  <= reg_last;

  ------------------------------------------------------------------------
  -- Ana kontrol
  --
  -- Her kenarda tek bir soru sorulur: "cikis yuvasi bosaliyor mu?"
  --   Bosaliyorsa  -> yuvaya bir sonraki beat'i yerlestir (once skid!)
  --   Bosalmiyorsa -> gelen beat'i skid'e kaydir
  ------------------------------------------------------------------------
  process (clk)
  begin
    if rising_edge(clk) then

      if reset = '1' then
        reg_valid  <= '0';
        skid_valid <= '0';

      -- (a) Cikis yuvasi bosaliyor: ya bostu, ya bu kenarda el sikisildi.
      elsif reg_valid = '0' or m_axis_tready = '1' then

        if skid_valid = '1' then
          -- Bekleyen beat once girer. SIRA BURADA KORUNUR.
          -- Not: skid doluyken s_axis_tready = '0' oldugu icin bu dalda
          -- girisle bir catisma olusamaz.
          reg_data   <= skid_data;
          reg_last   <= skid_last;
          reg_valid  <= '1';
          skid_valid <= '0';

        elsif s_axis_tvalid = '1' then
          -- skid bos => s_axis_tready = '1' => el sikisma gecerli.
          reg_data  <= s_axis_tdata;
          reg_last  <= s_axis_tlast;
          reg_valid <= '1';

        else
          -- Elde bir sey yok.
          reg_valid <= '0';
        end if;

      -- (b) Cikis tikali (reg dolu ve m_axis_tready = '0').
      else
        if s_axis_tvalid = '1' and skid_valid = '0' then
          -- skid bos oldugu icin s_axis_tready '1'di: bu beat kabul edildi,
          -- ama cikis yuvasi dolu. Kayacagi yer burasi.
          skid_data  <= s_axis_tdata;
          skid_last  <= s_axis_tlast;
          skid_valid <= '1';
        end if;
        -- skid de doluysa s_axis_tready = '0'; hicbir sey kipirdamaz.
      end if;

    end if;
  end process;

end architecture rtl;