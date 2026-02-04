# document_wizard/app.py - DOCUMENT WIZARD
from fastapi import FastAPI, Query, Form, UploadFile, Request, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from dotenv import load_dotenv
from typing import Dict
import uvicorn
import requests
#import aiofiles
import asyncio
import uuid
import time
import re
import sys
import os

load_dotenv()

templates = Jinja2Templates(directory="templates")

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Simple in-memory storage for background processing
analysis_queue: Dict[str, Dict] = {}

# For tracking user tokens (simplified version)
user_tokens: Dict[str, int] = {}  # user_email -> token_count

# This tells Python to look in root folder
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Now this imports from ROOT layout.py
from layout import layout

app = FastAPI()
DEEPSEEK_KEY = ""



# Add this debug endpoint to see the full layout
@app.get("/debug-layout")
async def debug_layout():
    # Show what layout() produces with minimal content
    test_content = "<h1>Test</h1>"
    full_html = layout("Test", test_content)
    
    # Return first 2000 chars to see navbar
    return HTMLResponse(f"<pre>{full_html[:2000]}</pre>")



# ========== DASHBOARD ==========
@app.get("/")
async def home():
    content = '''
    <div style="text-align: center; padding: 4rem 0;">
        <h1 style="color: var(--primary);">
            <i class="fas fa-file-contract"></i><br>
            Document Decoder
        </h1>
        <p style="font-size: 1.25rem; color: #6b7280; max-width: 600px; margin: 1rem auto;">
            AI-powered translation of complex documents. Understand legal, medical, and technical language in plain English.
        </p>
        
        <div style="margin: 3rem 0;">
            <a href="wizard" role="button" style="padding: 1rem 2.5rem; font-size: 1.25rem;">
                <i class="fas fa-magic"></i> Decode a Document
            </a>
        </div>
        
        <div class="card-grid">
            <div class="step-card">
                <i class="fas fa-gavel"></i>
                <h3>Legal Documents</h3>
                <p>Contracts, leases, terms of service</p>
            </div>
            
            <div class="step-card">
                <i class="fas fa-heart-pulse"></i>
                <h3>Medical Papers</h3>
                <p>Reports, prescriptions, instructions</p>
            </div>
            
            <div class="step-card">
                <i class="fas fa-file-signature"></i>
                <h3>Contracts</h3>
                <p>Employment, service, rental agreements</p>
            </div>
            
            <div class="step-card">
                <i class="fas fa-warning"></i>
                <h3>Warning Labels</h3>
                <p>Safety instructions, disclaimers</p>
            </div>
            
            <div class="step-card">
                <i class="fas fa-graduation-cap"></i>
                <h3>Academic Papers</h3>
                <p>Research, studies, technical docs</p>
            </div>
            
            <div class="step-card">
                <i class="fas fa-building"></i>
                <h3>Government Forms</h3>
                <p>Applications, permits, official docs</p>
            </div>
        </div>
        
        <div class="warning-box" style="max-width: 600px; margin: 3rem auto;">
            <h3 style="color: #d97706; margin-top: 0;">
                <i class="fas fa-exclamation-triangle"></i> Important Notice
            </h3>
            <p style="margin-bottom: 0;">
                This tool provides AI-assisted interpretation for educational purposes only. 
                For legal, medical, or financial decisions, always consult a qualified professional.
            </p>
        </div>
    </div>
    '''
    return HTMLResponse(layout("Home", content))

# ========== STEP 1: DOCUMENT TYPE ==========
@app.get("/wizard")
async def step1():
    content = '''
    <div style="max-width: 800px; margin: 0 auto;">
        <div class="steps">
            <div class="step active">1</div>
            <div class="step">2</div>
            <div class="step">3</div>
            <div class="step">4</div>
        </div>
        
        <h1 style="text-align: center; color: var(--primary);">Step 1: Document Type</h1>
        <p style="text-align: center; color: #6b7280;">
            What type of document are you trying to understand?
        </p>
        
        <div class="card-grid">
            <a href="/wizard/step2?doc_type=legal" class="step-card">
                <i class="fas fa-gavel"></i>
                <h3>Legal Document</h3>
                <p>Contract, lease, terms of service, agreement</p>
            </a>
            
            <a href="/wizard/step2?doc_type=medical" class="step-card">
                <i class="fas fa-heart-pulse"></i>
                <h3>Medical Document</h3>
                <p>Report, prescription, diagnosis, instructions</p>
            </a>
            
            <a href="/wizard/step2?doc_type=contract" class="step-card">
                <i class="fas fa-file-signature"></i>
                <h3>Contract/Agreement</h3>
                <p>Employment, service, rental, purchase agreement</p>
            </a>
            
            <a href="/wizard/step2?doc_type=financial" class="step-card">
                <i class="fas fa-money-bill-wave"></i>
                <h3>Financial Document</h3>
                <p>Loan terms, investment, insurance, tax forms</p>
            </a>
            
            <a href="/wizard/step2?doc_type=technical" class="step-card">
                <i class="fas fa-cogs"></i>
                <h3>Technical Manual</h3>
                <p>Instructions, specifications, warranty</p>
            </a>
            
            <a href="/wizard/step2?doc_type=government" class="step-card">
                <i class="fas fa-landmark"></i>
                <h3>Government Form</h3>
                <p>Application, permit, official document</p>
            </a>
            
            <a href="/wizard/step2?doc_type=academic" class="step-card">
                <i class="fas fa-graduation-cap"></i>
                <h3>Academic Paper</h3>
                <p>Research, study, scientific paper</p>
            </a>
            
            <a href="/wizard/step2?doc_type=other" class="step-card">
                <i class="fas fa-file-alt"></i>
                <h3>Other Complex Document</h3>
                <p>Any difficult-to-understand text</p>
            </a>
        </div>
        
        <div style="text-align: center; margin-top: 2rem;">
            <a href="/" role="button" class="secondary">Cancel</a>
        </div>
    </div>
    '''
    return HTMLResponse(layout("Step 1: Document Type", content))

