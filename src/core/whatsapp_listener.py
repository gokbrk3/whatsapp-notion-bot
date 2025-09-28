"""
WhatsApp Listener

WhatsApp Web'i dinleyerek yeni mesajları yakalayan sınıf.
"""

from typing import List
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import time
from .browser import BrowserConfig


class WhatsAppListener:
    """
    WhatsApp Web'i dinleyerek yeni mesajları yakalayan sınıf.
    """
    
    def __init__(self, config_loader, logger):
        """
        WhatsApp Listener'ı başlatır.
        
        Args:
            config_loader: ConfigLoader instance
            logger: Logger instance
        """
        self.config_loader = config_loader
        self.logger = logger
        
        # Browser configuration
        browser_config = BrowserConfig(config_loader, logger)
        self.driver = browser_config.create_driver()
        
        self.is_logged_in = False
        
    def _is_chat_list_visible(self):
        """
        Chat list görünür mü kontrol eder.
        
        Returns:
            bool: Chat list görünür mü
        """
        selectors = [
            '[data-testid="chat-list"]',
            'aside[aria-label="Chat list"]',
            'div[aria-label="Chats"]',
            'div[role="grid"][aria-label]'
        ]
        
        for selector in selectors:
            try:
                if self.driver.find_element(By.CSS_SELECTOR, selector):
                    return True
            except:
                continue
        return False
        
    def _wait_until_logged_in(self, timeout=180):
        """
        Giriş yapılana kadar bekler.
        
        Args:
            timeout: Maksimum bekleme süresi (saniye)
            
        Returns:
            bool: Giriş başarılı mı
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self._is_chat_list_visible():
                return True
            time.sleep(2)
        
        return False
        
    def login_to_whatsapp(self):
        """
        WhatsApp Web'e giriş yapar.
        
        Returns:
            bool: Giriş başarılı mı
        """
        try:
            self.driver.get("https://web.whatsapp.com")
            
            if self._wait_until_logged_in():
                self.is_logged_in = True
                return True
            else:
                return False
        except Exception as e:
            self.logger.error(f"WhatsApp giriş hatası: {e}")
            return False
        
    def open_group(self, group_name: str) -> bool:
        """
        Belirtilen grubu açar.
        
        Args:
            group_name: Grup adı
            
        Returns:
            bool: Grup açıldı mı
        """
        try:
            # Grubu bul ve tıkla
            group_xpath = f'//span[@title="{group_name}"]'
            group_element = self.driver.find_element(By.XPATH, group_xpath)
            group_element.click()
            
            # Mesaj paneli selector fallback listesi
            message_selectors = [
                "div[data-testid='conversation-panel-messages']",
                "div[data-testid='conversation-panel-body']",
                "div[aria-label='Mesajlar']",
                "div[aria-label='Message list']",
                "div.copyable-area",
                "div[role='region']"
            ]
            
            # 20 saniye boyunca mesaj panelini bekle
            start_time = time.time()
            while time.time() - start_time < 20:
                for selector in message_selectors:
                    try:
                        if self.driver.find_element(By.CSS_SELECTOR, selector):
                            return True
                    except:
                        continue
                time.sleep(1)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Grup açma hatası: {e}")
            return False
        
    def get_recent_messages(self, limit=10) -> List[str]:
        """
        Son mesajları getirir.
        
        Args:
            limit: Maksimum mesaj sayısı
            
        Returns:
            List[str]: Mesaj listesi
        """
        messages = []
        
        try:
            # Öncelikli selector
            try:
                message_elements = self.driver.find_elements(By.CSS_SELECTOR, '.selectable-text')
            except:
                # Fallback selector
                message_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div[role="row"] div[dir="auto"]')
            
            # Son limit kadar mesajı al
            for element in message_elements[-limit:]:
                try:
                    text = element.text.strip()
                    if text:
                        messages.append(text)
                except:
                    continue
                    
        except Exception as e:
            self.logger.error(f"Mesaj alma hatası: {e}")
            
        return messages
        
    def get_messages_by_date(self, target_date: str) -> List[str]:
        """
        Belirtilen tarih için mesajları getirir.
        Tarih ayracı bulup o günün mesajlarını toplar.
        """
        import re
        
        self.logger.info(f"Hedef tarih aranıyor: {target_date}")

        # Bir kere focus ver
        if not self._focus_message_panel():
            self.logger.error("Focus verilemedi, scroll yapılamıyor")
            return []

        # Tarih formatları hazırla
        date_formats = [
            target_date,  # 27.09.2025
            target_date.replace(".", "-"),  # 27-09-2025
            target_date.replace(".", "/"),  # 27/09/2025
        ]
        
        # Bugün ise ek formatlar ekle
        from datetime import datetime
        if target_date == datetime.now().strftime("%d.%m.%Y"):
            date_formats.extend(["BUGÜN", "TODAY"])

        # Tarih ayracı regex
        date_pattern = re.compile(
            r"^\s*(\d{1,2}[./-]\d{1,2}[./-]\d{2,4}|BUGÜN|DÜN|TODAY|YESTERDAY)\s*$",
            re.IGNORECASE
        )

        messages = []
        seen = set()
        collecting = False
        target_found = False
        next_date_found = False

        # Tek focus ile sürekli scroll - hiç bekleme yok
        self.logger.info("⬆️ Yukarı kaydırılıyor (PAGE_UP)")
        actions = ActionChains(self.driver)
        
        for scroll_attempt in range(50):  # Daha fazla scroll denemesi
            # Scroll yap
            actions.send_keys(Keys.PAGE_UP).perform()
            
            # Mevcut mesajları kontrol et
            try:
                rows = self.driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
                for row in rows:
                    try:
                        raw_text = row.text.strip()
                        if not raw_text:
                            continue
                            
                        # Tarih ayracı mı kontrol et
                        if date_pattern.match(raw_text):
                            normalized_date = raw_text.strip()
                            
                            # Hedef tarih bulundu mu?
                            if not target_found and normalized_date in date_formats:
                                self.logger.info(f"✅ Tarih ayracı bulundu: {raw_text}")
                                collecting = True
                                target_found = True
                                continue
                            
                            # Farklı tarih bulundu mu? (toplama durdur)
                            elif collecting and normalized_date not in date_formats:
                                self.logger.info(f"🛑 Sonraki tarih ayracı görüldü: {raw_text}")
                                next_date_found = True
                                break
                        
                        # Mesaj toplama
                        elif collecting and not next_date_found:
                            message_text = self._extract_text_from_row(row)
                            if message_text and message_text not in seen:
                                seen.add(message_text)
                                messages.append(message_text)
                                
                    except Exception as e:
                        continue
                
                # Hedef tarih bulundu ve sonraki tarih de bulundu
                if collecting and next_date_found:
                    break
                    
            except Exception as e:
                self.logger.warning(f"Scroll sırasında hata: {e}")
                continue

        # Hedef tarih bulunamadıysa son mesajları al
        if not target_found:
            self.logger.warning(f"Hedef tarih bulunamadı: {target_date}")
            try:
                message_elements = self.driver.find_elements(By.CSS_SELECTOR, '.selectable-text')
                for element in message_elements[-20:]:  # Son 20 mesaj
                    try:
                        text = element.text.strip()
                        if text and text not in seen:
                            seen.add(text)
                            messages.append(text)
                    except:
                        continue
            except Exception as e:
                self.logger.error(f"Son mesaj alma hatası: {e}")
        
        self.logger.info(f"📊 {target_date} için toplanan mesaj sayısı: {len(messages)}")
        return messages

    def _find_chat_panel(self, driver, timeout=10):
        """
        Chat messages panelini bulur ve bekler.
        
        Args:
            driver: WebDriver instance
            timeout: Maximum wait time in seconds
            
        Returns:
            WebElement or None: Chat panel element
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        # Daha kapsamlı selector listesi
        selectors = [
            "div[data-testid='conversation-panel-messages'][role='region']",
            "div[data-testid='conversation-panel-messages']",
            "div[aria-label='Mesajlar']",
            "div[aria-label='Messages']",
            "div.copyable-area",
            "div[role='region']"
        ]
        
        for selector in selectors:
            try:
                panel = WebDriverWait(driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                )
                self.logger.info(f"✅ Chat messages panel bulundu ({selector})")
                return panel
            except Exception as e:
                self.logger.debug(f"Selector başarısız: {selector} - {e}")
                continue
        
        self.logger.error(f"❌ Chat messages panel bulunamadı (timeout={timeout})")
        return None

    def _scroll_up_fast(self, driver, panel, step: int = 2000) -> bool:
        """
        Fast upward scrolling using JavaScript.
        
        Args:
            driver: WebDriver instance
            panel: Chat messages panel element
            step: Scroll step size in pixels
            
        Returns:
            bool: Success status
        """
        try:
            driver.execute_script("arguments[0].scrollTop -= 2000;", panel)
            self.logger.debug(f"⬆️ Hızlı yukarı kaydırıldı (step: {step})")
            time.sleep(0.2)  # Small delay after scroll
            return True
        except Exception as e:
            self.logger.warning(f"Hızlı yukarı kaydırma başarısız: {e}")
            return False

    def _scroll_down_fast(self, driver, panel, step: int = 2000) -> bool:
        """
        Fast downward scrolling using JavaScript.
        
        Args:
            driver: WebDriver instance
            panel: Chat messages panel element
            step: Scroll step size in pixels
            
        Returns:
            bool: Success status
        """
        try:
            driver.execute_script("arguments[0].scrollTop += 2000;", panel)
            self.logger.debug(f"⬇️ Hızlı aşağı kaydırıldı (step: {step})")
            time.sleep(0.2)  # Small delay after scroll
            return True
        except Exception as e:
            self.logger.warning(f"Hızlı aşağı kaydırma başarısız: {e}")
            return False

    def _wait_for_lazy_load(self, panel, previous_count: int, timeout: int = 3) -> bool:
        """
        Wait for lazy loading of new messages after scrolling.
        
        Args:
            panel: Chat messages panel element
            previous_count: Previous message count
            timeout: Maximum wait time in seconds
            
        Returns:
            bool: True if new messages loaded, False if timeout
        """
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                # Re-fetch messages to avoid stale elements
                dom_messages = self._extract_messages_from_dom()
                current_count = len(dom_messages)
                
                if current_count > previous_count:
                    self.logger.debug(f"Lazy load detected: {current_count} messages (was {previous_count})")
                    return True
                    
                time.sleep(0.2)
            except Exception as e:
                self.logger.warning(f"Lazy load detection hatası: {e}")
                break
        
        return False

    def _extract_messages_from_dom(self):
        """
        DOM'dan mesajları çıkarır.
        
        Returns:
            List[Tuple[str, str]]: (raw_text, message_text) çiftleri
        """
        from typing import Tuple
        from selenium.common.exceptions import StaleElementReferenceException
        
        messages = []
        try:
            # Her seferinde yeni elementleri bul (stale element hatası önlemek için)
            rows = self.driver.find_elements(By.CSS_SELECTOR, "div[role='row']")
            for row in rows:
                try:
                    raw_text = row.text.strip()
                    if raw_text:
                        message_text = self._extract_message_text(row)
                        messages.append((raw_text, message_text))
                except StaleElementReferenceException:
                    self.logger.warning("Stale element hatası - mesaj atlanıyor")
                    continue
                except Exception as e:
                    self.logger.warning(f"Mesaj çıkarma hatası: {e}")
                    continue
        except Exception as e:
            self.logger.warning(f"DOM'dan mesaj çıkarma hatası: {e}")
        return messages

    def _is_date_separator(self, text: str, date_pattern) -> bool:
        """
        Metnin tarih ayracı olup olmadığını kontrol eder.
        
        Args:
            text: Kontrol edilecek metin
            date_pattern: Regex pattern
            
        Returns:
            bool: Tarih ayracı mı
        """
        return bool(date_pattern.match(text))

    def _normalize_date(self, date_text: str) -> str:
        """
        Tarih metnini normalize eder.
        
        Args:
            date_text: Ham tarih metni
            
        Returns:
            str: Normalize edilmiş tarih
        """
        return date_text.strip()
        
    def _get_message_panels(self):
        """
        Mesaj panellerini getirir.
        
        Returns:
            List[WebElement]: Mesaj paneli elementleri
        """
        from selenium.webdriver.common.by import By
        
        panels = []
        for sel in [
            "div[data-testid='conversation-panel-messages']",
            "div[data-testid='conversation-panel-body']",
            "div[aria-label='Mesajlar']",
            "div[aria-label='Message list']",
            "div.copyable-area",
            "div[role='region']"
        ]:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    panels.extend(els)
            except:
                continue
        return panels
        
    def _extract_message_text(self, panel) -> str:
        """
        Panel'den mesaj metnini çıkarır.
        
        Args:
            panel: Selenium WebElement
            
        Returns:
            str: Mesaj metni
        """
        try:
            # Önce .selectable-text span elemanlarını al
            spans = panel.find_elements(By.CSS_SELECTOR, '.selectable-text span')
            if spans:
                # Son span'in text'ini döndür (alıntı mesajları atla)
                return spans[-1].text.strip()
            else:
                # Fallback olarak panel'in tüm text'ini döndür
                return panel.text.strip()
        except:
            return ""
        
    def _extract_text_from_row(self, row) -> str:
        """
        Satırdan mesaj metnini çıkarır.
        
        Args:
            row: Selenium WebElement
            
        Returns:
            str: Mesaj metni
        """
        try:
            # Önce .selectable-text span elemanlarını al
            spans = row.find_elements(By.CSS_SELECTOR, '.selectable-text span')
            if spans:
                # Son span'in text'ini döndür (alıntı mesajları atla)
                return spans[-1].text.strip()
            else:
                # Fallback olarak satırın tüm text'ini döndür
                return row.text.strip()
        except:
            return ""
            
    def _get_message_container(self):
        """
        Sağdaki aktif sohbet ekranındaki mesaj panelini bulur.
        Önce sohbet listesi değil, conversation panel aranır.
        """
        selectors = [
            "div.x5yr21d.xnpuxes.copyable-area",  # Ana mesaj alanı
            "div[data-testid='conversation-panel-messages']",
            "div.copyable-area",
            "div[role='region']",
            "div[aria-label='Mesajlar']",
            "div[aria-label='Messages']"
        ]
        for sel in selectors:
            try:
                return self.driver.find_element(By.CSS_SELECTOR, sel)
            except:
                continue
        return None

    def _focus_message_panel(self, timeout=10):
        """
        Mesaj panelini bulur ve fokuslar.
        Test scriptindeki tam aynı yaklaşımı kullanır.
        """
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        selectors = [
            "div[data-testid='conversation-panel-messages']",
            "div.copyable-area",
        ]
        for sel in selectors:
            try:
                panel = WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel))
                )
                panel.click()
                self.logger.info(f"✅ Mesaj paneline fokus verildi ({sel})")
                return True
            except:
                continue
        self.logger.error("❌ Mesaj paneli bulunamadı")
        return False

    def _scroll_up(self):
        """
        Mesaj panelini yukarı kaydırır.
        Test scriptindeki tam aynı yaklaşımı kullanır.
        """
        if not self._focus_message_panel():
            return

        actions = ActionChains(self.driver)
        actions.send_keys(Keys.PAGE_UP).perform()
        self.logger.debug("⬆️ Yukarı kaydırıldı (PAGE_UP)")

    def _scroll_down(self):
        """
        Mesaj panelini aşağı kaydırır.
        Test scriptindeki tam aynı yaklaşımı kullanır.
        """
        if not self._focus_message_panel():
            return

        actions = ActionChains(self.driver)
        actions.send_keys(Keys.PAGE_DOWN).perform()
        self.logger.debug("⬇️ Aşağı kaydırıldı (PAGE_DOWN)")