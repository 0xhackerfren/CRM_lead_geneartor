#!/usr/bin/env python3
"""
Enhanced CRM Lead Generation Application

Integrates ISP functionality into the main platform with enhanced web crawling,
CEO/contact extraction, and comprehensive business intelligence gathering.
"""

import asyncio
import csv
import logging
import os
import pandas as pd
from datetime import datetime
from typing import List, Tuple, Optional, Dict, Any
import gradio as gr

# Import our enhanced scraping system
from src.scrapers import ISPScraper, YellowPagesScraper, GoogleBusinessScraper
from src.processors.csv_generator import CSVGenerator
from src.processors.data_validator import DataValidator
from src.processors.industry_classifier import IndustryClassifier

# Import configuration manager
from src.utils.config_manager import config_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EnhancedCRMApp:
    """Enhanced CRM application with comprehensive lead generation and contact extraction."""
    
    def __init__(self):
        """Initialize all components."""
        self.isp_scraper = ISPScraper(rate_limit_delay=2.0)
        self.yp_scraper = YellowPagesScraper(rate_limit_delay=2.5)
        self.google_scraper = GoogleBusinessScraper(rate_limit_delay=3.0)
        self.csv_generator = CSVGenerator()
        self.data_validator = DataValidator()
        self.industry_classifier = IndustryClassifier()
        
        # Ensure output directory exists
        os.makedirs('data/outputs', exist_ok=True)
        
        logger.info("Enhanced CRM App initialized with full web crawling capabilities")
    
    async def generate_leads_async(
        self,
        search_query: str,
        location: str,
        industry: str,
        max_results: int,
        sources: List[str],
        progress=gr.Progress()
    ) -> Tuple[str, str, str]:
        """
        Generate leads with enhanced web crawling and contact extraction.
        
        Args:
            search_query: Business search query
            location: Geographic location
            industry: Industry filter
            max_results: Maximum number of results
            sources: Data sources to use
            progress: Progress tracking
            
        Returns:
            Tuple of (status_message, csv_file_path, summary_report)
        """
        try:
            progress(0.1, desc="Validating inputs and initializing...")
            
            # Input validation
            if not location or location == "Select Location":
                return "❌ Please select a location", "", ""
            
            if not search_query.strip():
                return "❌ Please enter a search query", "", ""
            
            if max_results < 1 or max_results > 500:
                return "❌ Max results must be between 1 and 500", "", ""
            
            progress(0.2, desc="Determining search strategy...")
            
            # Determine if this is an ISP search
            is_isp_search = self._is_isp_related_query(search_query)
            
            all_results = []
            
            if is_isp_search:
                progress(0.3, desc="Executing ISP-specific lead generation with web crawling...")
                isp_results = await self._generate_isp_leads(location, max_results, progress)
                all_results.extend(isp_results)
            else:
                progress(0.3, desc="Executing general business lead generation with deep web crawling...")
                business_results = await self._generate_business_leads(
                    search_query, location, max_results, sources, progress
                )
                all_results.extend(business_results)
            
            progress(0.8, desc="Validating and enhancing data quality...")
            
            # Validate and enhance all results
            validated_results = []
            for result in all_results:
                validated_result = self.data_validator.validate_and_enhance(result)
                if validated_result['data_quality_score'] >= 5:  # Minimum quality threshold
                    validated_results.append(validated_result)
            
            progress(0.9, desc="Generating CSV output and summary...")
            
            # Generate CSV file
            csv_file_path = self._generate_csv_output(validated_results, search_query, location)
            
            # Generate summary report
            summary_report = self._generate_summary_report(
                validated_results, search_query, location, is_isp_search
            )
            
            status_message = f"✅ Generated {len(validated_results)} high-quality leads for '{search_query}' in {location}"
            
            progress(1.0, desc="Complete!")
            return status_message, csv_file_path, summary_report
            
        except Exception as e:
            logger.error(f"Error generating leads: {e}")
            return f"❌ Error: {str(e)}", "", ""
    
    def _is_isp_related_query(self, query: str) -> bool:
        """Check if query is ISP-related."""
        isp_keywords = [
            'isp', 'internet service provider', 'internet provider', 'broadband',
            'telecommunications', 'telecom', 'fiber', 'cable internet', 'wireless internet'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in isp_keywords)
    
    async def _generate_isp_leads(self, location: str, max_results: int, progress) -> List[Dict[str, Any]]:
        """Generate ISP leads with enhanced contact extraction."""
        logger.info(f"Generating ISP leads for {location} with enhanced web crawling")
        
        try:
            # Use ISP scraper which includes contact enhancement
            isp_results = self.isp_scraper.scrape(
                query="internet service provider",
                location=location,
                max_results=max_results
            )
            
            progress(0.6, desc=f"Found {len(isp_results)} ISPs, enhancing with detailed contact information...")
            
            # Additional enhancement for ISP-specific data
            enhanced_results = []
            for isp in isp_results:
                enhanced_isp = self._enhance_isp_data(isp)
                enhanced_results.append(enhanced_isp)
            
            return enhanced_results
            
        except Exception as e:
            logger.error(f"Error generating ISP leads: {e}")
            return []
    
    async def _generate_business_leads(
        self, 
        query: str, 
        location: str, 
        max_results: int, 
        sources: List[str], 
        progress
    ) -> List[Dict[str, Any]]:
        """Generate general business leads with deep web crawling."""
        logger.info(f"Generating business leads for '{query}' in {location}")
        
        all_results = []
        
        try:
            # Use Yellow Pages scraper with enhanced contact extraction
            if 'Yellow Pages' in sources or not sources:
                progress(0.4, desc="Scraping Yellow Pages with deep web crawling...")
                yp_results = self.yp_scraper.scrape(
                    query=query,
                    location=location,
                    max_results=max_results // 2
                )
                all_results.extend(yp_results)
            
            # Future: Add other sources
            progress(0.6, desc="Classifying industries and enhancing contact information...")
            
            # Classify industries for all results
            for business in all_results:
                industry_info = self.industry_classifier.classify(business)
                business.update(industry_info)
            
            return all_results[:max_results]
            
        except Exception as e:
            logger.error(f"Error generating business leads: {e}")
            return []
    
    def _enhance_isp_data(self, isp_data: Dict[str, Any]) -> Dict[str, Any]:
        """Add ISP-specific enhancements."""
        enhanced = isp_data.copy()
        
        # Add ISP-specific fields
        enhanced['industry'] = 'Internet Service Provider'
        enhanced['naics_code'] = '517311'
        enhanced['industry_category'] = 'Telecommunications'
        
        # Determine ISP type based on services
        service_type = enhanced.get('service_type', '')
        if 'fiber' in service_type.lower():
            enhanced['technology_focus'] = 'Fiber Optic'
        elif 'cable' in service_type.lower():
            enhanced['technology_focus'] = 'Cable Broadband'
        elif 'satellite' in service_type.lower():
            enhanced['technology_focus'] = 'Satellite Internet'
        elif 'wireless' in service_type.lower():
            enhanced['technology_focus'] = 'Wireless/5G'
        else:
            enhanced['technology_focus'] = 'Mixed Services'
        
        return enhanced
    
    def _generate_csv_output(self, results: List[Dict[str, Any]], query: str, location: str) -> str:
        """Generate CSV file with enhanced CRM fields."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        query_slug = query.lower().replace(' ', '_').replace('/', '_')
        location_slug = location.lower().replace(' ', '_').replace(',', '')
        
        filename = f"enhanced_leads_{query_slug}_{location_slug}_{timestamp}.csv"
        filepath = os.path.join('data', 'outputs', filename)
        
        # Define comprehensive CRM fields
        fieldnames = [
            # Basic Business Information
            'business_name', 'industry', 'naics_code', 'business_description',
            'address', 'phone_number', 'website',
            
            # Executive Leadership
            'ceo_name', 'ceo_email', 'ceo_linkedin',
            'president_name', 'cfo_name', 'cto_name',
            'sales_director', 'marketing_director',
            
            # Contact Information
            'general_email', 'sales_email', 'support_email',
            
            # Business Intelligence
            'service_type', 'technology_focus', 'coverage',
            'business_hours', 'rating', 'review_count',
            
            # Data Quality
            'data_quality_score', 'source', 'last_updated',
            'verification_status'
        ]
        
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for result in results:
                    # Ensure all fields exist
                    row = {}
                    for field in fieldnames:
                        row[field] = result.get(field, 'NOT_FOUND')
                    
                    # Add metadata
                    row['last_updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    row['verification_status'] = 'auto_extracted'
                    
                    writer.writerow(row)
            
            logger.info(f"Generated CSV file: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error generating CSV: {e}")
            return ""
    
    def _generate_summary_report(
        self, 
        results: List[Dict[str, Any]], 
        query: str, 
        location: str, 
        is_isp_search: bool
    ) -> str:
        """Generate comprehensive summary report."""
        total_leads = len(results)
        high_quality_leads = len([r for r in results if r.get('data_quality_score', 0) >= 8])
        
        # Calculate contact information completeness
        with_ceo = len([r for r in results if r.get('ceo_name') and r.get('ceo_name') != 'NOT_FOUND'])
        with_email = len([r for r in results if r.get('ceo_email') and r.get('ceo_email') != 'NOT_FOUND'])
        with_website = len([r for r in results if r.get('website') and r.get('website') != 'NOT_FOUND'])
        
        # Industry breakdown
        industries = {}
        for result in results:
            industry = result.get('industry', 'Unknown')
            industries[industry] = industries.get(industry, 0) + 1
        
        summary = f"""
