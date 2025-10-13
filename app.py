import requests
from bs4 import BeautifulSoup
import re
import json
import csv
import os
from urllib.parse import urlparse

list_of_webpage_urls = [
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ai.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ao.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sp.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/nr.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/fb.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/cp.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ct.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/cx.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ec.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/eb.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/el.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/fs.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sh.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/it.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/po.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/lp.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sv.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/pa.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ro.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/rm.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/re.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/src.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sre.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/srw.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/so.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/tc.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/tr.html',
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ut.html',
]

json_file_path = 'task.json'
output_csv_file_path = 'results.csv'
all_results = [] # Initialize list to store results from all URLs

# Load keywords once outside the loop
keywords = []
try:
    with open(json_file_path, 'r') as f:
        data = json.load(f)
        keywords = data.get('search_keywords', [])
    print(f"Successfully loaded {len(keywords)} keywords.")
except Exception as e:
    print(f"Error loading keywords: {e}")

for url in list_of_webpage_urls:
    print(f"Processing URL: {url}")
    html_content = None
    soup = None
    group_name = "N/A" # Initialize group name
    grouped_sections = [] # List to hold BeautifulSoup elements, not text chunks

    try:
        response = requests.get(url)
        response.raise_for_status()
        html_content = response.text
        print("Successfully fetched webpage content.")

        soup = BeautifulSoup(html_content, 'html.parser')
        print("Successfully parsed HTML content.")

        # --- Extract Group Name ---
        group_tag = soup.find(string=re.compile(r'Group:'))
        if group_tag:
            parent_element = group_tag.find_parent()
            if parent_element:
                parent_text = parent_element.get_text(strip=True)
                match = re.search(r'Group:\s*(.*)', parent_text)
                if match:
                    extracted_group_name = match.group(1).strip()
                    group_name = re.sub(r'\(.*\)', '', extracted_group_name).strip()
                    print(f"Extracted Group Name: {group_name}")
                else:
                     print("Could not extract group name from the element text.")
            else:
                print("Could not find parent element for 'Group:' text.")
        else:
            print("Could not find 'Group:' text on the page.")
        # --- End Extract Group Name ---

        main_content_section = soup.find('div', class_='mwsgeneric-base-html')

        if main_content_section:
            elements = main_content_section.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6'])

            current_section_elements = []
            for element in elements:
                if element.name in ['h2', 'h3']:
                    if current_section_elements:
                        grouped_sections.append(current_section_elements)
                    current_section_elements = [element]
                elif element.name in ['h4', 'h5', 'h6', 'p']:
                    current_section_elements.append(element)

            if current_section_elements:
                grouped_sections.append(current_section_elements)

            print(f"Content grouped into {len(grouped_sections)} sections (BeautifulSoup elements).")

        else:
            print("Could not find the 'mwsgeneric-base-html' section for the main content.")
            grouped_sections = []


    except requests.exceptions.RequestException as e:
        print(f"Error fetching webpage {url}: {e}")
        html_content = None
        soup = None
        group_name = "Error Fetching"
        grouped_sections = []


    if grouped_sections and keywords:
        current_url_matches_count = 0 # Counter for matches in the current URL
        for section_elements in grouped_sections:
            section_heading = None
            section_paragraphs = []
            section_other_elements = []

            # Separate heading, paragraphs, and other elements
            for elem in section_elements:
                if elem.name in ['h2', 'h3', 'h4', 'h5', 'h6'] and section_heading is None:
                    section_heading = elem
                elif elem.name == 'p':
                    section_paragraphs.append(elem)
                else:
                    section_other_elements.append(elem) # Include other non-paragraph elements like lists if needed

            matching_paragraphs_text = []
            found_keywords_in_section = []

            # Search for keywords only in paragraphs within the section
            for paragraph in section_paragraphs:
                paragraph_text = paragraph.get_text(strip=True)
                if paragraph_text:
                    found_keywords_in_paragraph = [keyword for keyword in keywords if keyword.lower() in paragraph_text.lower()]
                    if found_keywords_in_paragraph:
                        matching_paragraphs_text.append(paragraph_text)
                        found_keywords_in_section.extend(found_keywords_in_paragraph)

            # Add results if any paragraph in the section matched
            if matching_paragraphs_text:
                # Construct the output paragraph: Heading + Matching Paragraphs
                output_paragraph_content = []
                if section_heading:
                    output_paragraph_content.append(section_heading.get_text(strip=True))

                # Add other non-paragraph elements before matching paragraphs if they exist
                for other_elem in section_other_elements:
                     other_text = other_elem.get_text(strip=True)
                     if other_text:
                         output_paragraph_content.append(other_text)


                output_paragraph_content.extend(matching_paragraphs_text) # Add the text of matching paragraphs


                all_results.append({
                    'Group': group_name,
                    'Keyword': ', '.join(sorted(list(set(found_keywords_in_section)))), # Unique and sorted keywords
                    'Paragraph': "\n\n".join(output_paragraph_content)
                })
                current_url_matches_count += 1


        print(f"Found {current_url_matches_count} matching sections for Group: {group_name}.")
    elif grouped_sections and not keywords:
         print("Keywords not loaded. Skipping search for this URL.")
    else:
        print("No searchable content available for processing for this URL.")

# --- Write all aggregated results to a CSV file after the loop ---
if all_results:
    with open(output_csv_file_path, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Group', 'Keyword', 'Paragraph']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_results)
    print(f"\nSuccessfully wrote aggregated results to '{output_csv_file_path}'.")
    print(f"Total matching chunks found across all URLs: {len(all_results)}")
    print("You can find the file in the file pane on the left.")
elif keywords:
    print("\nNo matching chunks were found across all URLs.")
else:
    print("\nKeywords not loaded, no search was performed.")
