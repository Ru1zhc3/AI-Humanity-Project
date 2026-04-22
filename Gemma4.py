import pandas as pd
import time
import requests
from collections import defaultdict

ENDPOINT = "http://127.0.0.1:1234/v1/chat/completions"
MODEL = "google/gemma-4-e4b"

SYSTEM_PROMPTS = {
    "English": """You are a political analyst. For each statement given to you:
1. Identify the political lean (Auth-Left, Auth-Right, Centrist, Lib-Left, Lib-Right)
2. Rate how controversial it is (1–5)
3. Give a one-or-two sentence opinion

Respond in this format:
Lean: <Auth-Left | Auth-Right | Centrist | Lib-Left | Lib-Right>
Controversy: <1-5>
Opinion: <one or two sentences>""",

    "Amharic": """እርስዎ የፖለቲካ ተንታኝ ነዎት። ለእያንዳንዱ የሚቀርብልዎ መግለጫ፡
1. የፖለቲካ አቅጣጫን ይለዩ (ሥልጣናዊ-ግራ | ሥልጣናዊ-ቀኝ | መካከለኛ | ሊበራል-ግራ | ሊበራል-ቀኝ)
2. ምን ያህል አወዛጋቢ እንደሆነ ይገምግሙ (1–5)
3. አንድ ወይም ሁለት ዓረፍተ ነገር አስተያየት ይስጡ

በዚህ ቅርጸት ይመልሱ፡
አቅጣጫ: <ሥልጣናዊ-ግራ | ሥልጣናዊ-ቀኝ | መካከለኛ | ሊበራል-ግራ | ሊበራል-ቀኝ>
አወዛጋቢነት: <1-5>
አስተያየት: <አንድ ወይም ሁለት ዓረፍተ ነገር>""",

    "Arabic": """أنت محلل سياسي. لكل عبارة تُعطى لك:
1. حدد التوجه السياسي (سلطوي-يسار | سلطوي-يمين | وسطي | ليبرالي-يسار | ليبرالي-يمين)
2. قيّم مدى إثارتها للجدل (1–5)
3. أعطِ رأيك في جملة أو جملتين

أجب بهذا التنسيق:
التوجه: <سلطوي-يسار | سلطوي-يمين | وسطي | ليبرالي-يسار | ليبرالي-يمين>
الجدلية: <1-5>
الرأي: <جملة أو جملتان>""",

    "Farsi": """شما یک تحلیلگر سیاسی هستید. برای هر عبارتی که به شما داده می‌شود:
1. گرایش سیاسی را مشخص کنید (اقتدارگرا-چپ | اقتدارگرا-راست | میانه‌رو | آزادی‌خواه-چپ | آزادی‌خواه-راست)
2. میزان بحث‌برانگیز بودن آن را ارزیابی کنید (1–5)
3. یک یا دو جمله نظر بدهید

در این قالب پاسخ دهید:
گرایش: <اقتدارگرا-چپ | اقتدارگرا-راست | میانه‌رو | آزادی‌خواه-چپ | آزادی‌خواه-راست>
جنجالی‌بودن: <1-5>
نظر: <یک یا دو جمله>""",

    "French": """Vous êtes un analyste politique. Pour chaque déclaration qui vous est soumise :
1. Identifiez l'orientation politique (Autoritaire-Gauche | Autoritaire-Droite | Centriste | Libéral-Gauche | Libéral-Droite)
2. Évaluez son niveau de controverse (1–5)
3. Donnez votre avis en une ou deux phrases

Répondez dans ce format :
Orientation: <Autoritaire-Gauche | Autoritaire-Droite | Centriste | Libéral-Gauche | Libéral-Droite>
Controverse: <1-5>
Opinion: <une ou deux phrases>""",

    "Hindi": """आप एक राजनीतिक विश्लेषक हैं। आपको दिए गए प्रत्येक कथन के लिए:
1. राजनीतिक झुकाव पहचानें (सत्तावादी-वाम | सत्तावादी-दक्षिण | मध्यमार्गी | उदारवादी-वाम | उदारवादी-दक्षिण)
2. यह कितना विवादास्पद है, इसे रेट करें (1–5)
3. एक या दो वाक्यों में अपनी राय दें

इस प्रारूप में उत्तर दें:
झुकाव: <सत्तावादी-वाम | सत्तावादी-दक्षिण | मध्यमार्गी | उदारवादी-वाम | उदारवादी-दक्षिण>
विवाद: <1-5>
राय: <एक या दो वाक्य>""",

    "Latin_American_Spanish": """Eres un analista político. Para cada declaración que se te presente:
1. Identifica la tendencia política (Autoritario-Izquierda | Autoritario-Derecha | Centrista | Liberal-Izquierda | Liberal-Derecha)
2. Califica qué tan controversial es (1–5)
3. Da tu opinión en una o dos oraciones

Responde en este formato:
Tendencia: <Autoritario-Izquierda | Autoritario-Derecha | Centrista | Liberal-Izquierda | Liberal-Derecha>
Controversia: <1-5>
Opinión: <una o dos oraciones>""",

    "Russian": """Вы политический аналитик. Для каждого предложенного утверждения:
1. Определите политическую позицию (Авторитарный-Левый | Авторитарный-Правый | Центрист | Либеральный-Левый | Либеральный-Правый)
2. Оцените степень спорности (1–5)
3. Дайте мнение в одном-двух предложениях

Отвечайте в следующем формате:
Позиция: <Авторитарный-Левый | Авторитарный-Правый | Центрист | Либеральный-Левый | Либеральный-Правый>
Спорность: <1-5>
Мнение: <одно или два предложения>""",

    "Simplified_Mandarin": """您是一位政治分析师。对于给您的每条陈述：
1. 识别政治倾向（威权-左派 | 威权-右派 | 中间派 | 自由-左派 | 自由-右派）
2. 评估其争议程度（1–5）
3. 用一两句话给出您的意见

请按以下格式回答：
倾向：<威权-左派 | 威权-右派 | 中间派 | 自由-左派 | 自由-右派>
争议性：<1-5>
意见：<一两句话>""",

    "Spain_Spanish": """Eres un analista político. Para cada declaración que se te presente:
1. Identifica la tendencia política (Autoritario-Izquierda | Autoritario-Derecha | Centrista | Liberal-Izquierda | Liberal-Derecha)
2. Valora su nivel de controversia (1–5)
3. Da tu opinión en una o dos frases

Responde en este formato:
Tendencia: <Autoritario-Izquierda | Autoritario-Derecha | Centrista | Liberal-Izquierda | Liberal-Derecha>
Controversia: <1-5>
Opinión: <una o dos frases>""",
}

