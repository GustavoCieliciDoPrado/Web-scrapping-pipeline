from cProfile import label
from urllib import response
from bs4 import BeautifulSoup
import requests
from pprint import pprint

# Amend the URL to the actual page you want to scrape by changing the postcode
url = 'https://landregistry.data.gov.uk/app/ppd/search?et%5B%5D=lrcommon%3Afreehold&et%5B%5D=lrcommon%3Aleasehold&limit=1000&nb%5B%5D=true&nb%5B%5D=false&postcode=UB6&ptype%5B%5D=lrcommon%3Adetached&ptype%5B%5D=lrcommon%3Asemi-detached&ptype%5B%5D=lrcommon%3Aterraced&ptype%5B%5D=lrcommon%3Aflat-maisonette&ptype%5B%5D=lrcommon%3AotherPropertyType&relative_url_root=%2Fapp%2Fppd&tc%5B%5D=ppd%3AstandardPricePaidTransaction&tc%5B%5D=ppd%3AadditionalPricePaidTransaction'

response = requests.get(url)
soup = BeautifulSoup(response.text, 'lxml')

properties = soup.select('ul.ppd-results > li')
results = []
for prop in properties:
    record = {}

    # The poroperty Adress as the Title
    title = prop.select_one('h3')
    record['property_address'] = title.get_text(strip=True) if title else None

    # Transaction History, including the date of the transaction and the price paid
    transactions = []
    rows = prop.select('.transaction-history tbody tr')

    for row in rows:
        cells = row.find_all('td')
        if len(cells) < 3:
            continue

        transaction = {
            'transaction_date': cells[1].get_text(strip=True),
            'price_paid': int(cells[2].get_text(strip=True).replace('£', '').replace(',', ''))
        }
        transactions.append(transaction)

    record['transactions'] = transactions

    # The detailed address and property characteristics are stored in tables, so we need to extract the data from those tables, this is a more accurate way to get the data as it is structured in the HTML, rather than relying on specific class names which may change
    def extract_table(table_div):
        data = {}
        rows = table_div.select('tr')
        for row in rows:
            cells = row.find_all('td')
            if len(cells) == 2:
                key = cells[0].get_text(strip=True)
                val = cells[1].get_text(strip=True)
                data[key] = val
        return data
    
    # This function is used to extract the building name from the property details table, it looks for the label "building name" in the first column of the table and returns the corresponding value from the second column
    def get_detail_contains(label):
        for td in prop.select('td.property-details-field-title'):
            text = td.get_text(" ", strip=True)
            if label in text:
                return td.find_next_sibling('td').get_text(strip=True)
        return None


    # These tables are nested within the property div, so we need to select them from the current property context, rather than the entire page, this ensures we are getting the correct data for each property
    address_table = prop.select_one('.detailed-address table')
    attr_table = prop.select_one('.property-characteristics table')

    # I am assigning the extracted data to the record dictionary, using the keys that match the labels in the tables, this way we can easily access the data later on when we want to store it in a database or perform analysis on it
    address_data = extract_table(address_table)
    attr_data = extract_table(attr_table)

    # The keys in the record dictionary are chosen to be descriptive and consistent, this makes it easier to understand what each field represents when we look at the data later on
    record['secondary_name'] = address_data.get('secondary name')
    record['building_name'] = get_detail_contains('building name')
    record['street'] = address_data.get('street')
    record['postcode'] = address_data.get('postcode')

    record['property_type'] = attr_data.get('property type')
    record['estate_type'] = attr_data.get('estate type')
    record['new_build'] = attr_data.get('new build?')

    results.append(record)
    print(results) # Print the first record to verify the output
