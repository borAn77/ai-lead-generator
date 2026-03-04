# ai-lead-generator

AI-powered system that generates verified B2B leads and outreach emails.

## Features

- Find businesses by niche + location
- Discover and verify emails
- Remove duplicates
- Generate AI outreach emails
- Export leads to CSV
- Simple Streamlit UI

## Tech Stack

- Python
- FastAPI
- Streamlit
- SerpAPI
- OpenAI

## Demo Video

[Watch the demo](assets/demo.mp4)

## Installation

```bash
git clone https://github.com/yourusername/ai-lead-generator
cd ai-lead-generator
pip install -r requirements.txt

#SETUP
Create .env file:

OPENAI_API_KEY=
SERPAPI_API_KEY=

#Run Backend
python -m uvicorn app.main:app --reload

#Run UI
streamlit run ui.py