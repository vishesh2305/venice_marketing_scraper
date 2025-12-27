# 🎯 Venice AI Marketing Scraper - 5 Intelligent Agents

A powerful marketing data scraping system powered by **Venice AI** with 5 specialized AI agents working together to find, analyze, and export professional profiles.

![Architecture](https://img.shields.io/badge/Architecture-Multi--Agent-blue)
![AI](https://img.shields.io/badge/AI-Venice%20AI-purple)
![License](https://img.shields.io/badge/License-MIT-green)

## 🌟 Features

- **5 Specialized AI Agents** working in concert
- **Venice AI Integration** - Privacy-first, uncensored models
- **Real-time Progress** via WebSocket
- **Professional Excel Export** with lead scoring & segmentation
- **Beautiful Web UI** - Modern React interface
- **CLI Mode** for automation/scripting

---

## 🤖 The 5 Intelligent Agents

| # | Agent | Purpose | Venice Model |
|---|-------|---------|--------------|
| 🔑 | **Keyword Intelligence** | Expands queries into comprehensive keyword sets | `zai-org-glm-4.6` |
| 🌐 | **Domain Scanner** | Analyzes websites & creates scraping strategies | `llama-3.3-70b` |
| 🎯 | **Profile Hunter** | Searches web & discovers matching profiles | `qwen3-235b` |
| 📊 | **Data Enrichment** | Enhances profiles with scores & additional data | `zai-org-glm-4.6` |
| 📤 | **Export Master** | Compiles data & creates formatted exports | `llama-3.3-70b` |

---

## 🚀 Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Venice AI API Key

```bash
export VENICE_API_KEY="your-api-key-here"
```

Get your API key at: https://venice.ai/settings/api

### 3. Run the Application

**Web UI (Recommended):**
```bash
python main.py --server
```
Then open: http://localhost:5000

**CLI Mode:**
```bash
python main.py --target "Marketing managers in SaaS" --domains linkedin.com
```

**Interactive Mode:**
```bash
python main.py --interactive
```

---

## 📖 Usage Examples

### Web UI

1. Open http://localhost:5000
2. Enter target profile description
3. Specify domains to scrape
4. Click "Start Scraping with 5 Agents"
5. Watch real-time progress
6. Export results to Excel/CSV

### CLI Examples

```bash
# Basic scrape
python main.py --target "CTOs at AI startups" --domains linkedin.com

# Multiple domains with max results
python main.py -t "Product Managers" -d linkedin.com twitter.com --max 100

# Custom output file
python main.py -t "Founders" -d linkedin.com -o founders_2024.xlsx

# Using CSV output
python main.py -t "Engineers" -d github.com -o engineers.csv
```

### API Usage

```bash
# Start a scrape job
curl -X POST http://localhost:5000/api/scrape \
  -H "Content-Type: application/json" \
  -d '{
    "target_profile": "Marketing managers in tech",
    "domains": ["linkedin.com"],
    "max_results": 50,
    "user_type": "Decision Makers"
  }'

# Check job status
curl http://localhost:5000/api/jobs/{job_id}

# Export results
curl -X POST http://localhost:5000/api/jobs/{job_id}/export \
  -H "Content-Type: application/json" \
  -d '{"format": "excel"}' \
  -o leads.xlsx
```

---

## 📊 Output Format

### Excel Export Contains:

1. **All Leads** - Complete profile list with all data
2. **🔥 Hot Leads** - High-priority prospects (score ≥70)
3. **📊 Statistics** - Summary metrics & charts
4. **🎯 Segments** - Categorized lead lists

### Profile Data Includes:

| Field | Description |
|-------|-------------|
| Name | Full name |
| Title | Job title |
| Company | Organization |
| Email | Contact email (found/inferred) |
| Phone | Phone number |
| LinkedIn | Profile URL |
| Bio | Professional summary |
| Lead Score | 0-100 quality score |
| Category | hot/warm/cold |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER INPUT                                │
│         "Marketing managers at SaaS companies"               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│     🔑 AGENT 1: KEYWORD INTELLIGENCE                        │
│     Model: zai-org-glm-4.6 (128k context)                   │
│     ───────────────────────────────────────                 │
│     INPUT:  "Marketing managers at SaaS"                    │
│     OUTPUT: {                                               │
│       primary_keywords: ["marketing manager", "SaaS"...],   │
│       job_titles: ["Head of Marketing", "CMO"...],          │
│       skills: ["digital marketing", "B2B"...],              │
│       ...200+ keyword variations                            │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│     🌐 AGENT 2: DOMAIN SCANNER                              │
│     Model: llama-3.3-70b (fast inference)                   │
│     ───────────────────────────────────────                 │
│     INPUT:  linkedin.com + keywords                         │
│     OUTPUT: {                                               │
│       profile_patterns: ["/in/{username}"],                 │
│       search_urls: ["linkedin.com/search?..."],             │
│       data_selectors: {name: ".top-card h1"...},            │
│       scraping_strategy: "optimal approach"                 │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│     🎯 AGENT 3: PROFILE HUNTER                              │
│     Model: qwen3-235b + Web Search                          │
│     ───────────────────────────────────────                 │
│     INPUT:  Keywords + Strategy                             │
│     OUTPUT: {                                               │
│       profiles_found: [                                     │
│         {name: "Jane Smith", title: "CMO"...},              │
│         {name: "John Doe", title: "Marketing VP"...}        │
│       ],                                                    │
│       total_found: 50                                       │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│     📊 AGENT 4: DATA ENRICHMENT                             │
│     Model: zai-org-glm-4.6 (reasoning)                      │
│     ───────────────────────────────────────                 │
│     INPUT:  Raw profiles                                    │
│     OUTPUT: {                                               │
│       enriched_profiles: [                                  │
│         {..., inferred_email: "jane@company.com",           │
│          lead_score: 85, category: "hot"...}                │
│       ],                                                    │
│       high_quality_leads: 15                                │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│     📤 AGENT 5: EXPORT MASTER                               │
│     Model: llama-3.3-70b (data processing)                  │
│     ───────────────────────────────────────                 │
│     INPUT:  Enriched profiles                               │
│     OUTPUT: {                                               │
│       export_ready_data: [...formatted profiles],           │
│       segments: {hot: [...], warm: [...], cold: [...]},     │
│       statistics: {total: 50, emails: 40, hot: 15...}       │
│     }                                                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     EXCEL EXPORT                             │
│     📄 marketing_leads_20240115_143022.xlsx                 │
│     ─────────────────────────────────────                   │
│     Sheet 1: All Leads (50 profiles)                        │
│     Sheet 2: 🔥 Hot Leads (15 priority contacts)            │
│     Sheet 3: 📊 Statistics (charts & metrics)               │
│     Sheet 4: 🎯 Segments (categorized lists)                │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
marketing_scraper/
├── agents/
│   ├── __init__.py
│   ├── venice_client.py      # Venice AI wrapper
│   └── marketing_agents.py   # 5 AI agents + orchestrator
├── utils/
│   ├── __init__.py
│   ├── scraper.py           # Async web scraping
│   └── excel_export.py      # Excel/CSV export
├── server/
│   ├── app.py               # Flask API server
│   └── static/
│       └── index.html       # React UI
├── exports/                  # Output directory
├── main.py                  # Main launcher
├── requirements.txt
└── README.md
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `VENICE_API_KEY` | Your Venice AI API key | Yes* |

*System runs in demo mode without API key

### Venice AI Models Used

| Model | Use Case | Context |
|-------|----------|---------|
| `zai-org-glm-4.6` | Deep reasoning, analysis | 128k |
| `llama-3.3-70b` | Fast inference | 128k |
| `qwen3-235b` | Tool calling, web search | 128k |
| `venice-uncensored` | Unfiltered generation | - |

---

## 🔒 Ethical Usage

This tool is designed for **legitimate marketing research**:

- ✅ Finding potential business contacts
- ✅ Market research and analysis
- ✅ Lead generation for sales teams
- ✅ Competitive intelligence

**Please ensure:**

- Compliance with GDPR, CCPA, and other privacy laws
- Respect for website terms of service
- Proper rate limiting and polite crawling
- Legal use of collected data

---

## 🛠️ Development

### Run in Development Mode

```bash
# Install dev dependencies
pip install -r requirements.txt

# Run with auto-reload
python main.py --server
```

### Testing Individual Agents

```python
from agents import VeniceClient, KeywordIntelligenceAgent

client = VeniceClient(api_key="your-key")
keyword_agent = KeywordIntelligenceAgent(client)

result = keyword_agent.expand_keywords("Marketing managers")
print(result)
```

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- [Venice AI](https://venice.ai) - Privacy-first AI platform
- [OpenAI](https://openai.com) - Compatible API format
- Flask & React communities

---

**Made with 💜 using Venice AI - The AI platform that doesn't spy on you**