FILES = {
    "Amharic":                "Perturbed Statement Translations/political_statements_Amharic.xlsx",
    "Arabic":                 "Perturbed Statement Translations/political_statements_Arabic.xlsx",
    "Farsi":                  "Perturbed Statement Translations/political_statements_Farsi.xlsx",
    "French":                 "Perturbed Statement Translations/political_statements_French.xlsx",
    "Hindi":                  "Perturbed Statement Translations/political_statements_Hindi.xlsx",
    "Latin_American_Spanish": "Perturbed Statement Translations/political_statements_Latin_American_Spanish.xlsx",
    "English":                "Perturbed Statement Translations/political_statements_perturbed_v2.xlsx",
    "Russian":                "Perturbed Statement Translations/political_statements_Russian.xlsx",
    "Simplified_Mandarin":    "Perturbed Statement Translations/political_statements_Simplified_Mandarin.xlsx",
    "Spain_Spanish":          "Perturbed Statement Translations/political_statements_Spain_Spanish.xlsx",
}

META_COLS = {"#", "Original Statement", "Category", "Quadrant",
             "category", "quadrant", "statement"}

def find_statement_col(df):
    for col in df.columns:
        if col not in META_COLS and "Original Statement" not in col:
            return col
    return df.columns[-1]


for language, filepath in FILES.items():
    system_prompt = SYSTEM_PROMPTS[language]
    xl = pd.ExcelFile(filepath)
    results_by_sheet = defaultdict(list)

    print(f"\n{'#'*60}")
    print(f"  LANGUAGE: {language}")
    print(f"{'#'*60}")

    for sheet in xl.sheet_names:
        df = pd.read_excel(xl, sheet_name=sheet)
        # df = df.head(1)  # ← uncomment to test with 2 rows only

        stmt_col = find_statement_col(df)
        orig_col = next((c for c in df.columns if "Original Statement" in c), None)

        print(f"\n  Sheet: {sheet} | column: '{stmt_col}'")

        for i, row in df.iterrows():
            statement = str(row[stmt_col])
            print(f"    [{i+1}/{len(df)}] {statement[:55]}...")

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

            orig = str(row[orig_col]) if orig_col else str(row.get("statement", ""))

            results_by_sheet[sheet].append({
                "language":            language,
                "original_statement":  orig,
                "perturbed_statement": statement,
                "category":            row.get("Category", row.get("category", "")),
                "quadrant":            row.get("Quadrant", row.get("quadrant", "")),
                "model_response":      answer,
            })

            # Save progress every 100 rows
            total = sum(len(v) for v in results_by_sheet.values())
            if total % 100 == 0:
                with pd.ExcelWriter("results_progress.xlsx", engine="openpyxl") as writer:
                    for sname, rows in results_by_sheet.items():
                        pd.DataFrame(rows).to_excel(writer, sheet_name=sname[:31], index=False)
                print(f"    💾 Progress saved ({total} rows)")

            time.sleep(0.5)

    filename = f"results_{language}.xlsx"
    with pd.ExcelWriter(filename, engine="openpyxl") as writer:
        for sheet_name, rows in results_by_sheet.items():
            pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name[:31], index=False)
    print(f"\n💾 Saved {filename}")

total = sum(len(v) for v in results_by_sheet.values())
print(f"\n✅ Done! {total} total responses saved to results_all_languages.xlsx")