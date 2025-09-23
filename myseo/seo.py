#!/usr/bin/env python3
"""
Simple Google Ads Keyword Research Tool
A streamlined keyword research module with OAuth authentication - Debug Version
"""

import os
import logging
from typing import List
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient
from google.ads.googleads.errors import GoogleAdsException
from google_auth_oauthlib.flow import InstalledAppFlow
import pandas as pd
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging with rich formatting
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)8s | %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

class KeywordMetrics(BaseModel):
    keyword: str = Field(..., description="The keyword text")
    search_volume: int = Field(default=0, description="Monthly search volume")
    competition: str = Field(default="UNKNOWN", description="Competition level")
    competition_index: float = Field(default=0.0, description="Competition index 0-1")
    low_bid_usd: float = Field(default=0.0, description="Low bid estimate in USD")
    high_bid_usd: float = Field(default=0.0, description="High bid estimate in USD")

class SimpleKeywordResearch:
    def __init__(self):
        logger.info("🚀 Initializing Google Ads Keyword Research Tool")
        self.client = self._setup_client()
        self.customer_id = os.getenv("GOOGLE_ADS_CUSTOMER_ID", "").replace('-', '')
        self.login_customer_id = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID", "").replace('-', '')
        if not self.customer_id:
            raise ValueError("❌ GOOGLE_ADS_CUSTOMER_ID environment variable is required")
        logger.info(f"🧪 Target Customer ID: {self.customer_id}")
        if self.login_customer_id:
            logger.info(f"🔑 Login Customer ID: {self.login_customer_id}")

    def _setup_client(self) -> GoogleAdsClient:
        refresh_token = os.getenv("GOOGLE_ADS_REFRESH_TOKEN")
        if refresh_token:
            logger.info("🔑 Using existing refresh token")
            config = {
                'developer_token': os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
                'client_id': os.getenv("GOOGLE_ADS_CLIENT_ID"),
                'client_secret': os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
                'refresh_token': refresh_token,
                'use_proto_plus': True
            }
            if os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"):
                config['login_customer_id'] = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID").replace('-', '')
                logger.info(f"🔑 Setting login_customer_id in config: {config['login_customer_id']}")
            return GoogleAdsClient.load_from_dict(config)
        else:
            return self._authenticate_oauth()

    def _authenticate_oauth(self) -> GoogleAdsClient:
        token_path = os.getenv("GOOGLE_ADS_CLIENT_TOKEN_PATH")
        if not token_path or not os.path.exists(token_path):
            raise FileNotFoundError("❌ GOOGLE_ADS_CLIENT_TOKEN_PATH not found")
        scopes = ["https://www.googleapis.com/auth/adwords"]
        flow = InstalledAppFlow.from_client_secrets_file(token_path, scopes=scopes)
        creds = flow.run_local_server(open_browser=True)
        logger.info("✅ OAuth authentication successful")
        config = {
            'developer_token': os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
            'client_id': os.getenv("GOOGLE_ADS_CLIENT_ID"),
            'client_secret': os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
            'refresh_token': creds.refresh_token,
            'use_proto_plus': True
        }
        if os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"):
            config['login_customer_id'] = os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID").replace('-', '')
        return GoogleAdsClient.load_from_dict(config)

    def search_keywords(self, 
                       keywords: List[str], 
                       location: str = "United States",
                       max_results: int = 50,
                       include_adult_keywords: bool = False) -> List[KeywordMetrics]:
        logger.info(f"🔍 Searching keywords: {', '.join(keywords)}")
        logger.info(f"📍 Location: {location} | Max results: {max_results}")
        logger.info(f"📋 Using Customer ID: {self.customer_id}")
        try:
            service = self.client.get_service("KeywordPlanIdeaService")
            request = self.client.get_type("GenerateKeywordIdeasRequest")
            request.customer_id = self.customer_id
            request.language = self.client.get_service("GoogleAdsService").language_constant_path("1000")
            location_id = "2840"
            if location.lower() in ["uk", "united kingdom"]:
                location_id = "2826"
            elif location.lower() in ["canada"]:
                location_id = "2124"
            request.geo_target_constants.append(
                self.client.get_service("GoogleAdsService").geo_target_constant_path(location_id)
            )
            request.keyword_plan_network = self.client.enums.KeywordPlanNetworkEnum.GOOGLE_SEARCH
            request.keyword_seed.keywords.extend(keywords)
            request.include_adult_keywords = include_adult_keywords
            logger.info("📡 Fetching data from Google Ads API...")
            ideas = service.generate_keyword_ideas(request=request)
            results = []
            for i, idea in enumerate(ideas):
                if i >= max_results:
                    break
                metrics = self._extract_metrics(idea)
                results.append(metrics)
            logger.info(f"✅ Found {len(results)} keyword ideas")
            return results
        except GoogleAdsException as ex:
            logger.error(f"❌ Google Ads API Error: {ex}")
            for error in ex.failure.errors:
                logger.error(f"  Error: {error.error_code}")
                logger.error(f"  Message: {error.message}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error: {str(e)}")
            raise

    def _extract_metrics(self, idea) -> KeywordMetrics:
        metrics = idea.keyword_idea_metrics
        volume = metrics.avg_monthly_searches if metrics.avg_monthly_searches else 0
        competition = metrics.competition.name if metrics.competition else "UNKNOWN"
        comp_index = getattr(metrics, 'competition_index', 0.0) or 0.0
        low_bid = (metrics.low_top_of_page_bid_micros or 0) / 1_000_000
        high_bid = (metrics.high_top_of_page_bid_micros or 0) / 1_000_000
        return KeywordMetrics(
            keyword=idea.text,
            search_volume=volume,
            competition=competition,
            competition_index=comp_index,
            low_bid_usd=low_bid,
            high_bid_usd=high_bid
        )

    def save_results(self, results: List[KeywordMetrics], format: str = "csv") -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if format.lower() == "csv":
            filename = f"keywords_{timestamp}.csv"
            df = pd.DataFrame([r.model_dump() for r in results])
            df.to_csv(filename, index=False)
        else:
            filename = f"keywords_{timestamp}.json"
            import json
            with open(filename, 'w') as f:
                json.dump([r.model_dump() for r in results], f, indent=2)
        logger.info(f"💾 Results saved to {filename}")
        return filename

    def print_summary(self, results: List[KeywordMetrics]):
        if not results:
            logger.warning("⚠️  No results to summarize")
            return
        volumes = [r.search_volume for r in results]
        high_vol = [r for r in results if r.search_volume > 1000]
        low_comp = [r for r in results if r.competition == "LOW"]
        logger.info("📈 KEYWORD RESEARCH SUMMARY:")
        logger.info(f"  Total keywords: {len(results)}")
        logger.info(f"  Avg search volume: {sum(volumes)/len(volumes):,.0f}")
        logger.info(f"  High volume (>1K): {len(high_vol)}")
        logger.info(f"  Low competition: {len(low_comp)}")
        top_keywords = sorted(results, key=lambda x: x.search_volume, reverse=True)[:3]
        logger.info("🏆 Top keywords:")
        for kw in top_keywords:
            logger.info(f"  {kw.keyword}: {kw.search_volume:,} searches, {kw.competition} competition")

def main():
    try:
        logger.info("🧪 Starting Google Ads Keyword Research - DEBUG MODE")
        kr = SimpleKeywordResearch()
        seed_keywords = ["python programming"]
        logger.info(f"\n🚀 Testing keyword research with customer {kr.customer_id}...")
        results = kr.search_keywords(
            keywords=seed_keywords,
            location="United States",
            max_results=100,
            include_adult_keywords=False
        )
        kr.print_summary(results)
        if results:
            csv_file = kr.save_results(results, format="csv")
            logger.info(f"\n🎉 Success! Results saved to {csv_file}")
        logger.info("\n✅ Keyword research completed successfully!")
    except Exception as e:
        logger.error(f"❌ Application error: {str(e)}")

if __name__ == "__main__":
    main()
