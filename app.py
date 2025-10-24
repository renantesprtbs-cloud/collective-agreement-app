import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import re

# ==============================================================================
# HELPER AND CORE LOGIC FUNCTIONS (Final Corrected and Simplified Version)
# ==============================================================================
def convert_results_to_txt(results):
    txt_output = []
    for record in results:
        provision_text = record.get('Paragraph', '').replace('\n', '[NL]')
        record_str = (
            "--- START RECORD ---\n"
            f"Collective Agreement: {record.get('Collective Agreement', 'N/A')}\n"
            f"Expiry Date: {record.get('Expiry Date', 'N/A')}\n"
            f"Keyword: {record.get('Keyword', 'N/A')}\n"
            f"Match Location: {record.get('Match Location', 'N/A')}\n"
            f"Source URL: {record.get('Source URL', 'N/A')}\n"
            f"Paragraph: {provision_text}\n"
            "--- END RECORD ---"
        )
        txt_output.append(record_str)
    return "\n\n".join(txt_output)

def find_provisions_in_agreements(urls, keywords):
    all_results = []
    urls_with_matches = set()
    all_group_names = set()

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
                match_group = re.search(r'(.*?) - Canada\.ca', title_tag.get_text(strip=True))
                if match_group: 
                    group_name = match_group.group(1).strip()
                    all_group_names.add(group_name)
            
            expiry_date = "N/A"
            expiry_date_tag = soup.find(string=re.compile(r'Expiry date:'))
            if expiry_date_tag:
                match_expiry = re.search(r'Expiry date:\s*(.*)', expiry_date_tag.find_parent().get_text(strip=True))
                if match_expiry: expiry_date = match_expiry.group(1).strip()

            grouped_sections = []
            main_content_section = soup.find('div', class_='mwsgeneric-base-html')
            if main_content_section:
                elements = main_content_section.find_all(True, recursive=False)
                current_section_elements = []
                for element in elements:
                    if element.name in ['h2', 'h3']:
                        if current_section_elements: grouped_sections.append(current_section_elements)
                        current_section_elements = [element]
                    else:
                        current_section_elements.append(element)
                if current_section_elements: grouped_sections.append(current_section_elements)
            
            match_found_in_url = False
            if grouped_sections and keywords:
                for section_elements in grouped_sections:
                    
                    # *** NEW, DEFINITIVE AND SIMPLIFIED LOGIC ***
                    heading_elements = [el for el in section_elements if el.name in ['h2', 'h3', 'h4', 'h5', 'h6']]
                    heading_text = ' '.join(h.get_text(strip=True) for h in heading_elements)
                    
                    found_keywords = []
                    matching_content = []
                    match_location = "Body" # Default

                    # Check heading for matches
                    found_in_heading = [kw for kw in keywords if kw.lower() in heading_text.lower()]
                    if found_in_heading:
                        match_location = "Heading"
                        found_keywords.extend(found_in_heading)
                        # If match is in heading, we want the whole section
                        matching_content.extend(section_elements)
                    else:
                        # If not in heading, check body elements individually
                        body_elements = [el for el in section_elements if el.name not in ['h2', 'h3', 'h4', 'h5', 'h6']]
                        temp_matching_body = []
                        for elem in body_elements:
                            elem_text = elem.get_text(strip=True)
                            if elem_text:
                                found_in_elem = [kw for kw in keywords if kw.lower() in elem_text.lower()]
                                if found_in_elem:
                                    temp_matching_body.append(elem)
                                    found_keywords.extend(found_in_elem)
                        # Add heading for context if body elements matched
                        if temp_matching_body:
                            matching_content.extend(heading_elements)
                            matching_content.extend(temp_matching_body)

                    if matching_content:
                        def format_display_content(elements_to_format):
                            content_parts = []
                            def get_alpha_char(n): return chr(ord('a') + n - 1)

                            for elem in elements_to_format:
                                text = elem.get_text(strip=True)
                                if elem.name in ['p', 'h2', 'h3', 'h4', 'h5', 'h6']:
                                    if text: content_parts.append(text)
                                elif elem.name == 'ul':
                                    for li in elem.find_all('li', recursive=False):
                                        li_text = li.get_text(strip=True)
                                        if li_text: content_parts.append(f"    • {li_text}")
                                elif elem.name == 'ol':
                                    list_items = elem.find_all('li', recursive=False)
                                    if list_items:
                                        start_index = int(elem.get('start', 1))
                                        is_lower_alpha = 'lst-lwr-alph' in elem.get('class', [])
                                        for idx, li in enumerate(list_items):
                                            li_text = li.get_text(strip=True)
                                            if li_text:
                                                current_index = start_index + idx
                                                prefix = f"{get_alpha_char(current_index)}." if is_lower_alpha else f"{current_index}."
                                                content_parts.append(f"    {prefix} {li_text}")
                            return "\n\n".join(content_parts)

                        display_content = format_display_content(matching_content)
                        if display_content:
                            all_results.append({
                                'Collective Agreement': group_name, 'Expiry Date': expiry_date,
                                'Keyword': ', '.join(sorted(list(set(found_keywords)))),
                                'Match Location': match_location, 'Paragraph': display_content, 
                                'Source URL': url
                            })
                            match_found_in_url = True
            
            if match_found_in_url:
                urls_with_matches.add(group_name)

        except requests.exceptions.RequestException as e:
            st.error(f"Could not process {url}. Error: {e}")
            continue

    progress_bar.progress(1.0, text="Completed!")
    
    urls_without_matches = sorted(list(all_group_names - urls_with_matches))
    summary_stats = {"total_searched": len(urls), "found_in": len(urls_with_matches),
                     "not_found_in_count": len(urls_without_matches), "not_found_in_list": urls_without_matches}
    return all_results, summary_stats

