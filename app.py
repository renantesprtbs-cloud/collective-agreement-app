import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# ==============================================================================
# NEW HELPER FUNCTION TO CREATE THE AI-FRIENDLY TXT FILE
# ==============================================================================
def convert_results_to_txt(results):
    """
    Converts the list of result dictionaries into a single, formatted
    plain text string suitable for an AI model.
    """
    txt_output = []
    for record in results:
        # Replace newlines in the provision text with [NL]
        provision_text = record.get('Provision', '').replace('\n', '[NL]')
        
        # Build the string for each record
        record_str = (
            "--- START RECORD ---\n"
            f"Group: {record.get('Group', 'N/A')}\n"
            f"Expiry Date: {record.get('Expiry Date', 'N/A')}\n"
            f"Keyword: {record.get('Keyword', 'N/A')}\n"
            f"Provision: {provision_text}\n"
            "--- END RECORD ---"
        )
        txt_output.append(record_str)
    
    # Join all records with two newlines for readability
    return "\n\n".join(txt_output)

# ==============================================================================
# CORE LOGIC FUNCTION
# ==============================================================================
def find_provisions_in_agreements(urls, keywords):
    """
    Scrapes a list of URLs for collective agreements, extracts key information,
    and searches for provisions matching a list of keywords.
    """
    all_results = []
    
    progress_bar = st.progress(0, text="Initializing...")
    total_urls = len(urls)

    for i, url in enumerate(urls):
        progress_text = f"Processing agreement {i+1}/{total_urls}..."
        progress_bar.progress((i) / total_urls, text=progress_text)

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            group_name = "N/A"
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                match_group = re.search(r'(.*?) - Canada\.ca', title_text)
                if match_group:
                    group_name = match_group.group(1).strip()
            
            expiry_date = "N/A"
            expiry_date_tag = soup.find(string=re.compile(r'Expiry date:'))
            if expiry_date_tag:
                expiry_element = expiry_date_tag.find_parent()
                if expiry_element:
                    match_expiry = re.search(r'Expiry date:\s*(.*)', expiry_element.get_text(strip=True))
                    if match_expiry:
                        expiry_date = match_expiry.group(1).strip()

            grouped_sections = []
            main_content_section = soup.find('div', class_='mwsgeneric-base-html')
            if main_content_section:
                elements = main_content_section.find_all(['p', 'h2', 'h3', 'h4', 'h5', 'h6'])
                current_section_elements = []
                for element in elements:
                    if element.name in ['h2', 'h3']:
                        if current_section_elements: grouped_sections.append(current_section_elements)
                        current_section_elements = [element]
                    else:
                        current_section_elements.append(element)
                if current_section_elements: grouped_sections.append(current_section_elements)
            
            if grouped_sections and keywords:
                for section_elements in grouped_sections:
                    section_text = ' '.join(elem.get_text() for elem in section_elements)
                    
                    found_keywords_in_section = [kw for kw in keywords if kw.lower() in section_text.lower()]
                    
                    if found_keywords_in_section:
                        display_content = "\n\n".join(elem.get_text(strip=True) for elem in section_elements if elem.get_text(strip=True))
                        
                        all_results.append({
                            'Group': group_name,
                            'Expiry Date': expiry_date,
                            'Keyword': ', '.join(sorted(list(set(found_keywords_in_section)))),
                            'Provision': display_content
                        })

        except requests.exceptions.RequestException as e:
            st.error(f"Could not process {url}. Error: {e}")
            continue

    progress_bar.progress(1.0, text="Completed!")
    return all_results

# ==============================================================================
# STREAMLIT USER INTERFACE CODE
# ==============================================================================

st.set_page_config(layout="wide")
st.title("📄 Collective Agreement Provision Finder")
st.info("Paste your keywords below, one per line or separated by commas. The app will scan all collective agreements and extract the relevant provisions.")

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

keyword_input = st.text_area(
    "Enter Keywords",
    height=150,
    placeholder="e.g., severance pay, parental leave, remote work policy"
)

if st.button("Find Provisions"):
    if not keyword_input.strip():
        st.warning("Please enter at least one keyword.")
    else:
        keywords = [k.strip() for k in keyword_input.replace(',', '\n').split('\n') if k.strip()]
        
        results = find_provisions_in_agreements(list_of_webpage_urls, keywords)

        if results:
            st.success(f"Found {len(results)} relevant provisions!")
            
            df = pd.DataFrame(results)
            df = df[['Group', 'Expiry Date', 'Keyword', 'Provision']] 
            
            st.dataframe(df, use_container_width=True, height=600)
            
            # --- PREPARE DATA FOR DOWNLOAD BUTTONS ---
            # Prepare CSV data
            csv_data = df.to_csv(index=False).encode('utf-8')
            # Prepare TXT data using the new helper function
            txt_data = convert_results_to_txt(results)

            # --- DISPLAY DOWNLOAD BUTTONS SIDE-BY-SIDE ---
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                   label="Download Results as CSV",
                   data=csv_data,
                   file_name="agreement_provisions.csv",
                   mime="text/csv",
                )
            with col2:
                st.download_button(
                   label="Download as TXT (for AI import)",
                   data=txt_data,
                   file_name="agreement_provisions.txt",
                   mime="text/plain",
                )
        else:
            st.warning("No provisions found matching the given keywords across all agreements.")
