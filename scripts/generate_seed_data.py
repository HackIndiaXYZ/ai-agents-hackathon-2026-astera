"""
Dataset Seed Generator — Creates initial Q&A pairs for Adaptive Data
Uses Gemini to generate authentic Bhojpuri + Assamese civic Q&A pairs
Then pushes them to Adaption platform

Run: python scripts/generate_seed_data.py
"""
import os
import sys
import json
import asyncio

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)

from google import genai
client = genai.Client(vertexai=True, project="asteria-497909", location="us-central1")

# ─── Seed Q&A pairs (Hand-crafted — guaranteed quality) ───────────────────────
SEED_PAIRS = [
    # ── PM KISAN ── BHOJPURI ─────────────────────────────────────
    {
        "language": "bhojpuri",
        "domain": "agriculture",
        "intent": "KNOW_SCHEME",
        "scheme": "PM_KISAN",
        "query": "PM Kisan Samman Nidhi का बा?",
        "response": "PM Kisan Samman Nidhi एगो सरकारी योजना बा जवना में छोट किसान परिवार के साल में 6000 रुपया मिलेला। ई पइसा तीन किस्त में आवेला — हर किस्त में 2000 रुपया। ई सीधे आपके बैंक खाते में आवेला। pmkisan.gov.in पर जाके आवेदन कर सकीलें।",
        "feedback": "correct"
    },
    {
        "language": "bhojpuri",
        "domain": "agriculture",
        "intent": "CHECK_ELIGIBILITY",
        "scheme": "PM_KISAN",
        "query": "PM Kisan के लाई हम eligible बानी का?",
        "response": "PM Kisan के लाई ई चाहीं: (1) आपके नाम पर खेती के जमीन होखे के चाही, (2) परिवार के आमदनी बहुत ज्यादा न होखे, (3) आधार से जुड़ल बैंक खाता होखे के चाही। सरकारी नौकरी वाला, आयकर भरे वाला, आ 10000 से ज्यादा पेंशन पाए वाला लोग eligible नइखें।",
        "feedback": "correct"
    },
    {
        "language": "bhojpuri",
        "domain": "agriculture",
        "intent": "GET_DOCUMENTS",
        "scheme": "PM_KISAN",
        "query": "PM Kisan के लाई का-का कागज चाही?",
        "response": "PM Kisan के लाई ई कागज चाही: (1) आधार कार्ड, (2) जमीन के कागज (खतियान/खतौनी), (3) बैंक पासबुक जवना में IFSC नंबर होखे, (4) आधार से जुड़ल मोबाइल नंबर, (5) पासपोर्ट साइज फोटो। सभी कागज के फोटोकॉपी आ असली दोनों रखीं।",
        "feedback": "correct"
    },
    {
        "language": "bhojpuri",
        "domain": "agriculture",
        "intent": "APPLY_SCHEME",
        "scheme": "PM_KISAN",
        "query": "PM Kisan में आवेदन कइसे करीं?",
        "response": "PM Kisan में आवेदन के लाई: pmkisan.gov.in पर जाईं या नजदीकी CSC सेंटर जाईं। 'नया किसान पंजीकरण' पर क्लिक करीं। आधार नंबर आ मोबाइल नंबर डालीं। अपनी जानकारी आ बैंक खाता भरीं। जमीन के कागज अपलोड करीं। Submit करे के बाद रजिस्ट्रेशन नंबर नोट करीं। हेल्पलाइन: 155261",
        "feedback": "correct"
    },
    {
        "language": "bhojpuri",
        "domain": "agriculture",
        "intent": "KNOW_SCHEME",
        "scheme": "PM_KISAN",
        "query": "PM Kisan के पइसा कब आवेला?",
        "response": "PM Kisan के पइसा साल में तीन बेर आवेला। पहिला किस्त अप्रैल-जुलाई में, दूसरा किस्त अगस्त-नवंबर में, आ तीसरा किस्त दिसंबर-मार्च में आवेला। हर किस्त में 2000 रुपया सीधे बैंक खाते में आवेला। Status pmkisan.gov.in पर 'Beneficiary Status' में चेक कर सकीलें।",
        "feedback": "correct"
    },

    # ── AYUSHMAN BHARAT ── BHOJPURI ──────────────────────────────
    {
        "language": "bhojpuri",
        "domain": "healthcare",
        "intent": "KNOW_SCHEME",
        "scheme": "AYUSHMAN_BHARAT",
        "query": "Ayushman Bharat का बा?",
        "response": "आयुष्मान भारत एगो स्वास्थ्य बीमा योजना बा। एह में गरीब परिवार के साल में 5 लाख रुपया तक के इलाज मुफ्त मिलेला। किसी भी सरकारी या सूचीबद्ध प्राइवेट अस्पताल में भर्ती हो सकीलें बिना पइसा दिहले। हेल्पलाइन: 14555",
        "feedback": "correct"
    },
    {
        "language": "bhojpuri",
        "domain": "healthcare",
        "intent": "GET_DOCUMENTS",
        "scheme": "AYUSHMAN_BHARAT",
        "query": "Ayushman card बनावे के लाई का चाही?",
        "response": "आयुष्मान कार्ड बनावे के लाई: (1) आधार कार्ड, (2) राशन कार्ड, (3) मोबाइल नंबर। सबसे पहिले pmjay.gov.in पर या 14555 पर कॉल करके देखीं कि रउरा परिवार eligible बा कि ना। नजदीकी आयुष्मान मित्र से मिलीं — ऊ कार्ड बनावे में मदद करेलें।",
        "feedback": "correct"
    },
    {
        "language": "bhojpuri",
        "domain": "healthcare",
        "intent": "APPLY_SCHEME",
        "scheme": "AYUSHMAN_BHARAT",
        "query": "Ayushman Bharat में कइसे register करीं?",
        "response": "आयुष्मान में रजिस्ट्रेशन के लाई: पहिले 14555 पर call करके या pmjay.gov.in पर पात्रता जांचीं। फिर नजदीकी सरकारी अस्पताल में आयुष्मान मित्र से मिलीं। आधार लेके जाईं — ऊ आपके आयुष्मान कार्ड बना देइहें। ई कार्ड से देश के किसी भी सूचीबद्ध अस्पताल में मुफ्त इलाज होई।",
        "feedback": "correct"
    },

    # ── PM AWAS ── BHOJPURI ──────────────────────────────────────
    {
        "language": "bhojpuri",
        "domain": "housing",
        "intent": "KNOW_SCHEME",
        "scheme": "PM_AWAS",
        "query": "PM Awas Yojana में का मिलेला?",
        "response": "PM Awas Yojana ग्रामीण में घर बनावे के लाई सरकार 1.2 लाख रुपया देलीं (पहाड़ी इलाका में 1.3 लाख)। ई पइसा किस्त में बैंक खाते में आवेला। गरीब परिवार जिनके पास पक्का घर नइखे ऊ लोग apply कर सकेलें। हेल्पलाइन: 1800-11-6446",
        "feedback": "correct"
    },
    {
        "language": "bhojpuri",
        "domain": "housing",
        "intent": "GET_DOCUMENTS",
        "scheme": "PM_AWAS",
        "query": "PM Awas Yojana के लाई का-का कागज चाही?",
        "response": "PM Awas के लाई ई कागज चाही: (1) आधार कार्ड, (2) जॉब कार्ड (मनरेगा), (3) बैंक खाता, (4) BPL प्रमाणपत्र, (5) मोबाइल नंबर। सबसे जरूरी बात — SECC 2011 सूची में नाम होखे के चाही। ग्राम पंचायत जाके देखीं।",
        "feedback": "correct"
    },

    # ── UJJWALA ── BHOJPURI ──────────────────────────────────────
    {
        "language": "bhojpuri",
        "domain": "energy",
        "intent": "KNOW_SCHEME",
        "scheme": "UJJWALA",
        "query": "Ujjwala Yojana में का मिलेला?",
        "response": "प्रधानमंत्री उज्ज्वला योजना में गरीब महिला लोग के मुफ्त LPG गैस कनेक्शन मिलेला। साथ में 1600 रुपया जमा आ पहिला सिलेंडर भी मुफ्त मिलेला। 18 साल से ऊपर BPL परिवार के महिला apply कर सकेलीं जिनके घर में पहिले से गैस कनेक्शन नइखे।",
        "feedback": "correct"
    },
    {
        "language": "bhojpuri",
        "domain": "energy",
        "intent": "GET_DOCUMENTS",
        "scheme": "UJJWALA",
        "query": "उज्ज्वला योजना के लाई का कागज चाही?",
        "response": "उज्ज्वला के लाई: (1) महिला आवेदक के आधार कार्ड, (2) BPL राशन कार्ड, (3) बैंक खाता, (4) पासपोर्ट साइज फोटो, (5) घर में LPG नइखे एकर घोषणापत्र। नजदीकी LPG वितरक के पास जाईं या mylpg.in पर online apply करीं। हेल्पलाइन: 1906",
        "feedback": "correct"
    },

    # ── JAN DHAN ── BHOJPURI ─────────────────────────────────────
    {
        "language": "bhojpuri",
        "domain": "finance",
        "intent": "KNOW_SCHEME",
        "scheme": "JAN_DHAN",
        "query": "Jan Dhan खाता में का फायदा बा?",
        "response": "Jan Dhan खाता में बहुत फायदा बा: (1) बिना पइसा के खाता खुली, (2) 10000 रुपया overdraft मिली जरूरत पर, (3) 2 लाख रुपया दुर्घटना बीमा, (4) 30000 रुपया जीवन बीमा, (5) RuPay डेबिट कार्ड मिली। 10 साल से ऊपर कोई भी खोल सकेला।",
        "feedback": "correct"
    },
    {
        "language": "bhojpuri",
        "domain": "finance",
        "intent": "APPLY_SCHEME",
        "scheme": "JAN_DHAN",
        "query": "Jan Dhan खाता कइसे खुलाई?",
        "response": "Jan Dhan खाता खोलावे खातिर: किसी भी राष्ट्रीयकृत बैंक (SBI, PNB, BOI) में जाईं। 'Jan Dhan खाता खोलना है' बोलीं। आधार कार्ड आ फोटो लेके जाईं। फॉर्म भरीं — 10-15 मिनट में काम हो जाई। 7 दिन में RuPay कार्ड मिली। कोई पइसा नइखे लागत!",
        "feedback": "correct"
    },

    # ── RATION CARD ── BHOJPURI ──────────────────────────────────
    {
        "language": "bhojpuri",
        "domain": "food",
        "intent": "KNOW_SCHEME",
        "scheme": "RATION_CARD",
        "query": "राशन कार्ड में का-का मिलेला?",
        "response": "राशन कार्ड से सरकारी दुकान (PDS) से सस्ता अनाज मिलेला: चावल 3 रुपया किलो, गेहूं 2 रुपया किलो, आ मोटा अनाज 1 रुपया किलो। गरीब परिवार के हर महीना तय मात्रा में अनाज मिलेला। ई बहुत जरूरी दस्तावेज भी बा — कई योजना में राशन कार्ड चाही।",
        "feedback": "correct"
    },

    # ── FASAL BIMA ── BHOJPURI ───────────────────────────────────
    {
        "language": "bhojpuri",
        "domain": "agriculture",
        "intent": "KNOW_SCHEME",
        "scheme": "FASAL_BIMA",
        "query": "Fasal Bima Yojana क्या बा?",
        "response": "PM Fasal Bima Yojana में किसान के फसल नुकसान होला बाढ़, सूखा या आंधी से त सरकार मुआवजा देलीं। किसान के बस थोड़ा premium भरे के होला — खरीफ में 2%, रबी में 1.5%। बाकी सरकार देलीं। फसल नुकसान होला त 72 घंटा में 1800-200-7710 पर call करीं।",
        "feedback": "correct"
    },

    # ─────────────────────────────────────────────────────────────
    # ASSAMESE PAIRS
    # ─────────────────────────────────────────────────────────────

    {
        "language": "assamese",
        "domain": "agriculture",
        "intent": "KNOW_SCHEME",
        "scheme": "PM_KISAN",
        "query": "PM Kisan Samman Nidhi কি?",
        "response": "PM Kisan Samman Nidhi এটা চৰকাৰী আঁচনি য'ত সৰু কৃষক পৰিয়ালক বছৰত ৬০০০ টকা দিয়া হয়। এই টকা তিনিটা কিস্তিত আহে — প্ৰতিটো কিস্তিত ২০০০ টকা। এই টকা পোনপটীয়াকৈ আপোনাৰ বেংক একাউণ্টত আহে। pmkisan.gov.in ত আবেদন কৰিব পাৰিব।",
        "feedback": "correct"
    },
    {
        "language": "assamese",
        "domain": "agriculture",
        "intent": "GET_DOCUMENTS",
        "scheme": "PM_KISAN",
        "query": "PM Kisan ৰ বাবে কি কি কাগজ লাগিব?",
        "response": "PM Kisan ৰ বাবে এই কাগজসমূহ লাগিব: (১) আধাৰ কাৰ্ড, (২) মাটিৰ কাগজ (খতিয়ান/খতাউনি), (৩) বেংক পাছবুক (IFSC সহ), (৪) আধাৰৰ সৈতে সংযুক্ত মোবাইল নম্বৰ, (৫) পাছপ'ৰ্ট সাইজ ফটো। সকলো কাগজৰ ফটোকপি আৰু মূলটো দুয়োটাকে ৰাখিব।",
        "feedback": "correct"
    },
    {
        "language": "assamese",
        "domain": "agriculture",
        "intent": "APPLY_SCHEME",
        "scheme": "PM_KISAN",
        "query": "PM Kisan ত কেনেকৈ আবেদন কৰিব?",
        "response": "PM Kisan ত আবেদনৰ বাবে: pmkisan.gov.in লৈ যাওক বা নিকটৱৰ্তী CSC কেন্দ্ৰলৈ যাওক। 'নতুন কৃষক পঞ্জীয়ন'ত ক্লিক কৰক। আধাৰ নম্বৰ আৰু মোবাইল নম্বৰ দিয়ক। তথ্য আৰু বেংক একাউণ্ট পূৰণ কৰক। মাটিৰ কাগজ আপলোড কৰক। জমা দিয়াৰ পিছত পঞ্জীয়ন নম্বৰ টোকা কৰক। হেল্পলাইন: ১৫৫২৬১",
        "feedback": "correct"
    },
    {
        "language": "assamese",
        "domain": "healthcare",
        "intent": "KNOW_SCHEME",
        "scheme": "AYUSHMAN_BHARAT",
        "query": "আয়ুষ্মান ভাৰত কি?",
        "response": "আয়ুষ্মান ভাৰত এটা স্বাস্থ্য বীমা আঁচনি। এইটোত দৰিদ্ৰ পৰিয়ালে বছৰত ৫ লাখ টকা পৰ্যন্ত বিনামূলীয়া চিকিৎসা পায়। যিকোনো চৰকাৰী বা তালিকাভুক্ত ব্যক্তিগত চিকিৎসালয়ত ভৰ্তি হ'ব পাৰিব কোনো টকা নিদিয়াকৈ। হেল্পলাইন: ১৪৫৫৫",
        "feedback": "correct"
    },
    {
        "language": "assamese",
        "domain": "healthcare",
        "intent": "GET_DOCUMENTS",
        "scheme": "AYUSHMAN_BHARAT",
        "query": "আয়ুষ্মান কাৰ্ড বনাবলৈ কি লাগে?",
        "response": "আয়ুষ্মান কাৰ্ডৰ বাবে: (১) আধাৰ কাৰ্ড, (২) ৰেচন কাৰ্ড, (৩) মোবাইল নম্বৰ। প্ৰথমে pmjay.gov.in ত বা ১৪৫৫৫ত ফোন কৰি আপোনাৰ পৰিয়াল যোগ্য নে নাই পৰীক্ষা কৰক। নিকটৱৰ্তী আয়ুষ্মান মিত্ৰক লগ কৰক — তেওঁ কাৰ্ড বনাওঁতে সহায় কৰিব।",
        "feedback": "correct"
    },
    {
        "language": "assamese",
        "domain": "housing",
        "intent": "KNOW_SCHEME",
        "scheme": "PM_AWAS",
        "query": "PM আৱাস যোজনাত কি পোৱা যায়?",
        "response": "PM আৱাস যোজনা গ্ৰামীণত ঘৰ নিৰ্মাণৰ বাবে চৰকাৰে ১.২ লাখ টকা দিয়ে (পাহাৰীয়া অঞ্চলত ১.৩ লাখ)। এই টকা কিস্তিত বেংক একাউণ্টত আহে। যাৰ পাকঘৰ নাই তেনে দৰিদ্ৰ পৰিয়ালে আবেদন কৰিব পাৰে। হেল্পলাইন: ১৮০০-১১-৬৪৪৬",
        "feedback": "correct"
    },
    {
        "language": "assamese",
        "domain": "energy",
        "intent": "KNOW_SCHEME",
        "scheme": "UJJWALA",
        "query": "উজ্জ্বলা যোজনাত কি পোৱা যায়?",
        "response": "প্ৰধানমন্ত্ৰী উজ্জ্বলা যোজনাত দৰিদ্ৰ মহিলাসকলে বিনামূলীয়া LPG গেছ সংযোগ পায়। লগতে ১৬০০ টকা জমা আৰু প্ৰথম চিলিণ্ডাৰো বিনামূলীয়া পোৱা যায়। ১৮ বছৰৰ ওপৰৰ BPL পৰিয়ালৰ মহিলা আবেদন কৰিব পাৰে যাৰ ঘৰত আগতে LPG নাই।",
        "feedback": "correct"
    },
    {
        "language": "assamese",
        "domain": "finance",
        "intent": "KNOW_SCHEME",
        "scheme": "JAN_DHAN",
        "query": "জন ধন একাউণ্টৰ সুবিধা কি?",
        "response": "জন ধন একাউণ্টত বহুত সুবিধা আছে: (১) শূন্য বেলেঞ্চত একাউণ্ট খোলা যায়, (২) প্ৰয়োজনত ১০০০০ টকা অভাৰড্ৰাফ্ট পোৱা যায়, (৩) ২ লাখ টকা দুৰ্ঘটনা বীমা, (৪) ৩০০০০ টকা জীৱন বীমা, (৫) RuPay ডেবিট কাৰ্ড পোৱা যায়। ১০ বছৰৰ ওপৰৰ যিকোনো ব্যক্তিয়ে খুলিব পাৰে।",
        "feedback": "correct"
    },
    {
        "language": "assamese",
        "domain": "agriculture",
        "intent": "KNOW_SCHEME",
        "scheme": "FASAL_BIMA",
        "query": "শস্য বীমা যোজনা কি?",
        "response": "PM শস্য বীমা যোজনাত বাঢ়নি, খৰাং বা ধুমুহাৰ কাৰণে শস্যৰ ক্ষতি হ'লে চৰকাৰে ক্ষতিপূৰণ দিয়ে। কৃষকে মাত্ৰ কম প্ৰিমিয়াম দিব লাগে — খাৰিফত ২%, ৰবিত ১.৫%। বাকী চৰকাৰে দিয়ে। শস্য ক্ষতি হ'লে ৭২ ঘণ্টাৰ ভিতৰত ১৮০০-২০০-৭৭১০ত ফোন কৰক।",
        "feedback": "correct"
    },
    {
        "language": "assamese",
        "domain": "food",
        "intent": "KNOW_SCHEME",
        "scheme": "RATION_CARD",
        "query": "ৰেচন কাৰ্ডত কি কি পোৱা যায়?",
        "response": "ৰেচন কাৰ্ডৰ জৰিয়তে চৰকাৰী দোকানৰ পৰা সস্তা শস্য পোৱা যায়: চাউল ৩ টকা কিলো, ঘেঁহু ২ টকা কিলো, মোটা শস্য ১ টকা কিলো। দৰিদ্ৰ পৰিয়ালে প্ৰতি মাহে নিৰ্ধাৰিত পৰিমাণত শস্য পায়। এইটো এটা গুৰুত্বপূৰ্ণ নথিও — বহু আঁচনিৰ বাবে ৰেচন কাৰ্ড লাগে।",
        "feedback": "correct"
    },

    # ── GENERAL ── BOTH LANGUAGES ────────────────────────────────
    {
        "language": "bhojpuri",
        "domain": "general",
        "intent": "LIST_SCHEMES",
        "scheme": None,
        "query": "कउन-कउन सरकारी योजना बा?",
        "response": "मुख्य सरकारी योजना इ बा: 🌾 PM Kisan (किसान के 6000 रुपया), 🏥 Ayushman Bharat (5 लाख इलाज), 🏠 PM Awas (घर बनावे पइसा), 🔥 Ujjwala (मुफ्त LPG), 🏦 Jan Dhan (बैंक खाता), 🌱 Fasal Bima (फसल बीमा), 🍚 Ration Card (सस्ता अनाज)। कउन योजना के बारे में जानना बा?",
        "feedback": "correct"
    },
    {
        "language": "assamese",
        "domain": "general",
        "intent": "LIST_SCHEMES",
        "scheme": None,
        "query": "কি কি চৰকাৰী আঁচনি আছে?",
        "response": "মুখ্য চৰকাৰী আঁচনিসমূহ হ'ল: 🌾 PM Kisan (কৃষকৰ ৬০০০ টকা), 🏥 আয়ুষ্মান ভাৰত (৫ লাখ চিকিৎসা), 🏠 PM আৱাস (ঘৰ নিৰ্মাণৰ টকা), 🔥 উজ্জ্বলা (বিনামূলীয়া LPG), 🏦 জন ধন (বেংক একাউণ্ট), 🌱 শস্য বীমা (শস্য বীমা), 🍚 ৰেচন কাৰ্ড (সস্তা শস্য)। কোন আঁচনিৰ বিষয়ে জানিব বিচাৰে?",
        "feedback": "correct"
    },
    {
        "language": "bhojpuri",
        "domain": "general",
        "intent": "GENERAL_QA",
        "scheme": None,
        "query": "CSC सेंटर क्या होला?",
        "response": "CSC माने Common Service Center — ई गाँव में एगो सरकारी दुकान बा जहाँ सभी सरकारी काम होला। इहाँ PM Kisan, Ayushman, Awas, Ration Card सभी के आवेदन हो सकेला। Aadhar बनावे, बैंक काम, आधार अपडेट — सब CSC पर होला। आपके नजदीकी CSC locatecscindia.in पर ढूंढ सकीलें।",
        "feedback": "correct"
    },
    {
        "language": "assamese",
        "domain": "general",
        "intent": "GENERAL_QA",
        "scheme": None,
        "query": "CSC কেন্দ্ৰ কি?",
        "response": "CSC মানে Common Service Center — এইটো গাঁৱত এটা চৰকাৰী সেৱা কেন্দ্ৰ য'ত সকলো চৰকাৰী কাম কৰা যায়। ইয়াত PM Kisan, Ayushman, Awas, ৰেচন কাৰ্ড সকলোৰে আবেদন কৰিব পৰা যায়। আধাৰ বনোৱা, বেংকৰ কাম, আধাৰ আপডেট — সব CSCত হয়। আপোনাৰ নিকটৱৰ্তী CSC locatecscindia.in ত বিচাৰিব পাৰিব।",
        "feedback": "correct"
    },
]


