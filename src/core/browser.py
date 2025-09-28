"""
Browser Configuration

Chrome WebDriver configuration and setup utilities.
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class BrowserConfig:
    """
    Chrome WebDriver configuration and setup.
    """
    
    def __init__(self, config_loader, logger):
        """
        Initialize browser configuration.
        
        Args:
            config_loader: ConfigLoader instance
            logger: Logger instance
        """
        self.config_loader = config_loader
        self.logger = logger
    
    def create_chrome_options(self):
        """
        Create and configure Chrome options.
        
        Returns:
            ChromeOptions: Configured Chrome options
        """
        options = webdriver.ChromeOptions()
        
        # Basic Chrome arguments
        options.add_argument(f"--user-data-dir={self.config_loader.get_session_path()}")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        # Headless mode
        if self.config_loader.get_headless():
            options.add_argument("--headless=new")
            # Headless modda pencere boyutu ayarla
            selenium_config = self.config_loader.get_selenium_config()
            window_size = selenium_config.get('window_size', [1200, 800])
            options.add_argument(f"--window-size={window_size[0]},{window_size[1]}")
        else:
            # Normal modda tam ekran başlat
            options.add_argument("--start-maximized")
        
        self.logger.info("Chrome options configured")
        return options
    
    def create_driver(self):
        """
        Create and return a configured Chrome WebDriver.
        
        Returns:
            WebDriver: Configured Chrome WebDriver
        """
        options = self.create_chrome_options()
        
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )
        
        # Normal modda tam ekran yap (ek güvenlik)
        if not self.config_loader.get_headless():
            try:
                driver.maximize_window()
                self.logger.info("Chrome penceresi tam ekran yapıldı")
            except Exception as e:
                self.logger.warning(f"Tam ekran yapılamadı: {e}")
        
        self.logger.info("Chrome WebDriver created successfully")
        return driver
