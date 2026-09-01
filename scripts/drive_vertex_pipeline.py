"""
NexusSphere Automation Engine
Integrates Google Drive API, Google Cloud Vertex AI (Gemini), and GitHub Actions
"""

import os
import sys
import json
import re
import argparse
from datetime import datetime
from typing import Dict, Any, List, Optional

# Optional imports with graceful fallbacks
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload
    import vertexai
    from vertexai.generative_models import GenerativeModel, Part, GenerationConfig
    GOOGLE_LIBS_AVAILABLE = True
except ImportError:
    GOOGLE_LIBS_AVAILABLE = False


class GoogleDriveService:
    """Manages Google Drive interactions for input prompts and output publication sync."""

    def __init__(self, credentials_path: Optional[str] = None):
        self.service = None
        if not GOOGLE_LIBS_AVAILABLE:
            print("[DriveService] Google API libraries not installed. Running in mock/dry-run mode.")
            return

        try:
            scopes = ['https://www.googleapis.com/auth/drive']
            if credentials_path and os.path.exists(credentials_path):
                creds = service_account.Credentials.from_service_account_file(credentials_path, scopes=scopes)
            else:
                import google.auth
                creds, _ = google.auth.default(scopes=scopes)
            self.service = build('drive', 'v3', credentials=creds)
            print("[DriveService] Successfully authenticated with Google Drive API.")
        except Exception as e:
            print(f"[DriveService] Authentication notice: {e}. Falling back to local/dry-run mode.")

    def fetch_prompts_from_folder(self, folder_id: str) -> List[Dict[str, str]]:
        """Scans Google Drive folder for topic prompt files (.txt, .md, docs)."""
        if not self.service or not folder_id:
            print("[DriveService] No active Drive service or folder_id provided.")
            return []

        try:
            query = f"'{folder_id}' in parents and trashed = false"
            results = self.service.files().list(
                q=query,
                pageSize=10,
                fields="files(id, name, mimeType)"
            ).execute()
            files = results.get('files', [])
            print(f"[DriveService] Found {len(files)} files in folder {folder_id}.")

            prompts = []
            for file in files:
                file_id = file['id']
                file_name = file['name']
                # Download text content
                content_bytes = self.service.files().get_media(fileId=file_id).execute()
                text_content = content_bytes.decode('utf-8', errors='ignore')
                prompts.append({
                    "id": file_id,
                    "name": file_name,
                    "content": text_content
                })
            return prompts
        except Exception as e:
            print(f"[DriveService] Error fetching files from Drive: {e}")
            return []

    def upload_article_backup(self, file_path: str, destination_folder_id: str) -> Optional[str]:
        """Uploads generated article HTML/MD to Google Drive as an archive."""
        if not self.service or not destination_folder_id:
            return None

        try:
            file_metadata = {
                'name': os.path.basename(file_path),
                'parents': [destination_folder_id]
            }
            media = MediaFileUpload(file_path, mimetype='text/html')
            uploaded_file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            print(f"[DriveService] Successfully archived {file_path} to Drive ID: {uploaded_file.get('id')}")
            return uploaded_file.get('id')
        except Exception as e:
            print(f"[DriveService] Upload error: {e}")
            return None


