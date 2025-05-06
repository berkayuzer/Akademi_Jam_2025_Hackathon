# Gemini API ile roadmap ve challenge üretimi için temel fonksiyonlar
import os
from google import genai
from google.genai import types
from dotenv import load_dotenv
load_dotenv()

GEMINI_KEY = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=GEMINI_KEY)

def extract_json_from_text(text):
    import re, json
    # Kod bloğu varsa sadece kod bloğunu al
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        text = match.group(1)
    text = text.strip()
    # Kod bloğu içindeki gömülü kodları (ör: ```z ... ```) temizle
    text = re.sub(r"```[a-zA-Z]*\s*([\s\S]+?)\s*```", "", text)
    # Çok satırlı stringlerdeki kaçış karakterlerini normalize et
    text = text.replace('\\n', '\\n').replace('\\"', '"')
    # Önce klasik json.loads ile dene
    try:
        if text.startswith('[') or text.startswith('{'):
            return json.loads(text)
        idx = text.find('{')
        if idx == -1:
            idx = text.find('[')
        if idx != -1:
            text = text[idx:]
            return json.loads(text)
    except Exception as e:
        print('extract_json_from_text error:', e)
        # Tek tırnakları çift tırnağa çevirip tekrar dene
        try:
            fixed = text.replace("'", '"')
            return json.loads(fixed)
        except Exception as e2:
            print('extract_json_from_text fallback error:', e2)
            # Son çare: roadmap bozulmasın diye hata fırlat
            raise
    raise ValueError('No valid JSON found in Gemini output')

def extract_json_from_text_step_challenge(text):
    import re, json
    # Kod bloğu varsa sadece kod bloğunu al
    match = re.search(r"```(?:json)?\s*([\s\S]+?)\s*```", text)
    if match:
        text = match.group(1)
    text = text.strip()
    # explanation alanındaki gömülü kod bloklarını, satır sonlarını ve çift tırnakları temizle
    def clean_explanation(m):
        explanation = m.group(2)
        # Gömülü kod bloklarını sil
        explanation = re.sub(r'```[a-zA-Z]*\s*([\s\S]+?)\s*```', '', explanation)
        # Satır sonlarını boşluk yap
        explanation = explanation.replace('\n', ' ').replace('\r', ' ')
        # Çift tırnakları escape et
        explanation = explanation.replace('"', '\\"')
        return m.group(1) + explanation + m.group(3)
    text = re.sub(r'("explanation"\s*:\s*")((?:[^"\\]|\\.)*)(")', clean_explanation, text, flags=re.DOTALL)
    text = text.replace('\\"', '"')
    # JSON parse
    try:
        if text.startswith('[') or text.startswith('{'):
            return json.loads(text)
        idx = text.find('{')
        if idx == -1:
            idx = text.find('[')
        if idx != -1:
            text = text[idx:]
            return json.loads(text)
    except Exception as e:
        print('extract_json_from_text_step_challenge error:', e)
        # Tek tırnakları çift tırnağa çevirip tekrar dene
        try:
            fixed = text.replace("'", '"')
            return json.loads(fixed)
        except Exception as e2:
            print('extract_json_from_text_step_challenge fallback error:', e2)
            raise
    raise ValueError('No valid JSON found in Gemini output')

def generate_roadmap(topics):
    prompt = f"Kullanıcının eksik olduğu yazılım konuları: {', '.join(topics)}. Her konu için öğrenme adımlarını ve kısa açıklamalarını kutucuklar halinde bir yol haritası (roadmap) olarak JSON formatında üret. Tüm açıklamalar ve başlıklar Türkçe olmalı. Sadece JSON döndür. Yapı: [{{'topic': '...', 'summary': '...'}}]"
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            max_output_tokens=2048,
            temperature=0.1
        )
    )
    import json as pyjson
    try:
        text = response.candidates[0].content.parts[0].text
        print('Gemini roadmap raw:', text)
        roadmap = extract_json_from_text(text)
        print('roadmap:', roadmap)
        return roadmap
    except Exception as e:
        print('Gemini roadmap error:', e)
        # Dummy veri ile doldur
        return [
            {"topic": "loops", "summary": "Döngüler programlamada tekrarlı işlemler için kullanılır."},
            {"topic": "functions", "summary": "Fonksiyonlar kodunuzu modüler ve tekrar kullanılabilir yapar."},
            {"topic": "variables", "summary": "Değişkenler verileri saklamak için kullanılır."}
        ]

