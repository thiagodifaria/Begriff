import google.generativeai as genai
import json
from typing import Dict, Any
from app.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)

async def generate_personalized_report(user: Dict[str, Any], analysis_data: Dict[str, Any]) -> Dict[str, Any]:
    model = genai.GenerativeModel('gemini-pro')
    prompt = f"""
You are 'Begriff', an expert and friendly financial advisor. Your task is to analyze the following JSON data and provide a personalized, narrative report for the user.

User:
- ID: {user.get('id')}
- Email: {user.get('email')}

Analysis Data:
```json
{json.dumps(analysis_data, indent=2)}
```

Based on the data, provide a concise executive summary (2-3 sentences), identify 2-3 positive insights, and list 3 concrete, actionable recommendations for improvement. Your tone should be encouraging and clear. Your entire response MUST be a single, valid JSON object with the following keys: 'executive_summary', 'positive_insights', 'areas_for_improvement', 'actionable_recommendations'.
"""
    try:
        response = await model.generate_content_async(prompt)
        return json.loads(response.text)
    except Exception as e:
        return {"error": str(e)}
