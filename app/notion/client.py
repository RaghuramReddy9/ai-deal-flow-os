"""Notion client wrapper for database operations."""

from notion_client import Client
import os

def get_notion_client():
    """Initialize and return Notion client."""
    token = os.getenv("NOTION_TOKEN")
    if not token:
        raise ValueError("NOTION_TOKEN environment variable not set")
    return Client(auth=token)

class NotionClient:
    """Wrapper for Notion database operations."""
    
    def __init__(self):
        self.client = get_notion_client()
        self.database_id = os.getenv("NOTION_DATABASE_ID")
    
    def create_page(self, properties):
        """Create a new page in the database."""
        return self.client.pages.create(
            parent={"database_id": self.database_id},
            properties=properties
        )
    
    def update_page(self, page_id, properties):
        """Update a page in the database."""
        return self.client.pages.update(page_id, properties=properties)