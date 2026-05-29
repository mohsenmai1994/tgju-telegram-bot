import time
import platform
from pathlib import Path
from typing import Final, List
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException

# --- Constants ---
# Defines the User-Agent string to mimic a real browser.
USER_AGENT: Final[str] = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
# Sets a default timeout in seconds for explicit waits, ensuring scripts don't wait indefinitely.
DEFAULT_TIMEOUT: Final[int] = 10
# Sets a default timeout for page loads.
DEFAULT_PAGE_LOAD_TIMEOUT: Final[int] = 15

# --- Driver Setup Functions ---

def get_driver_service() -> ChromeService:
    """
    Initializes and returns a ChromeDriver service object.

    It first checks for 'chromedriver.exe' (on Windows) or 'chromedriver' (on other OS)
    in the script's directory. If not found, it assumes the driver is available in the
    system's PATH environment variable.

    Returns:
        ChromeService: An initialized ChromeService object.

    Raises:
        FileNotFoundError: If chromedriver cannot be found either locally or in PATH.
    """
    driver_name = "chromedriver.exe" if platform.system() == "Windows" else "chromedriver"
    # Construct the potential path to the chromedriver executable.
    # This assumes the script is run from its own directory or a parent directory.
    # In more complex projects, managing driver versions and paths is crucial.
    script_dir = Path(__file__).resolve().parent
    potential_driver_path = script_dir / driver_name

    if potential_driver_path.exists():
        print(f"Using ChromeDriver found at: {potential_driver_path}")
        return ChromeService(executable_path=str(potential_driver_path))
    else:
        # If not found locally, Selenium will attempt to find it in the system's PATH.
        # If it's not in PATH, Selenium will raise an error during driver initialization.
        print("ChromeDriver not found locally. Assuming chromedriver is in system PATH.")
        return ChromeService()

def setup_chrome_options() -> webdriver.ChromeOptions:
    """
    Configures ChromeOptions for headless execution and other essential settings.

    These options are optimized for environments like CI/CD pipelines (e.g., GitHub Actions)
    and general automation tasks, aiming to bypass detection and ensure stability.

    Returns:
        webdriver.ChromeOptions: A configured ChromeOptions object.
    """
    options = webdriver.ChromeOptions()

    # Headless mode: Enables running Chrome without a visible UI, suitable for servers.
    # "--headless=new" is the recommended modern headless mode.
    options.add_argument("--headless=new")
    # Disables the sandbox, often necessary in containerized environments (like Docker)
    # or some CI/CD systems to avoid permission errors.
    options.add_argument("--no-sandbox")
    # Overcomes limited resource problems by using /dev/shm (shared memory)
    # which is a RAM-based filesystem, useful in constrained environments.
    options.add_argument("--disable-dev-shm-usage")
    # Disables GPU hardware acceleration, as it's not needed in headless mode
    # and can sometimes cause issues.
    options.add_argument("--disable-gpu")
    # Sets a custom User-Agent string to mimic a specific browser version.
    options.add_argument(f"--user-agent={USER_AGENT}")
    # Sets a fixed window size, important for consistent rendering in headless mode.
    options.add_argument("--window-size=1920,1080")

    # Disables automation-related flags that might be detected by websites.
    # 'enable-automation' and 'enable-logging' are common ones to exclude.
    options.add_experimental_option("excludeSwitches", ["enable-automation", "enable-logging"])
    # Disables the automation extension, another step to appear more like a regular browser.
    options.add_experimental_option('useAutomationExtension', False)

    return options

# --- Custom WebDriver Class ---