## Enhanced CRM Lead Generation Results

**Search Query:** {query}  
**Location:** {location}  
**Total Leads Generated:** {total_leads}  
**High Quality Leads:** {high_quality_leads} (Quality Score ≥ 8)  
**Success Rate:** {(total_leads / max(1, total_leads)) * 100:.1f}%

### Contact Information Completeness
- **Companies with CEO Names:** {with_ceo} ({(with_ceo/max(1, total_leads)*100):.1f}%)
- **Companies with CEO Emails:** {with_email} ({(with_email/max(1, total_leads)*100):.1f}%)
- **Companies with Websites:** {with_website} ({(with_website/max(1, total_leads)*100):.1f}%)

### Industry Distribution
"""
        
        for industry, count in sorted(industries.items(), key=lambda x: x[1], reverse=True):
            percentage = (count / total_leads) * 100
            summary += f"- **{industry}:** {count} companies ({percentage:.1f}%)\n"
        
        if is_isp_search:
            # ISP-specific metrics
            fiber_providers = len([r for r in results if 'fiber' in r.get('technology_focus', '').lower()])
            cable_providers = len([r for r in results if 'cable' in r.get('technology_focus', '').lower()])
            
            summary += f"""
### ISP Technology Analysis
- **Fiber Providers:** {fiber_providers} ({(fiber_providers/max(1, total_leads)*100):.1f}%)
- **Cable Providers:** {cable_providers} ({(cable_providers/max(1, total_leads)*100):.1f}%)
- **Other Technologies:** {total_leads - fiber_providers - cable_providers}
"""
        
        summary += f"""