async def generate_more_pairs_with_gemini(scheme_key: str, language: str, count: int = 10) -> list:
    """Use Gemini to generate additional Q&A pairs for a scheme"""
    from google import genai as g
    c = g.Client(vertexai=True, project="asteria-497909", location="us-central1")

    lang_name = "Bhojpuri (भोजपुरी)" if language == "bhojpuri" else "Assamese (অসমীয়া)"
    lang_instruction = (
        "Use authentic rural Bhojpuri dialect. Not Hindi. Bhojpuri words like: बा, बाटे, हऊ, बानी, मिलिही, चाही, होखे"
        if language == "bhojpuri"
        else "Use authentic Assamese. Words like: আছে, কৰক, পাব, যাওক, হ'ব, লাগিব, পাৰিব"
    )

    prompt = f"""Generate {count} realistic Q&A pairs in {lang_name} about the {scheme_key} government scheme in India.

{lang_instruction}

These should be real questions that rural Indian citizens would ask about this scheme.
Cover: eligibility, documents, application process, benefits, common problems, how to check status.

Return ONLY a JSON array like this:
[
  {{"query": "question in {lang_name}", "response": "helpful answer in {lang_name}", "intent": "KNOW_SCHEME"}},
  ...
]

Intent options: KNOW_SCHEME, CHECK_ELIGIBILITY, GET_DOCUMENTS, APPLY_SCHEME, COMPLAINT, GENERAL_QA

Return ONLY valid JSON array, no markdown:"""

    try:
        import asyncio
        response = await client.aio.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        text = response.text.strip()
        if "```" in text:
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        text = text.strip()

        pairs = json.loads(text)
        # Add metadata
        enriched = []
        for p in pairs:
            if "query" in p and "response" in p:
                enriched.append({
                    "language": language,
                    "domain": get_domain(scheme_key),
                    "intent": p.get("intent", "KNOW_SCHEME"),
                    "scheme": scheme_key,
                    "query": p["query"],
                    "response": p["response"],
                    "feedback": "correct",
                    "source": "gemini_generated"
                })
        return enriched
    except Exception as e:
        print(f"  ⚠️ Gemini generation failed for {scheme_key}/{language}: {e}")
        return []


