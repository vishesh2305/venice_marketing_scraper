"""
Marketing Scraper API Server
Flask backend with WebSocket support for real-time updates
"""

import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent.absolute()
STATIC_DIR = SCRIPT_DIR / 'static'

from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import threading
import time

# Add parent directory to path for imports
sys.path.insert(0, str(SCRIPT_DIR.parent))

from agents import MarketingScraperOrchestrator
from utils.excel_export import export_to_excel, export_to_csv

app = Flask(__name__, static_folder=str(STATIC_DIR), static_url_path='')
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
active_jobs: Dict[str, Dict] = {}
orchestrator: Optional[MarketingScraperOrchestrator] = None


def get_orchestrator():
    """Lazy load orchestrator"""
    global orchestrator
    if orchestrator is None:
        api_key = os.environ.get("VENICE_API_KEY", "")
        orchestrator = MarketingScraperOrchestrator(api_key)
    return orchestrator


@app.route('/')
def serve_ui():
    """Serve the main UI"""
    return send_from_directory(str(STATIC_DIR), 'index.html')


@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "venice_configured": bool(os.environ.get("VENICE_API_KEY"))
    })


@app.route('/api/scrape', methods=['POST'])
def start_scrape():
    """
    Start a new scraping job
    
    Request body:
    {
        "target_profile": "Marketing managers in SaaS companies",
        "domains": ["linkedin.com", "twitter.com"],
        "max_results": 50,
        "user_type": "B2B Decision Makers"
    }
    """
    data = request.json
    
    if not data:
        return jsonify({"error": "No data provided"}), 400
        
    target_profile = data.get("target_profile", "")
    domains = data.get("domains", [])
    max_results = data.get("max_results", 50)
    user_type = data.get("user_type", "")
    
    if not target_profile:
        return jsonify({"error": "target_profile is required"}), 400
        
    if not domains:
        return jsonify({"error": "At least one domain is required"}), 400
        
    # Combine target profile with user type for better search
    full_query = f"{target_profile} - {user_type}" if user_type else target_profile
    
    # Generate job ID
    job_id = f"job_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(active_jobs)}"
    
    # Initialize job state
    active_jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "stages": {},
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat()
    }
    
    # Start scraping in background thread
    def run_scrape():
        try:
            orch = get_orchestrator()
            
            def progress_callback(stage: str, data: Any):
                active_jobs[job_id]["stages"][stage] = data
                if data.get("status") == "complete":
                    active_jobs[job_id]["progress"] += 20
                    
                # Emit progress via WebSocket
                socketio.emit('scrape_progress', {
                    "job_id": job_id,
                    "stage": stage,
                    "progress": active_jobs[job_id]["progress"],
                    "data": data
                })
                
            active_jobs[job_id]["status"] = "running"
            socketio.emit('job_started', {"job_id": job_id})
            
            result = orch.run_pipeline(
                target_profile=full_query,
                domains=domains,
                max_results=max_results,
                callback=progress_callback
            )
            
            active_jobs[job_id]["status"] = "complete"
            active_jobs[job_id]["progress"] = 100
            active_jobs[job_id]["result"] = result
            
            socketio.emit('scrape_complete', {
                "job_id": job_id,
                "result": result
            })
            
        except Exception as e:
            active_jobs[job_id]["status"] = "error"
            active_jobs[job_id]["error"] = str(e)
            socketio.emit('scrape_error', {
                "job_id": job_id,
                "error": str(e)
            })
            
    thread = threading.Thread(target=run_scrape)
    thread.daemon = True
    thread.start()
    
    return jsonify({
        "job_id": job_id,
        "status": "queued",
        "message": "Scraping job started"
    })


@app.route('/api/jobs/<job_id>')
def get_job_status(job_id: str):
    """Get status of a scraping job"""
    if job_id not in active_jobs:
        return jsonify({"error": "Job not found"}), 404
        
    return jsonify(active_jobs[job_id])


@app.route('/api/jobs/<job_id>/export', methods=['POST'])
def export_job_results(job_id: str):
    """
    Export job results to Excel/CSV
    
    Request body:
    {
        "format": "excel" | "csv"
    }
    """
    if job_id not in active_jobs:
        return jsonify({"error": "Job not found"}), 404
        
    job = active_jobs[job_id]
    
    if job["status"] != "complete":
        return jsonify({"error": "Job not complete"}), 400
        
    if not job.get("result") or not job["result"].get("final_data"):
        return jsonify({"error": "No data to export"}), 400
        
    data = request.json or {}
    export_format = data.get("format", "excel")
    
    try:
        final_data = job["result"]["final_data"]
        
        if export_format == "csv":
            filepath = export_to_csv(final_data)
        else:
            filepath = export_to_excel(final_data)
            
        return send_file(
            filepath,
            as_attachment=True,
            download_name=os.path.basename(filepath)
        )
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/api/agents')
def list_agents():
    """List all 5 agents and their status"""
    return jsonify({
        "agents": [
            {
                "id": 1,
                "name": "KeywordIntelligence",
                "description": "Expands user queries into comprehensive keyword sets",
                "model": "zai-org-glm-4.6",
                "status": "ready"
            },
            {
                "id": 2,
                "name": "DomainScanner",
                "description": "Analyzes target domains and creates scraping strategies",
                "model": "llama-3.3-70b",
                "status": "ready"
            },
            {
                "id": 3,
                "name": "ProfileHunter",
                "description": "Searches and discovers profiles using keywords",
                "model": "qwen3-235b",
                "status": "ready"
            },
            {
                "id": 4,
                "name": "DataEnrichment",
                "description": "Enriches profiles with additional data and scoring",
                "model": "zai-org-glm-4.6",
                "status": "ready"
            },
            {
                "id": 5,
                "name": "ExportMaster",
                "description": "Compiles and exports data in various formats",
                "model": "llama-3.3-70b",
                "status": "ready"
            }
        ]
    })


# WebSocket events
@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    emit('connected', {'message': 'Connected to Marketing Scraper API'})


@socketio.on('subscribe_job')
def handle_subscribe(data):
    """Subscribe to job updates"""
    job_id = data.get('job_id')
    if job_id and job_id in active_jobs:
        emit('job_status', {
            'job_id': job_id,
            'status': active_jobs[job_id]
        })


if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════════╗
║       🎯 VENICE AI MARKETING SCRAPER - 5 INTELLIGENT AGENTS      ║
╠══════════════════════════════════════════════════════════════════╣
║                                                                  ║
║  AGENTS:                                                         ║
║  1. 🔑 Keyword Intelligence - Expands search queries             ║
║  2. 🌐 Domain Scanner - Analyzes target websites                 ║
║  3. 🎯 Profile Hunter - Discovers profiles on web                ║
║  4. 📊 Data Enrichment - Enhances profile data                   ║
║  5. 📤 Export Master - Creates Excel/CSV exports                 ║
║                                                                  ║
║  API: http://localhost:5000                                      ║
║  UI:  http://localhost:5000                                      ║
║                                                                  ║
╚══════════════════════════════════════════════════════════════════╝
    """)
    
    # Check for API key
    if not os.environ.get("VENICE_API_KEY"):
        print("⚠️  Warning: VENICE_API_KEY not set - running in demo mode")
        print("   Set your API key: export VENICE_API_KEY=your_key_here")
        print()
        
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
