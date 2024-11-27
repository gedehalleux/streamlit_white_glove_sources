
from src import firestore, utils, parsing, sources

def get_highlight_sources(streamlit_info):
    client_id = list(streamlit_info.keys())[0]
    best_sources, documents_info = {}, {}
    for document_link, highlight_info in list(streamlit_info.values())[0].items(): 
        if highlight_info["pages"]:
            document_info = firestore.query_documents_by_client_and_status_aws_link(client_id, ["indexed"], document_link) 
            document_name = document_info[0]["name"] 
            documents_info[document_name] = document_info[0]
            best_sources[document_name] = highlight_info

    highlighted_url = "https://esg-bff-acc-rue6nzr6qa-ew.a.run.app/pdf/reader/web/viewer.html?file=%2Ferp%2Fget-url%3Furl%3D<FILE_URL>#search=<TEXT_TO_SEARCH>"
    sources_txt = ""
    sources_txt_full = "\n\nSources:"
    source_count=1


    sources.update_signed_urls(client_id, documents_info, [document_name], update_in_firestore=True)
    
    for doc, source_info in best_sources.items():
        displayed_pages = []

        start_page, pages_per_page = documents_info.get(doc, {}).get("parsing_info", {}).get("start_page"), documents_info.get(doc, {}).get("parsing_info", {}).get("pages_per_page")
        if documents_info.get(doc, {}).get("rows_per_block"):
            pages_per_page=documents_info[doc]["rows_per_block"] #for long sheet where multiple rows per block
        all_pages = parsing.get_human_pages(source_info["pages"], start_page, pages_per_page)

        if len(all_pages)==0 :
            all_pages=[None]
        for i, best_page in enumerate(all_pages) :
            if best_page not in displayed_pages :
                displayed_pages.append(best_page)
                answer_useful = True
                doc_type = utils.get_doc_type(doc)
                doc_type_equivalent = utils.get_doc_type(doc, get_doc_type_search_equivalent=True)
                pages=[best_page]#list(set(source_info["pages"]))
                display_highlight = source_info["display_highlights"][i] if "display_highlights" in source_info else None #if error
                search_highlight = source_info["search_highlights"][i] if "search_highlights" in source_info else None # if error
                row_or_page = "page" if doc_type in ["pdf", "docx", "doc"] else "row" if doc_type_equivalent=="csv" else None
                
                try :
                    url = documents_info[doc]["signed_urls"]["original_doc"]#documents_info[doc]["aws_link"]
                    url=url.replace("https:https://", "https://")#should be ok on index side
                    if documents_info[doc]["signed_urls"].get("converted_pdf"): #in this case, embed doc name with original link (see sources.updated_signed_url but basically docx, gdoc, doc or pdf in drive) and embed page number and highligh text with the signed url of the pdf in GCP (note only works for 7 days)
                        url_to_equivalent_pdf = documents_info[doc]["signed_urls"]["converted_pdf"] #gcs.generate_download_signed_url_v4(documents_info[doc]["gcs_path_to_pdfs"][0].split("/", 1)[0], documents_info[doc]["gcs_path_to_pdfs"][0].split("/", 1)[1], minutes=60*24*30)
                    elif doc_type=="pdf" :
                        url_to_equivalent_pdf = url
                    else : 
                        url_to_equivalent_pdf = None
                    embed_type = "bbcode"
                except Exception as e:
                    url = None
                    embed_type=None
                is_search_available=url_to_equivalent_pdf is not None and search_highlight is not None and len(search_highlight.replace(" ",""))>10
                sources_txt += f"\n\t{source_count}. "
                source_count+=1
                sources_txt += utils.link_embedded(client_id, url, doc, config=highlighted_url, embed_type=embed_type if url_to_equivalent_pdf!=url or best_page is None else None) #embed_type) to much link, no real need as the page after will redirect
                if row_or_page and best_page!=None:
                    
                    start_page, pages_per_page = documents_info.get(doc, {}).get("parsing_info", {}).get("start_page"), documents_info.get(doc, {}).get("parsing_info", {}).get("pages_per_page")
                    if documents_info.get(doc, {}).get("rows_per_block"):
                        pages_per_page=documents_info[doc]["rows_per_block"] #for long sheet where multiple rows per block
                    zero_based_page_numbers = parsing.get_0_based_pages(pages, start_page, pages_per_page)
                    pages_links = ', '.join([utils.link_embedded(client_id, url_to_equivalent_pdf, s_str if pages_per_page is None or pages_per_page==1 else f"{s_str}-{s_str+pages_per_page-1}", zero_based_page=s, config=highlighted_url, embed_type=embed_type) for s, s_str in zip(zero_based_page_numbers, pages) if s_str!=best_page])
                    page_txt = f"{row_or_page} {best_page if pages_per_page is None or pages_per_page==1 else f'{best_page}-{best_page+pages_per_page-1}'}"
                    sources_txt += f' at {utils.link_embedded(client_id, url_to_equivalent_pdf, page_txt, config=highlighted_url, embed_type=embed_type if url_to_equivalent_pdf else None, zero_based_page=zero_based_page_numbers[pages.index(best_page)])}'
                    if display_highlight is not None :
                        sources_txt+=f'  : "...{utils.link_embedded(client_id, url_to_equivalent_pdf, display_highlight, config=highlighted_url, embed_type=embed_type if is_search_available else None, text_to_search=search_highlight)}..."'
                    
                    if len(pages)>1 :
                        sources_txt += f" (+ {pages_links} )"
                elif display_highlight is not None :
                    sources_txt += f' : "...{display_highlight}..."'
                if i<len(all_pages)-1 and best_page in all_pages[i+1:] and display_highlight is not None:
                    for j, other_page in enumerate(all_pages[i+1:]):
                        if best_page==other_page  :
                            sources_txt += f', "...{utils.link_embedded(client_id, url_to_equivalent_pdf, source_info["display_highlights"][i+j+1], config=highlighted_url, embed_type=embed_type, text_to_search=source_info["search_highlights"][i+j+1]) if is_search_available else source_info["display_highlights"][i+j+1]}..."'

    if answer_useful :
        sources_txt_full+=sources_txt
    
    return sources_txt_full

