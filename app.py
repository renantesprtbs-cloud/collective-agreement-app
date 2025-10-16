import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# ==============================================================================
# HELPER AND CORE LOGIC FUNCTIONS (Unchanged)
# ==============================================================================
def convert_results_to_txt(results):
    txt_output = []
    for record in results:
        provision_text = record.get('Provision', '').replace('\n', '[NL]')
        record_str = (
            "--- START RECORD ---\n"
            f"Group: {record.get('Group', 'N/A')}\n"
            f"Expiry Date: {record.get('Expiry Date', 'N/A')}\n"
            f"Keyword: {record.get('Keyword', 'N/A')}\n"
            f"Provision: {provision_text}\n"
            "--- END RECORD ---"
        )
        txt_output.append(record_str)
    return "\n\n".join(txt_output)

def find_provisions_in_agreements(urls, keywords):
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
# STREAMLIT USER INTERFACE CODE (Updated with State Management)
# ==============================================================================

st.set_page_config(layout="wide")
st.title("📄 Collective Agreement Provision Finder")
st.info("Paste your keywords below, one per line or separated by commas. The app will scan all collective agreements and extract the relevant provisions.")

# --- 1. Initialize session_state ---
# This ensures that 'results' exists in the session state from the very first run.
if 'results' not in st.session_state:
    st.session_state['results'] = None

list_of_webpage_urls = [
    # ... (Your list of URLs remains the same) ...
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ai.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ao.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sp.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/nr.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/fb.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/cp.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ct.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/cx.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ec.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/eb.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/el.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/fs.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sh.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/it.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/po.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/lp.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sv.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/pa.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ro.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/rm.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/re.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/src.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sre.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/srw.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/so.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/tc.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/tr.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ut.html',
]

keyword_input = st.text_area(
    "Enter Keywords",
    height=150,
    placeholder="e.g., severance pay, parental leave, remote work policy"
)

if st.button("Find Provisions"):
    if not keyword_input.strip():
        st.warning("Please enter at least one keyword.")
        st.session_state['results'] = None # Clear previous results if input is empty
    else:
        keywords = [k.strip() for k in keyword_input.replace(',', '\n').split('\n') if k.strip()]
        
        # Run the search logic and store the output in session state
        results = find_provisions_in_agreements(list_of_webpage_urls, keywords)
        # --- 2. Store results in session_state ---
        st.session_state['results'] = results if results else [] # Store empty list if no results found

# --- 3. Display results if they exist in session_state ---
# This block is now OUTSIDE the button's 'if' statement. It will run every time,
# displaying the results as long as they are stored in the session.
if st.session_state['results'] is not None:
    if st.session_state['results']:
        results = st.session_state['results']
        st.success(f"Found {len(results)} relevant provisions!")
        
        df = pd.DataFrame(results)
        df = df[['Group', 'Expiry Date', 'Keyword', 'Provision']]
        
        st.dataframe(df, use_container_width=True, height=600)
        
        # Prepare data for download buttons
        csv_data = df.to_csv(index=False).encode('utf-8')
        txt_data = convert_results_to_txt(results)

        # Display download buttons side-by-side
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
               label="Download Results as CSV",
               data=csv_data,
               file_name="agreement_provisions.csv",
               mime="text/csv",
               key="csv_download" # Added a key for stability
            )
        with col2:
            st.download_button(
               label="Download as TXT (for AI import)",
               data=txt_data,
               file_name="agreement_provisions.txt",
               mime="text/plain",
               key="txt_download" # Added a key for stability
            )
    else:
        # This handles the case where a search was run but found nothing
        st.warning("No provisions found matching the given keywords across all agreements.")