# ========== STEP 2: AUDIENCE LEVEL ==========
@app.get("/wizard/step2")
async def step2(doc_type: str = Query("legal")):
    doc_type_names = {
        "legal": "Legal Document",
        "medical": "Medical Document", 
        "contract": "Contract/Agreement",
        "financial": "Financial Document",
        "technical": "Technical Manual",
        "government": "Government Form",
        "academic": "Academic Paper",
        "other": "Complex Document"
    }
    
    content = f'''
    <div style="max-width: 800px; margin: 0 auto;">
        <div class="steps">
            <div class="step">1</div>
            <div class="step active">2</div>
            <div class="step">3</div>
            <div class="step">4</div>
        </div>
        
        <h1 style="text-align: center; color: var(--primary);">Step 2: Your Knowledge Level</h1>
        <p style="text-align: center; color: #6b7280;">
            How familiar are you with {doc_type_names[doc_type].lower()}s?
        </p>
        
        <p style="text-align: center;"><strong>Document Type:</strong> {doc_type_names[doc_type]}</p>
        
        <div class="card-grid">
            <a href="/wizard/step3?doc_type={doc_type}&level=novice" class="step-card">
                <i class="fas fa-seedling"></i>
                <h3>Novice</h3>
                <p>Little to no experience. Explain like I'm new.</p>
            </a>
            
            <a href="/wizard/step3?doc_type={doc_type}&level=general" class="step-card">
                <i class="fas fa-user"></i>
                <h3>General Public</h3>
                <p>Basic understanding. Use everyday language.</p>
            </a>
            
            <a href="/wizard/step3?doc_type={doc_type}&level=educated" class="step-card">
                <i class="fas fa-user-graduate"></i>
                <h3>Educated Layperson</h3>
                <p>Some background. Can handle some terminology.</p>
            </a>
            
            <a href="/wizard/step3?doc_type={doc_type}&level=professional" class="step-card">
                <i class="fas fa-briefcase"></i>
                <h3>Related Professional</h3>
                <p>Work in related field. Want deeper analysis.</p>
            </a>
        </div>
        
        <div class="info-box">
            <p style="margin: 0;">
                <strong>Tip:</strong> Choose "Novice" for maximum plain English translation. 
                The AI will avoid all jargon and use simple analogies.
            </p>
        </div>
        
        <div style="text-align: center; margin-top: 2rem;">
            <a href="wizard" role="button" class="secondary">Back</a>
        </div>
    </div>
    '''
    return HTMLResponse(layout("Step 2: Knowledge Level", content))

