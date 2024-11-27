from google.cloud  import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
from google.oauth2 import service_account
import os
import logging
from datetime import datetime, timezone
import pytz


paris_timezone = pytz.timezone('Europe/Paris')

CRED_PATH = os.path.abspath(os.environ.get(
                    "CRED_PATH", "./credentials/cred.json"))

def custom_json_serializer(document):
    
    if document.get("history"):
        document["history"]="See firestore for more info"
   
    for key, value in document.items():
        if isinstance(value, datetime):
            document[key]=value.isoformat()
            # Convert datetime to string
    return document

def get_firestore_transaction_and_object_ref(collection_name, document_ids):
    credentials = service_account.Credentials.from_service_account_file(
        CRED_PATH
    )
    db = firestore.Client(credentials=credentials)
    

    object_refs = {document_id : db.collection(collection_name).document(document_id) for document_id in document_ids}

    transaction=db.transaction()

    return transaction, object_refs

def query_documents_by_client_and_status_aws_link(client_id, status_list, aws_link):
    credentials = service_account.Credentials.from_service_account_file(CRED_PATH)
    db = firestore.Client(credentials=credentials)
    collection_name = "documents"

    collection_ref = db.collection(collection_name)
   
    # Query documents based on client_id and status
    query = collection_ref.where(filter=FieldFilter("client_id", "==", client_id)).where(filter=FieldFilter("status", "in", status_list)).where(filter=FieldFilter("aws_link", "==", aws_link))

    # Get the documents
    query_result = query.stream()

    # Process the query result
    documents = []
    for document in query_result:
        document_id = document.id
        document=document.to_dict()
        document=custom_json_serializer(document)
        document['_id'] = document_id
        documents.append(document)

    return documents

def initialize_multiple_object(collection_name, document_ids_content_dict, field_to_keep_in_history=[]):
    credentials = service_account.Credentials.from_service_account_file(
        CRED_PATH
    )
    db = firestore.Client(credentials=credentials)
    batch=db.batch()
    for document_id, content_as_dict in document_ids_content_dict.items():
        survey_ref = db.collection(collection_name).document(document_id)
        content_as_dict["created_dt"]=datetime.now().astimezone(paris_timezone)
        content_as_dict["updated_dt"]=content_as_dict["created_dt"]
        if field_to_keep_in_history :
            field_to_keep_in_history.append("updated_dt")
            history=[{f : content_as_dict[f] for f in field_to_keep_in_history if f in content_as_dict}]
        
            content_as_dict["history"]=history
        batch.set(survey_ref, content_as_dict)
        
    batch.commit()
    logging.info(f"{collection_name} with ids = {list(document_ids_content_dict.keys())} created in firestore")


@firestore.transactional
def update_object(transaction, doc_ref, update_snapshot_func=None, info_to_update_as_dict={}, field_to_keep_in_history=[], update_snapshot_func_additional_arg={}):
    snapshot = doc_ref.get(transaction=transaction)
    init_doc=snapshot.to_dict()
    if "verify_name" not in info_to_update_as_dict or init_doc["name"]==info_to_update_as_dict["verify_name"] :
        info_to_update_as_dict["update_dt"]=datetime.now().astimezone(paris_timezone)
        if len(field_to_keep_in_history)>0 :
            field_to_keep_in_history.append("update_dt")
            if snapshot.get("history"):
                history=snapshot.get("history")
            else :
                history = []
                
            history.append({h : info_to_update_as_dict[h] for h in field_to_keep_in_history if h in info_to_update_as_dict.keys()})
            info_to_update_as_dict["history"]=history
        
        if update_snapshot_func :
            snapshot_updated=update_snapshot_func(snapshot, update_snapshot_func_additional_arg)
        else :
            snapshot_updated={}
        
        snapshot_updated.update({k : v for k, v in info_to_update_as_dict.items() if k!="verify_name"})
        transaction.update(doc_ref, snapshot_updated)

        init_doc.update(snapshot_updated)
    else :
        print(f"Trying to update status but name is not the same as the one in firestore {info_to_update_as_dict['verify_name']}!={init_doc['name']}", client_id=init_doc['client_id'])
    
    return custom_json_serializer(init_doc)

def insert_or_update_object(collection_name, document_ids_content_dict, field_to_keep_in_history=[], update_snapshot_func=None, update_snapshot_func_additional_arg={}, update_only=False):#verify name only usefull if update, because currently same id can be construct from different name (with -, ., ' ')
    transaction, object_refs = get_firestore_transaction_and_object_ref(collection_name, document_ids_content_dict.keys())
    bulk_init = {}
    for doc_id, doc_ref in object_refs.items():
        if doc_ref.get().exists :
            update_object(transaction, doc_ref, info_to_update_as_dict=document_ids_content_dict[doc_id], field_to_keep_in_history=field_to_keep_in_history, update_snapshot_func=update_snapshot_func, update_snapshot_func_additional_arg=update_snapshot_func_additional_arg)
        else :
            if update_only :
                message=f"Trying to update firestore {collection_name} {doc_id} but this one has never been initialized before"
                logging.warning(message)
                raise Exception(message)
            bulk_init[doc_id]= document_ids_content_dict[doc_id]
    if len(bulk_init) > 0 :
        initialize_multiple_object(collection_name, bulk_init, field_to_keep_in_history=field_to_keep_in_history)

