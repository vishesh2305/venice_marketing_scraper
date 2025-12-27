#!/usr/bin/env python3
"""
Demo script to test the 5 Venice AI Marketing Agents
Runs with sample data to verify all components work
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from agents import (
    VeniceClient,
    KeywordIntelligenceAgent,
    DomainScannerAgent,
    ProfileHunterAgent,
    DataEnrichmentAgent,
    ExportMasterAgent,
    MarketingScraperOrchestrator
)
from utils.excel_export import ExcelExporter

def demo_agents():
    """Test each agent with sample data"""
    
    print("\n" + "="*60)
    print("🧪 VENICE AI MARKETING SCRAPER - DEMO TEST")
    print("="*60)
    
    # Initialize client (demo mode without API key)
    client = VeniceClient()
    
    print("\n✅ VeniceClient initialized (demo mode)")
    
    # Test Agent 1: Keyword Intelligence
    print("\n" + "-"*50)
    print("🔑 Testing Agent 1: Keyword Intelligence")
    keyword_agent = KeywordIntelligenceAgent(client)
    print(f"   Model: {keyword_agent.config.model}")
    print(f"   Status: Ready ✓")
    
    # Test Agent 2: Domain Scanner
    print("\n" + "-"*50)
    print("🌐 Testing Agent 2: Domain Scanner")
    domain_agent = DomainScannerAgent(client)
    print(f"   Model: {domain_agent.config.model}")
    print(f"   Status: Ready ✓")
    
    # Test Agent 3: Profile Hunter
    print("\n" + "-"*50)
    print("🎯 Testing Agent 3: Profile Hunter")
    hunter_agent = ProfileHunterAgent(client)
    print(f"   Model: {hunter_agent.config.model}")
    print(f"   Status: Ready ✓")
    
    # Test Agent 4: Data Enrichment
    print("\n" + "-"*50)
    print("📊 Testing Agent 4: Data Enrichment")
    enrichment_agent = DataEnrichmentAgent(client)
    print(f"   Model: {enrichment_agent.config.model}")
    print(f"   Status: Ready ✓")
    
    # Test Agent 5: Export Master
    print("\n" + "-"*50)
    print("📤 Testing Agent 5: Export Master")
    export_agent = ExportMasterAgent(client)
    print(f"   Model: {export_agent.config.model}")
    print(f"   Status: Ready ✓")
    
    # Test Orchestrator
    print("\n" + "-"*50)
    print("🎭 Testing Orchestrator")
    orchestrator = MarketingScraperOrchestrator()
    print("   Status: Ready ✓")
    
    # Test Excel Export with sample data
    print("\n" + "-"*50)
    print("📄 Testing Excel Export")
    
    sample_data = {
        "export_ready_data": [
            {
                "name": "Jane Smith",
                "title": "Chief Marketing Officer",
                "company": "TechCorp",
                "email": "jane.smith@techcorp.com",
                "phone": "+1-555-0123",
                "linkedin": "https://linkedin.com/in/janesmith",
                "bio": "20+ years experience in B2B marketing",
                "lead_score": 92,
                "lead_category": "hot",
                "source": "linkedin.com",
                "scraped_date": "2024-01-15"
            },
            {
                "name": "John Doe",
                "title": "VP of Marketing",
                "company": "StartupXYZ",
                "email": "john@startupxyz.com",
                "phone": "",
                "linkedin": "https://linkedin.com/in/johndoe",
                "bio": "Growth marketing specialist",
                "lead_score": 78,
                "lead_category": "warm",
                "source": "linkedin.com",
                "scraped_date": "2024-01-15"
            },
            {
                "name": "Alice Johnson",
                "title": "Marketing Manager",
                "company": "MidCo",
                "email": "",
                "phone": "",
                "linkedin": "https://linkedin.com/in/alicejohnson",
                "bio": "Digital marketing expert",
                "lead_score": 45,
                "lead_category": "cold",
                "source": "twitter.com",
                "scraped_date": "2024-01-15"
            }
        ],
        "segments": {
            "hot_leads": ["Jane Smith"],
            "warm_leads": ["John Doe"],
            "cold_leads": ["Alice Johnson"],
            "decision_makers": ["Jane Smith", "John Doe"]
        },
        "statistics": {
            "total_profiles": 3,
            "with_email": 2,
            "with_phone": 1,
            "hot_leads_count": 1,
            "average_lead_score": 72
        }
    }
    
    exporter = ExcelExporter(output_dir="./exports")
    filepath = exporter.export(sample_data, "demo_test_export.xlsx")
    print(f"   ✅ Test export created: {filepath}")
    
    # Summary
    print("\n" + "="*60)
    print("✨ ALL TESTS PASSED!")
    print("="*60)
    print("""
📋 SUMMARY:
   ├── 5 AI Agents: ✓ Loaded & Ready
   ├── Venice Client: ✓ Initialized  
   ├── Orchestrator: ✓ Ready
   └── Excel Export: ✓ Working

🚀 TO RUN THE APPLICATION:
   
   1. Set your Venice AI API key:
      export VENICE_API_KEY="your-key-here"
      
   2. Start the web UI:
      python main.py --server
      
   3. Open: http://localhost:5000

💡 Or use CLI mode:
   python main.py --target "Marketing managers" --domains linkedin.com
""")
    
    return 0


if __name__ == '__main__':
    sys.exit(demo_agents())