# ========== STEP 3: DOCUMENT INPUT (ENHANCED) ==========
@app.get("/wizard/step3")
async def step3(
    doc_type: str = Query("legal"),
    level: str = Query("novice")
):
    doc_type_names = {
        "legal": "Legal Document",
        "medical": "Medical Document",
        "contract": "Contract/Agreement", 
        "financial": "Financial Document",
        "technical": "Technical Manual",
        "government": "Government Form",
        "academic": "Academic Paper",
        "other": "Complex Document"
    }
    
    level_names = {
        "novice": "Novice",
        "general": "General Public", 
        "educated": "Educated Layperson",
        "professional": "Related Professional"
    }
    
    content = f'''
    <div style="max-width: 800px; margin: 0 auto;">
        <!-- Steps indicator (same as before) -->
        <div class="steps">
            <div class="step">1</div>
            <div class="step">2</div>
            <div class="step active">3</div>
            <div class="step">4</div>
        </div>
        
        <h1 style="text-align: center; color: var(--primary);">Step 3: Add Your Document</h1>
        
        <!-- TAB NAVIGATION -->
        <div style="display: flex; border-bottom: 2px solid #374151; margin: 2rem 0;">
            <button class="tab-btn active" onclick="showTab('text-tab')" 
                    style="flex: 1; padding: 1rem; background: none; border: none; color: #0cc0df; border-bottom: 2px solid #0cc0df; cursor: pointer;">
                <i class="fas fa-paste"></i> Paste Text
            </button>
            <button class="tab-btn" onclick="showTab('upload-tab')" 
                    style="flex: 1; padding: 1rem; background: none; border: none; color: #9ca3af; cursor: pointer;">
                <i class="fas fa-upload"></i> Upload File
            </button>
            <button class="tab-btn" onclick="showTab('url-tab')" 
                    style="flex: 1; padding: 1rem; background: none; border: none; color: #9ca3af; cursor: pointer;">
                <i class="fas fa-link"></i> From URL
            </button>
        </div>
        
                <!-- TEXT TAB (default visible) -->
        <div id="text-tab" class="tab-content">
            <form action="/process" method="POST" id="documentForm">
                <input type="hidden" name="doc_type" value="{doc_type}">
                <input type="hidden" name="level" value="{level}">
                
                <div style="margin: 2rem 0;">
                    <label for="document_text">
                        <strong>Paste Document Text:</strong>
                        <p style="color: #6b7280; margin: 0.5rem 0;">
                            Copy and paste the text you want to understand (max 50,000 characters)
                        </p>
                    </label>
                    <textarea id="document_text" name="document_text" rows="12" 
                              placeholder="Paste your legal clause, medical report, contract section, or any complex text here..."
                              style="width: 100%; padding: 1rem; border: 2px solid #374151; border-radius: 0.5rem; background: rgba(255,255,255,0.05); color: white; font-family: monospace;"></textarea>
                    <div style="text-align: right; margin-top: 0.5rem;">
                        <span id="charCount" style="color: #6b7280; font-size: 0.9rem;">0/50000 characters</span>
                    </div>
                </div>
                
                <div style="margin: 2rem 0;">
                    <label for="specific_questions">
                        <strong>Specific Questions (Optional):</strong>
                        <p style="color: #6b7280; margin: 0.5rem 0;">
                            What specifically do you want to understand about this document?
                        </p>
                    </label>
                    <textarea id="specific_questions" name="specific_questions" rows="3" 
                              placeholder="• What are the hidden risks? 
• What does this medical term mean?
• What am I really agreeing to?"
                              style="width: 100%; padding: 1rem; border: 2px solid #374151; border-radius: 0.5rem; background: rgba(255,255,255,0.05); color: white;"></textarea>
                </div>
                
                <div style="text-align: center; margin: 2rem 0;">
                    <button type="submit" id="submitBtn" style="padding: 1rem 3rem; font-size: 1.2rem; background: #0cc0df; color: white; border: none; border-radius: 8px; cursor: pointer;">
                        <i class="fas fa-search"></i> Decode Document (3 tokens)
                    </button>
                </div>
            </form>
            
            <script>
            // Character counter
            document.getElementById('document_text').addEventListener('input', function(e) {{
                const count = e.target.value.length;
                document.getElementById('charCount').textContent = count + '/50000 characters';
                if (count > 50000) {{
                    e.target.value = e.target.value.substring(0, 50000);
                    document.getElementById('charCount').textContent = '50000/50000 characters (limit reached)';
                    document.getElementById('charCount').style.color = '#dc2626';
                }} else if (count > 40000) {{
                    document.getElementById('charCount').style.color = '#d97706';
                }} else {{
                    document.getElementById('charCount').style.color = '#6b7280';
                }}
            }});
            </script>
        </div>
        
                <!-- UPLOAD TAB (hidden by default) -->
        <div id="upload-tab" class="tab-content" style="display: none;">
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <div style="font-size: 3rem; color: #0cc0df; margin-bottom: 0.5rem;">
                    <i class="fas fa-cloud-upload-alt"></i>
                </div>
                <h3 style="color: white;">Upload a File</h3>
                <p style="color: #9ca3af;">PDF, DOC, or TXT file (max 10MB)</p>
            </div>
            
            <form action="/process-upload" method="POST" enctype="multipart/form-data">
                <input type="hidden" name="doc_type" value="{doc_type}">
                <input type="hidden" name="level" value="{level}">
                
                <div style="margin: 1.5rem 0;">
                    <label for="file" style="color: white;"><strong>Choose File:</strong></label>
                    <input type="file" id="file" name="file" accept=".pdf,.doc,.docx,.txt" required
                           style="width: 100%; padding: 1rem; border: 2px dashed #0cc0df; border-radius: 8px; margin-top: 0.5rem; background: rgba(255,255,255,0.05); color: white;">
                </div>
                
                <div style="margin: 2rem 0;">
                    <label for="upload_questions" style="color: white;">
                        <strong>Specific Questions (Optional):</strong>
                        <p style="color: #9ca3af; margin: 0.5rem 0;">
                            What specifically do you want to understand about this document?
                        </p>
                    </label>
                    <textarea id="upload_questions" name="specific_questions" rows="3" 
                              placeholder="• What are the hidden risks? 
• What does this medical term mean?
• What am I really agreeing to?"
                              style="width: 100%; padding: 1rem; border: 2px solid #374151; border-radius: 0.5rem; background: rgba(255,255,255,0.05); color: white;"></textarea>
                </div>
                
                <div style="text-align: center;">
                    <button type="submit" style="padding: 1rem 2rem; background: #0cc0df; color: white; border: none; border-radius: 8px; font-size: 1.1rem; cursor: pointer;">
                        <i class="fas fa-search"></i> Upload & Analyze (3 tokens)
                    </button>
                    <p style="color: #9ca3af; margin-top: 0.5rem; font-size: 0.9rem;">
                        File will be processed securely on our servers
                    </p>
                </div>
            </form>
        </div>
        
                <!-- URL TAB (hidden by default) -->
        <div id="url-tab" class="tab-content" style="display: none;">
            <div style="text-align: center; margin-bottom: 1.5rem;">
                <div style="font-size: 3rem; color: #0cc0df; margin-bottom: 0.5rem;">
                    <i class="fas fa-link"></i>
                </div>
                <h3 style="color: white;">Analyze Web Page</h3>
                <p style="color: #9ca3af;">Enter a URL to analyze webpage content</p>
            </div>
            
            <form action="/process-url" method="POST" id="urlForm">
                <input type="hidden" name="doc_type" value="{doc_type}">
                <input type="hidden" name="level" value="{level}">
                
                <div style="margin: 1.5rem 0;">
                    <label for="url" style="color: white;"><strong>Web Page URL:</strong></label>
                    <input type="url" id="url" name="url" 
                           placeholder="https://example.com/terms-of-service"
                           required
                           style="width: 100%; padding: 1rem; border: 2px solid #374151; border-radius: 0.5rem; background: rgba(255,255,255,0.05); color: white; font-family: monospace;">
                    <p style="color: #9ca3af; font-size: 0.9rem; margin-top: 0.5rem;">
                        Works with most public web pages (terms of service, articles, documentation)
                    </p>
                </div>
                
                <div style="margin: 2rem 0;">
                    <label for="url_questions" style="color: white;">
                        <strong>Specific Questions (Optional):</strong>
                        <p style="color: #9ca3af; margin: 0.5rem 0;">
                            What specifically do you want to understand about this page?
                        </p>
                    </label>
                    <textarea id="url_questions" name="specific_questions" rows="3" 
                              placeholder="• What are the key requirements?
• What are my obligations?
• What rights am I giving up?"
                              style="width: 100%; padding: 1rem; border: 2px solid #374151; border-radius: 0.5rem; background: rgba(255,255,255,0.05); color: white;"></textarea>
                </div>
                
                <div style="text-align: center;">
                    <button type="submit" style="padding: 1rem 2rem; background: #0cc0df; color: white; border: none; border-radius: 8px; font-size: 1.1rem; cursor: pointer;">
                        <i class="fas fa-globe"></i> Fetch & Analyze (3 tokens)
                    </button>
                    <p style="color: #9ca3af; margin-top: 0.5rem; font-size: 0.9rem;">
                        Content will be fetched and analyzed securely
                    </p>
                </div>
            </form>
            
            <div style="background: rgba(12, 192, 223, 0.1); border-radius: 8px; padding: 1rem; margin-top: 2rem;">
                <p style="margin: 0; color: #0cc0df; font-size: 0.9rem;">
                    <i class="fas fa-info-circle"></i> 
                    <strong>Note:</strong> Some websites may block automated access. For private pages, use copy/paste instead.
                </p>
            </div>
        </div>
        
        <!-- Tab switching JavaScript -->
        <script>
        function showTab(tabId) {{
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(tab => {{
                tab.style.display = 'none';
            }});
            // Show selected tab
            document.getElementById(tabId).style.display = 'block';
            
            // Update tab buttons
            document.querySelectorAll('.tab-btn').forEach(btn => {{
                btn.style.color = '#9ca3af';
                btn.style.borderBottom = 'none';
            }});
            event.currentTarget.style.color = '#0cc0df';
            event.currentTarget.style.borderBottom = '2px solid #0cc0df';
        }}
        </script>
    </div>
    '''
    return HTMLResponse(layout("Step 3: Document Input", content))

