"""
train_legal_detector.py
------------------------
Trains a binary classifier:   legal document  vs  non-legal document

Positive examples : all PDFs in dataset/{Civil,Criminal}/...  (real court cases)
Negative examples : diverse synthetic non-legal text (news, business, tech, etc.)

Output: models/legal_detector.pkl
        { "pipeline": Pipeline, "threshold": float }

The detector replaces the keyword-based _compute_legal_confidence() in app.py.
"""

import os
import re
import random
import joblib
import pdfplumber
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.metrics import classification_report

random.seed(42)
np.random.seed(42)

SCRIPT_DIR       = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR      = os.path.join(SCRIPT_DIR, "..", "dataset")
PROCESSED_TEXT_DIR = os.path.join(SCRIPT_DIR, "..", "backend-N", "data", "processed_text")
MODELS_DIR       = os.path.join(SCRIPT_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)


# ── Helpers ───────────────────────────────────────────────────────────────────
def extract_pdf_text(path: str) -> str:
    text = ""
    try:
        with pdfplumber.open(path) as pdf:
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    text += t + "\n"
    except Exception as e:
        print(f"  [WARN] Could not read {path}: {e}")
    return text.strip()


def load_legal_docs() -> list[str]:
    """Load pre-extracted .txt files from backend-N/data/processed_text/
    (fast — no PDF parsing needed). Falls back to scanning dataset PDFs."""
    texts = []

    # Fast path: use pre-extracted text files
    if os.path.isdir(PROCESSED_TEXT_DIR):
        for fname in os.listdir(PROCESSED_TEXT_DIR):
            if fname.lower().endswith(".txt"):
                path = os.path.join(PROCESSED_TEXT_DIR, fname)
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        t = f.read().strip()
                    if t and len(t) > 80:
                        texts.append(t)
                except Exception as e:
                    print(f"  [WARN] Could not read {path}: {e}")
        if texts:
            return texts

    # Slow fallback: parse PDFs
    print("  (No processed_text folder found — falling back to PDF extraction, this may take a while)")
    for category in os.listdir(DATASET_DIR):
        cat_path = os.path.join(DATASET_DIR, category)
        if not os.path.isdir(cat_path):
            continue
        for subcategory in os.listdir(cat_path):
            sub_path = os.path.join(cat_path, subcategory)
            if not os.path.isdir(sub_path):
                continue
            for fname in os.listdir(sub_path):
                if fname.lower().endswith(".pdf"):
                    t = extract_pdf_text(os.path.join(sub_path, fname))
                    if t and len(t) > 80:
                        texts.append(t)
    return texts


