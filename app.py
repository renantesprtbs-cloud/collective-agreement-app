import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# ==============================================================================
# YOUR PROVEN LOGIC - MOVED INTO A FUNCTION
# This is the core of your Colab script, now structured to work with Streamlit.
# ==============================================================================
def find_provisions_in_agreements(urls, keywords):
    """
    This function contains the main scraping and searching logic from your Colab script.
    It takes a list of URLs and keywords, and returns the results.
    """
    all_results = []
    
    # Create a progress bar to give the user feedback
    progress_bar = st.progress(0, text="Initializing...")
    total_urls = len(urls)

    for i, url in enumerate(urls):
        # Update progress bar
        progress_text = f"Processing agreement {i+1}/{total_urls}..."
        progress_bar.progress((i) / total_urls, text=progress_text)

        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')

            # --- Your Group Name Extraction Logic ---
            group_name = "N/A"
            group_tag = soup.find(string=re.compile(r'Group:'))
            if group_tag:
                parent_element = group_tag.find_parent()
                if parent_element:
                    match = re.search(r'Group:\s*(.*)', parent_element.get_text(strip=True))
                    if match:
                        extracted_group_name = match.group(1).strip()
                        group_name = re.sub(r'\(.*\)', '', extracted_group_name).strip()

            # --- Your Content Grouping Logic ---
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
            
            # --- Your Keyword Searching Logic ---
            if grouped_sections and keywords:
                for section_elements in grouped_sections:
                    section_text = ' '.join(elem.get_text() for elem in section_elements)
                    
                    # Find which keywords match in the entire section text
                    found_keywords_in_section = [kw for kw in keywords if kw.lower() in section_text.lower()]
                    
                    if found_keywords_in_section:
                        # Reconstruct the section content for display
                        display_content = "\n\n".join(elem.get_text(strip=True) for elem in section_elements if elem.get_text(strip=True))
                        
                        all_results.append({
                            'Group': group_name,
                            'Keyword': ', '.join(sorted(list(set(found_keywords_in_section)))),
                            'Provision': display_content
                        })

        except requests.exceptions.RequestException as e:
            st.error(f"Could not process {url}. Error: {e}")
            continue # Skip to the next URL if one fails

    progress_bar.progress(1.0, text="Completed!")
    return all_results

# ==============================================================================
# STREAMLIT USER INTERFACE CODE
# This is the "menu" part of the app that the user will interact with.
# ==============================================================================

st.set_page_config(layout="wide")
st.title("📄 Collective Agreement Provision Finder")
st.info("Paste your keywords below, one per line or separated by commas. The app will scan all collective agreements and extract the relevant provisions.")

# List of URLs from your script
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
        # Clean up the keyword input
        keywords = [k.strip() for k in keyword_input.replace(',', '\n').split('\n') if k.strip()]
        
        # Call your logic function
        results = find_provisions_in_agreements(list_of_webpage_urls, keywords)

        if results:
            st.success(f"Found {len(results)} relevant provisions!")
            
            # Convert results to a Pandas DataFrame for easy viewing and download
            df = pd.DataFrame(results)
            df = df[['Group', 'Keyword', 'Provision']] # Ensure column order
            
            st.dataframe(df, use_container_width=True, height=600)
            
            # Convert DataFrame to CSV for the download button
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
               label="Download Results as CSV",
               data=csv,
               file_name="agreement_provisions.csv",
               mime="text/csv",
            )
        else:
            st.warning("No provisions found matching the given keywords across all agreements.")
