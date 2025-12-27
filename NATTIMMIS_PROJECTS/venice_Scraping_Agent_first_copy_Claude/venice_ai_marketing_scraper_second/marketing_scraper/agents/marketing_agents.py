"""
5 Intelligent Marketing Scraper Agents
Each agent specializes in a specific task in the data collection pipeline
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import json
import re
from .venice_client import VeniceClient, AgentConfig, AgentBase


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 1: KEYWORD INTELLIGENCE AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class KeywordIntelligenceAgent(AgentBase):
    """
    🔑 Agent 1: Keyword Intelligence Agent
    
    PURPOSE: Expands user queries into comprehensive keyword sets
    - Generates synonyms, related terms, industry jargon
    - Creates search combinations for maximum coverage
    - Understands context (B2B, B2C, industry-specific)
    """
    
    def __init__(self, client: VeniceClient):
        config = AgentConfig(
            name="KeywordIntelligence",
            model="zai-org-glm-4.6",  # Deep reasoning for keyword expansion
            system_prompt="""You are an expert Keyword Intelligence Agent specializing in marketing research.

Your job is to take a user's target profile description and generate COMPREHENSIVE keyword sets for scraping.

OUTPUT FORMAT (JSON only, no markdown):
{
    "primary_keywords": ["exact terms to search"],
    "secondary_keywords": ["related/broader terms"],
    "job_titles": ["specific titles to target"],
    "industries": ["relevant industries"],
    "skills": ["skills these people have"],
    "seniority_levels": ["Junior", "Senior", "Director", etc],
    "company_types": ["startup", "enterprise", etc],
    "search_combinations": ["keyword + keyword combinations"],
    "exclusion_terms": ["terms to filter OUT"],
    "geographic_hints": ["location-related terms if any"]
}

Be EXHAUSTIVE. Think of every possible variation, abbreviation, alternate spelling.
For job titles: include both formal and informal versions.
Always return VALID JSON only.""",
            temperature=0.8,
            max_tokens=4096
        )
        super().__init__(client, config)
        
    def expand_keywords(self, user_query: str, target_domain: str = "") -> Dict[str, List[str]]:
        """
        Takes user input and generates comprehensive keyword expansion
        """
        prompt = f"""
        User Target Profile: {user_query}
        Target Domain/Platform: {target_domain}
        
        Generate an exhaustive keyword expansion for scraping marketing leads.
        Consider: job titles, skills, industries, seniority, company types.
        Return ONLY valid JSON.
        """
        
        response = self.think(prompt)
        
        try:
            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
            
        # Fallback: structured extraction
        return {
            "primary_keywords": [user_query],
            "secondary_keywords": [],
            "job_titles": [],
            "industries": [],
            "skills": [],
            "seniority_levels": [],
            "company_types": [],
            "search_combinations": [],
            "exclusion_terms": [],
            "geographic_hints": []
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 2: DOMAIN SCANNER AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class DomainScannerAgent(AgentBase):
    """
    🌐 Agent 2: Domain Scanner Agent
    
    PURPOSE: Analyzes target domains and creates scraping strategies
    - Identifies profile URL patterns
    - Detects pagination structures
    - Maps data locations on pages
    - Creates domain-specific scraping blueprints
    """
    
    def __init__(self, client: VeniceClient):
        config = AgentConfig(
            name="DomainScanner",
            model="llama-3.3-70b",  # Fast analysis
            system_prompt="""You are an expert Domain Scanner Agent for web scraping.

Your job is to analyze target websites and create scraping strategies.

For each domain, you identify:
1. Profile URL patterns (e.g., /user/{username}, /people/{id})
2. Search functionality patterns
3. Pagination mechanisms
4. Data locations (CSS selectors, XPath patterns)
5. Rate limiting considerations
6. Best scraping approaches

OUTPUT FORMAT (JSON only):
{
    "domain": "example.com",
    "profile_patterns": ["/users/{id}", "/profile/{username}"],
    "search_urls": ["https://example.com/search?q={keyword}"],
    "pagination": {"type": "page_number|cursor|infinite_scroll", "pattern": "?page={n}"},
    "data_selectors": {
        "name": "css:.profile-name | xpath://h1[@class='name']",
        "bio": "css:.bio-text",
        "company": "css:.company-name",
        "email": "css:a[href^='mailto:']",
        "linkedin": "css:a[href*='linkedin.com']"
    },
    "rate_limit": {"requests_per_minute": 10, "delay_seconds": 3},
    "scraping_strategy": "description of best approach"
}

