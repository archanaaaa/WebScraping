import os
import csv
import requests
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime

# Function to write the scraped data to a CSV file
def write_to_csv(data):

    # Check if the file exists or is empty
    file_exists = os.path.isfile('CPSCScraper_output.csv') and os.stat('CPSCScraper_output.csv').st_size > 0
    
    with open('CPSCScraper_output.csv', 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write headers if the file is empty
        if not file_exists:
          
            headers = ['Web Link', 'Headline', 'Name of Product', 'Hazard', 'Remedy', 'Recall Date', 'Units',
                       'Description', 'Remedy', 'Incidents Injuries', 'Sold at', 'Importers/Distributors/Manufacturers', 'Manufactured In',
                       'Recall number','Consumer Contact']
            
            writer.writerow(headers)
        
        # Write the data
        writer.writerow(data)

# Check and get the latest GeckoDriver version
def get_latest_driver_version():
    pass


# Function to set up the browser (Used: Mozilla Firefox)
def browser_setup():
    # Set up Chrome WebDriver
    driver_path = "../chromedriver_win32/chromedriver.exe"

    # driver_version = get_latest_driver_version()
    # driver_path = f"chromedriver_{driver_version}"

    # Configure Chrome options for headless mode
    options = Options()
    options.headless = False

    service = Service(driver_path)

    driver = webdriver.Chrome(options=options, service=service)

    # Set window size to avoid "element not interactable" error
    driver.set_window_size(1920, 1080)
     
    return driver

# Function to scrape data for every result
def scrape(driver,i):
    try:
        # headline hyperlink
        element = driver.find_element(By.XPATH, f"/html/body/main/div[2]/div/div/div[2]/div[2]/div[{i+1}]/div[2]/div[2]/div[1]/a")

        # Scroll the element into view
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", element)

        # Click on the headline hyperlink for each result
        driver.execute_script("arguments[0].click();", element)

        # Wait for the search results to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/main/h1/div/span')))

        # Extract the desired data
        data = []

        # web link
        web_link = driver.current_url

        # headline
        headline = driver.find_element(By.XPATH, '/html/body/main/h1/div/span').text

        # product name
        product_name_element = driver.find_element(By.CSS_SELECTOR, ".desktop\:grid-col-fill > div:nth-child(1)")
        product_name = product_name_element.text.replace("Name of Product:", "").strip()

        # hazard
        hazard = driver.find_element(By.XPATH, '/html/body/main/div[2]/article/div/div/div[3]/div/div[2]/div[2]/div[2]/p').text

        # remedy 1
        remedy_1 = driver.find_element(By.XPATH, '/html/body/main/div[2]/article/div/div/div[3]/div/div[2]/div[3]/div[2]/div').text

        # recall date
        recall_date_element = driver.find_element(By.CSS_SELECTOR, "div.view-rows:nth-child(4)")
        recall_date = recall_date_element.text.replace("Recall Date:", "").strip()

        # units
        units = driver.find_element(By.XPATH, '/html/body/main/div[2]/article/div/div/div[3]/div/div[2]/div[5]/div[2]/p').text

        # description
        details_element = driver.find_element(By.CLASS_NAME, "recall-product__details")
        description = details_element.find_element(By.XPATH, ".//div[contains(@class, 'recall-product__field-title') and contains(text(), 'Description')]/following-sibling::div").text

        # remedy 2
        remedy_2 = details_element.find_element(By.XPATH, ".//div[contains(@class, 'recall-product__field-title') and contains(text(), 'Remedy')]/following-sibling::div").text

        # incidents injuries
        incidents_injuries = details_element.find_element(By.XPATH, ".//div[contains(@class, 'recall-product__field-title') and contains(text(), 'Incidents/Injuries')]/following-sibling::div").text

        # sold at
        sold_at_title_element = details_element.find_element(By.XPATH, ".//div[contains(@class, 'recall-product__field-title') and contains(text(), 'Sold At')]")
        sold_at = driver.execute_script("return arguments[0].nextSibling.textContent.trim();", sold_at_title_element)

        # importers/distributors/manufacturers
        parent_element = driver.find_element(By.XPATH, "//div[contains(@class, 'recall-product__details-fields')]//div[contains(text(), 'Importer(s):') or contains(text(), 'Distributor(s):') or contains(text(), 'Manufacturer(s):')]/parent::div")
        importer_distributor_manufacturer = parent_element.text.strip()
        importer_distributor_manufacturer = importer_distributor_manufacturer.replace("Importer(s):","").replace("Distributor(s):", "").replace("Manufacturer(s):", "").strip()

        # manufactured In
        manufactured_in = details_element.find_element(By.XPATH, ".//div[contains(@class, 'recall-product__field-title') and contains(text(), 'Manufactured In')]/following-sibling::div").text

        # recall number
        div_elements = driver.find_elements(By.XPATH, "//div")
        recall_number = None
        for element in div_elements:
            if "Recall number:" in element.text:
                recall_number = element.text.split("Recall number:")[-1].strip()
                recall_number = recall_number[:6]
                break

        # consumer contact
        combined_selector = ".recall-product__cc-info > p:nth-child(1) > span:nth-child(1) > span:nth-child(1) > span:nth-child(1) > span:nth-child(1) > span:nth-child(1) > span:nth-child(1), .recall-product__cc-info > p:nth-child(1)"
        consumer_contact_element = driver.find_element(By.CSS_SELECTOR, combined_selector)
        consumer_contact = consumer_contact_element.text

        data.append(web_link)
        data.append(headline)
        data.append(product_name)
        data.append(hazard)
        data.append(remedy_1)
        data.append(recall_date)
        data.append(units)
        data.append(description)
        data.append(remedy_2)
        data.append(incidents_injuries)
        data.append(sold_at)
        data.append(importer_distributor_manufacturer)
        data.append(manufactured_in)
        data.append(recall_number)
        data.append(consumer_contact)

        write_to_csv(data)

    except Exception as e:
        print("result : ", i+1, " error : ", e)
        with open('CPSCScraper.err', 'a') as err_file:
            err_file.write(f"Error for result #{i+1}: {str(e)}\n")

    finally:
        # Go back to the search results page
        driver.back()
        return

# Function to extract data for a given year
def extract_data_for_year(year):
    date_from = f"01/01/{year}"
    date_to = f"31/12/{year}"

    print("Duration : ",date_from," to ",date_to)
    driver = browser_setup()

    # Open the CPSC recalls page
    driver.get('https://www.cpsc.gov/Recalls')

    results_count = 0

    try:
        # Select the date range
        driver.find_element(By.CSS_SELECTOR, '#edit-field-rc-date-value--2').send_keys(date_from)
        driver.find_element(By.CSS_SELECTOR, '#edit-field-rc-date-value-1--2').send_keys(date_to)

        # Click the Apply button
        driver.find_element(By.CSS_SELECTOR, '#edit-submit-recalls-list-filter-blocks').click()

        while True:
            # Wait for the search results to load
            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'recall-list')))

            # Get the total number of search results
            results_count += len(driver.find_elements(By.CLASS_NAME, 'recall-list'))

            # Scrape data for each result
            for i in range(10):
               scrape(driver,i)
           
            # Find the next button element
            next_button = driver.find_element(By.CSS_SELECTOR, ".pager-primary-btn > a:nth-child(1)")

            # Check if the next button is clickable
            if next_button.is_displayed():

                # Scroll the element into view using JavaScript
                driver.execute_script("arguments[0].scrollIntoView();", next_button)

                # Click on the next button using JavaScript
                driver.execute_script("arguments[0].click();", next_button)

                # Wait for the next page to load
                time.sleep(10)

            else:
                break

            # Write the results count to the log file
            log_message = f"CPSCScraper.exe found {results_count} results for DATE FROM {date_from} and DATE TO {date_to}."
            with open('CPSCScraper.log', 'a') as log_file:
                log_file.write(log_message + '\n')


    finally:
        driver.quit()



# Prompt user for the year
year = input("Enter the year for scraping: ")
extract_data_for_year(year)