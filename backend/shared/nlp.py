"""
nagarAI - shared/nlp.py
==========================
Category classification and summarization, shared by voice, text, and image pipelines.
"""

from typing import Optional, Tuple

CATEGORIES = [
    "Roads & Traffic",
    "Water & Drainage",
    "Waste Management",
    "Street Lighting & Electricity",
    "Infrastructure Damage",
    "Public Safety",
    "Public Health & Sanitation",
    "Public Transport",
    "Other / General",
]

CATEGORY_DESCRIPTIONS = {
    "Roads & Traffic": "potholes, broken roads, traffic signals not working, traffic jams, illegal parking, road accidents, speed breakers",
    "Water & Drainage": "water supply issues, drainage overflow, sewage leakage, blocked drains, water pipeline leakage, contaminated water",
    "Waste Management": "garbage not collected, overflowing dustbins, illegal dumping, waste segregation issues, dead animals not removed",
    "Street Lighting & Electricity": "street lights not working, power outage, exposed electrical wires, transformer issues, streetlight damaged",
    "Infrastructure Damage": "damaged public property, broken footpaths, collapsed walls, damaged bridges, construction debris left unattended",
    "Public Safety": "unsafe areas, open manholes, stray animals causing danger, unsafe construction sites, lack of security",
    "Public Health & Sanitation": "unhygienic public toilets, mosquito breeding, unsanitary conditions, disease outbreak risk",
    "Public Transport": "bus delays, auto/taxi overcharging, bus stop issues, unavailability of public transport, poor transport infrastructure",
    "Other / General": "general civic complaints not covered elsewhere",
}


class CategoryClassifier:
    def __init__(self, model_name: str = "paraphrase-multilingual-mpnet-base-v2"):
        from sentence_transformers import SentenceTransformer, util
        self.model = SentenceTransformer(model_name)
        self.util = util
        self.category_names = list(CATEGORY_DESCRIPTIONS.keys())
        self.category_embeddings = self.model.encode(
            list(CATEGORY_DESCRIPTIONS.values()), convert_to_tensor=True
        )

    def classify(self, text: str) -> Tuple[str, float]:
        query_embedding = self.model.encode(text, convert_to_tensor=True)
        scores = self.util.cos_sim(query_embedding, self.category_embeddings)[0]
        best_idx = int(scores.argmax())
        return self.category_names[best_idx], float(scores[best_idx])


class Summarizer:
    def __init__(self, use_llm: bool = False, gemini_api_key: Optional[str] = None):
        self.use_llm = use_llm
        if use_llm:
            from google import genai
            self.client = genai.Client(api_key=gemini_api_key)
        else:
            from transformers import pipeline
            self.pipe = pipeline("summarization", model="facebook/bart-large-cnn")

    def summarize(self, english_text: str, category: str) -> str:
        if len(english_text.split()) < 25:
            return english_text.strip()

        if self.use_llm:
            prompt = (
                f"Summarize this civic complaint (category: {category}) "
                f"in one short, neutral sentence (max 25 words):\n\n{english_text}"
            )
            response = self.client.generate_text(model="gemini-1.5-flash", prompt=prompt)
            return response.text.strip()
        else:
            result = self.pipe(english_text, max_length=40, min_length=8, do_sample=False)
            return result[0]["summary_text"].strip()