# ========== PROCESS (ENHANCED) ==========
@app.post("/process")
async def process_document(
    doc_type: str = Form(...),
    level: str = Form(...),
    document_text: str = Form(...),
    specific_questions: str = Form("")
):
    # Validate input
    if not document_text.strip():
        return HTMLResponse(layout("Error", '''
            <div style="text-align: center; padding: 4rem 0;">
                <h1 style="color: #dc2626;"><i class="fas fa-exclamation-triangle"></i> No Document Text</h1>
                <p>Please paste some text or upload a file.</p>
                <a href="/wizard/step3?doc_type={doc_type}&level={level}" role="button">Try Again</a>
            </div>
        '''))
    
    # Check token limit (simplified - you'll need user auth)
    # For now, assume user has tokens
    
    # Generate unique ID for this analysis
    analysis_id = str(uuid.uuid4())
    
    # Store in queue
    analysis_queue[analysis_id] = {
        "doc_type": doc_type,
        "level": level,
        "document_text": document_text[:10000],  # Limit to 10K chars
        "specific_questions": specific_questions,
        "status": "processing",
        "created_at": time.time(),
        "progress": 0.1,
        "message": "Starting analysis..."
    }
    
    # Start background task
    asyncio.create_task(process_document_background(analysis_id))
    
    # Show loading page with progress updates
    loading_content = f'''
    <!DOCTYPE html>
<html>
<head>
    <title>Analyzing Document - Document Wizard</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #000;
            color: #fff;
            margin: 0;
            padding: 0;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .container {{
            max-width: 600px;
            text-align: center;
            padding: 3rem;
        }}
        .spinner {{
            font-size: 4rem;
            color: #0cc0df;
            margin-bottom: 1rem;
            animation: spin 1s linear infinite;
        }}
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        h1 {{ color: #0cc0df; margin-bottom: 1rem; }}
        p {{ color: #9ca3af; margin-bottom: 2rem; }}
        .progress-bar {{
            width: 100%;
            height: 8px;
            background: #374151;
            border-radius: 4px;
            margin: 2rem 0;
            overflow: hidden;
        }}
        .progress {{
            height: 100%;
            background: #0cc0df;
            width: 0%;
            animation: loading 2s infinite;
            border-radius: 4px;
        }}
        @keyframes loading {{
            0% {{ width: 0%; margin-left: 0%; }}
            50% {{ width: 50%; }}
            100% {{ width: 0%; margin-left: 100%; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="spinner">
            <i class="fas fa-hat-wizard"></i>
        </div>
        
        <h1>Analyzing Your Document</h1>
        <p>We're decoding your {doc_type.replace("_", " ").title()} for {level.replace("_", " ").title()} understanding</p>
        
        <div class="progress-bar">
            <div class="progress"></div>
        </div>
        
        <p id="status" style="color: #0cc0df;">Reading document and preparing analysis...</p>
        
        <div style="background: rgba(12, 192, 223, 0.1); padding: 1rem; border-radius: 8px; margin-top: 2rem;">
            <p style="margin: 0; color: #0cc0df; font-size: 0.9rem;">
                <i class="fas fa-lightbulb"></i> 
                <span id="tip">Looking for tricky language and hidden meanings...</span>
            </p>
        </div>
    </div>
    
    <script>
    const analysisId = "{analysis_id}";
    
    function checkProgress() {{
        fetch('/api/analysis-status/' + analysisId)
            .then(r => r.json())
            .then(data => {{
                if (data.status === 'complete') {{
                    window.location.href = '/result/' + analysisId;
                }} else if (data.status === 'error') {{
                    window.location.href = '/error?message=' + encodeURIComponent(data.error);
                }} else {{
                    // Update status message if available
                    if (data.message) {{
                        document.getElementById('status').textContent = data.message;
                    }}
                    // Continue polling
                    setTimeout(checkProgress, 1000);
                }}
            }})
            .catch(error => {{
                console.error('Progress check failed:', error);
                setTimeout(checkProgress, 2000);
            }});
    }}
    
    // Start polling after 1 second
    setTimeout(checkProgress, 1000);
    </script>
</body>
</html>
    '''

    return HTMLResponse(loading_content)