class CustomWebDriver(webdriver.Chrome):
    """
    A custom Chrome WebDriver class that extends the base Selenium WebDriver.

    It incorporates enhanced methods for safer navigation, element finding,
    and error handling, utilizing explicit waits for improved reliability.
    """
    def __init__(self, service=None, options=None, keep_alive=True):
        """
        Initializes the CustomWebDriver.

        Args:
            service (ChromeService, optional): The ChromeDriver service. Defaults to None,
                                               which triggers `get_driver_service()`.
            options (webdriver.ChromeOptions, optional): Chrome browser options. Defaults to None,
                                                         which triggers `setup_chrome_options()`.
            keep_alive (bool, optional): Whether to keep the driver process alive. Defaults to True.
        """
        if options is None:
            options = setup_chrome_options()
        if service is None:
            service = get_driver_service()

        # Initialize the base Chrome driver with the provided or default service and options.
        super().__init__(service=service, options=options, keep_alive=keep_alive)
        # Ensure the window size is set, even if already in options, for robustness.
        self.set_window_size(1920, 1080)
        print("CustomWebDriver initialized successfully.")

    def safe_get(self, url: str, timeout: int = DEFAULT_PAGE_LOAD_TIMEOUT):
        """
        Navigates to a given URL with robust error handling and page load verification.

        It waits until the document's readyState is 'complete', indicating that
        the page and its resources have fully loaded.

        Args:
            url (str): The URL to navigate to.
            timeout (int): The maximum time in seconds to wait for the page to load.

        Raises:
            TimeoutException: If the page does not load completely within the specified timeout.
            Exception: For any other errors during navigation.
        """
        print(f"Navigating to: {url}")
        try:
            self.get(url)
            # Use WebDriverWait to poll the document's readyState.
            WebDriverWait(self, timeout).until(
                lambda driver: driver.execute_script('return document.readyState') == 'complete'
            )
            print("Page loaded successfully.")
        except TimeoutException:
            print(f"Error: Page load timed out after {timeout} seconds at URL: {url}")
            raise
        except Exception as e:
            print(f"An unexpected error occurred during navigation to {url}: {e}")
            raise

    def safe_find_element(self, by: By, value: str, timeout: int = DEFAULT_TIMEOUT):
        """
        Finds a single web element using explicit waits for visibility and presence.

        This method ensures that the element is not only present in the DOM but also
        visible to the user before returning it, preventing interactions with hidden elements.

        Args:
            by (By): The locator strategy (e.g., By.ID, By.XPATH, By.CSS_SELECTOR).
            value (str): The locator value (e.g., the ID, XPath expression, or CSS selector).
            timeout (int): The maximum time in seconds to wait for the element to become visible.

        Returns:
            webdriver.remote.webelement.WebElement: The found and visible element.

        Raises:
            TimeoutException: If the element is not found or visible within the specified timeout.
            NoSuchElementException: If the element is not present in the DOM.
        """
        print(f"Attempting to find visible element by '{by}' with value '{value}' (timeout: {timeout}s)")
        try:
            # Wait for the element to be present in the DOM and visible.
            element = WebDriverWait(self, timeout).until(
                EC.visibility_of_element_located((by, value))
            )
            print("Element found and is visible.")
            return element
        except TimeoutException:
            print(f"Error: Element not found or visible after {timeout} seconds using locator: ({by}, '{value}')")
            raise
        except NoSuchElementException:
             print(f"Error: Element not present in the DOM using locator: ({by}, '{value}')")
             raise
        except Exception as e:
            print(f"An unexpected error occurred while finding element ({by}, '{value}'): {e}")
            raise

    def find_elements(self, by: By, value: str, timeout: int = DEFAULT_TIMEOUT) -> List[webdriver.remote.webelement.WebElement]:
        """
        Finds multiple web elements using explicit waits for presence.

        This method waits until at least one element matching the locator is present
        in the DOM before attempting to retrieve all matching elements.

        Args:
            by (By): The locator strategy (e.g., By.ID, By.XPATH, By.CSS_SELECTOR).
            value (str): The locator value.
            timeout (int): The maximum time in seconds to wait for elements to be present.

        Returns:
            List[webdriver.remote.webelement.WebElement]: A list of found elements. Returns an empty list
                                                          if no elements are found after the timeout.
        """
        print(f"Attempting to find elements by '{by}' with value '{value}' (timeout: {timeout}s)")
        try:
            # Wait for at least one element to be present in the DOM.
            WebDriverWait(self, timeout).until(
                EC.presence_of_all_elements_located((by, value))
            )
            # Find all elements matching the locator.
            elements = super().find_elements(by, value)
            print(f"Found {len(elements)} elements.")
            return elements
        except TimeoutException:
            print(f"No elements found after {timeout} seconds using locator: ({by}, '{value}')")
            return [] # Return an empty list if the timeout is reached.
        except Exception as e:
            print(f"An unexpected error occurred while finding elements ({by}, '{value}'): {e}")
            return []


# --- Example Usage ---
# This block demonstrates how to use the CustomWebDriver class.
# It will only run when the script is executed directly (not imported as a module).
if __name__ == "__main__":
    driver = None  # Initialize driver to None for the finally block
    try:
        # Instantiate the custom driver.
        driver = CustomWebDriver()

        # Example 1: Navigate to a page and find a specific heading element.
        print("\n--- Example 1: Finding a heading ---")
        driver.safe_get("https://www.example.com")
        # Find the main heading (h1) using XPath.
        heading_element = driver.safe_find_element(By.XPATH, "//h1")
        if heading_element:
            print(f"Found heading text: '{heading_element.text}'")

        # Example 2: Find all paragraph elements on the page.
        print("\n--- Example 2: Finding all paragraphs ---")
        # Find all paragraph tags (p).
        paragraphs = driver.find_elements(By.TAG_NAME, "p")
        if paragraphs:
            for i, p in enumerate(paragraphs):
                # Print the first 50 characters of each paragraph's text.
                print(f"Paragraph {i+1}: '{p.text[:50]}...'")
        else:
            print("No paragraphs found on the page.")

        # Example 3: Demonstrating a case where an element might not be found immediately.
        # (This example assumes a hypothetical element that might take time to load or not exist)
        print("\n--- Example 3: Demonstrating element search (may time out) ---")
        try:
            # Trying to find an element that might not exist or take longer than default timeout
            non_existent_element = driver.safe_find_element(By.ID, "a-very-unlikely-id", timeout=5)
            print("This message should not appear if the ID doesn't exist.")
        except TimeoutException:
            print("Successfully caught TimeoutException for a non-existent element (as expected).")
        except Exception as e:
            print(f"Caught an unexpected exception: {e}")

    except Exception as e:
        # Catch any exceptions that occur during driver setup or operations.
        print(f"\nAn error occurred during script execution: {e}")
    finally:
        # Ensure the browser is closed even if errors occur.
        if driver:
            print("\nClosing the browser.")
            driver.quit()
            print("Browser closed.")