Return ONLY valid JSON.""",
            temperature=0.3,  # More deterministic for technical analysis
            max_tokens=4096
        )
        super().__init__(client, config)
        
    def analyze_domain(self, domain: str, sample_html: str = "") -> Dict[str, Any]:
        """
        Analyzes a domain and returns scraping strategy
        """
        prompt = f"""
        Analyze this domain for scraping:
        Domain: {domain}
        
        {f'Sample HTML structure: {sample_html[:2000]}' if sample_html else 'No sample HTML provided - use common patterns for this type of site.'}
        
        Create a complete scraping strategy. Return ONLY valid JSON.
        """
        
        response = self.think(prompt)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
            
        return self._default_strategy(domain)
    
    def _default_strategy(self, domain: str) -> Dict[str, Any]:
        """Generate default scraping strategy"""
        return {
            "domain": domain,
            "profile_patterns": [f"/{domain}/users/{{id}}"],
            "search_urls": [f"https://{domain}/search?q={{keyword}}"],
            "pagination": {"type": "page_number", "pattern": "?page={n}"},
            "data_selectors": {
                "name": "css:h1, .name, .profile-name",
                "bio": "css:.bio, .about, .description",
                "company": "css:.company, .organization",
                "email": "css:a[href^='mailto:']",
                "linkedin": "css:a[href*='linkedin.com']"
            },
            "rate_limit": {"requests_per_minute": 10, "delay_seconds": 3},
            "scraping_strategy": "Standard crawling with respectful delays"
        }


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 3: PROFILE HUNTER AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class ProfileHunterAgent(AgentBase):
    """
    🎯 Agent 3: Profile Hunter Agent
    
    PURPOSE: Actively searches and discovers profiles using keywords
    - Constructs optimal search queries
    - Uses Venice AI's web search for real-time discovery
    - Filters and validates discovered profiles
    - Handles multiple platforms simultaneously
    """
    
    def __init__(self, client: VeniceClient):
        config = AgentConfig(
            name="ProfileHunter",
            model="qwen3-235b",  # Best for web search tasks
            system_prompt="""You are an expert Profile Hunter Agent for marketing lead generation.

Your job is to SEARCH the web and FIND real profiles matching criteria.

When searching:
1. Construct precise search queries
2. Look for professional profiles (LinkedIn, company pages, directories)
3. Extract: Name, Title, Company, Bio, Contact info
4. Validate that profiles match the target criteria

OUTPUT FORMAT (JSON array):
{
    "profiles_found": [
        {
            "name": "Full Name",
            "title": "Job Title",
            "company": "Company Name",
            "bio": "Professional summary",
            "email": "email@company.com or null",
            "phone": "phone or null",
            "linkedin": "LinkedIn URL or null",
            "source_url": "where found",
            "confidence_score": 0.0-1.0,
            "relevance_notes": "why this profile matches"
        }
    ],
    "search_queries_used": ["query1", "query2"],
    "total_found": 10,
    "pages_searched": 5
}