# Add this endpoint
@app.get("/api/analysis-status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    if analysis_id in analysis_queue:
        status = analysis_queue[analysis_id]
        # Calculate progress based on status
        progress = 0.25  # Default
        if status.get("ai_processing"):
            progress = 0.5
        if status.get("formatting"):
            progress = 0.75
        
        return {
            "status": status["status"],
            "progress": progress,
            "message": status.get("message", "Processing...")
        }
    return {"status": "not_found"}

@app.post("/process-url")
async def process_url(
    doc_type: str = Form(...),
    level: str = Form(...),
    url: str = Form(...),
    specific_questions: str = Form("")
):
    """Fetch and analyze content from a URL"""
    
    try:
        # 1. Fetch the webpage
        import requests
        from bs4 import BeautifulSoup
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Document Wizard Bot)'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # 2. Extract text (simple version - you might want more sophisticated extraction)
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer", "header"]):
            script.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        # Limit text length
        text = text[:15000]  # 15K chars max
        
        if not text.strip():
            return HTMLResponse(layout("URL Error", f"""
                <div style="text-align: center; padding: 4rem;">
                    <h1>No Text Extracted</h1>
                    <p>Could not extract readable text from {url}</p>
                    <p>Try copying the text manually and using the Paste Text option.</p>
                    <a href="/wizard/step3?doc_type={doc_type}&level={level}">Try Again</a>
                </div>
            """))
        
        # 3. Use the same process as text input
        return await process_document(
            doc_type=doc_type,
            level=level,
            document_text=text,
            specific_questions=specific_questions
        )
        
    except requests.exceptions.RequestException as e:
        return HTMLResponse(layout("URL Error", f"""
            <div style="text-align: center; padding: 4rem;">
                <h1>URL Error</h1>
                <p>Failed to fetch {url}</p>
                <p>Error: {str(e)}</p>
                <p>Make sure the URL is public and accessible.</p>
                <a href="/wizard/step3?doc_type={doc_type}&level={level}">Try Again</a>
            </div>
        """))
    
    except Exception as e:
        return HTMLResponse(layout("Error", f"""
            <div style="text-align: center; padding: 4rem;">
                <h1>Processing Error</h1>
                <p>Error: {str(e)}</p>
                <a href="/wizard/step3?doc_type={doc_type}&level={level}">Try Again</a>
            </div>
        """))

# ========== RESULT BY ID ==========
@app.get("/result/{analysis_id}")
async def show_result_by_id(analysis_id: str):
    if analysis_id not in analysis_queue:
        return HTMLResponse(layout("Result Expired", '''
            <div style="text-align: center; padding: 4rem 0;">
                <h1><i class="fas fa-hourglass-end"></i> Result Expired</h1>
                <p>This analysis result has expired or wasn't found.</p>
                <a href="/wizard" role="button">Start New Analysis</a>
            </div>
        '''))
    
    data = analysis_queue[analysis_id]
    
    if data["status"] != "complete":
        return HTMLResponse(layout("Still Processing", f'''
            <div style="text-align: center; padding: 4rem 0;">
                <h1><i class="fas fa-spinner fa-spin"></i> Still Processing</h1>
                <p>The analysis is still running. Please wait...</p>
                <meta http-equiv="refresh" content="2;url=/result/{analysis_id}">
            </div>
        '''))
    
    # Use your existing show_result logic but pass the stored data
    return await show_result_internal(
        doc_type=data["doc_type"],
        level=data["level"],
        document_text=data["document_text"],
        specific_questions=data["specific_questions"],
        ai_text=data.get("result", "No result available")
    )

# Helper function (modified from your original show_result)
async def show_result_internal(doc_type: str, level: str, document_text: str, 
                              specific_questions: str, ai_text: str):
    # This is your existing show_result logic, but using the passed ai_text
    # Copy the body of your show_result function here, but:
    # 1. Remove the TEST_MODE logic
    # 2. Use the passed ai_text parameter
    # 3. Keep all your formatting
    
    # For now, I'll give you a simplified version:
    TURQUOISE = "#0cc0df"
    
    result_content = f'''
    <div style="max-width: 800px; margin: 0 auto;">
        <div style="text-align: center; margin-bottom: 2rem;">
            <div style="font-size: 3rem; color: {TURQUOISE};">
                <i class="fas fa-file-contract"></i>
            </div>
            <h1 style="color: {TURQUOISE};">Document Analysis Complete</h1>
            <p style="color: #64748b;">
                {doc_type.replace("_", " ").title()} analyzed for {level.replace("_", " ").title()} understanding
            </p>
        </div>
        
        <div style="position: relative;">
            
            <div style="position: relative; margin: 2rem 0;">
            <div style="text-align: right; margin-bottom: 0.5rem;">
                <button onclick="copyText()" 
                        style="background: #0cc0df; color: white; border: none; padding: 0.5rem 1rem; border-radius: 4px; cursor: pointer;"
                        id="copy-btn">
                    <i class="fas fa-copy"></i> Copy
                </button>
            </div>
            
            <div id="ai-output" style="line-height: 1.6; color: #f0f0f0; background: rgba(255,255,255,0.05); border-radius: 12px; padding: 2rem; box-shadow: 0 4px 12px rgba(0,0,0,0.05);">
                {ai_text.lstrip().replace(chr(10), '<br>').replace('•', '•')}
            </div>
        </div>
        </div>

        <div style="text-align: center; margin-top: 3rem;">
            <a href="/wizard" role="button" style="margin-right: 1rem; background: {TURQUOISE}; border-color: {TURQUOISE};">
                <i class="fas fa-file-contract"></i> Analyze Another Document
            </a>
            <a href="/" role="button" style="background: #64748b; border-color: #64748b;">
                <i class="fas fa-home"></i> Dashboard
            </a>
        </div>
        
        <div style="background: #fef3c7; border: 2px solid #f59e0b; border-radius: 8px; padding: 1rem; margin-top: 2rem;">
            <p style="margin: 0; color: #d97706; font-size: 0.9rem;">
                <i class="fas fa-gavel"></i> 
                <strong>Disclaimer:</strong> This AI analysis is for educational purposes only. 
                It is NOT legal, medical, or financial advice. For important decisions, consult a qualified professional.
            </p>
        </div>

        <script>
        function copyText() {{
            const output = document.getElementById('ai-output');
            const text = output.innerText;
            
            navigator.clipboard.writeText(text).then(() => {{
                const btn = document.getElementById('copy-btn');
                btn.innerHTML = '<i class="fas fa-check"></i> Copied!';
                btn.style.background = '#10b981';
                
                setTimeout(() => {{
                    btn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                    btn.style.background = '#0cc0df';
                }}, 2000);
            }}).catch(err => {{
                alert('Failed to copy. Please select and copy manually.');
            }});
        }}
        </script>
    </div>
    '''
    
    return HTMLResponse(layout("Analysis Results", result_content))

