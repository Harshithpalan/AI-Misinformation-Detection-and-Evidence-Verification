from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import requests
from bs4 import BeautifulSoup
import httpx
import re
from typing import List, Optional
import json

app = FastAPI(title="AI Misinformation Detection and Evidence Verification")

# Configuration
OLLAMA_BASE_URL = "http://localhost:11434"
MODEL_NAME = "llama2"  # Can be changed to other models like mistral, etc.

class TextAnalysisRequest(BaseModel):
    text: str
    model: Optional[str] = MODEL_NAME

class URLCheckRequest(BaseModel):
    url: str

class EvidenceExtractionRequest(BaseModel):
    text: str
    model: Optional[str] = MODEL_NAME

class AnalysisResponse(BaseModel):
    status: str
    result: dict
    confidence: float
    explanation: str

class URLCheckResponse(BaseModel):
    url: str
    is_accessible: bool
    credibility_score: float
    domain_info: dict
    security_flags: List[str]

def check_ollama_available():
    """Check if Ollama is running"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=2)
        return response.status_code == 200
    except:
        return False

def query_ollama(prompt: str, model: str = MODEL_NAME) -> str:
    """Query local LLM via Ollama"""
    try:
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        response.raise_for_status()
        return response.json().get("response", "")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM query failed: {str(e)}")

def analyze_misinformation(text: str, model: str = MODEL_NAME) -> dict:
    """Analyze text for potential misinformation using local LLM"""
    prompt = f"""Analyze the following text for potential misinformation. Provide:
1. A verdict (MISINFORMATION/POTENTIALLY MISLEADING/LIKELY TRUE/UNCERTAIN)
2. A confidence score (0-100)
3. Key claims identified
4. Evidence or reasoning for your verdict

Text: {text}

Respond in JSON format:
{{
    "verdict": "VERDICT",
    "confidence": 0-100,
    "claims": ["claim1", "claim2"],
    "reasoning": "explanation"
}}"""
    
    response = query_ollama(prompt, model)
    
    # Try to extract JSON from response
    try:
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    
    # Fallback if JSON parsing fails
    return {
        "verdict": "UNCERTAIN",
        "confidence": 50,
        "claims": [],
        "reasoning": response
    }

def extract_evidence(text: str, model: str = MODEL_NAME) -> dict:
    """Extract supporting evidence from text"""
    prompt = f"""Extract evidence and supporting claims from the following text. Identify:
1. Factual statements that can be verified
2. Sources or references mentioned
3. Statistics or data points
4. Logical arguments presented

Text: {text}

Respond in JSON format:
{{
    "factual_statements": ["statement1", "statement2"],
    "sources_mentioned": ["source1", "source2"],
    "statistics": ["stat1", "stat2"],
    "arguments": ["argument1", "argument2"],
    "verifiability_score": 0-100
}}"""
    
    response = query_ollama(prompt, model)
    
    try:
        json_match = re.search(r'\{[^}]+\}', response, re.DOTALL)
        if json_match:
            return json.loads(json_match.group())
    except:
        pass
    
    return {
        "factual_statements": [],
        "sources_mentioned": [],
        "statistics": [],
        "arguments": [],
        "verifiability_score": 50,
        "raw_response": response
    }

def check_url_credibility(url: str) -> dict:
    """Check URL credibility and accessibility"""
    result = {
        "url": url,
        "is_accessible": False,
        "credibility_score": 0,
        "domain_info": {},
        "security_flags": []
    }
    
    try:
        # Extract domain
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        
        result["domain_info"] = {
            "domain": domain,
            "scheme": parsed.scheme,
            "path": parsed.path
        }
        
        # Check accessibility
        try:
            response = requests.get(url, timeout=10, allow_redirects=True)
            result["is_accessible"] = response.status_code == 200
            
            # Basic credibility heuristics
            score = 50  # Base score
            
            # HTTPS bonus
            if parsed.scheme == "https":
                score += 20
                result["security_flags"].append("HTTPS_ENABLED")
            else:
                result["security_flags"].append("HTTP_ONLY")
            
            # Check for suspicious patterns
            suspicious_patterns = [
                r'bit\.ly', r'tinyurl', r'goo\.gl',  # URL shorteners
                r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}',  # IP addresses
                r'free|win|prize|click|verify|account',  # Suspicious keywords
            ]
            
            for pattern in suspicious_patterns:
                if re.search(pattern, url, re.IGNORECASE):
                    score -= 10
                    result["security_flags"].append(f"SUSPICIOUS_PATTERN: {pattern}")
            
            # Domain length check
            if len(domain) > 50:
                score -= 10
                result["security_flags"].append("LONG_DOMAIN")
            
            # Subdomain count
            subdomain_count = domain.count('.')
            if subdomain_count > 3:
                score -= 5
                result["security_flags"].append("MANY_SUBDOMAINS")
            
            result["credibility_score"] = max(0, min(100, score))
            
        except Exception as e:
            result["security_flags"].append(f"ACCESS_ERROR: {str(e)}")
            
    except Exception as e:
        result["security_flags"].append(f"PARSE_ERROR: {str(e)}")
    
    return result

@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the frontend"""
    with open("index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    ollama_available = check_ollama_available()
    return {
        "status": "healthy",
        "ollama_available": ollama_available,
        "ollama_url": OLLAMA_BASE_URL
    }

@app.post("/api/analyze", response_model=AnalysisResponse)
async def analyze_text(request: TextAnalysisRequest):
    """Analyze text for misinformation"""
    if not check_ollama_available():
        raise HTTPException(
            status_code=503, 
            detail="Ollama is not running. Please start Ollama first."
        )
    
    result = analyze_misinformation(request.text, request.model)
    
    return AnalysisResponse(
        status="success",
        result=result,
        confidence=result.get("confidence", 50),
        explanation=result.get("reasoning", "")
    )

@app.post("/api/extract-evidence", response_model=AnalysisResponse)
async def extract_evidence_endpoint(request: EvidenceExtractionRequest):
    """Extract evidence from text"""
    if not check_ollama_available():
        raise HTTPException(
            status_code=503,
            detail="Ollama is not running. Please start Ollama first."
        )
    
    result = extract_evidence(request.text, request.model)
    
    return AnalysisResponse(
        status="success",
        result=result,
        confidence=result.get("verifiability_score", 50),
        explanation=f"Extracted {len(result.get('factual_statements', []))} factual statements"
    )

@app.post("/api/check-url", response_model=URLCheckResponse)
async def check_url(request: URLCheckRequest):
    """Check URL credibility"""
    result = check_url_credibility(request.url)
    return URLCheckResponse(**result)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