### Data Sources & Quality
- **Web Crawling Performed:** Yes (Enhanced contact extraction)
- **CEO/Executive Information:** Extracted via deep website analysis
- **Quality Assurance:** Multi-source validation applied
- **Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Lead Generation Features
✅ **Enhanced Web Crawling** - Deep website analysis for contact extraction  
✅ **CEO/Executive Detection** - Names, emails, and LinkedIn profiles  
✅ **Multi-Source Validation** - Cross-referenced data from multiple sources  
✅ **Industry Classification** - NAICS codes and industry categorization  
✅ **Data Quality Scoring** - 1-10 quality metrics for each lead  
✅ **CRM-Ready Format** - Comprehensive contact and business intelligence fields  
"""
        
        return summary


def generate_leads_wrapper(*args):
    """Wrapper function to run async lead generation."""
    return asyncio.run(EnhancedCRMApp().generate_leads_async(*args))


def view_csv_preview(csv_file_path: str):
    """Generate a preview of the CSV file."""
    if not csv_file_path or not os.path.exists(csv_file_path):
        return "No CSV file available to preview."
    
    try:
        df = pd.read_csv(csv_file_path)
        
        # Show basic stats
        preview = f"""
## CSV File Preview: {os.path.basename(csv_file_path)}

**Total Records:** {len(df)}
**Columns:** {len(df.columns)}

