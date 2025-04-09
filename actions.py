import logging
import os
from typing import Any, Text, Dict, List, Optional, Tuple
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import psycopg2

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Database connection settings
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "1530")
DB_PORT = os.getenv("DB_PORT", "5432")

# Establishing database connection
def get_db_connection() -> Tuple[Optional[psycopg2.extensions.connection], Optional[psycopg2.extensions.cursor]]:
    try:
        conn = psycopg2.connect(
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT
        )
        cursor = conn.cursor()
        logger.debug("Database connection established successfully!")
        return conn, cursor
    except Exception as e:
        logger.error(f"Database connection failed: {str(e)}")
        return None, None

class ActionVerifyPhone(Action):
    def name(self) -> Text:
        return "action_verify_phone"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        phone_number = tracker.get_slot("contact")
        logger.debug(f"Debug: phone_number = {phone_number}")

        if not phone_number:
            phone_number = tracker.latest_message.get('text')
            logger.debug(f"Debug: phone_number from latest message = {phone_number}")

        if not phone_number or not self._is_valid_phone_number(phone_number):
            dispatcher.utter_message(text="Please enter a valid phone number.")
            return []

        conn, cursor = get_db_connection()
        if not conn or not cursor:
            dispatcher.utter_message(text="Sorry, there was an error verifying your phone number.")
            return []

        try:
            query = "SELECT occupation FROM employees WHERE contact = %s"
            logger.debug(f"Debug: Running query with phone number: {phone_number}")
            cursor.execute(query, (phone_number,))
            user = cursor.fetchone()

            if user:
                occupation = user[0]
                logger.debug(f"Debug: Occupation found: {occupation}")
                dispatcher.utter_message(text=f"You are verified the {occupation}, how can I assist you?")
                return [SlotSet("phone_verified", True), SlotSet("occupation", occupation)]
            else:
                logger.debug(f"Debug: No user found for phone number {phone_number}")
                dispatcher.utter_message(text="The phone number is not registered. Please contact Admin.")
                return [SlotSet("phone_verified", False)]
        finally:
            cursor.close()
            conn.close()

    def _is_valid_phone_number(self, phone: str) -> bool:
        return phone.isdigit() and len(phone) >= 10

class ActionCheckAssetStatus(Action):
    def name(self) -> Text:
        return "action_check_asset_status"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        if not tracker.get_slot("phone_verified"):
            dispatcher.utter_message(text="You need to verify your phone number first.")
            return []

        plate = tracker.get_slot("plate")
        logger.debug(f"Debug: Checking asset status for plate number: {plate}")

        if not plate:
            dispatcher.utter_message(text="Please provide a valid plate number to check the asset status.")
            return []

        conn, cursor = get_db_connection()
        if not conn or not cursor:
            dispatcher.utter_message(text="Sorry, there was an error fetching asset details.")
            return []

        try:
            query = """
                SELECT plate, imei, asset_type, tr_model, inst_status, branch, asset_status, client_name
                FROM gps_installations WHERE plate = %s
            """
            cursor.execute(query, (plate,))
            asset = cursor.fetchone()

            if asset:
                response = "\n".join([
                    f"PLATE: {asset[0] or 'N/A'}",
                    f"IMEI: {asset[1] or 'N/A'}",
                    f"Asset Type: {asset[2] or 'N/A'}",
                    f"Tracker Model: {asset[3] or 'N/A'}",
                    f"Inst Status: {asset[4] or 'N/A'}",
                    f"Branch: {asset[5] or 'N/A'}",
                    f"Asset Status: {asset[6] or 'N/A'}",
                    f"Client Name: {asset[7] or 'N/A'}",
                ])
                dispatcher.utter_message(text=response)
            else:
                dispatcher.utter_message(text="No asset found with the provided plate number.")
        finally:
            cursor.close()
            conn.close()

        return []

class ActionVerifyEmployee(Action):
    def name(self) -> Text:
        return "action_verify_employee"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        phone_number = tracker.get_slot("contact")
        logger.debug(f"Debug: Verifying employee with phone number = {phone_number}")

        if not phone_number:
            dispatcher.utter_message(text="Please enter your phone number for verification.")
            return []

        conn, cursor = get_db_connection()
        if not conn or not cursor:
            dispatcher.utter_message(text="Sorry, there was an error verifying your phone number.")
            return []

        try:
            query = "SELECT * FROM employees WHERE contact = %s"
            cursor.execute(query, (phone_number,))
            employee = cursor.fetchone()

            if employee:
                dispatcher.utter_message(text="You are successfully verified as an employee.")
                return [SlotSet("employee_verified", True)]
            else:
                dispatcher.utter_message(text="The phone number does not match any registered employee.")
                return [SlotSet("employee_verified", False)]
        finally:
            cursor.close()
            conn.close()

class ActionHelp(Action):
    def name(self) -> Text:
        return "action_help"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text=(
            "I can help you with the following:\n"
            "1. Check asset status\n"
            "2. Provide phone financing options\n"
            "3. Assist with payment issues\n"
            "4. Explain why your phone is locked"
        ))
        return []

class ActionFallback(Action):
    def name(self) -> Text:
        return "action_fallback"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Sorry, I didn't quite understand that. Could you please rephrase?")
        return []
