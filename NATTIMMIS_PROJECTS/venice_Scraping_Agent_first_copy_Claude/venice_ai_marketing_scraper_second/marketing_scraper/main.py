#!/usr/bin/env python3
"""
🎯 Venice AI Marketing Scraper - 5 Intelligent Agents
Main launcher script with CLI and server modes
"""

import os
import sys
import json
import argparse
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def print_banner():
    """Print the application banner"""
    banner = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                                                                               ║
║   ██╗   ██╗███████╗███╗   ██╗██╗ ██████╗███████╗     █████╗ ██╗               ║
║   ██║   ██║██╔════╝████╗  ██║██║██╔════╝██╔════╝    ██╔══██╗██║               ║
║   ██║   ██║█████╗  ██╔██╗ ██║██║██║     █████╗      ███████║██║               ║
║   ╚██╗ ██╔╝██╔══╝  ██║╚██╗██║██║██║     ██╔══╝      ██╔══██║██║               ║
║    ╚████╔╝ ███████╗██║ ╚████║██║╚██████╗███████╗    ██║  ██║██║               ║
║     ╚═══╝  ╚══════╝╚═╝  ╚═══╝╚═╝ ╚═════╝╚══════╝    ╚═╝  ╚═╝╚═╝               ║
║                                                                               ║
║   🎯 MARKETING SCRAPER - 5 INTELLIGENT AI AGENTS                             ║
║                                                                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   AGENTS:                                                                     ║
║   ┌───────────────────────────────────────────────────────────────────────┐   ║
║   │ 🔑 Agent 1: Keyword Intelligence  │ Expands queries → keywords        │   ║
║   │ 🌐 Agent 2: Domain Scanner        │ Analyzes target websites          │   ║
║   │ 🎯 Agent 3: Profile Hunter        │ Discovers profiles on web         │   ║
║   │ 📊 Agent 4: Data Enrichment       │ Enhances & scores profiles        │   ║
║   │ 📤 Agent 5: Export Master         │ Creates Excel/CSV exports         │   ║
║   └───────────────────────────────────────────────────────────────────────┘   ║
║                                                                               ║
║   Powered by Venice AI • Privacy-First • Uncensored Models                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
    """
    print(banner)


def run_server():
    """Start the web server with UI"""
    print_banner()
    print("\n🚀 Starting web server...")
    print("   📡 API: http://localhost:5000")
    print("   🖥️  UI:  http://localhost:5000")
    print("\n   Press Ctrl+C to stop\n")
    
    # Add project root to path for imports
    project_root = os.path.dirname(os.path.abspath(__file__))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    # Import and run - disable reloader to avoid path issues on Windows
    from server.app import app, socketio
    socketio.run(app, host='0.0.0.0', port=5000, debug=True, use_reloader=False)


def run_cli(args):
    """Run in CLI mode"""
    print_banner()
    
    from agents import MarketingScraperOrchestrator
    from utils.excel_export import export_to_excel, export_to_csv
    
    print("\n🔧 Initializing 5 AI Agents...")
    
    api_key = args.api_key or os.environ.get("VENICE_API_KEY", "")
    if not api_key:
        print("\n⚠️  Warning: No VENICE_API_KEY found. Running in demo mode.")
        print("   Set your key: export VENICE_API_KEY=your_key_here")
    
    orchestrator = MarketingScraperOrchestrator(api_key)
    
    print("✅ Agents ready!\n")
    
    # Progress callback
    def progress(stage, data):
        status = data.get('status', 'processing')
        emoji = '🔄' if status == 'running' else '✅' if status == 'complete' else '❌'
        print(f"   {emoji} {stage}: {status}")
    
    print(f"📋 Target: {args.target}")
    print(f"🌐 Domains: {', '.join(args.domains)}")
    print(f"📊 Max Results: {args.max_results}")
    print("\n" + "─" * 60)
    print("🚀 Starting scraping pipeline...\n")
    
    # Run the pipeline
    result = orchestrator.run_pipeline(
        target_profile=args.target,
        domains=args.domains,
        max_results=args.max_results,
        callback=progress
    )
    
    print("\n" + "─" * 60)
    
    if result['status'] == 'complete':
        final_data = result.get('final_data', {})
        stats = final_data.get('statistics', {})
        
        print("\n📊 RESULTS SUMMARY")
        print("─" * 40)
        print(f"   Total Profiles:    {stats.get('total_profiles', 0)}")
        print(f"   With Email:        {stats.get('with_email', 0)}")
        print(f"   With Phone:        {stats.get('with_phone', 0)}")
        print(f"   Hot Leads:         {stats.get('hot_leads_count', 0)}")
        print(f"   Average Score:     {stats.get('average_lead_score', 0)}")
        
        # Export
        if args.output:
            print(f"\n📤 Exporting to {args.output}...")
            
            if args.output.endswith('.csv'):
                filepath = export_to_csv(final_data, args.output)
            else:
                filepath = export_to_excel(final_data, args.output)
                
            print(f"✅ Exported to: {filepath}")
        else:
            # Auto-export to Excel
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"marketing_leads_{timestamp}.xlsx"
            filepath = export_to_excel(final_data, filename)
            print(f"\n📤 Auto-exported to: {filepath}")
            
        print("\n✨ Scraping complete!")
        
    else:
        print(f"\n❌ Scraping failed: {result.get('errors', ['Unknown error'])}")
        return 1
        
    return 0


def run_interactive():
    """Run in interactive mode"""
    print_banner()
    
    print("\n🎯 INTERACTIVE MODE\n")
    
    # Get inputs
    target = input("Enter target profile description:\n> ")
    domains_input = input("\nEnter domains (comma-separated, e.g., linkedin.com,twitter.com):\n> ")
    domains = [d.strip() for d in domains_input.split(',') if d.strip()]
    
    max_results_input = input("\nMax results (default: 50):\n> ")
    max_results = int(max_results_input) if max_results_input.isdigit() else 50
    
    # Create args object
    class Args:
        pass
    
    args = Args()
    args.target = target
    args.domains = domains
    args.max_results = max_results
    args.api_key = None
    args.output = None
    
    return run_cli(args)


def main():
    parser = argparse.ArgumentParser(
        description='🎯 Venice AI Marketing Scraper - 5 Intelligent Agents',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start web UI (recommended)
  python main.py --server
  
  # CLI mode - quick scrape
  python main.py --target "CTOs at AI startups" --domains linkedin.com
  
  # CLI mode - with options
  python main.py --target "Marketing managers" --domains linkedin.com,twitter.com --max 100 --output leads.xlsx
  
  # Interactive mode
  python main.py --interactive
        """
    )
    
    parser.add_argument('--server', action='store_true',
                        help='Start web server with UI (recommended)')
    parser.add_argument('--interactive', '-i', action='store_true',
                        help='Interactive mode with prompts')
    parser.add_argument('--target', '-t', type=str,
                        help='Target profile description')
    parser.add_argument('--domains', '-d', type=str, nargs='+', default=['linkedin.com'],
                        help='Target domains to scrape')
    parser.add_argument('--max-results', '--max', type=int, default=50,
                        help='Maximum profiles to find')
    parser.add_argument('--api-key', type=str,
                        help='Venice AI API key (or set VENICE_API_KEY env var)')
    parser.add_argument('--output', '-o', type=str,
                        help='Output filename (.xlsx or .csv)')
    
    args = parser.parse_args()
    
    # Determine run mode
    if args.server:
        run_server()
    elif args.interactive:
        sys.exit(run_interactive())
    elif args.target:
        sys.exit(run_cli(args))
    else:
        # Default to server mode
        print("\n💡 Tip: Use --help to see all options")
        print("   Starting web server by default...\n")
        run_server()


if __name__ == '__main__':
    main()