class VertexAIService:
    """Manages content generation using Vertex AI Gemini models."""

    def __init__(self, project_id: Optional[str] = None, location: str = "us-central1"):
        self.model = None
        self.project_id = project_id or os.getenv("GCP_PROJECT_ID")
        self.location = location

        if not GOOGLE_LIBS_AVAILABLE or not self.project_id:
            print("[VertexAI] Vertex AI environment not initialized. Dry-run mode enabled.")
            return

        try:
            vertexai.init(project=self.project_id, location=self.location)
            self.model = GenerativeModel("gemini-1.5-pro-002")
            print(f"[VertexAI] Connected to Vertex AI project '{self.project_id}' using Gemini 1.5 Pro.")
        except Exception as e:
            print(f"[VertexAI] Initialization notice: {e}")

    def generate_full_article(self, topic_brief: str) -> Dict[str, Any]:
        """Generates a complete, structured 1500+ words article with metadata."""
        if not self.model:
            print("[VertexAI] Generating sample structured article in dry-run mode...")
            return self._generate_dry_run_article(topic_brief)

        system_instruction = """
        You are the Chief Technology Editor at NexusSphere, a world-class technology publication.
        Generate an exhaustive, highly technical, and engaging 1500+ words deep-dive article.
        You must return ONLY a valid JSON object matching this schema:
        {
          "title": "Article Title",
          "subtitle": "Comprehensive subtitle explaining key takeaways",
          "category": "ai|tech|science|health|economics",
          "category_badge": "Category Display Name",
          "author_name": "Dr. Author Name",
          "author_role": "Author Title / Research Lab",
          "read_time": "12 min read",
          "word_count": 1600,
          "lead_image_caption": "Caption describing the lead visual",
          "executive_summary": "Paragraph summarizing core findings and implications",
          "table_of_contents": [
            {"id": "section-1", "title": "1. Section Heading"}
          ],
          "sections_html": "Full semantic HTML for the article body including <h2>, <h3>, <p>, <ul>, <ol>, <blockquote class='editorial-quote'>, and comparison <table> with .data-table class.",
          "faq": [
            {"question": "FAQ question?", "answer": "Detailed answer"}
          ]
        }
        Ensure the sections_html prose is thoroughly detailed and contains 1,500+ words of content.
        """

        prompt = f"Write an authoritative 1,500+ words investigative article on the following topic/brief:\n\n{topic_brief}"

        try:
            config = GenerationConfig(
                response_mime_type="application/json",
                temperature=0.7,
                max_output_tokens=8192
            )
            response = self.model.generate_content(
                contents=[system_instruction, prompt],
                generation_config=config
            )
            return json.loads(response.text)
        except Exception as e:
            print(f"[VertexAI] Error during generation: {e}. Falling back to dry-run template.")
            return self._generate_dry_run_article(topic_brief)

    def _generate_dry_run_article(self, topic: str) -> Dict[str, Any]:
        """Fallback mock generator for dry runs and verification."""
        clean_topic = topic.strip() if topic else "Autonomous Edge Computing & Decentralized Neural Networks"
        slug = re.sub(r'[^a-zA-Z0-9]+', '-', clean_topic.lower()).strip('-')
        return {
            "title": f"The Evolution of {clean_topic}: Architectures, Scale, and Frontiers",
            "subtitle": "How next-generation infrastructure, algorithmic efficiency, and distributed protocols are redefining real-time computation.",
            "category": "tech",
            "category_badge": "Distributed Computing",
            "author_name": "Dr. Elena Vance",
            "author_role": "Senior Fellow in Autonomous Systems",
            "read_time": "11 min read",
            "word_count": 1580,
            "slug": slug,
            "lead_image_caption": "Figure 1.1: Decentralized compute clusters executing real-time distributed tensor parallelism across edge nodes.",
            "executive_summary": "As computational demands soar, monolithic centralized datacenters face fundamental physical latency and bandwidth thresholds. This investigation explores the transition toward decentralized neuromorphic fabrics and zero-latency edge topologies.",
            "table_of_contents": [
              {"id": "section-foundations", "title": "1. Foundational Architecture"},
              {"id": "section-benchmarks", "title": "2. Performance & Latency Matrix"},
              {"id": "section-deployment", "title": "3. Real-World Deployment Models"},
              {"id": "section-future", "title": "4. The Next Decade Roadmap"}
            ],
            "sections_html": f"""
              <section id="section-foundations">
                <h2>1. Foundational Architecture</h2>
                <p>The historical trajectory of computing has oscillated between extreme centralization and distributed decentralization. In the current computational epoch, the demands of real-time synthetic cognition, autonomous robotics, and municipal sensor telemetries necessitate processing paradigms that execute directly at the point of data acquisition.</p>
                <p>By leveraging sparse activation models, weight quantization down to sub-4-bit precision, and micro-kernel hardware accelerators, modern engineers can deploy multi-billion parameter foundation models across compact edge devices without sacrificing numerical fidelity.</p>
                <blockquote class="editorial-quote">
                  "Decentralized intelligence is not simply an optimization—it is the indispensable foundation for resilient global systems."
                  <span class="quote-author">&mdash; NexusSphere Research Collective</span>
                </blockquote>
              </section>

              <section id="section-benchmarks">
                <h2>2. Performance &amp; Latency Matrix</h2>
                <p>Empirical evaluations across 50,000 distributed edge nodes demonstrate dramatic throughput gains compared to conventional centralized API routing:</p>
                <div class="table-container">
                  <table class="data-table">
                    <thead>
                      <tr>
                        <th>Metric</th>
                        <th>Centralized Cloud Compute</th>
                        <th>Hybrid Regional Clusters</th>
                        <th>Autonomous Edge Fabric</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr>
                        <td><strong>Roundtrip Latency</strong></td>
                        <td>120ms - 450ms</td>
                        <td>35ms - 80ms</td>
                        <td>&lt; 4ms</td>
                      </tr>
                      <tr>
                        <td><strong>Offline Resilience</strong></td>
                        <td>0% (Connection Dependent)</td>
                        <td>Partial Buffer</td>
                        <td>100% Autonomous Function</td>
                      </tr>
                      <tr>
                        <td><strong>Bandwidth Ingestion Cost</strong></td>
                        <td>High ($0.08 / GB)</td>
                        <td>Moderate ($0.03 / GB)</td>
                        <td>Near Zero (Local Processing)</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </section>

              <section id="section-deployment">
                <h2>3. Real-World Deployment Models</h2>
                <p>From autonomous agricultural swarms managing soil nutrient hydration in real time to robotic surgery assistants operating in remote clinics, localized edge inference decouples mission-critical performance from brittle wide-area telecom infrastructure.</p>
                <p>Furthermore, privacy-preserving cryptographic protocols—such as federated differential privacy and secure multi-party computation—ensure user data remains localized on-device while model weights receive decentralized global improvements.</p>
              </section>

              <section id="section-future">
                <h2>4. The Next Decade Roadmap</h2>
                <p>Over the coming decade, the symbiosis between neuromorphic silicon, photonics, and adaptive sparse architectures will unlock always-on, zero-watt standby intelligence across billions of interconnected physical nodes.</p>
              </section>
            """,
            "faq": [
              {
                "question": "What is the primary advantage of edge neural computing?",
                "answer": "Sub-millisecond latency, complete operational autonomy during network partitions, and guaranteed data privacy since data never leaves the local perimeter."
              },
              {
                "question": "How does quantization preserve model accuracy?",
                "answer": "Advanced techniques like post-training mixed-precision quantization and outlier-channel protection retain over 99.2% of full-precision benchmark performance."
              }
            ]
        }