def generate_topic_summary_and_challenges(language, topic):
    # language parametresi aslında kullanıcı adı ise, doğru dili UserProgress tablosundan çek
    from database import SessionLocal, UserProgress
    db = SessionLocal()
    user = language
    user_progress = db.query(UserProgress).filter(UserProgress.username == user, UserProgress.topic == topic).first()
    if user_progress:
        language_real = user_progress.language
    else:
        language_real = "python"  # fallback
    db.close()
    prompt = (
        f"{language_real} programlama dilinde '{topic}' konusu için kısa bir özet ve kolay, orta, zor seviyede 3 programlama challenge'ı başlığı ve açıklaması üret. "
        f"Her challenge için örnek input/output ve gizli test case'ler de üret. "
        f"Tüm kod ve örnekler {language_real} dilinde ve açıklamalar Türkçe olmalı. "
        "Sonucu şu JSON formatında döndür: "
        "{'summary': '...', 'challenges': [{'level': 'easy', 'title': '...', 'description': '...', 'example_input': '...', 'example_output': '...', 'hidden_tests': [{'input': '...', 'output': '...'}]}]}"
        ". Sadece JSON döndür. Açıklamalar ve başlıklar Türkçe olmalı."
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            max_output_tokens=2048,
            temperature=0.1
        )
    )
    import json as pyjson
    try:
        text = response.candidates[0].content.parts[0].text
        print('Gemini topic raw:', text)
        result = extract_json_from_text(text)
        print('result:', result)
        return result
    except Exception as e:
        print('Gemini topic error:', e)
        return {}

def generate_step_examples_and_challenges(language, topic, step):
    prompt = (
        f"{language} dilinde '{topic}' başlığı altındaki '{step}' konusu için kısa bir konu anlatımı (açıklama kısmında kod bloğu kullanma, sadece düz metin yaz). "
        "Bu step için 2 örnek (input ve output ile) ve kolay, orta, zor seviyede 3 farklı challenge üret. "
        "Her challenge için: seviye (easy/medium/hard), başlık, açıklama, örnek input, örnek output ve 2 gizli test case üret. "
        "Tüm açıklamalar ve başlıklar Türkçe olmalı. "
        "Sonucu şu JSON formatında döndür: "
        "{"
        "'explanation': '...', "
        "'examples': [{'input': '...', 'output': '...'}], "
        "'challenges': ["
        "  {'level': 'kolay', 'title': '...', 'description': '...', 'example_input': '...', 'example_output': '...', 'hidden_tests': [{'input': '...', 'output': '...'}]},"
        "  {'level': 'orta', 'title': '...', 'description': '...', 'example_input': '...', 'example_output': '...', 'hidden_tests': [{'input': '...', 'output': '...'}]},"
        "  {'level': 'zor', 'title': '...', 'description': '...', 'example_input': '...', 'example_output': '...', 'hidden_tests': [{'input': '...', 'output': '...'}]}"
        "]"
        "}"
    )
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[prompt],
        config=types.GenerateContentConfig(
            max_output_tokens=2048,
            temperature=0.1
        )
    )
    try:
        text = response.candidates[0].content.parts[0].text
        print('Gemini step raw:', text)
        result = extract_json_from_text_step_challenge(text)
        print('step result:', result)
        return result
    except Exception as e:
        print('Gemini step error:', e)
        return {}

def check_code_with_testcases(user_code, language, testcases):
    import subprocess
    results = []
    for case in testcases:
        try:
            proc = subprocess.run(["python", "-c", user_code], input=case['input'].encode(), capture_output=True, timeout=3)
            output = proc.stdout.decode().strip()
            results.append(output == case['output'].strip())
        except Exception:
            results.append(False)
    return results
