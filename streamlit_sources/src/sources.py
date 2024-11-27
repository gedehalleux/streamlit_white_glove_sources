
from src import gcs, utils, firestore
import traceback
from datetime import datetime, timedelta
import pytz
import threading
import time
import logging

max_sources_files_expiration_date="9999-12-31"
paris_timezone = pytz.timezone('Europe/Paris')

def update_signed_urls(client_id, document_infos, docs, update_in_firestore=False):
    try :
        #Note : In firestore you have :
        #- aws_link : bubble link (public, to become private)
        #- gcs_path_to_doc : link to blob (bucket_name/client_id/...) to doc
        #- gcs_path_to_pdfs : link to pdfs blob (list) (bucket_name/client_id/...). doc_type==docx, doc and gdoc and one pdf -> Pdf equivalent, usefull for highlight
        docs =[item for sublist in docs for item in (sublist if isinstance(sublist, list) or isinstance(sublist, tuple) else [sublist])]
        if type(docs)==str :
            docs=[docs]
        threads = []
        do_update_docs = []

        for doc in docs :
            now=datetime.now(paris_timezone)
            use_signed_url_in_sources= False
            max_signed_url_expiration_days= 30 if use_signed_url_in_sources else 7 #max possible, will apply only on docx and gdoc (or pdf drive) for pdf version anyway if use_signed_url_in_sources is false
            min_signed_url_expiration_days_in_sources= 25 if use_signed_url_in_sources else 6 # Means it will be recompute potentially every day, but less time would mean less time for signe url to be valid

            min_date_to_reindexed=now+timedelta(minutes=60*24*min_signed_url_expiration_days_in_sources)
            min_date_to_reindexed_str=min_date_to_reindexed.strftime('%Y-%m-%dT%H-%M-%S')
            max_date_to_reindexed=now+timedelta(minutes=60*24*max_signed_url_expiration_days)
            max_date_to_reindexed_str=max_date_to_reindexed.strftime('%Y-%m-%dT%H-%M-%S')
            if document_infos[doc].get("signed_urls") is None or document_infos[doc].get("signed_urls").get("expiration_date") is None or document_infos[doc].get("signed_urls").get("expiration_date") <= min_date_to_reindexed_str or document_infos[doc].get("signed_urls").get("expiration_date") >= max_date_to_reindexed_str : #max happend if change of config and reducing existing expiration date
                
                blob_doc = document_infos[doc]["gcs_path_to_doc"].split("/", 1)[1]
                blob_bucket = document_infos[doc]["gcs_path_to_doc"].split("/", 1)[0]
                minutes = 60*24*max_signed_url_expiration_days
                new_expiration_date=now+timedelta(minutes=minutes)
                document_infos[doc]["signed_urls"]={"expiration_date" : new_expiration_date.strftime('%Y-%m-%dT%H-%M-%S')}
                if document_infos[doc].get('other_info', {}).get("token") is not None or utils.get_doc_type(doc)=="url" or not use_signed_url_in_sources: #force aws link all the time
                    if document_infos[doc]["signed_urls"].get("original_doc")!=document_infos[doc]["aws_link"]:
                        document_infos[doc]["signed_urls"]["original_doc"]=document_infos[doc]["aws_link"]
                        do_update_docs.append(doc)
                else :
                    do_update_docs.append(doc)
                    t=threading.Thread(target=gcs.generate_download_signed_url_v4, args=(blob_bucket, blob_doc), kwargs={"minutes" : minutes, "thread_url" : document_infos[doc]["signed_urls"], "thread_key" : "original_doc"})
                    t.start()
                    threads.append(t)
                    time.sleep(0.05)
                if type(document_infos[doc].get("gcs_path_to_pdfs"))==list and len(document_infos[doc]["gcs_path_to_pdfs"])==1 and (utils.get_doc_type(doc) in ["gdoc", "docx", "doc"] or (utils.get_doc_type(doc)=="pdf" and document_infos[doc].get("other_info", {}).get("token"))):
                    do_update_docs.append(doc)
                    blob_pdf = document_infos[doc]["gcs_path_to_pdfs"][0].split("/", 1)[1]
                    blob_bucket = document_infos[doc]["gcs_path_to_pdfs"][0].split("/", 1)[0] #should be the same but we never know
                    t2=threading.Thread(target=gcs.generate_download_signed_url_v4, args=(blob_bucket, blob_pdf), kwargs={"minutes" : minutes, "thread_url" : document_infos[doc]["signed_urls"], "thread_key" : "converted_pdf"})
                    t2.start()
                    threads.append(t2)
                    time.sleep(0.05)

        for thread in threads:
            thread.join()

        do_update_docs=list(set(do_update_docs))
        if update_in_firestore and len(do_update_docs)>0 :
            logging.info(f"Updating {len(do_update_docs)} document signed urls")
            to_update_dict = {document_infos[doc]["_id"] : {"signed_urls" : document_infos[doc]["signed_urls"]} for doc in do_update_docs}
            firestore.insert_or_update_object("documents", to_update_dict, update_only=True)
    except :
        print("qa fill (non-critical)", f"Impossible to update signed url, keep like this. Not critical (only for highlight in docx) if use signed url = False (use signed url = {use_signed_url_in_sources}) : \n {traceback.format_exc()}", "None")