class ContentPublisher:
    """Renders structured article data into full HTML and updates website archives."""

    def __init__(self, workspace_root: str):
        self.workspace_root = workspace_root

    def render_and_save_article(self, article_data: Dict[str, Any]) -> str:
        """Renders an article into standard NexusSphere HTML template."""
        slug = article_data.get('slug') or re.sub(r'[^a-zA-Z0-9]+', '-', article_data['title'].lower()).strip('-')
        file_name = f"article-{slug}.html"
        output_path = os.path.join(self.workspace_root, file_name)

        # Build TOC list HTML
        toc_items = ""
        for item in article_data.get('table_of_contents', []):
            toc_items += f'<li><a href="#{item["id"]}" class="toc-link">{item["title"]}</a></li>\n'

        # Build FAQ list HTML
        faq_items = ""
        for idx, faq in enumerate(article_data.get('faq', [])):
            active_class = " active" if idx == 0 else ""
            faq_items += f"""
            <div class="faq-item{active_class}">
              <button class="faq-question">
                {faq["question"]}
                <span class="faq-icon">▼</span>
              </button>
              <div class="faq-answer">
                {faq["answer"]}
              </div>
            </div>
            """

        date_str = datetime.now().strftime("%B %d, %Y")

        html_content = f"""<!DOCTYPE html>
<html lang="en" data-theme="light">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{article_data['title']} | NexusSphere</title>
  <meta name="description" content="{article_data.get('subtitle', '')}">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Merriweather:ital,wght@0,300;0,400;0,700;1,300;1,400&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
  <link rel="stylesheet" href="css/styles.css">
</head>
<body>
  <div id="reading-progress"></div>

  <header class="site-header">
    <div class="container header-inner">
      <a href="index.html" class="brand-logo">
        <span class="brand-icon">⚡</span>
        NexusSphere
      </a>
      <nav>
        <ul class="nav-links">
          <li><a href="index.html" class="nav-link">Home</a></li>
          <li><a href="categories.html" class="nav-link">Categories</a></li>
          <li><a href="article.html" class="nav-link">Featured Article</a></li>
          <li><a href="about.html" class="nav-link">About</a></li>
          <li><a href="contact.html" class="nav-link">Contact</a></li>
        </ul>
      </nav>
      <div class="header-actions">
        <button class="theme-toggle-btn" aria-label="Toggle Theme">
          <span class="theme-toggle-icon">🌙</span>
        </button>
        <a href="categories.html" class="btn btn-primary">Explore Hub</a>
        <button class="mobile-menu-toggle" aria-label="Open Navigation Menu">☰</button>
      </div>
    </div>
  </header>

  <main class="container section-padding">
    <header class="article-header">
      <div class="hero-badge badge-{article_data.get('category', 'tech')}">⚡ {article_data.get('category_badge', 'Editorial')}</div>
      <h1 class="article-main-title">{article_data['title']}</h1>
      <p class="article-subtitle">{article_data.get('subtitle', '')}</p>
      
      <div class="article-author-bar">
        <div class="author-mini">
          <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=100&auto=format&fit=crop&q=80" alt="{article_data.get('author_name', 'NexusSphere Fellow')}">
          <div class="author-mini-info">
            <h4>{article_data.get('author_name', 'Dr. Elena Vance')}</h4>
            <span>{article_data.get('author_role', 'Senior Fellow')}</span>
          </div>
        </div>
        <div class="article-meta">
          <span>📅 Published: {date_str}</span>
          <span>⏱️ {article_data.get('read_time', '10 min read')}</span>
          <span>💬 Automated Dispatch</span>
        </div>
      </div>
    </header>

    <figure class="article-lead-image">
      <img src="assets/images/ai_future_hero.jpg" alt="{article_data['title']}">
      <figcaption class="image-caption">{article_data.get('lead_image_caption', 'Visual investigation figure')}</figcaption>
    </figure>

    <div class="article-layout">
      <aside class="article-toc-sidebar">
        <h4 class="toc-title">📑 In This Article</h4>
        <ul class="toc-list">
          {toc_items}
          <li><a href="#section-faq" class="toc-link">Frequently Asked Questions</a></li>
        </ul>
      </aside>

      <article class="article-prose">
        <div class="takeaway-box">
          <h4>💡 Executive Summary</h4>
          <p>{article_data.get('executive_summary', '')}</p>
        </div>

        {article_data.get('sections_html', '')}

        <section id="section-faq">
          <h2>Frequently Asked Questions</h2>
          <div class="faq-list">
            {faq_items}
          </div>
        </section>

        <div class="author-bio-card">
          <img src="https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=200&auto=format&fit=crop&q=80" alt="{article_data.get('author_name', 'Fellow')}" class="author-bio-avatar">
          <div class="author-bio-details">
            <h3>{article_data.get('author_name', 'Dr. Elena Vance')}</h3>
            <span class="author-role">{article_data.get('author_role', 'Senior Fellow')}</span>
            <p>Contributing researcher and technology architect specializing in distributed systems, autonomous machine learning, and emerging computing paradigms.</p>
          </div>
        </div>
      </article>

      <aside class="article-tools-sidebar">
        <div class="share-widget">
          <h4>Share Insight</h4>
          <div class="share-buttons">
            <button class="share-btn" data-platform="twitter" title="Share on X / Twitter">𝕏</button>
            <button class="share-btn" data-platform="linkedin" title="Share on LinkedIn">in</button>
            <button class="share-btn" data-platform="copy" title="Copy Link to Clipboard">🔗</button>
          </div>
        </div>
      </aside>
    </div>
  </main>

  <footer class="site-footer">
    <div class="container">
      <div class="footer-bottom">
        <p>&copy; 2026 NexusSphere Media Inc. All rights reserved.</p>
        <p>Automated via GitHub Actions, Vertex AI &amp; Google Drive APIs.</p>
      </div>
    </div>
  </footer>

  <script src="js/main.js"></script>
</body>
</html>
"""
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"[Publisher] Saved new publication to {output_path}")
        return output_path


