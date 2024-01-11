import os
import csv
import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.firefox.service import Service
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime
from selenium.webdriver.common.keys import Keys

# Function to format date
def format_date():

    # Get the current date
    today = datetime.now().date()

    # Format the date as YYYYMMDD
    return today.strftime("%Y%m%d")

# Function to write the scraped data to an xlsx file
def write_to_csv(data, year):
    formatted_date = format_date()

    # Check if the file exists or is empty
    file_name = f"{formatted_date}-CPSC scraper - Output - {year}.csv"
    file_exists = os.path.isfile(file_name) and os.stat(file_name).st_size > 0
    
    with open(file_name, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        
        # Write headers if the file is empty
        if not file_exists:
            headers = ['Web Link', 'Headline', 'Name of Product', 'Hazard', 'Remedy', 'Recall Date', 'Units',
                       'Description', 'Remedy', 'Incidents Injuries', 'Sold at', 'Importers/Distributors/Manufacturers/Retailers', 'Manufactured In',
                       'Recall number', 'Consumer Contact']
            
            writer.writerow(headers)
        
        # Write the data
        writer.writerow(data)

    # Convert CSV to XLSX
    df = pd.read_csv(file_name)
    xlsx_file_name = f"{formatted_date}-CPSC scraper - Output - {year}.xlsx"
    df.to_excel(xlsx_file_name, index=False)

# Check and get the latest GeckoDriver version
def get_latest_driver_version():
    url = "https://github.com/mozilla/geckodriver/releases/latest"
    response = requests.get(url)
    if response.status_code == 200:
        version_start_index = response.url.rfind("/") + 1
        return response.url[version_start_index:]
    else:
        raise Exception("Failed to retrieve the latest GeckoDriver version.")

# Function to set up the browser (Used: Mozilla Firefox)
def browser_setup():
    # Set up Firefox WebDriver
    driver_version = get_latest_driver_version()
    driver_path = f"geckodriver_{driver_version}"

    # Configure Firefox options for headless mode
    options = Options()
    options.add_argument("--headless")

    service = Service(driver_path)

    driver = webdriver.Firefox(options=options, service=service)

    # Set window size to avoid "element not interactable" error
    driver.set_window_size(1920, 1080)
     
    return driver

# Function to find total number of pages in the navigation pane
def total_pages(driver):
    
    pager_nav = driver.find_element(By.CLASS_NAME,'pager-nav')
    page_links = pager_nav.find_elements(By.TAG_NAME,'a')
    highest_page_number = 0
    for link in page_links:
        page_number = link.text.strip()
        if page_number.isdigit() and int(page_number) > highest_page_number:
            highest_page_number = int(page_number)

    print("Total number of pages:", highest_page_number)
    return highest_page_number

# Funtion to find the current active page
def current_page(driver):
    try:
        page_number_element = driver.find_element(By.CLASS_NAME,"is-active")
        page_number = page_number_element.text
        print("Currently scraping data from page ",page_number)
        return page_number
    except:
        print("End of results")
        return

# Function to scrape data for every result
def scrape(driver,i,year,page_number,current_count, err_file):

    # Store the handle of the original tab
    original_tab = driver.current_window_handle

    try:
        # headline hyperlink
        link_element = driver.find_element(By.XPATH, f"/html/body/main/div[2]/div/div/div[2]/div[2]/div[{i+1}]/div[2]/div[2]/div[1]/a")

        # Scroll the element into view
        driver.execute_script("arguments[0].scrollIntoView({ behavior: 'smooth', block: 'center' });", link_element)

        # Simulate a keyboard action to open the link in a new tab
        link_element.send_keys(Keys.CONTROL + Keys.RETURN)

        # Switch to the new tab
        driver.switch_to.window(driver.window_handles[-1])

        # Wait for the search results to load
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/main/h1/div/span')))

    except Exception as e:
        with open(err_file, 'a') as err_file:
            err_file.write(f"{str(e)}\n")

    data = []

    web_link = "NA"
    headline = "NA"
    product_name = "NA"
    hazard = "NA"
    remedy_1 = "NA"
    recall_date = "NA"
    units = "NA"
    description = "NA"
    remedy_2 = "NA"
    incidents_injuries = "NA"
    sold_at = "NA"
    importer_distributor_manufacturer_retailer = "NA"
    manufactured_in = "NA"
    recall_number = "NA"
    consumer_contact = "NA"


    print(f"RESULT #{current_count} on PAGE #{page_number}")
    # web link
    web_link = driver.current_url
    data.append(web_link)

    # headline
    try:
        headline_element = driver.find_element(By.CSS_SELECTOR,"h1.margin-0.page-title span")
        headline = headline_element.text
    except:
        headline = "NA"
        with open(err_file, 'a') as err_file:
            err_file.write(f"Error for result #{current_count} on page #{page_number}: Headline not found\n")
    data.append(headline)

    # product name
    try:
        product_name_element = driver.find_element(By.CSS_SELECTOR, ".desktop\:grid-col-fill > div:nth-child(1)")
        if "Name of Product:" in product_name_text:
            product_name = product_name_text.replace("Name of Product:", "").strip()
        else:
            raise Exception    
    except:
        try:
            name_element = driver.find_element(By.XPATH, "//p[contains(strong, 'Name of Product')]/following-sibling::p[1]")
            product_name_text = name_element.text.strip()
            if "Name of Product:" in product_name_text:
                product_name = product_name_text.replace("Name of Product:", "").strip()
            else:
                raise Exception
        except:
            product_name = "NA"
            with open(err_file, 'a') as err_file:
                err_file.write(f"Error for result #{current_count} on page #{page_number}: Product Name not found\n")
    data.append(product_name)

    # hazard
    try:
        hazard_element = driver.find_element(By.XPATH,"//div[contains(@class, 'view-rows')]//*[contains(text(), 'Hazard:')]/following-sibling::div/p")
        hazard = hazard_element.text
    except:
        try:
            hazard_element = driver.find_element(By.CSS_SELECTOR,"div.view-rows:nth-child(2)")
            if "Hazard:" in hazard_element.text:
                hazard = hazard_element.text.replace("Hazard:", "").strip()
            else:
                raise Exception
        except:
            try:
                hazard_element = driver.find_element(By.XPATH,"//p[contains(strong, 'Hazard')]/following-sibling::p[1]")
                if "Hazard:" in hazard_element.text:
                    hazard = hazard_element.text.replace("Hazard:", "").strip()
                else:
                    raise Exception
            except:
                hazard = "NA"
                with open(err_file, 'a') as err_file:
                    err_file.write(f"Error for result #{current_count} on page #{page_number}: Hazard not found\n")
    data.append(hazard)

    # remedy 1
    try:
        remedy_options_div = driver.find_element(By.CLASS_NAME,'recall-product__remedy-options')
        div_elements = remedy_options_div.find_elements(By.TAG_NAME,'div')
        remedy_1 = []
        for div_element in div_elements:
            text = div_element.text.strip()
            remedy_1.append(text)
    except:
        try:
            remedy_element = driver.find_element(By.XPATH,"//div[contains(@class, 'recall-product__field-title') and contains(text(), 'Remedy')]/following-sibling::div")
            if "Remedy:" in remedy_element.text: 
                remedy_1 = remedy_element.text.strip()
            else:
                raise Exception
        except:
            remedy_1 = "NA"
            with open(err_file, 'a') as err_file:
                err_file.write(f"Error for result #{current_count} on page #{page_number}: Remedy not found\n")
    data.append(remedy_1)

    # recall date
    try:
        recall_date_element = driver.find_element(By.CSS_SELECTOR, "div.view-rows:nth-child(4)")
        if "Recall Date" in recall_date_element.text:
            recall_date = recall_date_element.text.replace("Recall Date:", "").strip()
        else:
            raise Exception
    except:
        recall_date = "NA"
        with open(err_file, 'a') as err_file:
            err_file.write(f"Error for result #{current_count} on page #{page_number}: Recall Date not found\n")
    data.append(recall_date)

    # units
    try:
        # Find the element containing the units
        units_element = driver.find_element(By.XPATH,"//div[contains(@class, 'view-rows')]//*[contains(text(), 'Units:')]/following-sibling::div")            
        units = units_element.text        
    except:
        try:
            units_element = driver.find_element(By.XPATH,"//p[contains(strong, 'Units')]/following-sibling::p[1]")
            units = units_element.text.replace("Units:", "").strip()
            print("Units -----> ", units)
        except:
            units = "NA"
            with open(err_file, 'a') as err_file:
                err_file.write(f"Error for result #{current_count} on page #{page_number}: Units not found\n")
    data.append(units)

    # description
    try:
        details_element = driver.find_element(By.CLASS_NAME, "recall-product__details")
        description = details_element.find_element(By.XPATH, ".//div[contains(@class, 'recall-product__field-title') and contains(text(), 'Description')]/following-sibling::div").text
    except:
        try:
            description_element = driver.find_element(By.XPATH,"//p[contains(strong, 'Description')]/following-sibling::p[1]")
            description = description_element.text.replace("Description:", "").strip()
            print("DESCriptionnnn ----> ",description)
        except:
            description = "NA"
            with open(err_file, 'a') as err_file:
                err_file.write(f"Error for result #{current_count} on page #{page_number}: Description not found\n")
    data.append(description)

    # remedy 2
    try:
        remedy_2 = details_element.find_element(By.XPATH, ".//div[contains(@class, 'recall-product__field-title') and contains(text(), 'Remedy')]/following-sibling::div").text
    except:
        try:
            remedy_element = driver.find_element(By.XPATH,"//p[contains(strong, 'Remedy')]/following-sibling::p[1]")
            remedy_2 = remedy_element.text.replace("Remedy:", "").strip()
            print("Remedyyy 2 ----> ",remedy_2)
        except:
            remedy_2 = "NA"
            with open(err_file, 'a') as err_file:
                err_file.write(f"Error for result #{current_count} on page #{page_number}: Remedy not found\n")
    data.append(remedy_2)

    # incidents injuries
    try:
        incidents_injuries = details_element.find_element(By.XPATH, ".//div[contains(@class, 'recall-product__field-title') and contains(text(), 'Incidents/Injuries')]/following-sibling::div").text
    except:
        try:
            incidents_injuries_element = driver.find_element(By.XPATH,"//p[contains(strong, 'Incidents/Injuries')]/following-sibling::p[1]")
            incidents_injuries = incidents_injuries_element.text.replace("Incidents/Injuries:", "").strip()
            print("INCIIII ----> ",incidents_injuries)
        except:
            incidents_injuries = "NA"
            with open(err_file, 'a') as err_file:
                err_file.write(f"Error for result #{current_count} on page #{page_number}: Incidents/Injuries not found\n")
    data.append(incidents_injuries)

    # sold at
    try:
        sold_at_title_element = details_element.find_element(By.XPATH, ".//div[contains(@class, 'recall-product__field-title') and (  contains(text(), 'Sold At') or contains(text(), 'Sold Exclusively At') or contains(text(), 'Sold Online At') or contains(text(), 'Sold Exclusively Online') ) ]")
        sold_at = driver.execute_script("return arguments[0].nextSibling.textContent.trim();", sold_at_title_element)
    except:
        try:
            sold_at_element = driver.find_element(By.XPATH,"//p[contains(strong, 'Sold at')]/following-sibling::p[1]")
            sold_at = sold_at_element.text.replace("Solt at:","").strip()
            print("SOLDDD AT ----> ",sold_at)
        except:
            sold_at = "NA"
            with open(err_file, 'a') as err_file:
                err_file.write(f"Error for result #{current_count} on page #{page_number}: Sold at info not found\n")
    data.append(sold_at)

    # importers/distributors/manufacturers
    try:                                                
        parent_element = driver.find_element(By.XPATH, "//div[contains(@class, 'recall-product__details-fields')]//div[ contains(text(), 'Importer(s):') or contains(text(), 'Distributor(s):') or contains(text(), 'Manufacturer(s):') or contains(text(), 'Retailer:') ]/parent::div")
        importer_distributor_manufacturer_retailer = parent_element.text.strip()
        importer_distributor_manufacturer_retailer = importer_distributor_manufacturer_retailer.replace("Importer(s):","").replace("Distributor(s):", "").replace("Manufacturer(s):", "").replace("Retailer:", "").strip()
    except:
        try:
            parent_element = driver.find_element(By.XPATH,"//div[contains(@class, 'recall-product__field-title') and ( contains(text(), 'Importer') or contains(text(), 'Distributor') or contains(text(), 'Manufacturer') or contains(text(), 'Retailer') )]/following-sibling::div/p")
            importer_distributor_manufacturer_retailer = parent_element.text.replace("Importer(s):","").replace("Distributor(s):", "").replace("Manufacturer(s):", "").replace("Retailer:", "").strip()
            print("Second try importerrr----> ",importer_distributor_manufacturer_retailer)
        except:
            try:
                importer_distributor_manufacturer_retailer_element = driver.find_element(By.XPATH,"//p[contains(strong, 'Importer') or contains(strong, 'Distributor') or contains(strong, 'Manufacturer') or contains(strong, 'Retailer')]/following-sibling::p[1]")
                importer_distributor_manufacturer_retailer = importer_distributor_manufacturer_retailer_element.text.replace("Importer:","").replace("Distributor:", "").replace("Manufacturer:", "").replace("Retailer:", "").strip()
                print("Third try importerrr----> ",importer_distributor_manufacturer_retailer)

            except:
                importer_distributor_manufacturer_retailer = "NA"
                with open(err_file, 'a') as err_file:
                    err_file.write(f"Error for result #{current_count} on page #{page_number}: Importers/Distributors/Manufacturers/Retailers not found\n")
    data.append(importer_distributor_manufacturer_retailer)

    # manufactured In
    try:
        manufactured_in = details_element.find_element(By.XPATH, ".//div[contains(@class, 'recall-product__field-title') and contains(text(), 'Manufactured In')]/following-sibling::div").text
    except:
        try:
            manufactured_in_element = driver.find_element(By.XPATH,"//p[contains(strong, 'Manufactured in')]/following-sibling::p[1]")
            manufactured_in = manufactured_in_element.text.replace("Manufactured in:","").strip()
            print("Manuuuu in ----> ",manufactured_in)
        except:
            manufactured_in = "NA"
            with open(err_file, 'a') as err_file:
                err_file.write(f"Error for result #{current_count} on page #{page_number}: Manufactured in info not found\n")
    data.append(manufactured_in)


    # recall number
    try:
        div_elements = driver.find_elements(By.XPATH, "//div")
        for element in div_elements:
            if "Recall number:" in element.text:
                recall_number = element.text.split("Recall number:")[-1].strip()
                recall_number = recall_number[:6]
                break            
    except:
        recall_number = "NA"
        with open(err_file, 'a') as err_file:
            err_file.write(f"Error for result #{current_count} on page #{page_number}: Recall number not found\n")
    data.append(recall_number)

    # consumer contact
    try:                                                                  
        consumer_contact_element = driver.find_element(By.CSS_SELECTOR, ".recall-product__cc-info-container p")
        consumer_contact = consumer_contact_element.text
    except:
        try:
            consumer_contact_element = driver.find_element(By.CSS_SELECTOR,".recall-product__cc-info")
            consumer_contact = consumer_contact_element.text.replace("Consumer contact:","").strip()
            print("second tryyy COnsumer contact ----> ",consumer_contact)
        except:
            try:
                consumer_contact_element = driver.find_element(By.XPATH,"//p[contains(strong, 'Consumer Contact')]/following-sibling::p[1]")
                consumer_contact = consumer_contact_element.text.replace("Consumer contact:","").strip()
                print("third tryyy COnsumer contact ----> ",consumer_contact)

            except:
                consumer_contact = "NA"
                with open(err_file, 'a') as err_file:
                    err_file.write(f"Error for result #{current_count} on page #{page_number}: Consumer contact not found\n")
    data.append(consumer_contact)

    print(f"Data for result #{current_count} on page #{page_number}: \n")
    print(data)

    write_to_csv(data,year)


    
    # Close the new tab
    driver.close()

    # Switch back to the original tab
    driver.switch_to.window(original_tab)
    return

# Function to extract data for a given year
def extract_data_for_year(year):

    date_from = f"{year}-01-01"
    date_to = f"{year}-12-31"

    print("Duration : ",date_from," to ",date_to)
    driver = browser_setup()

    # Open the CPSC recalls page
    driver.get('https://www.cpsc.gov/Recalls')

    results_count = 0
    current_count = 0
    totalPages = 0
    pageNumber = 0

    try:
        # Select the date range
        driver.find_element(By.CSS_SELECTOR, '#edit-field-rc-date-value--2').send_keys(date_from)
        driver.find_element(By.CSS_SELECTOR, '#edit-field-rc-date-value-1--2').send_keys(date_to)

        # Click the Apply button
        driver.find_element(By.CSS_SELECTOR, '#edit-submit-recalls-list-filter-blocks').click()

        # totalPages = total_pages(driver)

        while True:
            # Wait for the search results to load
            time.sleep(10)

            # Get the total number of search results
            results_count += len(driver.find_elements(By.CLASS_NAME, 'recall-list'))

            pageNumber = current_page(driver)

            formatted_date = format_date()

            # Check if the file exists or is empty
            err_file = f"{formatted_date}-CPSC scraper - Error - {year}.err"

            # Scrape data for each result
            for i in range(10):
               current_count+=1
               scrape(driver,i,year,pageNumber,current_count,err_file)
           
            try:
                # Find the next button element
                next_button = driver.find_element(By.LINK_TEXT, "Next")

                # Check if the next button is clickable
                if next_button.is_displayed():

                    print("Clicking next button")
                    # Scroll the element into view
                    driver.execute_script("arguments[0].scrollIntoView();", next_button)

                    # Click on the next button
                    driver.execute_script("arguments[0].click();", next_button)

                    # Wait for the next page to load
                    time.sleep(10)

            except:
                print("End of results")
                break


    except Exception as e:

        print("End of results for the given year")
        print(f"ERROR MESSAGE :{str(e)}\n")

    finally:
        formatted_date = format_date()

        # Check if the file exists or is empty
        log_file_name = f"{formatted_date}-CPSC scraper - Log - {year}.log"

        # Write the results count to the log file
        log_message = f"CPSCScraper.exe found {results_count} results for DATE FROM {date_from} and DATE TO {date_to}."
        with open(log_file_name, 'a') as log_file:
            log_file.write(log_message + '\n')
        driver.quit()



# for year in range(1975,2018):
#     extract_data_for_year(year)

# Prompt user for the year
year = input("Enter the year for scraping: ")
extract_data_for_year(year)