@app.post("/api/extract-text")
async def extract_text(file: UploadFile = File(...)):
    # Simple text extraction - expand based on file type
    if file.filename.endswith('.txt'):
        content = await file.read()
        return {"text": content.decode('utf-8', errors='ignore')}
    
    elif file.filename.endswith('.pdf'):
        # Use PyPDF2 or pdfplumber
        try:
            import PyPDF2
            import io
            content = await file.read()
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
            return {"text": text[:20000]}  # Limit to 20K chars
        except:
            return {"error": "PDF processing failed. Try converting to text first."}
    
    elif file.filename.endswith(('.doc', '.docx')):
        # For DOCX, you might need python-docx
        return {"error": "DOC/DOCX support coming soon. Save as PDF or text first."}
    
    return {"error": "Unsupported file type"}

async def process_document_background(analysis_id: str):
    data = analysis_queue[analysis_id]
    
    client = AsyncOpenAI(
        api_key=DEEPSEEK_API_KEY,  
        base_url="https://api.deepseek.com"
    )

    try:
        # 1. Pre-process document (limit size, clean)
        text = data["document_text"][:20000]  # 20K char limit for speed
        
        # 2. Smart prompt based on doc_type and level
        prompt_templates = {
            "legal": """Analyze this legal document for a {level}. Focus on:
1. Plain English translation
2. Hidden risks or unfair clauses
3. Rights vs responsibilities
4. Actionable next steps

Keep analysis under 500 words. No markdown.""",
            
            "medical": """Analyze this medical document for a {level}. Focus on:
1. Plain English explanation
2. Medical terms translated
3. Treatment implications
4. Questions to ask doctor

Keep analysis under 500 words. No markdown."""
        }
        
        prompt = prompt_templates.get(
            data["doc_type"], 
            "Analyze this document in plain English for a {level} audience."
        ).format(level=data["level"])
        
        # 3. Call DeepSeek with timeout
        import asyncio
        try:
            # Your DeepSeek API call here
            # Add timeout
            response = await asyncio.wait_for(
                deepseek.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": "You are a document analysis expert."},
                        {"role": "user", "content": f"{prompt}\n\nDOCUMENT:\n{text}"}
                    ],
                    max_tokens=1000
                ),
                timeout=30.0  # 30 second timeout
            )
            
            ai_text = response.choices[0].message.content
            
        except asyncio.TimeoutError:
            ai_text = "Analysis timed out. Document may be too complex or service busy. Try a shorter section."
        
        # 4. Store result
        data["result"] = ai_text
        data["status"] = "complete"
        
    except Exception as e:
        data["status"] = "error"
        data["error"] = str(e)

# Instead of complex parsing, use simple sections
def format_ai_response(ai_text: str, doc_type: str, level: str):
    # Just wrap in a clean div - parsing can fail
    return f'''
    <div style="background: rgba(255,255,255,0.05); border-radius: 12px; padding: 2rem; margin: 2rem 0;">
        <h3 style="color: #0cc0df; margin-top: 0;">
            <i class="fas fa-file-alt"></i> Analysis for {level.replace("_", " ").title()}
        </h3>
        <div style="line-height: 1.6; color: #f0f0f0; white-space: pre-wrap;">
            {ai_text}
        </div>
    </div>
    '''

# ========== FILE EXTRACTION API ==========
@app.post("/api/extract-text")
async def extract_text(file: UploadFile):
    try:
        # Read file content
        content = await file.read()
        
        # Handle different file types
        if file.filename.endswith('.txt') or file.content_type == 'text/plain':
            text = content.decode('utf-8', errors='ignore')
            return {"text": text[:10000]}  # Limit to 10K chars
        
        elif file.filename.endswith('.pdf') or file.content_type == 'application/pdf':
            try:
                # Try PyPDF2 first
                import PyPDF2
                import io
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                text = ""
                # Limit to first 10 pages for speed
                for i, page in enumerate(pdf_reader.pages):
                    if i >= 10:  # Only first 10 pages
                        break
                    text += page.extract_text() + "\n"
                return {"text": text[:10000]}
            except Exception as e:
                # Fallback: return error
                return {"error": f"PDF extraction failed. Try converting to text first. Error: {str(e)}"}
        
        elif file.filename.endswith(('.doc', '.docx')):
            return {"error": "Word document support coming soon. Please save as PDF or text first."}
        
        else:
            return {"error": "Unsupported file type. Please upload PDF, DOC, DOCX, or TXT."}
            
    except Exception as e:
        return {"error": f"Error processing file: {str(e)}"}

