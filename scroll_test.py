import re
import time
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.common.by import By

# Saat desenini ayıklamak için regex
TIME_RE = re.compile(r"^\s*\d{1,2}:\d{2}\s*(AM|PM)?\s*$", re.IGNORECASE)

def _attach_driver():
    """Açık Chrome'a bağlanır (9222 port)."""
    options = webdriver.ChromeOptions()
    options.debugger_address = "127.0.0.1:9222"
    return webdriver.Chrome(options=options)

def _open_group_if_needed(driver, group_name: str):
    """Grubu açar (zaten açıksa devam eder)."""
    try:
        el = driver.find_element(By.XPATH, f"//span[@title='{group_name}']")
        el.click()
        time.sleep(1.0)
    except:
        print("ℹ️ Grup zaten açık veya bulunamadı, devam ediliyor...")

def _find_scroll_container(driver):
    """Kaydırılabilir sohbet panelini bulur."""
    js = """
    const isScrollable = el => {
      if (!el) return false;
      const s = getComputedStyle(el);
      return (el.scrollHeight > el.clientHeight) && /(auto|scroll)/.test(s.overflowY);
    };
    const climb = start => {
      let el = start;
      while (el) {
        if (isScrollable(el)) return el;
        el = el.parentElement;
      }
      return null;
    };

    const seeds = [
      document.querySelector("div.message-in"),
      document.querySelector("div.message-out"),
      document.querySelector("div.copyable-text"),
      document.querySelector("div.x141l45o")
    ].filter(Boolean);

    for (const seed of seeds) {
      const sc = climb(seed);
      if (sc) return sc;
    }
    return document.scrollingElement || document.body;
    """
    return driver.execute_script("return (function(){%s})()" % js)

def _scroll_up(driver, scroller, px=1200, wait=0.7):
    """Paneli yukarı kaydırır."""
    driver.execute_script(
        "arguments[0].scrollTop = arguments[0].scrollTop - arguments[1];",
        scroller, px
    )
    time.sleep(wait)

def _get_timeline_nodes_in_scroller(scroller):
    """Sohbet panelindeki tarih ve mesaj node'larını döndürür."""
    xpath = (
        ".//div[contains(@class,'x141l45o')]"  # tarih etiketleri
        " | .//div[contains(@class,'message-in') or contains(@class,'message-out') or contains(@class,'copyable-text')]"
    )
    return scroller.find_elements(By.XPATH, xpath)

def _extract_message_text(msg_el):
    """
    Mesajı tek blok olarak döndürür.
    - Önce .copyable-text varsa onun textContent'i
    - Yoksa tüm elementin textContent'i
    """
    try:
        conts = msg_el.find_elements(By.CSS_SELECTOR, ".copyable-text")
        if conts:
            txt = conts[0].get_attribute("textContent").strip()
        else:
            txt = msg_el.get_attribute("textContent").strip()
        if not txt or TIME_RE.match(txt):
            return ""
        return txt
    except:
        return ""

def test_pazar_to_sali(group_name: str, max_scrolls: int = 300):
    driver = _attach_driver()
    _open_group_if_needed(driver, group_name)

    scroller = _find_scroll_container(driver)
    if not scroller:
        print("❌ Kaydırılabilir sohbet container'ı bulunamadı.")
        return

    print("✅ Sohbet paneli bulundu → Pazar aranıyor...")

    # 1. Pazar bulunana kadar hızlı kaydır
    pazar_found = False
    for i in range(max_scrolls):
        labels = scroller.find_elements(By.CSS_SELECTOR, "div.x141l45o")
        for lbl in labels:
            txt = (lbl.text or "").strip()
            if txt.lower().startswith("pazar"):
                pazar_found = True
                print(f"📅 Pazar bulundu: {txt}")
                break
        if pazar_found:
            break
        _scroll_up(driver, scroller, px=2000, wait=0.5)

    if not pazar_found:
        print("❌ Pazar bulunamadı.")
        return

    # 2. Pazar → Salı arası mesajları topla
    print("🔎 Pazar mesajları okunuyor, Salı'ya kadar devam edilecek...")
    bucket = defaultdict(list)
    current_date = None
    sali_seen = False

    for _ in range(max_scrolls):
        timeline = _get_timeline_nodes_in_scroller(scroller)
        for el in timeline:
            classes = el.get_attribute("class") or ""
            if "x141l45o" in classes:  # tarih etiketi
                label = (el.text or "").strip()
                if not label:
                    continue
                current_date = label
                bucket.setdefault(current_date, [])
                if label.lower().startswith("salı"):
                    sali_seen = True
            else:  # mesaj
                msg = _extract_message_text(el)
                if msg and current_date:
                    if msg not in bucket[current_date]:
                        bucket[current_date].append(msg)
        if sali_seen:
            print("📅 Salı bulundu, okuma tamamlandı.")
            break
        _scroll_up(driver, scroller, px=600, wait=0.8)

    # 3. ÇIKTI
    for date_label, msgs in bucket.items():
        print(f"\n📅 {date_label} ({len(msgs)} mesaj):")
        for m in msgs:
            print("  " + m)

# Doğrudan çalıştırma
if __name__ == "__main__":
    test_pazar_to_sali("Takip Grubu", max_scrolls=300)
