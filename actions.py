import logging
import firebase_admin
from firebase_admin import credentials, firestore, storage
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from typing import Any, Text, Dict, List
import datetime

# Initialize Firebase Admin SDK
cred = credentials.Certificate("C:/dynamic_TUNI/serviceAccountKey.json")
firebase_admin.initialize_app(cred, {
    'storageBucket': 'tunitest-e022d.appspot.com'
})
db = firestore.client()
bucket = storage.bucket()


class ActionFetchProductImages(Action):

    def name(self) -> Text:
        return "action_fetch_product_image"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        #print(tracker.latest_message.get('text', ''))
        product_type = tracker.latest_message.get('text', '')
        # Define the collection path (path up to the collection containing documents)
        collection_path = ''
        if 'combo' in product_type:
            collection_path = 'combo_products'
        else:
            collection_path = 'clothes/Men/Tshirt/collar/'+product_type
        print(collection_path)

        try:
            # Fetch all documents in the specified collection path
            docs = db.collection(collection_path).stream()

            if not docs:
                dispatcher.utter_message(text="No products found in this category.")
                return []

            all_buttons = []
            for doc in docs:
                product_data = doc.to_dict()
                image_names = []
                if "combo" in product_type:
                    #combo
                    combo_details = product_data.get("combo_details", [])
                    for item in combo_details:
                        if 'imageturls' in item:
                            image_names.append(item['imageturls'])
                else:
                    #Plain Printed check
                    image_names = product_data.get("imageUrl", [])                  # Assuming 'image_names' is a list of image filenames
                print(image_names)

                if not image_names:
                    continue

                for image_name in image_names:
                    # image_blob = bucket.blob(image_name)
                    try:
                        # Generate a signed URL for the image
                        # url = image_blob.generate_signed_url(
                        #     expiration=datetime.timedelta(minutes=15),  # Set expiration time
                        #     method='GET'
                        # )
                        url = image_name
                        #print(url)
                        all_buttons.append({"title": image_name, "url": url})
                    except Exception as e:
                        logging.error(f'Error generating image URL for {image_name}: {e}')
                        dispatcher.utter_message(text=f"Unable to fetch image URL for {image_name}.")

            if all_buttons:
                dispatcher.utter_message(text="Here are the images you requested:", buttons=all_buttons)
            else:
                dispatcher.utter_message(text="No image URLs could be generated.")

        except Exception as e:
            logging.error(f'Error while fetching product data: {e}')
            dispatcher.utter_message(text="An error occurred while retrieving product information. Please try again later.")
        
        return []
    
    def XXrun(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        # Fetch data from Firebase Firestore
        product_ref = db.collection('products').document('cloth')
        product = product_ref.get()

        if product.exists:
            product_data = product.to_dict()
            # Fetch image URL from Firebase Storage
            image_blob = bucket.blob(f'images/{product_data["Men"]}')
            try:
                url = image_blob.generate_signed_url(expiration=datetime.timedelta(minutes=15),  # Set expiration time 
                                                method='GET')
                dispatcher.utter_message(text="Here's the image you requested:", buttons=[{"title": image_blob.name, "url": url}
        ])
                # dispatcher.utter_message(text=f"Here is the product image: {image_url}")
            except Exception as e:
                logging.error(f'Error generating image URL: {e}')
                dispatcher.utter_message(text="Unable to fetch image URL.")
        else:
            dispatcher.utter_message(text="Sorry, I couldn't find the product information.")
        return []
