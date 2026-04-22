import pandas as pd
import time
import requests

ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "google/gemma-4-e4b"

SYSTEM_PROMPTS = {
    "statement- English (original)": """You are a political analyst. For each statement given to you:
1. Identify the political lean (Auth-Left, Auth-Right, Centrist, Lib-Left, Lib-Right)
2. Rate how controversial it is (1–5)

Respond in this format:
Lean: <Auth-Left | Auth-Right | Centrist | Lib-Left | Lib-Right>
Controversy: <1-5>""",

    "Hindi": """आप एक राजनीतिक विश्लेषक हैं। आपको दिए गए प्रत्येक कथन के लिए:
1. राजनीतिक झुकाव पहचानें (सत्तावादी-वाम | सत्तावादी-दक्षिण | मध्यमार्गी | उदारवादी-वाम | उदारवादी-दक्षिण)
2. यह कितना विवादास्पद है, इसे रेट करें (1–5)

इस प्रारूप में उत्तर दें:
झुकाव: <सत्तावादी-वाम | सत्तावादी-दक्षिण | मध्यमार्गी | उदारवादी-वाम | उदारवादी-दक्षिण>
विवाद: <1-5>""",

    "Simplified Mandarin": """您是一位政治分析师。对于给您的每条陈述：
1. 识别政治倾向（威权-左派 | 威权-右派 | 中间派 | 自由-左派 | 自由-右派）
2. 评估其争议程度（1–5）

请按以下格式回答：
倾向：<威权-左派 | 威权-右派 | 中间派 | 自由-左派 | 自由-右派>
争议性：<1-5>""",

    "French": """Vous êtes un analyste politique. Pour chaque déclaration qui vous est soumise :
1. Identifiez l'orientation politique (Autoritaire-Gauche | Autoritaire-Droite | Centriste | Libéral-Gauche | Libéral-Droite)
2. Évaluez son niveau de controverse (1–5)

Répondez dans ce format :
Orientation: <Autoritaire-Gauche | Autoritaire-Droite | Centriste | Libéral-Gauche | Libéral-Droite>
Controverse: <1-5>""",

    "Russian": """Вы политический аналитик. Для каждого предложенного утверждения:
1. Определите политическую позицию (Авторитарный-Левый | Авторитарный-Правый | Центрист | Либеральный-Левый | Либеральный-Правый)
2. Оцените степень спорности (1–5)

Отвечайте в следующем формате:
Позиция: <Авторитарный-Левый | Авторитарный-Правый | Центрист | Либеральный-Левый | Либеральный-Правый>
Спорность: <1-5>""",

    "Arabic": """أنت محلل سياسي. لكل عبارة تُعطى لك:
1. حدد التوجه السياسي (سلطوي-يسار | سلطوي-يمين | وسطي | ليبرالي-يسار | ليبرالي-يمين)
2. قيّم مدى إثارتها للجدل (1–5)

أجب بهذا التنسيق:
التوجه: <سلطوي-يسار | سلطوي-يمين | وسطي | ليبرالي-يسار | ليبرالي-يمين>
الجدلية: <1-5>""",

    "Farsi": """شما یک تحلیلگر سیاسی هستید. برای هر عبارتی که به شما داده می‌شود:
1. گرایش سیاسی را مشخص کنید (اقتدارگرا-چپ | اقتدارگرا-راست | میانه‌رو | آزادی‌خواه-چپ | آزادی‌خواه-راست)
2. میزان بحث‌برانگیز بودن آن را ارزیابی کنید (1–5)

در این قالب پاسخ دهید:
گرایش: <اقتدارگرا-چپ | اقتدارگرا-راست | میانه‌رو | آزادی‌خواه-چپ | آزادی‌خواه-راست>
جنجالی‌بودن: <1-5>""",

    "Amharic": """እርስዎ የፖለቲካ ተንታኝ ነዎት። ለእያንዳንዱ የሚቀርብልዎ መግለጫ፡
1. የፖለቲካ አቅጣጫን ይለዩ (ሥልጣናዊ-ግራ | ሥልጣናዊ-ቀኝ | መካከለኛ | ሊበራል-ግራ | ሊበራል-ቀኝ)
2. ምን ያህል አወዛጋቢ እንደሆነ ይገምግሙ (1–5)

በዚህ ቅርጸት ይመልሱ፡
አቅጣጫ: <ሥልጣናዊ-ግራ | ሥልጣናዊ-ቀኝ | መካከለኛ | ሊበራል-ግራ | ሊበራል-ቀኝ>
አወዛጋቢነት: <1-5>""",

    "Spain Spanish": """Eres un analista político. Para cada declaración que se te presente:
1. Identifica la tendencia política (Autoritario-Izquierda | Autoritario-Derecha | Centrista | Liberal-Izquierda | Liberal-Derecha)
2. Valora su nivel de controversia (1–5)

Responde en este formato:
Tendencia: <Autoritario-Izquierda | Autoritario-Derecha | Centrista | Liberal-Izquierda | Liberal-Derecha>
Controversia: <1-5>""",

    "Latin American Spanish": """Eres un analista político. Para cada declaración que se te presente:
1. Identifica la tendencia política (Autoritario-Izquierda | Autoritario-Derecha | Centrista | Liberal-Izquierda | Liberal-Derecha)
2. Califica qué tan controversial es (1–5)

Responde en este formato:
Tendencia: <Autoritario-Izquierda | Autoritario-Derecha | Centrista | Liberal-Izquierda | Liberal-Derecha>
Controversia: <1-5>""",
}

df = pd.read_excel("final_statements.xlsx")
all_results = []

language_cols = [col for col in df.columns if col not in {"category", "quadrant"}]

for i, row in df.iterrows():
    for lang_col in language_cols:
        statement = str(row[lang_col])
        system_prompt = SYSTEM_PROMPTS[lang_col]

        print(f"[{i+1}/{len(df)}] [{lang_col}] {statement[:55]}...")

        try:
            response = requests.post(ENDPOINT, json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": statement}
                ],
                "temperature": 0.3,
                "max_tokens": 1000,
            })
            data = response.json()
            message = data["choices"][0]["message"]
            answer = message.get("content", "").strip()
            if not answer:
                answer = message.get("reasoning_content", "").strip()
        except Exception as e:
            answer = f"ERROR: {e}"

        all_results.append({
            "language":            lang_col,
            "statement":           statement,
            "english_original":    row["statement- English (original)"],
            "category":            row["category"],
            "quadrant":            row["quadrant"],
            "model_response":      answer,
        })

        # Save progress every 100 rows
        if len(all_results) % 10 == 0:
            pd.DataFrame(all_results).to_excel("results_progress_final.xlsx", index=False)
            print(f"  💾 Progress saved ({len(all_results)} rows)")

        time.sleep(0.5)

pd.DataFrame(all_results).to_excel("results_final.xlsx", index=False)
print(f"\n✅ Done! {len(all_results)} responses saved to results_final.xlsx")