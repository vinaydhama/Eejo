from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time

# Specify the path to your ChromeDriver executable
# Replace 'path/to/chromedriver' with the actual path on your system
chrome_driver_path = 'C:\Program Files\Google\Chrome\Application\chrome.exe' 

# Configure Chrome options for fullscreen and initial setup
chrome_options = Options()
chrome_options.add_argument("--start-fullscreen") # Starts the browser in fullscreen mode
# chrome_options.add_argument("--kiosk") # Alternative for kiosk mode (may hide browser UI)

# Initialize the WebDriver
service = Service(executable_path=chrome_driver_path)
driver = webdriver.Chrome(service=service, options=chrome_options)

try:
    # Open the desired URL
    url = "https://www.example.com"
    driver.get(url)

    # Set the zoom level using JavaScript
    # 'document.body.style.zoom' controls the page zoom
    # '150%' means 150% zoom. Adjust as needed.
    driver.execute_script("document.body.style.zoom='150%'")

    # Keep the browser open for a few seconds to observe (optional)
    time.sleep(5) 

finally:
    # Close the browser
    driver.quit()