# ── Synthetic non-legal corpus ────────────────────────────────────────────────
# Covers typical documents users might accidentally submit:
#   news, business, medical, academic, tech, personal, sports, cooking
NON_LEGAL_TEMPLATES = [
    # ── News / journalism ────────────────────────────────────────────────────
    "Breaking news: The national cricket team won the championship final yesterday in a thrilling match against Australia. Thousands of fans gathered at the stadium to celebrate the historic victory.",
    "The government announced a new infrastructure project to build 500 km of highways across the country. The project is expected to create over 20,000 jobs and be completed by 2027.",
    "Scientists have discovered a new species of bird in the rainforest of South America. The bird, which has bright blue and yellow feathers, was previously unknown to researchers.",
    "The stock market closed higher today as investors reacted positively to the latest earnings reports from major technology companies. The index rose by 1.5 percent.",
    "A massive earthquake measuring 7.2 on the Richter scale struck the coastal region early this morning, triggering a tsunami warning for nearby islands.",
    "The Prime Minister addressed the nation in a televised speech, outlining the government's five-year economic development plan aimed at reducing unemployment.",
    "Local authorities issued a weather alert for heavy rainfall expected over the next three days. Residents in low-lying areas are advised to take precautions.",
    "The international film festival opened today with screenings of films from over 50 countries. The opening ceremony was attended by famous directors and actors.",
    "Health officials confirmed 200 new cases of the flu virus in the capital city, urging residents to get vaccinated and practice good hygiene.",
    "The annual marathon took place on Sunday, with thousands of runners participating from around the world. The winner completed the race in just over two hours.",

    # ── Business / corporate ─────────────────────────────────────────────────
    "INVOICE #1024\nBilled To: ABC Company Ltd\nDate: 15 March 2024\nItem: Software License (Annual) — Rs. 150,000\nItem: Technical Support — Rs. 25,000\nTotal Due: Rs. 175,000\nPayment Terms: Net 30 days",
    "MEMORANDUM\nTo: All Staff\nFrom: Human Resources Department\nSubject: Annual Performance Review\nThe annual performance review cycle for 2023-2024 will commence on 1 April. All managers are requested to complete their team evaluations by 30 April.",
    "Q3 Financial Report — XYZ Corporation\nRevenue this quarter reached $4.2 million, representing a 12% increase year-over-year. Operating expenses were $2.8 million. Net profit margin improved to 18%.",
    "MEETING MINUTES — Board of Directors\nDate: 10 February 2024\nPresent: CEO, CFO, COO, 3 Directors\nAgenda: Budget approval for FY2024-25, new product launch strategy, HR policy updates.",
    "Dear Mr. Silva,\nThank you for your application for the position of Senior Software Engineer. We are pleased to offer you the role with a starting salary of Rs. 200,000 per month.",
    "PURCHASE ORDER\nSupplier: Tech Supplies Pvt Ltd\nDelivery Address: 45 Main Street, Colombo 03\nItems: 10x Desktop Computers @ Rs. 120,000 each\nTotal Order Value: Rs. 1,200,000",
    "Annual General Meeting Notice\nShareholders of Sunshine Holdings PLC are hereby notified that the Annual General Meeting will be held on 15 May 2024 at the company's registered office.",
    "Business Proposal: Digital Marketing Services\nWe propose to provide comprehensive digital marketing services including SEO, social media management, and content creation at a monthly retainer of Rs. 80,000.",
    "EMPLOYMENT CONTRACT\nThis contract is between Sunrise Pvt Ltd (employer) and Mr. Kamal Perera (employee) for the role of Accountant. Start date: 1 March 2024. Probation: 6 months.",
    "EXPENSE CLAIM FORM\nEmployee: Sarah Johnson\nDepartment: Marketing\nDate: 20 March 2024\nItems: Flight ticket Colombo-London Rs. 85,000, Hotel 5 nights Rs. 45,000, Meals Rs. 12,000",

    # ── Medical / health ─────────────────────────────────────────────────────
    "MEDICAL REPORT\nPatient: Nimal Bandara, Age: 45\nDiagnosis: Type 2 Diabetes Mellitus\nTreatment: Metformin 500mg twice daily, dietary modifications, regular exercise\nFollow-up appointment scheduled in 3 months.",
    "PRESCRIPTION\nPatient Name: Mrs. Kamala Jayawardena\nDate: 5 April 2024\nRx: Amoxicillin 500mg — Take one capsule three times a day for 7 days\nRx: Paracetamol 500mg — As needed for pain and fever",
    "Discharge Summary\nPatient was admitted for appendectomy. Surgery performed successfully under general anaesthesia. Patient recovered without complications and is discharged with instructions for wound care.",
    "Blood Test Results — Patient ID: 10045\nHemoglobin: 13.2 g/dL (Normal)\nWhite Blood Cell Count: 7,500/μL (Normal)\nPlatelet Count: 250,000/μL (Normal)\nFasting Blood Sugar: 98 mg/dL (Normal)",
    "Vaccination Record\nName: Priya Wijesinghe, DOB: 12/06/1988\nDPT: Completed\nMMR: Completed\nHepatitis B: 3 doses completed\nCOVID-19: 2 doses (Pfizer) + 1 booster",
    "Referral Letter\nDear Dr. Perera,\nI am referring Mrs. Gunawardena, aged 58, for cardiac evaluation. She has been experiencing intermittent chest pain and shortness of breath for the past 2 months.",

    # ── Academic / educational ───────────────────────────────────────────────
    "ABSTRACT\nThis research paper examines the impact of social media on academic performance of university students. A survey was conducted among 300 students. Results indicate a negative correlation between social media usage and GPA.",
    "ASSIGNMENT SUBMISSION\nCourse: Introduction to Economics, ECO 101\nStudent: Amali Fernando\nStudent ID: 2021/ICT/089\nSubmission: The Effects of Inflation on Consumer Behavior in Sri Lanka",
    "LECTURE NOTES — Chapter 5: Photosynthesis\nPhotosynthesis is the process by which plants convert sunlight into chemical energy. The equation is: 6CO2 + 6H2O + light energy → C6H12O6 + 6O2",
    "UNIVERSITY OF COLOMBO — EXAMINATION PAPER\nSubject: English Literature\nTime Allowed: 3 hours\nSection A: Answer any FOUR questions. Each question carries 25 marks.\n1. Discuss the themes of love and war in Shakespeare's sonnets.",
    "REPORT CARD — Term 1, 2024\nStudent: Danushka Mendis\nGrade: 9B\nMathematics: 85/100 (A)\nScience: 78/100 (B+)\nEnglish: 90/100 (A+)\nHistory: 72/100 (B)",
    "Literature Review: Machine Learning in Healthcare\nRecent advances in machine learning have shown promising results in medical diagnostics. Convolutional neural networks achieve 95% accuracy in detecting diabetic retinopathy from retinal images.",

    # ── Technology / IT ──────────────────────────────────────────────────────
    "README.md\n# Web Scraper Tool\nThis Python script scrapes product data from e-commerce websites.\n## Installation\npip install requests beautifulsoup4\n## Usage\npython scraper.py --url https://example.com --output data.csv",
    "ERROR LOG — Application Server\n2024-03-15 10:23:45 ERROR NullPointerException at line 342 in UserService.java\n2024-03-15 10:23:46 INFO Attempting automatic recovery\n2024-03-15 10:23:47 ERROR Database connection timeout after 30 seconds",
    "SYSTEM REQUIREMENTS\nOperating System: Windows 10 or later, macOS 12 or later, Ubuntu 20.04 or later\nRAM: Minimum 8GB, Recommended 16GB\nStorage: 256GB SSD\nProcessor: Intel Core i5 or AMD Ryzen 5 equivalent",
    "API DOCUMENTATION\nEndpoint: POST /api/users/login\nRequest Body: { username: string, password: string }\nResponse: { token: string, expires_in: 3600 }\nError Codes: 401 Unauthorized, 400 Bad Request",
    "SPRINT REVIEW — Sprint 12\nCompleted User Stories: Login page redesign, Password reset email, Dashboard analytics chart\nVelocity: 42 story points\nCarried Over: Mobile notifications (blocked on push service integration)",

    # ── Personal / social ────────────────────────────────────────────────────
    "Dear Grandmother,\nI hope this letter finds you in good health. We are all doing well here. My son started school last month and is enjoying it very much. The weather has been quite hot lately.",
    "CURRICULUM VITAE\nName: Sanjay Kumar\nEducation: BSc Computer Science, University of Moratuwa (2020)\nExperience: 3 years as Software Developer at TechCorp Pvt Ltd\nSkills: Java, Python, SQL, React\nLanguages: Sinhala, English, Tamil",
    "Birthday Party Invitation\nYou are cordially invited to celebrate the 10th birthday of Sasha!\nDate: Saturday, 20 April 2024\nTime: 3:00 PM – 6:00 PM\nVenue: Sunny Gardens Hall, No. 25 Park Road, Colombo 05\nKindly RSVP by 15 April.",
    "RENTAL AGREEMENT\nThis agreement is between the landlord Mr. Suresh Patel and the tenant Ms. Deepika Rathnayake for the apartment at 12/B Lake View Road, Nugegoda. Monthly rent: Rs. 35,000. Duration: 12 months from 1 April 2024.",
    "Shopping List for This Week:\n- Rice 5kg\n- Dhal 2kg\n- Coconut oil 1 bottle\n- Onions 1kg\n- Tomatoes 500g\n- Milk powder 400g\n- Bread 2 loaves\n- Eggs 1 dozen",
    "PASSPORT APPLICATION FORM\nFull Name: Lasith Perera\nDate of Birth: 14 August 1995\nNational ID: 952265678V\nOccupation: Teacher\nEmergency Contact: Mrs. Manel Perera (Mother) — 0112345678",

    # ── Sports / entertainment ───────────────────────────────────────────────
    "Match Report: Sri Lanka vs India ODI\nSri Lanka won the toss and elected to bat. The team scored 287/6 in 50 overs. Kusal Mendis top-scored with 112 runs off 98 balls. India were bowled out for 265.",
    "MOVIE REVIEW: Oppenheimer (2023)\nChristopher Nolan's biographical thriller about the development of the atomic bomb is a cinematic masterpiece. Cillian Murphy delivers an Oscar-worthy performance.",
    "RECIPE: Chicken Curry\nIngredients: 500g chicken, 2 onions, 4 garlic cloves, 1 tsp turmeric, 2 tsp chili powder, coconut milk 400ml\nMethod: Fry onions and garlic. Add spices. Add chicken. Simmer 30 minutes. Add coconut milk.",
    "TRAVEL GUIDE: Kandy, Sri Lanka\nKandy is the cultural capital of Sri Lanka, famous for the Temple of the Tooth Relic. Must-visit: Peradeniya Botanical Gardens, Kandy Lake, the Kandyan cultural show.",
    "Fitness Journal — Week 3\nMonday: 5km run, 30min yoga\nTuesday: Rest\nWednesday: Weight training (chest/back)\nThursday: 6km run\nFriday: Weight training (legs)\nSaturday: 10km long run\nSunday: Rest\nTotal: 21km",

    # ── Scientific / research ────────────────────────────────────────────────
    "Abstract: The Effect of Fertilizer on Paddy Yield\nThis study investigated how different nitrogen fertilizer levels affect paddy yield in tropical climates. Three plots were treated with 0, 50, and 100 kg/ha of nitrogen. Results showed a statistically significant increase in yield at 100 kg/ha (p<0.05).",
    "WEATHER FORECAST — Colombo Region\nToday: Partly cloudy. Temperature 28-32°C. 40% chance of afternoon showers.\nTomorrow: Mostly sunny in the morning. Thunderstorms expected in the afternoon and evening.",
    "GEOLOGY REPORT — Site Investigation\nThe soil investigation at the proposed construction site revealed sandy clay soil up to 3m depth, transitioning to decomposed granite rock. Bearing capacity estimated at 150 kN/m².",
    "Lab Report: Determination of Vitamin C Content in Fruits\nObjective: To measure ascorbic acid in orange, lemon, and guava using titration method.\nResults: Orange: 53mg/100g, Lemon: 77mg/100g, Guava: 228mg/100g",

    # ── Government / administrative forms (non-legal) ────────────────────────
    "BIRTH CERTIFICATE APPLICATION\nThis is to certify that the birth of Malini Dissanayake was registered on 3 June 1998. Father: Ruwan Dissanayake. Mother: Chamari Wijesinghe. District: Gampaha.",
    "VEHICLE REGISTRATION FORM\nVehicle Make: Toyota\nModel: Corolla\nYear of Manufacture: 2019\nEngine Number: 2NZ-4512387\nChassisNumber: JTDBT923X95123456\nOwner: Mr. Pradeep Jayasena",
    "LETTER FROM BANK\nDear Valued Customer,\nYour fixed deposit account FD-20041 has matured on 28 March 2024. The principal amount of Rs. 500,000 plus interest of Rs. 62,500 has been credited to your savings account.",
    "TAX RETURN FORM — INLAND REVENUE\nTaxpayer Name: Kumari Senanayake\nTax Year: 2023/2024\nEmployment Income: Rs. 1,800,000\nTax Payable: Rs. 180,000\nTax Already Paid (PAYE): Rs. 165,000\nBalance Due: Rs. 15,000",
    "SCHOOL LEAVING CERTIFICATE\nThis is to certify that Dilshan Rathnayake, Admission No. 2456, was a student of Ananda College, Colombo from 2010 to 2021. He sat for the G.C.E. Advanced Level Examination in 2021.",
]


