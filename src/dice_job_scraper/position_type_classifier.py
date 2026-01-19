from llama_index.llms.ollama import Ollama
from llama_index.llms.groq import Groq

import os

# LLM setup (adjust to your environment)
llm = Ollama(
    model="qwen2:0.5b",
    request_timeout=120.0,
    context_window=8000,
    temperature=0.2,
)

groq = Groq(
    model="llama-3.1-8b-instant",
    api_key="",  # TODO: set Groq API key here
)

POSITION_TYPE_KEYWORDS = [
    # General types
    "full time",
    "full-time",
    "part time",
    "part-time",
    "contract",
    "contractor",
    "w2",
    "c2c",
    "corp to corp",
    "corp-to-corp",
    "c2h",
    "contract to hire",
    "temp to perm",
    "temporary",
    "permanent",
    "internship",
    "intern",

    # Explicit allow/deny
    "c2c accepted",
    "c2c not accepted",
    "no c2c",
    "c2c ok",
    "w2 only",
    "w2 preferred",
    "no w2",
]


def build_position_type_prompt(job_description: str) -> str:
    """
    Build a fail-safe prompt to extract position-type information.

    False positives are acceptable; false negatives are not.
    The LLM is instructed to *never* say "none" if there is any possible hint.
    """
    keyword_hint = ", ".join(sorted(set(POSITION_TYPE_KEYWORDS)))

    prompt = f"""
You are an assistant that analyzes JOB DESCRIPTIONS and identifies anything related to POSITION TYPE.

POSITION TYPE information includes (but is NOT limited to) things like:
- Employment type: Full-time, Part-time, Contract, Temporary, Permanent, Internship.
- Pay-structure type: W2, C2C (Corp to Corp), C2H (Contract to Hire), Contract-to-Hire, Temp-to-Perm.
- Explicit statements such as:
  - "C2C accepted", "C2C not accepted", "No C2C"
  - "W2 only", "W2 preferred", "no W2"
- Any synonyms or phrasing that implies the position type, even if the wording is slightly different.

IMPORTANT CONSTRAINTS (MUST FOLLOW):
1. FALSE POSITIVES ARE OK. FALSE NEGATIVES ARE NOT.
   - If you are unsure whether a phrase indicates a position type, INCLUDE IT and explain briefly.
2. If there is ANY possible reference to position type, YOU MUST RETURN IT.
3. ONLY return "none" when you are absolutely certain that there is truly no position-type information at all.
   - In ambiguous cases, DO NOT return "none".
4. Do NOT invent information that contradicts the job description.
   - You may be generous in interpreting hints, but they must at least plausibly come from the text.

KNOWN POSITION-TYPE KEYWORDS for guidance (this list is NOT exhaustive):
{keyword_hint}

JOB DESCRIPTION:
----------------
{job_description}
----------------

Your task:
1. Scan the job description carefully for ANY mention or hint of position type.
2. If you find one or more, return a concise JSON object with this structure:

{{
  "position_types": [
    "string describing type 1",
    "string describing type 2",
    ...
  ],
  "raw_phrases": [
    "exact or near-exact phrase from the text that made you think so",
    ...
  ]
}}

Rules:
- "position_types" should be short canonical labels (e.g., "Full-time", "Contract", "C2C accepted", "C2C not accepted", "W2 only", "C2H", etc.).
- "raw_phrases" MUST come from or be extremely close to the job description text.
- If nothing at all is found, return:

{{
  "position_types": [],
  "raw_phrases": []
}}

BUT remember: when in doubt, ASSUME there is some position type and include it.
""".strip()

    return prompt


def extract_position_type(job_description: str) -> dict:
    """
    Use the Groq LLM to extract position-type info from a job description.

    False positives are allowed; we aim to avoid missing any type info.
    Returns a Python dict parsed from the JSON the model should output.
    """
    prompt = build_position_type_prompt(job_description)
    result = groq.complete(prompt)
    text = result.text.strip()

    # Very defensive JSON parsing:
    import json

    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Try to salvage by extracting the first {...} block
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                # As a fallback, wrap the whole text as a single position type
                data = {
                    "position_types": [text],
                    "raw_phrases": [],
                }
        else:
            data = {
                "position_types": [text],
                "raw_phrases": [],
            }

    # Normalize structure to avoid KeyErrors
    position_types = data.get("position_types") or []
    raw_phrases = data.get("raw_phrases") or []

    # Ensure both are lists of strings
    if not isinstance(position_types, list):
        position_types = [str(position_types)]
    else:
        position_types = [str(x) for x in position_types]

    if not isinstance(raw_phrases, list):
        raw_phrases = [str(raw_phrases)]
    else:
        raw_phrases = [str(x) for x in raw_phrases]

    return {
        "position_types": position_types,
        "raw_phrases": raw_phrases,
    }


if __name__ == "__main__":
    job_description = """
Candidate Must Have Google Cloud Platform Certificate

Rate $65/hrs

Working Title: JAVA Developer
Position Type: 30 months
Work Arrangement: Onsite- Hybrid
Work Location: 1200 WASHINGTON AVE BLG. 12, ALBANY, NY, 12226, Hybrid
Department:  Information Technology Services (ITS)

Note: Contact will be on with Multi- Layer

Summary:
The resource will assist in moving the Worker Protection applications to the Google cloud. The resource will develop new code, as well as maintain and troubleshoot production problems/outages.
Required Skills:
84 months of experience creating JAVA programs.
84 months of experience working with Angular to create web-based programs.
60 months of experience working with Spring boot applications.
84 months of experience working in the Google Cloud Platform environment.
Bachelor s Degree or greater in computer science or related field.
Google Google Cloud Platform Certification.
Responsibilities:
Monitor the application during infrastructure changes and during normal application hours.
Make application changes to satisfy business requirements.
Work with technical testers and business testers as a liaison to check backend results and provide testing data.

Regards

Subhash at Techridge .net
""".strip()

    result = extract_position_type(job_description)
    print("Position types:", result["position_types"])
    print("Raw phrases:", result["raw_phrases"])
