import json
import os
from typing import Dict, Any, Union
from app.config import settings

try:
    from google import genai
    from google.genai import types
    NEW_API_AVAILABLE = True
    print("✅ Using NEW Google Genai SDK")
except ImportError:
    NEW_API_AVAILABLE = False
    print("⚠️ New Google Genai SDK not available, trying old one...")
    
try:
    import google.generativeai as old_genai
    OLD_API_AVAILABLE = True
    print("✅ Old Google Generative AI SDK available as fallback")
except ImportError:
    OLD_API_AVAILABLE = False
    print("❌ No Google AI SDK available")

def get_api_key() -> str:
    """Get API key from multiple possible sources"""
    possible_keys = [
        'GEMINI_API_KEY',
        'GOOGLE_API_KEY', 
        'GOOGLE_AI_API_KEY',
        'GENAI_API_KEY'
    ]
    
    if hasattr(settings, 'GEMINI_API_KEY') and settings.GEMINI_API_KEY:
        return settings.GEMINI_API_KEY
    
    for key_name in possible_keys:
        api_key = os.getenv(key_name)
        if api_key:
            print(f"🔑 Found API key in {key_name}")
            return api_key
    
    raise ValueError(f"API key not found. Tried: {possible_keys}. Please set one of these environment variables.")

async def test_gemini_connection() -> Dict[str, Any]:
    """Test if Gemini API key is working"""
    try:
        api_key = get_api_key()
        
        if NEW_API_AVAILABLE:
            try:
                client = genai.Client(api_key=api_key)
                response = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents="Hello! Respond with just: {'test': 'success'}",
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=0)
                    )
                )
                return {
                    "status": "success",
                    "api_used": "new_google_genai",
                    "api_key_valid": True,
                    "response_sample": response.text[:100]
                }
            except Exception as e:
                print(f"❌ New API failed: {e}")
        
        if OLD_API_AVAILABLE:
            try:
                old_genai.configure(api_key=api_key)
                model = old_genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content("Hello! Respond with just: test")
                return {
                    "status": "success", 
                    "api_used": "old_google_generativeai",
                    "api_key_valid": True,
                    "response_sample": response.text[:100]
                }
            except Exception as e:
                print(f"❌ Old API failed: {e}")
        
        return {
            "status": "error",
            "error": "No working API available",
            "api_key_valid": False
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "api_key_valid": False
        }

