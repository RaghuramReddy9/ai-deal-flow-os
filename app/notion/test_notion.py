from notion_client import Client
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

notion = Client(auth=os.getenv("NOTION_API_KEY"))

database_id = os.getenv("NOTION_DATABASE_ID")

notion.pages.create(
    parent={"database_id": database_id},
    properties={
        "Deal Name": {"title":[{"text":{"content":"Test HVAC Business"}}]},
        "Score": {"number":7.5}
    }
)