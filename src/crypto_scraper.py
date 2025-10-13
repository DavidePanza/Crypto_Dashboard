# flows/bitcoin_flow.py
from prefect import flow, task
import requests
import boto3
from datetime import datetime, UTC
import os


@task(retries=3, retry_delay_seconds=10)
def fetch_crypto_data():
    """Fetch crypto price data"""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin,ethereum,tether,binancecoin,solana,ripple,usd-coin,cardano,dogecoin,tron',
        'vs_currencies': 'eur',
        'include_24hr_change': 'false',
        'include_24hr_vol': 'false',
        'include_market_cap': 'false'
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


@task
def transform_data(raw_data):
    """Add timestamp and format data"""
    return {
       'timestamp': datetime.now(UTC).isoformat(),
       **{key: item['eur'] for key, item in raw_data.items()}
    }


@task
def save_to_dynamodb(data, table_name='crypto-prices'):
    """Save to DynamoDB - all cryptos in one item per timestamp"""
    from decimal import Decimal
    import time
    
    dynamodb = boto3.resource('dynamodb', region_name=os.getenv('AWS_DEFAULT_REGION'))
    table = dynamodb.Table(table_name)
    
    timestamp = data['timestamp']
    ttl = int(time.time()) + (180 * 24 * 3600)  # Expire in 180 days
    
    item = {
        'PK': 'CRYPTO_PRICES',  # fixed partition key
        'timestamp': timestamp,  # sort key
        'ttl': ttl
    }

    for key, value in data.items():
        if key == 'timestamp':
            continue
        item[key] = Decimal(str(value))
    
    table.put_item(Item=item)
    
    return 1 


@flow(name="Crypto Price Tracker")
def crypto_tracking_flow():
    """Main flow to track Crypto prices"""
    raw_data = fetch_crypto_data()
    transformed = transform_data(raw_data)
    dynamodb_path = save_to_dynamodb(transformed)

    print(f"Saved crypto data to {dynamodb_path}")


if __name__ == "__main__":
    crypto_tracking_flow()