IMPORTANT: Only include REAL profiles with verifiable data.
Return ONLY valid JSON.""",
            temperature=0.5,
            max_tokens=8192
        )
        super().__init__(client, config)
        
    def hunt_profiles(
        self,
        keywords: Dict[str, List[str]],
        domain: str,
        max_results: int = 50
    ) -> Dict[str, Any]:
        """
        Searches for profiles using expanded keywords and web search
        """
        # Construct search queries
        search_queries = self._build_search_queries(keywords, domain)
        
        prompt = f"""
        MISSION: Find {max_results} professional profiles matching these criteria:
        
        Keywords: {json.dumps(keywords, indent=2)}
        Target Domain/Platform: {domain}
        
        Search queries to use:
        {json.dumps(search_queries[:10], indent=2)}
        
        Search the web NOW and return discovered profiles.
        Focus on: Name, Title, Company, Bio, Contact info.
        Return ONLY valid JSON with profiles_found array.
        """
        
        # Use web search enabled model
        response = self.client.with_web_search(prompt, model="llama-3.3-70b")
        content = response.get("content", "")
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
            
        return {
            "profiles_found": [],
            "search_queries_used": search_queries,
            "total_found": 0,
            "pages_searched": 0
        }
    
    def _build_search_queries(self, keywords: Dict, domain: str) -> List[str]:
        """Build optimized search queries"""
        queries = []
        
        primary = keywords.get("primary_keywords", [])
        titles = keywords.get("job_titles", [])
        
        # Combine for LinkedIn-style searches
        for kw in primary[:3]:
            queries.append(f'site:{domain} "{kw}"')
            for title in titles[:3]:
                queries.append(f'site:{domain} "{kw}" "{title}"')
                
        return queries[:20]


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 4: DATA ENRICHMENT AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class DataEnrichmentAgent(AgentBase):
    """
    📊 Agent 4: Data Enrichment Agent
    
    PURPOSE: Enriches discovered profiles with additional data
    - Finds missing contact information
    - Validates email addresses
    - Discovers social profiles
    - Adds company information
    - Calculates lead scores
    """
    
    def __init__(self, client: VeniceClient):
        config = AgentConfig(
            name="DataEnrichment",
            model="zai-org-glm-4.6",  # Deep reasoning for data analysis
            system_prompt="""You are an expert Data Enrichment Agent for B2B marketing.

Your job is to ENRICH profile data with additional information:

1. VALIDATE: Check if data looks legitimate
2. ENRICH: Add missing fields where possible
3. SCORE: Calculate lead quality score
4. CATEGORIZE: Assign lead categories

For each profile, you:
- Infer email patterns from company domain (e.g., firstname.lastname@company.com)
- Estimate company size from available signals
- Determine decision-making authority
- Calculate engagement potential

OUTPUT FORMAT (JSON):
{
    "enriched_profiles": [
        {
            ...original_profile_data,
            "inferred_email": "email pattern guess",
            "email_confidence": 0.0-1.0,
            "company_size": "1-50|51-200|201-500|500+",
            "decision_maker_score": 0.0-1.0,
            "lead_score": 0-100,
            "lead_category": "hot|warm|cold",
            "enrichment_notes": "what was added/inferred"
        }
    ],
    "enrichment_summary": {
        "profiles_enriched": 10,
        "emails_inferred": 5,
        "high_quality_leads": 3
    }
}

Return ONLY valid JSON.""",
            temperature=0.4,
            max_tokens=8192
        )
        super().__init__(client, config)
        
    def enrich_profiles(self, profiles: List[Dict]) -> Dict[str, Any]:
        """
        Enriches a batch of profiles with additional data
        """
        if not profiles:
            return {
                "enriched_profiles": [],
                "enrichment_summary": {
                    "profiles_enriched": 0,
                    "emails_inferred": 0,
                    "high_quality_leads": 0
                }
            }
            
        prompt = f"""
        MISSION: Enrich these {len(profiles)} profiles with additional marketing data.
        
        Profiles to enrich:
        {json.dumps(profiles[:20], indent=2)}
        
        For each profile:
        1. Infer email if missing (using company domain patterns)
        2. Estimate company size
        3. Score decision-making authority
        4. Calculate overall lead score (0-100)
        5. Categorize as hot/warm/cold lead
        
        Return ONLY valid JSON with enriched_profiles array.
        """
        
        response = self.think(prompt)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
            
        # Fallback: basic enrichment
        return self._basic_enrichment(profiles)
    
    def _basic_enrichment(self, profiles: List[Dict]) -> Dict[str, Any]:
        """Fallback basic enrichment"""
        enriched = []
        for p in profiles:
            enriched.append({
                **p,
                "inferred_email": self._infer_email(p),
                "email_confidence": 0.5,
                "company_size": "unknown",
                "decision_maker_score": 0.5,
                "lead_score": 50,
                "lead_category": "warm",
                "enrichment_notes": "Basic enrichment applied"
            })
            
        return {
            "enriched_profiles": enriched,
            "enrichment_summary": {
                "profiles_enriched": len(enriched),
                "emails_inferred": sum(1 for p in enriched if p.get("inferred_email")),
                "high_quality_leads": sum(1 for p in enriched if p.get("lead_score", 0) >= 70)
            }
        }
    
    def _infer_email(self, profile: Dict) -> Optional[str]:
        """Basic email inference"""
        name = profile.get("name", "").lower().split()
        company = profile.get("company", "").lower().replace(" ", "")
        
        if len(name) >= 2 and company:
            return f"{name[0]}.{name[-1]}@{company}.com"
        return None


# ═══════════════════════════════════════════════════════════════════════════════
# AGENT 5: EXPORT MASTER AGENT
# ═══════════════════════════════════════════════════════════════════════════════

class ExportMasterAgent(AgentBase):
    """
    📤 Agent 5: Export Master Agent
    
    PURPOSE: Compiles and exports data in various formats
    - Creates Excel/CSV exports
    - Generates summary reports
    - Formats data for CRM import
    - Creates segmented lists
    """
    
    def __init__(self, client: VeniceClient):
        config = AgentConfig(
            name="ExportMaster",
            model="llama-3.3-70b",  # Fast for data processing
            system_prompt="""You are an expert Export Master Agent for marketing data.