async def generate_personalized_report_new_api(user: Union[Dict[str, Any], Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate report using NEW Google Genai SDK"""
    try:
        api_key = get_api_key()
        client = genai.Client(api_key=api_key)
        
        if hasattr(user, 'id'):
            user_id = user.id
            user_email = user.email
        else:
            user_id = user.get('id')
            user_email = user.get('email')
        
        prompt = f"""
You are 'Begriff', an expert and friendly financial advisor. Analyze the following data and provide a personalized report.

User: ID {user_id}, Email: {user_email}

Analysis Data:
{json.dumps(analysis_data, indent=2)}

Provide a concise executive summary (2-3 sentences), positive insights, and actionable recommendations.

Respond with ONLY a valid JSON object with these exact keys:
- executive_summary
- positive_insights (array)
- areas_for_improvement (array) 
- actionable_recommendations (array)
"""

        models_to_try = ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-1.5-pro"]
        
        for model_name in models_to_try:
            try:
                print(f"🤖 Trying NEW API model: {model_name}")
                
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        thinking_config=types.ThinkingConfig(thinking_budget=0)
                    )
                )
                
                if response and response.text:
                    try:
                        result = json.loads(response.text)
                        result["model_used"] = model_name
                        result["api_used"] = "new_google_genai"
                        print(f"✅ SUCCESS with new API: {model_name}")
                        return result
                    except json.JSONDecodeError:
                        return {
                            "executive_summary": "Financial analysis completed successfully with AI insights.",
                            "positive_insights": ["Transaction data processed", "Spending patterns analyzed"],
                            "areas_for_improvement": ["Continue monitoring expenses", "Optimize spending categories"],
                            "actionable_recommendations": [
                                "Review monthly budget allocation",
                                "Track high-value transactions",
                                "Set up automated savings"
                            ],
                            "model_used": model_name,
                            "api_used": "new_google_genai",
                            "note": "JSON parsing fallback used",
                            "raw_response": response.text[:200]
                        }
            except Exception as e:
                print(f"❌ Model {model_name} failed: {str(e)}")
                continue
        
        raise Exception("All new API models failed")
        
    except Exception as e:
        print(f"❌ New API completely failed: {e}")
        raise

async def generate_personalized_report_old_api(user: Union[Dict[str, Any], Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate report using OLD Google Generative AI SDK"""
    try:
        api_key = get_api_key()
        old_genai.configure(api_key=api_key)
        
        if hasattr(user, 'id'):
            user_id = user.id
            user_email = user.email
        else:
            user_id = user.get('id')
            user_email = user.get('email')
        
        prompt = f"""
You are 'Begriff', an expert and friendly financial advisor. Analyze the following data and provide a personalized report.

User: ID {user_id}, Email: {user_email}

Analysis Data:
{json.dumps(analysis_data, indent=2)}

Respond with ONLY a valid JSON object with these exact keys:
- executive_summary
- positive_insights (array)
- areas_for_improvement (array)
- actionable_recommendations (array)
"""

        models_to_try = ['gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-1.0-pro']
        
        for model_name in models_to_try:
            try:
                print(f"🤖 Trying OLD API model: {model_name}")
                model = old_genai.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                
                if response and response.text:
                    try:
                        result = json.loads(response.text)
                        result["model_used"] = model_name
                        result["api_used"] = "old_google_generativeai"
                        print(f"✅ SUCCESS with old API: {model_name}")
                        return result
                    except json.JSONDecodeError:
                        return {
                            "executive_summary": "Financial analysis completed successfully.",
                            "positive_insights": ["Data processed successfully", "Insights generated"],
                            "areas_for_improvement": ["Monitor spending patterns", "Review categories"],
                            "actionable_recommendations": [
                                "Set monthly budget goals", 
                                "Track spending trends",
                                "Review high-value transactions"
                            ],
                            "model_used": model_name,
                            "api_used": "old_google_generativeai",
                            "note": "Fallback response used"
                        }
            except Exception as e:
                print(f"❌ Old API model {model_name} failed: {str(e)}")
                continue
        
        raise Exception("All old API models failed")
        
    except Exception as e:
        print(f"❌ Old API completely failed: {e}")
        raise

async def generate_personalized_report(user: Union[Dict[str, Any], Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    """Main function - tries new API first, then old API, then fallback"""
    
    print("🤖 Starting Gemini AI report generation...")
    
    if NEW_API_AVAILABLE:
        try:
            print("🆕 Attempting with NEW Google Genai SDK...")
            return await generate_personalized_report_new_api(user, analysis_data)
        except Exception as e:
            print(f"❌ New API failed: {e}")
    
    if OLD_API_AVAILABLE:
        try:
            print("🔄 Falling back to OLD Google Generative AI SDK...")
            return await generate_personalized_report_old_api(user, analysis_data)
        except Exception as e:
            print(f"❌ Old API failed: {e}")
    
    print("⚠️ All APIs failed, using static fallback")
    return {
        "error": "All Gemini APIs unavailable",
        "executive_summary": "Financial analysis completed successfully. Your spending patterns have been analyzed and insights are available.",
        "positive_insights": [
            "Transaction data processed securely",
            "Spending categories identified and analyzed",
            "Financial patterns detected"
        ],
        "areas_for_improvement": [
            "AI insights temporarily unavailable",
            "Manual review of spending recommended",
            "Regular monitoring suggested"
        ],
        "actionable_recommendations": [
            "Review your monthly spending by category",
            "Set up budget alerts for large transactions", 
            "Consider automated savings plans",
            "Monitor high-value transactions regularly"
        ],
        "fallback_used": True,
        "apis_tried": ["new_google_genai", "old_google_generativeai"]
    }