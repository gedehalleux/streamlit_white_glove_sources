
import urllib.parse
import unicodedata

def get_doc_type(name, get_doc_type_search_equivalent=False, raise_error_if_wrong_doc_type=False):
    
    config = {"DOC_TYPES_ALLOWED" : {
    "csv": "csv",
    "pdf": "pdf",
    "xls": "csv",
    "xlsx": "csv",
    "gdoc": "pdf",
    "gspread": "csv",
    "url": "pdf",
    "docx": "pdf",
    "doc": "pdf",
    "txt": "pdf",
    "jpg": "pdf",  # ocr + vision
    "jpeg": "pdf",  # ocr + vision
    "png": "pdf"  # ocr + vision
}}
    doc_types_allowed = config["DOC_TYPES_ALLOWED"].keys()

    if "https://" in name and name.rsplit(".", 1)[-1] not in doc_types_allowed :
        doc_type = "url"
    else :
        doc_type = name.rsplit(".", 1)[-1].lower()


    if doc_type.split("-")[-1] not in doc_types_allowed :
        assert not raise_error_if_wrong_doc_type, f"Doc type is {doc_type} but we only cover : {doc_types_allowed}"
        return None #raising error if raise_error_if_wrong_doc_type else returning None (even for search equivalent) if not in doc type allowed

    if get_doc_type_search_equivalent:

        return config["DOC_TYPES_ALLOWED"][doc_type.split("-")[-1]]
    else:
        return doc_type
    

def get_source_url(client_id, link, text_to_search=None, page=None, config=None):
    if link is None :
        return None
    
    highlight_url="https://esg-bff-acc-rue6nzr6qa-ew.a.run.app/pdf/reader/web/viewer.html?file=%2Ferp%2Fget-url%3Furl%3D<FILE_URL>#search=<TEXT_TO_SEARCH>"
    if "=" in link :
        highlight_url=highlight_url.replace("<FILE_URL>", urllib.parse.quote(urllib.parse.quote(link, safe=""), safe=""))
    else :
        highlight_url=highlight_url.replace("<FILE_URL>", urllib.parse.quote(link, safe=''))

    if text_to_search is not None :
        cleaned_text_to_search=''.join(char if (
         ord(char) >= 32
        ) and not (unicodedata.category(char).startswith('C') or unicodedata.category(char) == 'Cf') else " " for char in text_to_search)
        if text_to_search != cleaned_text_to_search :
            print("Text has been cleaned")
            #print(f"Text has been cleaned from\n{text_to_search}\nto\n{cleaned_text_to_search}")

        highlight_url=highlight_url.replace("<TEXT_TO_SEARCH>", "%22"+urllib.parse.quote(cleaned_text_to_search)+"%22&phrase=true")
    else :
        highlight_url=highlight_url.split("#search=")[0]+"#page="+str(page+1)#here is 1_based page and page is given as 0 based.

    return highlight_url


    
def link_embedded(client_id, url, text, zero_based_page=None, embed_type="bbcode", config=None, text_to_search=None):
    if embed_type is None :
        return str(text)

    if embed_type=="bbcode":
        if type(text)==int or zero_based_page is not None: #page search
            url=get_source_url(client_id, url, page=zero_based_page if zero_based_page is not None else text, config=config)
            return f"[i][u][url={url}]{text}[/url][/u][/i]"
        elif text_to_search is not None :
            url = get_source_url(client_id, url, text_to_search=text_to_search, config=config)
            return f"[i][url={url}]{text}[/url][/i]"
        else :
            return f"[i][url={url}]{text}[/url][/i]"
    else :
        return str(text) #todo html