# ── Augment negatives with small perturbations ────────────────────────────────
def augment(text: str, n: int = 3) -> list[str]:
    """Simple augmentation: randomly drop sentences to create variety."""
    sentences = re.split(r"(?<=[.!?\n])\s+", text.strip())
    results = [text]
    for _ in range(n - 1):
        if len(sentences) > 3:
            keep = random.sample(sentences, max(3, len(sentences) - random.randint(1, 3)))
            results.append(" ".join(keep))
        else:
            results.append(text)
    return results


def build_negatives() -> list[str]:
    negatives = []
    for template in NON_LEGAL_TEMPLATES:
        negatives.extend(augment(template, n=3))
    return negatives


# ── Main training ─────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Training Legal Document Detector")
    print("=" * 60)

    # Positive examples
    print("\n[1/4] Loading legal PDFs from dataset folder...")
    legal_texts = load_legal_docs()
    print(f"      Loaded {len(legal_texts)} legal documents.")
    if len(legal_texts) < 10:
        print("  [ERROR] Not enough legal documents found. Check DATASET_DIR.")
        return

    # Negative examples
    print("\n[2/4] Building non-legal examples...")
    non_legal_texts = build_negatives()
    print(f"      Generated {len(non_legal_texts)} non-legal examples.")

    # Combine
    texts  = legal_texts + non_legal_texts
    labels = [1] * len(legal_texts) + [0] * len(non_legal_texts)

    print(f"\n[3/4] Training binary classifier (legal=1, non-legal=0)...")
    print(f"      Total samples: {len(texts)}  (legal={len(legal_texts)}, non-legal={len(non_legal_texts)})")

    pipe = Pipeline([
        ("tfidf", TfidfVectorizer(
            max_features=20_000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            strip_accents="unicode",
            analyzer="word",
            token_pattern=r"(?u)\b\w+\b",
            min_df=1,
        )),
        ("clf", LogisticRegression(
            C=1.0,
            max_iter=1000,
            class_weight="balanced",
            random_state=42,
            solver="lbfgs",
        )),
    ])

    cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    scores = cross_val_score(pipe, texts, labels, cv=cv, scoring="f1")
    print(f"      Cross-validation F1: {scores.mean():.3f} ± {scores.std():.3f}")

    pipe.fit(texts, labels)

    # Print classification report on training data
    print("\n── Training-set report ──")
    preds = pipe.predict(texts)
    print(classification_report(labels, preds, target_names=["non-legal", "legal"], zero_division=0))

    # Save
    out_path = os.path.join(MODELS_DIR, "legal_detector.pkl")
    joblib.dump({"pipeline": pipe}, out_path, compress=3)
    print(f"\n[4/4] Saved → {out_path}")
    print("      Done! Update app.py to load this model.")

    # Quick sanity check
    samples = [
        ("Sample legal text",
         "The plaintiff filed a petition before the High Court seeking a writ of certiorari. "
         "The respondent filed objections. After hearing both parties, the judge dismissed the application."),
        ("Sample non-legal text",
         "Today I went to the supermarket and bought rice, vegetables and some fruit. "
         "The weather was nice so I decided to walk home."),
    ]
    print("\n── Sanity check ──")
    for label, text in samples:
        prob = pipe.predict_proba([text])[0][1]   # probability of class 1 (legal)
        print(f"  {label}: legal_confidence = {prob:.2%}")


if __name__ == "__main__":
    main()