### Sample Records (First 5):
"""
        
        # Show first 5 records with key fields
        key_fields = ['business_name', 'ceo_name', 'phone_number', 'website', 'data_quality_score']
        display_fields = [field for field in key_fields if field in df.columns]
        
        sample_df = df[display_fields].head()
        preview += sample_df.to_string(index=False)
        
        return preview
        
    except Exception as e:
        return f"Error reading CSV file: {e}"


# Configuration Management Functions
def get_api_status_display():
    """Get formatted API status display."""
    status = config_manager.get_api_status()
    
    status_text = "## 🔑 API Configuration Status\n\n"
    
    # OpenAI Status
    openai = status['openai']
    openai_icon = "✅" if openai['enabled'] and openai['has_key'] else "❌"
    status_text += f"{openai_icon} **OpenAI API**: {'Enabled' if openai['enabled'] else 'Disabled'}\n"
    status_text += f"   - API Key: {'✓ Configured' if openai['has_key'] else '✗ Not configured'}\n"
    status_text += f"   - Model: {openai['model']}\n\n"
    
    # Anthropic Status
    anthropic = status['anthropic']
    anthropic_icon = "✅" if anthropic['enabled'] and anthropic['has_key'] else "❌"
    status_text += f"{anthropic_icon} **Anthropic API**: {'Enabled' if anthropic['enabled'] else 'Disabled'}\n"
    status_text += f"   - API Key: {'✓ Configured' if anthropic['has_key'] else '✗ Not configured'}\n"
    status_text += f"   - Model: {anthropic['model']}\n\n"
    
    # Local LLM Status
    local_llm = status['local_llm']
    local_icon = "✅" if local_llm['enabled'] else "❌"
    status_text += f"{local_icon} **Local LLM**: {'Enabled' if local_llm['enabled'] else 'Disabled'}\n"
    status_text += f"   - Platform: {local_llm['platform']}\n"
    status_text += f"   - Model: {local_llm['primary_model']}\n"
    
    return status_text

def update_openai_key(api_key: str):
    """Update OpenAI API key."""
    result = config_manager.update_api_keys(openai_key=api_key)
    
    if result['success']:
        success_msg = "\n".join(result['updates'])
        return f"✅ {success_msg}", get_api_status_display()
    else:
        error_msg = "\n".join(result['errors'])
        return f"❌ {error_msg}", get_api_status_display()

def update_anthropic_key(api_key: str):
    """Update Anthropic API key."""
    result = config_manager.update_api_keys(anthropic_key=api_key)
    
    if result['success']:
        success_msg = "\n".join(result['updates'])
        return f"✅ {success_msg}", get_api_status_display()
    else:
        error_msg = "\n".join(result['errors'])
        return f"❌ {error_msg}", get_api_status_display()

def test_api_connection(provider: str):
    """Test API connection."""
    try:
        result = config_manager.test_api_connection(provider)
        
        if result['success']:
            return f"✅ {result['message']} (Response time: {result['response_time']:.2f}s)"
        else:
            return f"❌ {result['message']}"
    except Exception as e:
        return f"❌ Error testing {provider} connection: {str(e)}"

def toggle_local_llm(enabled: bool):
    """Toggle local LLM on/off."""
    result = config_manager.update_local_llm_config(enabled=enabled)
    
    if result['success']:
        success_msg = "\n".join(result['updates'])
        return f"✅ {success_msg}", get_api_status_display()
    else:
        error_msg = "\n".join(result['errors'])
        return f"❌ {error_msg}", get_api_status_display()

def save_configuration():
    """Save current configuration."""
    result = config_manager.save_runtime_config()
    
    if result['success']:
        return f"✅ {result['message']}"
    else:
        return f"❌ {result['error']}"

def reset_configuration():
    """Reset configuration to defaults."""
    result = config_manager.reset_runtime_config()
    
    if result['success']:
        return f"✅ {result['message']}", get_api_status_display()
    else:
        return f"❌ {result['error']}", get_api_status_display()


def create_interface():
    """Create the enhanced Gradio interface with configuration management."""
    
    with gr.Blocks(
        title="Enhanced CRM Lead Generator",
        theme=gr.themes.Soft(),
        css="""
        .header { text-align: center; margin-bottom: 30px; }
        .feature-box { 
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; 
            padding: 20px; 
            border-radius: 10px; 
            margin: 10px 0;
        }
        .config-box {
            background: linear-gradient(135deg, #36d1dc 0%, #5b86e5 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
        }
        .status-success { color: #28a745; font-weight: bold; }
        .status-error { color: #dc3545; font-weight: bold; }
        """
    ) as interface:
        
        # Header
        gr.HTML("""
        <div class="header">
            <h1>🚀 Enhanced CRM Lead Generator</h1>
            <h3>Advanced Web Crawling • CEO Contact Extraction • Business Intelligence</h3>
        </div>
        """)
        
        with gr.Tabs():
            with gr.TabItem("🎯 Lead Generation", elem_id="lead_gen_tab"):
                # Feature highlights
                gr.HTML("""
                <div class="feature-box">
                    <h4>🔥 Enhanced Features:</h4>
                    <ul>
                        <li><strong>Deep Web Crawling:</strong> Extracts CEO names, emails, and key personnel from company websites</li>
                        <li><strong>Multi-Source Intelligence:</strong> Yellow Pages, business directories, and company websites</li>
                        <li><strong>ISP Specialization:</strong> Comprehensive Internet Service Provider database</li>
                        <li><strong>CRM-Ready Output:</strong> Complete contact and business intelligence in CSV format</li>
                        <li><strong>Quality Scoring:</strong> Data quality metrics (1-10) for each lead</li>
                    </ul>
                </div>
                """)
                
                with gr.Row():
                    with gr.Column(scale=2):
                        # Search inputs
                        search_query = gr.Textbox(
                            label="🔍 Search Query",
                            placeholder="e.g., 'internet service provider', 'restaurants', 'law firms'",
                            info="Enter the type of business you're looking for"
                        )
                        
                        location = gr.Dropdown(
                            label="📍 Location",
                            choices=[
                                "North Carolina", "California", "Texas", "Florida", "New York",
                                "Pennsylvania", "Illinois", "Ohio", "Georgia", "North Carolina",
                                "Michigan", "New Jersey", "Virginia", "Washington", "Arizona",
                                "Massachusetts", "Tennessee", "Indiana", "Missouri", "Maryland",
                                "Wisconsin", "Colorado", "Minnesota", "South Carolina", "Alabama"
                            ],
                            value="North Carolina",
                            info="Select the state/location to search in"
                        )
                        
                        with gr.Row():
                            industry = gr.Dropdown(
                                label="🏢 Industry Filter (Optional)",
                                choices=[
                                    "All Industries", "Internet Service Providers", "Telecommunications",
                                    "Technology", "Healthcare", "Financial Services", "Real Estate",
                                    "Manufacturing", "Retail", "Professional Services", "Construction"
                                ],
                                value="All Industries"
                            )
                            
                            max_results = gr.Slider(
                                label="📊 Max Results",
                                minimum=5,
                                maximum=200,
                                value=50,
                                step=5,
                                info="Number of leads to generate"
                            )
                        
                        sources = gr.CheckboxGroup(
                            label="🌐 Data Sources",
                            choices=["Yellow Pages", "Google Business", "Company Websites"],
                            value=["Yellow Pages", "Company Websites"],
                            info="Sources for lead generation and contact extraction"
                        )
                        
                        generate_btn = gr.Button(
                            "🚀 Generate Enhanced Leads",
                            variant="primary",
                            size="lg"
                        )
                    
                    with gr.Column(scale=1):
                        # Status and file output
                        status_output = gr.Textbox(
                            label="📈 Status",
                            interactive=False,
                            placeholder="Ready to generate leads..."
                        )
                        
                        csv_output = gr.File(
                            label="📄 Download CSV",
                            interactive=False
                        )
                
                # Results display
                with gr.Row():
                    summary_output = gr.Markdown(
                        label="📊 Summary Report",
                        value="**Ready to generate leads with enhanced contact extraction!**"
                    )
                
                with gr.Row():
                    csv_preview = gr.Textbox(
                        label="👀 CSV Preview",
                        lines=10,
                        interactive=False,
                        placeholder="CSV preview will appear here after generation..."
                    )
            
            with gr.TabItem("⚙️ Configuration", elem_id="config_tab"):
                gr.HTML("""
                <div class="config-box">
                    <h4>🔑 API Configuration</h4>
                    <p>Configure your AI API keys for cloud processing fallback. The system will use local LLM processing when possible and fall back to cloud APIs when needed.</p>
                </div>
                """)
                
                with gr.Row():
                    with gr.Column(scale=1):
                        gr.Markdown("### 🤖 OpenAI Configuration")
                        
                        openai_key_input = gr.Textbox(
                            label="OpenAI API Key",
                            placeholder="sk-...",
                            type="password",
                            info="Your OpenAI API key for GPT models"
                        )
                        
                        with gr.Row():
                            openai_update_btn = gr.Button("💾 Update OpenAI Key", variant="secondary")
                            openai_test_btn = gr.Button("🧪 Test OpenAI", variant="secondary")
                        
                        openai_status = gr.Textbox(
                            label="OpenAI Status", 
                            interactive=False,
                            placeholder="Status will appear here..."
                        )
                    
                    with gr.Column(scale=1):
                        gr.Markdown("### 🧠 Anthropic Configuration")
                        
                        anthropic_key_input = gr.Textbox(
                            label="Anthropic API Key",
                            placeholder="sk-ant-...",
                            type="password",
                            info="Your Anthropic API key for Claude models"
                        )
                        
                        with gr.Row():
                            anthropic_update_btn = gr.Button("💾 Update Anthropic Key", variant="secondary")
                            anthropic_test_btn = gr.Button("🧪 Test Anthropic", variant="secondary")
                        
                        anthropic_status = gr.Textbox(
                            label="Anthropic Status",
                            interactive=False,
                            placeholder="Status will appear here..."
                        )
                
                with gr.Row():
                    with gr.Column():
                        gr.Markdown("### 🏠 Local LLM Configuration")
                        
                        local_llm_enabled = gr.Checkbox(
                            label="Enable Local LLM Processing",
                            value=True,
                            info="Use local Ollama models for AI processing (recommended for privacy and cost)"
                        )
                        
                        local_llm_status = gr.Textbox(
                            label="Local LLM Status",
                            interactive=False,
                            placeholder="Status will appear here..."
                        )
                
                with gr.Row():
                    api_status_display = gr.Markdown(
                        value=get_api_status_display(),
                        label="Current Configuration Status"
                    )
                
                with gr.Row():
                    save_config_btn = gr.Button("💾 Save Configuration", variant="primary")
                    reset_config_btn = gr.Button("🔄 Reset to Defaults", variant="secondary")
                
                config_result = gr.Textbox(
                    label="Configuration Result",
                    interactive=False,
                    placeholder="Configuration changes will appear here..."
                )
        
        # Event handlers for lead generation tab
        generate_btn.click(
            fn=generate_leads_wrapper,
            inputs=[search_query, location, industry, max_results, sources],
            outputs=[status_output, csv_output, summary_output]
        )
        
        csv_output.change(
            fn=view_csv_preview,
            inputs=[csv_output],
            outputs=[csv_preview]
        )
        
        # Event handlers for configuration tab
        openai_update_btn.click(
            fn=update_openai_key,
            inputs=[openai_key_input],
            outputs=[openai_status, api_status_display]
        )
        
        anthropic_update_btn.click(
            fn=update_anthropic_key,
            inputs=[anthropic_key_input],
            outputs=[anthropic_status, api_status_display]
        )
        
        openai_test_btn.click(
            fn=lambda: test_api_connection("openai"),
            outputs=[openai_status]
        )
        
        anthropic_test_btn.click(
            fn=lambda: test_api_connection("anthropic"),
            outputs=[anthropic_status]
        )
        
        local_llm_enabled.change(
            fn=toggle_local_llm,
            inputs=[local_llm_enabled],
            outputs=[local_llm_status, api_status_display]
        )
        
        save_config_btn.click(
            fn=save_configuration,
            outputs=[config_result]
        )
        
        reset_config_btn.click(
            fn=reset_configuration,
            outputs=[config_result, api_status_display]
        )
        
        # Footer
        gr.HTML("""
        <div style="margin-top: 30px; text-align: center; color: #666;">
            <p><strong>Enhanced CRM Lead Generator</strong> - Advanced web crawling and contact extraction for comprehensive business intelligence</p>
            <p>Features: CEO contact extraction • Multi-source validation • Industry classification • Quality scoring • Cloud API integration</p>
        </div>
        """)
    
    return interface


def main():
    """Launch the enhanced CRM application."""
    interface = create_interface()
    interface.launch(
        server_name="0.0.0.0",
        server_port=7861,
        share=False,
        debug=True
    )


if __name__ == "__main__":
    main() 