def main():
    parser = argparse.ArgumentParser(description="NexusSphere Content Automation Engine")
    parser.add_argument("--topic", type=str, default="", help="Direct topic brief for article generation")
    parser.add_argument("--drive-folder", type=str, default=os.getenv("DRIVE_FOLDER_ID", ""), help="Google Drive input folder ID")
    parser.add_argument("--backup-folder", type=str, default=os.getenv("DRIVE_BACKUP_FOLDER_ID", ""), help="Google Drive output folder ID")
    parser.add_argument("--credentials", type=str, default=os.getenv("GCP_SA_KEY_PATH", "sa_credentials.json"), help="Service account credentials JSON path")
    parser.add_argument("--dry-run", action="store_true", help="Execute without calling live APIs")

    args = parser.parse_args()
    workspace_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    print(f"=== Starting NexusSphere Automation Pipeline ===")
    print(f"Workspace root: {workspace_root}")

    # 1. Initialize Drive & Vertex AI services
    drive_service = GoogleDriveService(args.credentials)
    vertex_service = VertexAIService()
    publisher = ContentPublisher(workspace_root)

    # 2. Check for Drive prompts or CLI topic
    prompts_to_process = []
    if args.drive_folder and not args.dry_run:
        prompts_to_process = drive_service.fetch_prompts_from_folder(args.drive_folder)

    if not prompts_to_process:
        topic = args.topic or "Quantum Neuromorphic Architectures & Next-Gen Edge Intelligence"
        prompts_to_process.append({"name": "manual_trigger.txt", "content": topic})

    # 3. Process each prompt with Vertex AI and publish
    for prompt_item in prompts_to_process:
        print(f"\n[Pipeline] Processing topic: {prompt_item['name']}")
        article_data = vertex_service.generate_full_article(prompt_item['content'])
        
        output_file = publisher.render_and_save_article(article_data)

        # 4. Optional backup to Google Drive
        if args.backup_folder and not args.dry_run:
            drive_service.upload_article_backup(output_file, args.backup_folder)

    print("\n=== Automation Pipeline Run Complete ===")


if __name__ == "__main__":
    main()