def get_domain(scheme_key: str) -> str:
    domains = {
        "PM_KISAN": "agriculture", "FASAL_BIMA": "agriculture",
        "AYUSHMAN_BHARAT": "healthcare",
        "PM_AWAS": "housing",
        "UJJWALA": "energy",
        "JAN_DHAN": "finance",
        "RATION_CARD": "food"
    }
    return domains.get(scheme_key, "civic")


async def push_to_adaption(pairs: list) -> int:
    """Push seed pairs to Adaption platform"""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
        from adaption.client import adaption_client

        success = 0
        for pair in pairs:
            result = await adaption_client.ingest_qa_pair(
                query=pair["query"],
                response=pair["response"],
                language=pair["language"],
                domain=pair["domain"],
                intent=pair["intent"],
                scheme=pair.get("scheme"),
                feedback=pair.get("feedback"),
                session_id="seed_data"
            )
            if result.get("local"):
                success += 1
        return success
    except Exception as e:
        print(f"  ⚠️ Adaption push error: {e}")
        return 0


async def main():
    print("=" * 60)
    print("🌱 ASTERIA — Seed Dataset Generator")
    print("=" * 60)

    all_pairs = list(SEED_PAIRS)
    print(f"\n✅ Hand-crafted seed pairs: {len(all_pairs)}")

    # Generate additional pairs with Gemini
    schemes = ["PM_KISAN", "AYUSHMAN_BHARAT", "PM_AWAS", "UJJWALA", "JAN_DHAN", "FASAL_BIMA", "RATION_CARD"]
    languages = ["bhojpuri", "assamese"]

    print("\n🤖 Generating additional pairs with Gemini...")
    for scheme in schemes:
        for lang in languages:
            print(f"  → {scheme} / {lang}...", end=" ")
            new_pairs = await generate_more_pairs_with_gemini(scheme, lang, count=8)
            all_pairs.extend(new_pairs)
            print(f"✓ +{len(new_pairs)} pairs")
            await asyncio.sleep(1)  # Rate limit

    print(f"\n📊 Total dataset size: {len(all_pairs)} pairs")

    # Save locally
    output_dir = os.path.join(os.path.dirname(__file__), "..", "dataset")
    os.makedirs(output_dir, exist_ok=True)

    bho = [p for p in all_pairs if p["language"] == "bhojpuri"]
    asm = [p for p in all_pairs if p["language"] == "assamese"]

    with open(os.path.join(output_dir, "bhojpuri_civic_qa.jsonl"), "w", encoding="utf-8") as f:
        for pair in bho:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    with open(os.path.join(output_dir, "assamese_civic_qa.jsonl"), "w", encoding="utf-8") as f:
        for pair in asm:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")

    print(f"  💾 Bhojpuri: {len(bho)} pairs → dataset/bhojpuri_civic_qa.jsonl")
    print(f"  💾 Assamese: {len(asm)} pairs → dataset/assamese_civic_qa.jsonl")

    # Push to Adaption
    print(f"\n📤 Pushing to Adaptive Data platform...")
    pushed = await push_to_adaption(all_pairs)
    print(f"  ✅ Pushed {pushed} pairs to Adaption (+ local backup)")

    print("\n" + "=" * 60)
    print(f"🎉 Dataset ready! {len(all_pairs)} total Q&A pairs")
    print(f"   Bhojpuri: {len(bho)} | Assamese: {len(asm)}")
    print("=" * 60)
    print("\nNext step: python scripts/push_to_huggingface.py")


if __name__ == "__main__":
    asyncio.run(main())