@app.post("/api/extract-text")
async def extract_text(file: UploadFile):
    try:
        content = await file.read()
        
        # PDF handling with better error messages
        if file.filename.endswith('.pdf') or file.content_type == 'application/pdf':
            try:
                import PyPDF2
                import io
                
                pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
                
                # Check if PDF is encrypted
                if pdf_reader.is_encrypted:
                    return {"error": "PDF is encrypted/password protected. Please save as unencrypted PDF or copy text manually."}
                
                # Check number of pages
                if len(pdf_reader.pages) > 20:
                    return {"error": f"PDF has {len(pdf_reader.pages)} pages. Please extract the most important 1-2 pages or use a shorter document."}
                
                # Extract text
                text = ""
                for i, page in enumerate(pdf_reader.pages):
                    if i >= 10:  # Limit to first 10 pages
                        text += f"\n[Document truncated after page 10. Total pages: {len(pdf_reader.pages)}]"
                        break
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n\n"
                
                if not text.strip():
                    return {"error": "PDF appears to be scanned or image-based. No text could be extracted. Try OCR software or manual typing."}
                
                return {"text": text[:15000]}  # Limit characters
                
            except ImportError:
                return {"error": "PDF library not installed. Run: pip install PyPDF2"}
            except Exception as e:
                return {"error": f"PDF processing failed: {str(e)}"}
        
        # TXT file handling
        elif file.filename.endswith('.txt') or file.content_type == 'text/plain':
            try:
                text = content.decode('utf-8', errors='ignore')
                return {"text": text[:15000]}
            except:
                return {"error": "Could not read text file. Try UTF-8 encoding."}
        
        else:
            return {"error": f"Unsupported file type: {file.filename}. Use PDF or TXT."}
            
    except Exception as e:
        return {"error": f"File processing error: {str(e)}"}

# ========== ANALYSIS STATUS API ==========
@app.get("/api/analysis-status/{analysis_id}")
async def get_analysis_status(analysis_id: str):
    if analysis_id in analysis_queue:
        data = analysis_queue[analysis_id]
        return {
            "status": data["status"],
            "progress": data.get("progress", 0.1),
            "message": data.get("message", "Processing..."),
            "error": data.get("error")
        }
    return {"status": "not_found", "error": "Analysis not found"}

# ========== BACKGROUND PROCESSING ==========
async def process_document_background(analysis_id: str):
    data = analysis_queue[analysis_id]
    
    try:
        # Update progress
        data["progress"] = 0.2
        data["message"] = "Reading document..."
        await asyncio.sleep(0.5)
        
        # Extract and clean text
        text = data["document_text"][:8000]  # Further limit for speed
        word_count = len(text.split())
        
        # Update progress
        data["progress"] = 0.4
        data["message"] = f"Analyzing {word_count} words with AI..."
        
        # Prepare prompt based on document type and level
        prompt_templates = {
            "legal": """Analyze this LEGAL document for a {level} audience. Focus on:
1. PLAIN ENGLISH TRANSLATION: What does this actually say?
2. TRICKY LANGUAGE: Watch out for these specific terms/phrases
3. YOUR RIGHTS: What you're entitled to
4. YOUR RESPONSIBILITIES: What you must do
5. RED FLAGS: Potential concerns to address
6. NEXT STEPS: Actionable advice

Keep analysis under 400 words. Use bullet points. No markdown.""",
            
            "medical": """Analyze this MEDICAL document for a {level} audience. Focus on:
1. PLAIN ENGLISH EXPLANATION: What this means for the patient
2. MEDICAL TERMS TRANSLATED: Simple definitions
3. TREATMENT IMPLICATIONS: What happens next
4. QUESTIONS TO ASK DOCTOR: Specific things to discuss
5. URGENCY LEVEL: How soon to act

Keep analysis under 400 words. Use bullet points. No markdown.""",
            
            "contract": """Analyze this CONTRACT for a {level} audience. Focus on:
1. PLAIN ENGLISH SUMMARY: What you're agreeing to
2. KEY TERMS: Important dates, amounts, deadlines
3. RISKS & PROTECTIONS: What could go wrong, what protects you
4. NEGOTIATION POINTS: What to ask for
5. TERMINATION: How to get out of it

Keep analysis under 400 words. Use bullet points. No markdown."""
        }
        
        prompt = prompt_templates.get(
            data["doc_type"],
            """Analyze this document for a {level} audience. Provide:
1. Plain English summary
2. Key points to understand
3. Actionable next steps

Keep analysis under 400 words. Use bullet points. No markdown."""
        ).format(level=data["level"])
        
        # Add specific questions if provided
        if data["specific_questions"]:
            prompt += f"\n\nSPECIFIC USER QUESTIONS:\n{data['specific_questions']}"
        
        # Add document
        prompt += f"\n\nDOCUMENT TEXT:\n{text}"
        
        # Update progress
        data["progress"] = 0.6
        data["message"] = "Processing with AI ..."
        
        # ========== API CALL SECTION ==========
        try:
            # Check for API key first
            api_key = os.getenv("DEEPSEEK_API_KEY", "")
            
            if not api_key or api_key.startswith("your-"):
                # Provide mock response
                ai_text = f"""MOCK ANALYSIS (API Key Needed)

Document Type: {data['doc_type'].title()}
Audience Level: {data['level'].title()}

KEY POINTS TO REVIEW:
1. Identify all parties involved
2. Note important dates and deadlines
3. Look for financial terms and amounts
4. Check termination conditions
5. Watch for liability clauses

NEXT STEPS:
1. Add your DeepSeek API key to .env file
2. Get a key from platform.deepseek.com
3. Restart the application for real AI analysis

This is a placeholder. Real AI analysis requires an API key."""
                data["is_mock"] = True
                
            else:
                # Real API call
                from openai import AsyncOpenAI
                
                client = AsyncOpenAI(
                    api_key=api_key,
                    base_url="https://api.deepseek.com"
                )
                
                response = await asyncio.wait_for(
                    client.chat.completions.create(
                        model="deepseek-chat",
                        messages=[
                            {"role": "system", "content": "You are a document analysis expert."},
                            {"role": "user", "content": prompt}
                        ],
                        max_tokens=800,
                        temperature=0.3
                    ),
                    timeout=25.0  # 25 second timeout
                )
                
                ai_text = response.choices[0].message.content
                data["is_mock"] = False
                
        except asyncio.TimeoutError:
            ai_text = """ANALYSIS TIMED OUT

The document was too complex or the service is busy. 

SUGGESTIONS:
1. Try a shorter section (1-2 paragraphs)
2. Focus on the specific clause you don't understand
3. Try again in a few minutes

PLAIN ENGLISH ADVICE:
For complex documents, break them into smaller parts and analyze each section separately."""
            data["is_error"] = True
            data["error_type"] = "timeout"
            
        except Exception as api_error:
            error_msg = str(api_error)
            if "401" in error_msg or "authentication" in error_msg.lower():
                ai_text = f"""API KEY ERROR: {error_msg}
                Please add your DeepSeek API key to the .env file."""
            elif "timeout" in error_msg.lower() or "timed out" in error_msg:
                ai_text = f"""ANALYSIS TIMED OUT: {error_msg}
                Try a shorter document (under 1000 words)."""
            else:
                ai_text = f"""AI SERVICE ERROR: {error_msg}
                Please try again or contact support."""
            data["is_error"] = True
            data["error_type"] = "api_error"
        
        # Update progress
        data["progress"] = 0.8
        data["message"] = "Formatting results..."
        await asyncio.sleep(0.5)
        
        # Store result
        data["result"] = ai_text
        data["status"] = "complete"
        data["progress"] = 1.0
        data["message"] = "Analysis complete!"
        
        # Clean up old analyses (keep last 100)
        if len(analysis_queue) > 100:
            # Remove oldest entries
            oldest_ids = sorted(analysis_queue.keys(), 
                              key=lambda k: analysis_queue[k].get("created_at", 0))[:50]
            for old_id in oldest_ids:
                if old_id != analysis_id:  # Keep current
                    analysis_queue.pop(old_id, None)
        
    except Exception as e:
        # This catches OTHER errors outside the main try block
        data["status"] = "error"
        data["error"] = str(e)
        data["message"] = f"System Error: {str(e)}"
        data["result"] = f"""SYSTEM ERROR

The application encountered an unexpected error:

{str(e)}

PLEASE TRY:
1. Refreshing the page
2. Using a different document
3. Contacting support if it continues"""