Your job is to:
1. Format scraped data for export
2. Create segmented lists (by score, category, etc.)
3. Generate summary statistics
4. Prepare data for CRM import

OUTPUT FORMAT (JSON):
{
    "export_ready_data": [
        {
            "name": "Full Name",
            "title": "Job Title",
            "company": "Company Name",
            "email": "email@company.com",
            "phone": "phone",
            "linkedin": "LinkedIn URL",
            "bio": "Professional summary",
            "lead_score": 85,
            "lead_category": "hot",
            "source": "LinkedIn",
            "scraped_date": "2024-01-15"
        }
    ],
    "segments": {
        "hot_leads": [array of names],
        "warm_leads": [array of names],
        "cold_leads": [array of names],
        "decision_makers": [array of names]
    },
    "statistics": {
        "total_profiles": 100,
        "with_email": 75,
        "with_phone": 30,
        "hot_leads_count": 15,
        "average_lead_score": 65
    },
    "export_formats_available": ["excel", "csv", "json", "crm"]
}

Return ONLY valid JSON.""",
            temperature=0.2,  # Very deterministic for data processing
            max_tokens=8192
        )
        super().__init__(client, config)
        
    def prepare_export(
        self,
        enriched_data: Dict[str, Any],
        format_type: str = "excel"
    ) -> Dict[str, Any]:
        """
        Prepares data for export in specified format
        """
        profiles = enriched_data.get("enriched_profiles", [])
        
        prompt = f"""
        MISSION: Prepare {len(profiles)} profiles for {format_type} export.
        
        Data to export:
        {json.dumps(profiles[:20], indent=2)}
        
        Tasks:
        1. Clean and standardize all fields
        2. Create segments (hot/warm/cold, decision-makers)
        3. Calculate statistics
        4. Format for {format_type} export
        
        Return ONLY valid JSON with export_ready_data array.
        """
        
        response = self.think(prompt)
        
        try:
            json_match = re.search(r'\{[\s\S]*\}', response)
            if json_match:
                return json.loads(json_match.group())
        except json.JSONDecodeError:
            pass
            
        # Fallback: direct formatting
        return self._format_export(profiles)
    
    def _format_export(self, profiles: List[Dict]) -> Dict[str, Any]:
        """Direct export formatting"""
        from datetime import datetime
        
        hot_leads = [p.get("name") for p in profiles if p.get("lead_category") == "hot"]
        warm_leads = [p.get("name") for p in profiles if p.get("lead_category") == "warm"]
        cold_leads = [p.get("name") for p in profiles if p.get("lead_category") == "cold"]
        
        return {
            "export_ready_data": [
                {
                    "name": p.get("name", ""),
                    "title": p.get("title", ""),
                    "company": p.get("company", ""),
                    "email": p.get("email") or p.get("inferred_email", ""),
                    "phone": p.get("phone", ""),
                    "linkedin": p.get("linkedin", ""),
                    "bio": p.get("bio", "")[:200] if p.get("bio") else "",
                    "lead_score": p.get("lead_score", 50),
                    "lead_category": p.get("lead_category", "warm"),
                    "source": p.get("source_url", ""),
                    "scraped_date": datetime.now().strftime("%Y-%m-%d")
                }
                for p in profiles
            ],
            "segments": {
                "hot_leads": hot_leads,
                "warm_leads": warm_leads,
                "cold_leads": cold_leads,
                "decision_makers": [
                    p.get("name") for p in profiles 
                    if p.get("decision_maker_score", 0) >= 0.7
                ]
            },
            "statistics": {
                "total_profiles": len(profiles),
                "with_email": sum(1 for p in profiles if p.get("email") or p.get("inferred_email")),
                "with_phone": sum(1 for p in profiles if p.get("phone")),
                "hot_leads_count": len(hot_leads),
                "average_lead_score": sum(p.get("lead_score", 50) for p in profiles) // max(len(profiles), 1)
            },
            "export_formats_available": ["excel", "csv", "json", "crm"]
        }


# ═══════════════════════════════════════════════════════════════════════════════
# ORCHESTRATOR: COORDINATES ALL 5 AGENTS
# ═══════════════════════════════════════════════════════════════════════════════

class MarketingScraperOrchestrator:
    """
    🎭 Master Orchestrator
    
    Coordinates all 5 agents in the scraping pipeline:
    1. KeywordIntelligence → Expands search terms
    2. DomainScanner → Analyzes target sites
    3. ProfileHunter → Finds profiles
    4. DataEnrichment → Enhances data
    5. ExportMaster → Prepares exports
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.client = VeniceClient(api_key)
        
        # Initialize all 5 agents
        self.keyword_agent = KeywordIntelligenceAgent(self.client)
        self.domain_agent = DomainScannerAgent(self.client)
        self.hunter_agent = ProfileHunterAgent(self.client)
        self.enrichment_agent = DataEnrichmentAgent(self.client)
        self.export_agent = ExportMasterAgent(self.client)
        
        self.pipeline_state = {}
        
    def run_pipeline(
        self,
        target_profile: str,
        domains: List[str],
        max_results: int = 50,
        callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Run the complete scraping pipeline
        
        Args:
            target_profile: Description of profiles to find
            domains: List of domains to scrape
            max_results: Maximum profiles to find
            callback: Optional progress callback function
        """
        results = {
            "status": "running",
            "stages": {},
            "final_data": None,
            "errors": []
        }
        
        def update(stage: str, data: Any):
            results["stages"][stage] = data
            if callback:
                callback(stage, data)
                
        try:
            # Stage 1: Keyword Expansion
            update("keywords", {"status": "running"})
            keywords = self.keyword_agent.expand_keywords(target_profile, domains[0] if domains else "")
            update("keywords", {"status": "complete", "data": keywords})
            
            # Stage 2: Domain Analysis
            domain_strategies = {}
            for domain in domains:
                update(f"domain_{domain}", {"status": "running"})
                strategy = self.domain_agent.analyze_domain(domain)
                domain_strategies[domain] = strategy
                update(f"domain_{domain}", {"status": "complete", "data": strategy})
                
            # Stage 3: Profile Hunting
            all_profiles = []
            for domain in domains:
                update(f"hunt_{domain}", {"status": "running"})
                hunt_result = self.hunter_agent.hunt_profiles(
                    keywords, 
                    domain, 
                    max_results // len(domains)
                )
                all_profiles.extend(hunt_result.get("profiles_found", []))
                update(f"hunt_{domain}", {"status": "complete", "data": hunt_result})
                
            # Stage 4: Data Enrichment
            update("enrichment", {"status": "running"})
            enriched = self.enrichment_agent.enrich_profiles(all_profiles)
            update("enrichment", {"status": "complete", "data": enriched})
            
            # Stage 5: Export Preparation
            update("export", {"status": "running"})
            export_data = self.export_agent.prepare_export(enriched, "excel")
            update("export", {"status": "complete", "data": export_data})
            
            results["status"] = "complete"
            results["final_data"] = export_data
            
        except Exception as e:
            results["status"] = "error"
            results["errors"].append(str(e))
            
        return results
