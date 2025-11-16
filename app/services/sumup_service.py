import requests
from flask import current_app


class SumUpService:
    """Sum Up payment API service"""
    
    BASE_URL = 'https://api.sumup.com'
    
    def __init__(self, api_key=None):
        self.api_key = api_key or current_app.config.get('SUMUP_API_KEY')
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }
    
    def create_checkout(self, amount, currency='EUR', description='', return_url=''):
        """Create a checkout session"""
        payload = {
            'amount': int(amount * 100),  # Convert to cents
            'currency': currency,
            'description': description,
            'return_url': return_url
        }
        
        response = requests.post(
            f'{self.BASE_URL}/v0.1/checkouts',
            json=payload,
            headers=self.headers
        )
        
        return response.json() if response.status_code == 201 else None
    
    def get_transaction(self, transaction_id):
        """Get transaction details"""
        response = requests.get(
            f'{self.BASE_URL}/v0.1/transactions/{transaction_id}',
            headers=self.headers
        )
        
        return response.json() if response.status_code == 200 else None
    
    def verify_payment(self, transaction_id):
        """Verify if payment was successful"""
        transaction = self.get_transaction(transaction_id)
        
        if not transaction:
            return False
        
        return transaction.get('status') == 'SUCCESSFUL'
