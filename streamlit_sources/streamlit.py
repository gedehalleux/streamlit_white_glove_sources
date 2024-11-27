import streamlit as st
import main
from bbcode import Parser


#### change virtual to human page!!! 

# Set page configuration to use the wide layout
st.set_page_config(layout="wide")

# Initialize session state to store data
if "client_data" not in st.session_state:
    st.session_state.client_data = {}

st.title("Get highlighted sources")

# Input for Client ID
client_id = st.text_input("Enter Client ID")

if client_id:
    if client_id not in st.session_state.client_data:
        st.session_state.client_data = {}
        st.session_state.client_data[client_id] = {}

    st.write(f"Managing documents for Client ID: {client_id}")

    # Add Document Section
    st.session_state.doc_link = st.text_input("Enter Document Link", key="doc_input")
    if st.button("Add Document"):
        if st.session_state.doc_link:
            if st.session_state.doc_link not in st.session_state.client_data[client_id]:
                st.session_state.client_data[client_id][st.session_state.doc_link] = {"pages":[], "display_highlights": [], "search_highlights": []}
                st.success(f"Document '{st.session_state.doc_link}' added.")
            else:
                st.warning(f"Document '{st.session_state.doc_link}' already exists.")
        else:
            st.error("Document name cannot be empty.")

    # Display existing documents
    if st.session_state.client_data[client_id]:
        st.subheader("Documents")

        for doc_link, doc_info in st.session_state.client_data[client_id].items():
            expanded = True if st.session_state.doc_link == doc_link else False
        
            def add_page_and_highlight(doc_link, client_id):
                # Access the inputs using their keys
                page_number = st.session_state[f"{doc_link}_page_number"]
                sentence_to_highlight = st.session_state[f"{doc_link}_sentence_to_highlight"]

                if sentence_to_highlight:
                    # Update the client data
                    st.session_state.client_data[client_id][doc_link]["pages"].append(page_number)
                    st.session_state.client_data[client_id][doc_link]["display_highlights"].append(str(sentence_to_highlight))
                    st.session_state.client_data[client_id][doc_link]["search_highlights"].append(str(sentence_to_highlight))
                    
                    # Set success message in session state to trigger UI update
                    st.session_state[f"{doc_link}_success_message"] = f"Page {page_number} added"
                    
                    # Clear the inputs by resetting their session state
                    st.session_state[f"{doc_link}_page_number"] = 1  # Default value
                    st.session_state[f"{doc_link}_sentence_to_highlight"] = ""  # Clear text area

            # Widget definitions
            with st.expander(f"Document link: {doc_link}", expanded=expanded):

                # Input widgets with session state keys
                st.number_input(f"Page Number", min_value=1, key=f"{doc_link}_page_number")
                st.text_area(f"Display highlights", key=f"{doc_link}_sentence_to_highlight")
                
                success_placeholder = st.empty()

                # Check if a success message exists in session state and display it
                if f"{doc_link}_success_message" in st.session_state:
                    success_placeholder.success(st.session_state[f"{doc_link}_success_message"])


                # Button with on_click
                st.button(
                    f"Add Page and highlight info",
                    key=f"{doc_link}_add_page",
                    on_click=add_page_and_highlight,
                    args=(doc_link, client_id)  # Pass required arguments to the function
                )
                
                # Display pages
                if doc_info and len(doc_info["pages"]) > 0:
                    for i, page in enumerate(doc_info["pages"]):  # Use enumerate for better tracking
                        col1, col2 = st.columns([4, 1])  # Create two columns: one for content, one for the button
                        with col1:
                            st.markdown(
                                f"""
                                - **Page**: {page}  
                                **Sentence to highlight**: {doc_info['display_highlights'][i]}  
                                """
                            )
                        with col2:
                            # Use the page content or a unique attribute as part of the key to avoid duplicate keys
                            if st.button(f"Remove Page {page}", key=f"remove_page_{i}_{page}_{doc_link}"):
                                # Remove the page from doc_info
                                doc_info["pages"].pop(i)
                                doc_info["display_highlights"].pop(i)
                                doc_info["search_highlights"].pop(i)
                                st.rerun()

                # if doc_info and len(doc_info["pages"])>0:
                #     for i in range(len(doc_info["pages"])):
                #         st.markdown(
                #             f"""
                #             - **Page**: {doc_info['pages'][i]}  
                #             **Display highlights**: {doc_info['display_highlights'][i]}  
                #             **Search highlights**: {doc_info['search_highlights'][i]}
                #             """
                #         )

    has_pages = any(
        len(v["pages"]) > 0 for v in list(st.session_state.client_data[client_id].values())
    )
    if has_pages:
        if st.button("Get highlighted sources"):
            highlighted_url = main.get_highlight_sources(st.session_state.client_data)
            col1, col2 = st.columns([2, 2])  
            with col1:
                st.title("Sources to copy")
                st.write(highlighted_url)

            with col2:
                st.title("Bubble Source Preview")
                parser = Parser()
                highlighted_url_html = parser.format(highlighted_url)
                st.markdown(str(highlighted_url_html), unsafe_allow_html=True)

                
            
        
# # # Debug: Show the complete structure
# # if st.checkbox("Show Client Data Debug"):
# #     st.write(st.session_state.client_data)