# ==============================================================================
# STREAMLIT USER INTERFACE CODE (Unchanged)
# ==============================================================================

st.set_page_config(layout="wide")
st.title("📄 Collective Agreement Provision Finder")
st.info("Paste your keywords below, one per line or separated by commas. The app will scan all collective agreements and extract the relevant provisions.")

if 'results' not in st.session_state:
    st.session_state['results'] = None
    st.session_state['summary'] = None

list_of_webpage_urls = [
    'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ai.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ao.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sp.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/nr.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/fb.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/cp.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ct.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/cx.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ec.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/eb.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/el.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/fs.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sh.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/it.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/po.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/lp.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sv.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/pa.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ro.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/rm.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/re.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/src.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/sre.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/srw.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/so.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/tc.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/tr.html', 'https://www.canada.ca/en/treasury-board-secretariat/topics/pay/collective-agreements/ut.html',
]

keyword_input = st.text_area("Enter Keywords", height=150, placeholder="e.g., severance pay, parental leave, remote work policy")

if st.button("Find Provisions"):
    if not keyword_input.strip():
        st.warning("Please enter at least one keyword.")
        st.session_state['results'] = None
        st.session_state['summary'] = None
    else:
        keywords = [k.strip() for k in keyword_input.replace(',', '\n').split('\n') if k.strip()]
        results, summary = find_provisions_in_agreements(list_of_webpage_urls, keywords)
        st.session_state['results'] = results if results else []
        st.session_state['summary'] = summary

if st.session_state['results'] is not None:
    if st.session_state['summary']:
        summary = st.session_state['summary']
        st.subheader("Search Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Agreements Searched", summary['total_searched'])
        col2.metric("Agreements with Matches", summary['found_in'])
        col3.metric("Agreements without Matches", summary['not_found_in_count'])
        if summary['not_found_in_list']:
            with st.expander("Show Agreements Without Matches"):
                st.write(summary['not_found_in_list'])

    if st.session_state['results']:
        results = st.session_state['results']
        st.success(f"Found {len(results)} relevant provisions!")
        df = pd.DataFrame(results)
        df = df[['Collective Agreement', 'Expiry Date', 'Match Location', 'Keyword', 'Source URL', 'Paragraph']]
        st.dataframe(df, use_container_width=True, height=600,
            column_config={"Source URL": st.column_config.LinkColumn("Source Link", display_text="🔗 Link")}
        )
        csv_data = df.to_csv(index=False).encode('utf-8')
        txt_data = convert_results_to_txt(results)
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(label="Download Results as CSV", data=csv_data, file_name="agreement_provisions.csv", mime="text/csv", key="csv_download")
        with col2:
            st.download_button(label="Download as TXT (for AI import)", data=txt_data, file_name="agreement_provisions.txt", mime="text/plain", key="txt_download")
    else:
        st.warning("No provisions found matching the given keywords across all agreements.")
