"""Notion synchronization module for pushing deal data."""

from .client import NotionClient

def sync_deal_to_notion(deal):
    """
    Sync a single deal to Notion database.
    
    Args:
        deal: Deal record dict
        
    Returns:
        dict: Notion page response
    """
    client = NotionClient()
    
    properties = {
        "Deal Name": {"title": [{"text": {"content": deal.get('deal_name', 'Untitled')}}]},
        "Industry": {"select": {"name": deal.get('industry', 'Unknown')}},
        "Location": {"rich_text": [{"text": {"content": deal.get('location', '')}}]},
        "Revenue": {"number": deal.get('revenue')},
        "EBITDA": {"number": deal.get('ebitda')},
        "Asking Price": {"number": deal.get('asking_price')},
        "Summary": {"rich_text": [{"text": {"content": deal.get('summary', '')}}]},
        "Score": {"number": deal.get('score', 0)},
        "Risks": {"rich_text": [{"text": {"content": deal.get('risks', '')}}]},
        "Stage": {"select": {"name": deal.get('stage', 'New')}},
        "Source URL": {"url": deal.get('source_url')}
    }
    
    return client.create_page(properties)