# ========== ERROR PAGE ==========
@app.get("/error")
async def error_page():
    # Your error page code here
    error_content = '''
    <div style="text-align: center; padding: 4rem 0;">
        <h1 style="color: #dc2626;"><i class="fas fa-exclamation-triangle"></i> Error</h1>
        <p>Something went wrong with the analysis.</p>
        <a href="/wizard" role="button">Try Again</a>
    </div>
    '''
    return HTMLResponse(layout("Error", error_content))

async def process_document_internal(doc_type, level, text, specific_questions):
    """Actually process document with AI instead of returning placeholder"""
    
    # Generate unique ID for this analysis
    analysis_id = str(uuid.uuid4())
    
    # Store in queue (like your other process does)
    analysis_queue[analysis_id] = {
        "doc_type": doc_type,
        "level": level,
        "document_text": text[:10000],
        "specific_questions": specific_questions,
        "status": "processing",
        "created_at": time.time(),
        "progress": 0.1,
        "message": "Starting analysis..."
    }
    
    # Start background task using your existing function
    asyncio.create_task(process_document_background(analysis_id))
    
    # Wait for completion (with timeout)
    max_wait = 60  # seconds
    wait_interval = 0.5
    
    for _ in range(int(max_wait / wait_interval)):
        await asyncio.sleep(wait_interval)
        
        if analysis_id in analysis_queue:
            data = analysis_queue[analysis_id]
            
            if data["status"] == "complete":
                # Return the actual AI result
                return {
                    "status": "complete",
                    "summary": data.get("result", "No result generated"),
                    "analysis_id": analysis_id,
                    "is_mock": data.get("is_mock", False),
                    "is_error": data.get("is_error", False)
                }
            elif data["status"] == "error":
                return {
                    "status": "error",
                    "summary": f"Analysis failed: {data.get('error', 'Unknown error')}"
                }
    
    # If we timeout
    return {
        "status": "timeout",
        "summary": "Analysis timed out. Please try a shorter document."
    }

@app.post("/process-upload")
async def process_upload(
    doc_type: str = Form(...),
    level: str = Form(...),
    file: UploadFile = File(...),
    specific_questions: str = Form("")
):
    """Process uploaded file by extracting text and using the normal flow"""
    # 1. Extract text from file
    result = await extract_text(file)
    
    if "error" in result:
        return HTMLResponse(layout("Upload Error", f"""
            <div style="text-align: center; padding: 4rem;">
                <h1>File Processing Error</h1>
                <p>{result['error']}</p>
                <a href="/wizard/step3?doc_type={doc_type}&level={level}">Try Again</a>
            </div>
        """))
    
    text = result.get("text", "")
    
    if not text:
        return HTMLResponse(layout("Upload Error", f"""
            <div style="text-align: center; padding: 4rem;">
                <h1>No Text Extracted</h1>
                <p>The file appears to be empty or couldn't be read.</p>
                <a href="/wizard/step3?doc_type={doc_type}&level={level}">Try Again</a>
            </div>
        """))
    
    # 2. Create a fake request that mimics what /process expects
    # We'll use FastAPI's RedirectResponse with POST data
    # But actually, let's just call process_document directly
    
    # First, let's check what parameters process_document needs
    # Looking at your code: async def process_document(doc_type, level, document_text, specific_questions)
    
    # Call it directly - this will trigger the same loading screen
    return await process_document(
        doc_type=doc_type,
        level=level,
        document_text=text,
        specific_questions=specific_questions
    )

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
