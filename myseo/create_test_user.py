# not needed
import os
from datetime import datetime
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient

# Load environment variables
load_dotenv()

config = {
    "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
    "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
    "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
    "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
    "login_customer_id": os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
    "use_proto_plus": True,  # ←  This line is essential
}

client = GoogleAdsClient.load_from_dict(config)
customer_service = client.get_service("CustomerService")

customer = client.get_type("Customer")
customer.descriptive_name = f"Test Account {datetime.now():%Y-%m-%d %H:%M:%S}"
customer.currency_code = "USD"
customer.time_zone = "America/New_York"

resp = customer_service.create_customer_client(
    customer_id=config["login_customer_id"],
    customer_client=customer
)
print("✅ Created new test account:", resp.resource_name)
