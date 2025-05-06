import gradio as gr
import requests
import json
import os
import requests as pyrequests
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
print(f"[DEBUG] os.environ.get('GEMINI_KEY') = {os.environ.get('GEMINI_KEY')}")


def gr_register(username, password):
    try:
        r = requests.post("http://localhost:8000/register", json={"username": username, "password": password})
        if r.status_code == 200:
            return "Kayıt başarılı! Giriş yapabilirsiniz.", ""
        else:
            return f"Hata: {r.json().get('detail', 'Bilinmeyen hata')}", ""
    except Exception as e:
        return f"Hata: {str(e)}", ""

def gr_login(username, password):
    try:
        r = requests.post("http://localhost:8000/login", data={"username": username, "password": password})
        if r.status_code == 200:
            return "success", username, ""
        else:
            return "error", "", f"Hata: {r.json().get('detail', 'Bilinmeyen hata')}"
    except Exception as e:
        return "error", "", f"Hata: {str(e)}"

def save_deficiencies(username, python, variables):
    try:
        try:
            with open("deficiencies.json", "r") as f:
                data = json.load(f)
        except FileNotFoundError:
            data = {}
        data[username] = {
            "languages": ["Python"] if python else [],
            "fields": ["Değişkenler"] if variables else []
        }
        with open("deficiencies.json", "w") as f:
            json.dump(data, f)
        return "Kaydedildi!"
    except Exception as e:
        return f"Hata: {str(e)}"

def call_gemini_roadmap_api(username):
    GEMINI_KEY = os.getenv("GEMINI_KEY")
    print(f"[DEBUG] Using GEMINI_KEY: {GEMINI_KEY}")
    try:
        with open("deficiencies.json", "r") as f:
            data = json.load(f)
        user_def = data.get(username, {})
        print(f"[DEBUG] User deficiencies for {username}: {user_def}")
    except Exception as e:
        print(f"[DEBUG] Error reading deficiencies.json: {e}")
        user_def = {}
    prompt = (
        "Kullanıcının eksik olduğu konulara yönelik, her konu için adım adım ilerleyen bir öğrenme yol haritası oluştur. "
        "Her adım kısa olmalı ve şunları içermeli: 1) adım başlığı (sade ve öz olmalı.), 2) konuya dair kısa bir açıklama, 3) 1-2 adet kaliteli kaynak önerisi (kitap, makale, dokümantasyon, online kurs veya video). "
        "Kaynakların *adı* ve *URL*’i mutlaka verilmeli. Sıralama mantıklı bir öğrenme sürecini yansıtmalı (temelden karmaşığa). "
        "Yalnızca GEÇERLİ ve PARSABLE bir JSON döndür. JSON dışı hiçbir açıklama, cümle ya da başlık ekleme. "
        "JSON formatı şöyle olmalı:\n"
        "{\n"
        "  \"KonuAdı\": [\n"
        "    {\n"
        "      \"adim\": \"Adım Başlığı\",\n"
        "      \"aciklama\": \"Bu adımda öğrenilecek temel kavram veya uygulama açıklanır.\",\n"
        "      \"kaynaklar\": [\n"
        "        {\"ad\": \"Kaynak Adı\", \"url\": \"https://...\"},\n"
        "        {\"ad\": \"Kaynak Adı\", \"url\": \"https://...\"}\n"
        "      ]\n"
        "    },\n"
        "    ...\n"
        "  ]\n"
        "}\n"
        f"Kullanıcının eksik olduğu alanlar: Diller: {', '.join(user_def.get('languages', []))}; Alanlar: {', '.join(user_def.get('fields', []))}.\n"
        "Bu konuların her biri için yol haritası oluştur."
    )

    print(f"[DEBUG] Gemini prompt: {prompt}")
    try:
        client = genai.Client(api_key=GEMINI_KEY)
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                max_output_tokens=2048,
                temperature=0.1
            )
        )
        text = response.text
        text = text.strip()
        # Markdown bloklarını temizle
        if text.startswith("```json"):
            text = text[7:]
        if text.startswith("```"):
            text = text[3:]
        if text.endswith("```"):
            text = text[:-3]
        import re
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            roadmap_json = match.group(0)
            print(f"[DEBUG] Extracted JSON: {roadmap_json}")
            # save json
            with open("roadmap.json", "w", encoding="utf-8") as f:
                json.dump(json.loads(roadmap_json), f, ensure_ascii=False, indent=2)
            try:
                # load roadmap.json 
                with open("roadmap.json", "r") as f:
                    roadmap_json_f = f.read()

                roadmap = json.loads(roadmap_json_f)
                return roadmap, None
            except Exception as e:
                print(f"[DEBUG] JSON parse error: {e}")
                return None, f"Gemini yanıtı JSON olarak ayrıştırılamadı: {e}<br><br>Yanıt:<br><pre>{text}</pre>"
        else:
            print("[DEBUG] Gemini yanıtı beklenen formatta değil.")
            return None, f"Gemini yanıtı beklenen formatta değil.<br><br>Yanıt:<br><pre>{text}</pre>"
    except Exception as e:
        print(f"[DEBUG] Gemini SDK hatası: {str(e)}")
        return None, f"Gemini SDK hatası: {str(e)}"

def parse_and_render_roadmap_json(filepath="roadmap.json"):
    import json
    import codecs
    try:
        with codecs.open(filepath, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except Exception as e:
        return f"<b>Yol haritası okunamadı:</b> {e}"
    html = ""
    for topic, steps in data.items():
        html += f'<h3>{topic}</h3><ol>'
        for step in steps:
            html += f'<li><b>{step.get("adim", "")}</b>: {step.get("aciklama", "")}<ul>'
            for kaynak in step.get("kaynaklar", []):
                html += f'<li><a href="{kaynak.get("url", "#")}" target="_blank">{kaynak.get("ad", "Kaynak")}</a></li>'
            html += '</ul></li>'
        html += '</ol>'
    return html

def render_simple_roadmap(roadmap):
    import gradio as gr
    with gr.Blocks() as roadmap_ui:
        gr.Markdown("## Kişisel Yol Haritası")
        for main_topic, steps in roadmap.items():
            with gr.Accordion(main_topic, open=False):
                for idx, step in enumerate(steps):
                    with gr.Row():
                        gr.Markdown(f"**{step.get('adim', '')}**")
                        summary_btn = gr.Button("Konu Özeti & Kaynaklar", elem_id=f"summary_{main_topic}_{idx}")
                        problem_btn = gr.Button("Problem Çözme", elem_id=f"problem_{main_topic}_{idx}")
                        summary_output = gr.Textbox(label="Konu Özeti & Kaynaklar", visible=False)
                        problem_output = gr.Textbox(label="Problem Çözme", visible=False)
                        def show_summary(step=step):
                            summary = f"**Açıklama:** {step.get('aciklama', '')}\n\n"
                            summary += "**Kaynaklar:**\n"
                            for kaynak in step.get("kaynaklar", []):
                                summary += f"- [{kaynak.get('ad', 'Kaynak')}]({kaynak.get('url', '#')})\n"
                            return gr.update(value=summary, visible=True), gr.update(visible=False)
                        def show_problem(step=step):
                            return gr.update(visible=False), gr.update(value=f"Bu başlık için problem çözme sayfası (örnek: {step.get('adim', '')})", visible=True)
                        summary_btn.click(show_summary, outputs=[summary_output, problem_output])
                        problem_btn.click(show_problem, outputs=[summary_output, problem_output])
    return roadmap_ui

def render_simple_roadmap_from_file(filepath="roadmap.json"):
    import json
    import codecs
    try:
        with codecs.open(filepath, "r", encoding="utf-8", errors="replace") as f:
            data = json.load(f)
    except Exception as e:
        return f"<b>Yol haritası okunamadı:</b> {e}"
    html = "<div><h2>Kişisel Yol Haritası</h2>"
    for main_topic, subtopics in data.items():
        html += f'<details><summary><b>{main_topic}</b></summary>'
        if isinstance(subtopics, dict):
            for subtopic, steps in subtopics.items():
                html += f'<details style="margin-left:20px"><summary>{subtopic}</summary>'
                for step in steps:
                    html += f'<div style="margin-left:40px"><b>{step.get("adim", "")}</b>: {step.get("aciklama", "")}<ul>'
                    for kaynak in step.get("kaynaklar", []):
                        html += f'<li><a href="{kaynak.get("url", "#")}" target="_blank">{kaynak.get("ad", "Kaynak")}</a></li>'
                    html += '</ul></div>'
                html += '</details>'
        elif isinstance(subtopics, list):
            for step in subtopics:
                html += f'<div style="margin-left:20px"><b>{step.get("adim", "")}</b>: {step.get("aciklama", "")}<ul>'
                for kaynak in step.get("kaynaklar", []):
                    html += f'<li><a href="{kaynak.get("url", "#")}" target="_blank">{kaynak.get("ad", "Kaynak")}</a></li>'
                html += '</ul></div>'
        html += '</details>'
    html += "</div>"
    return html
def build_challenge_ui():
        with gr.Blocks() as challenge_ui:
            gr.Markdown("## Kod Challenge'ları")

            # Challenge seçimi
            challenge_dropdown = gr.Dropdown(
                label="Challenge Seçin",
                choices=[c["title"] for c in load_challenges()],
                type="index"
            )

            challenge_description = gr.Markdown()
            difficulty_label = gr.Label(label="Zorluk Seviyesi")
            starter_code = gr.Code(label="Başlangıç Kodu", language="python")

            user_code = gr.Code(label="Çözümünüz", language="python")
            run_btn = gr.Button("Kodu Çalıştır")

            test_results = gr.Textbox(label="Test Sonuçları", interactive=False)

            def load_challenge_details(index):
                challenges = load_challenges()
                if 0 <= index < len(challenges):
                    challenge = challenges[index]
                    return (
                        f"### {challenge['title']}\n\n{challenge['description']}",
                        challenge["difficulty"],
                        challenge["starter_code"],
                        challenge["starter_code"]
                    )
                return "", "", "", ""

            challenge_dropdown.change(
                load_challenge_details,
                inputs=[challenge_dropdown],
                outputs=[challenge_description, difficulty_label, starter_code, user_code]
            )

            def execute_code(code, challenge_index):
                challenges = load_challenges()
                if 0 <= challenge_index < len(challenges):
                    challenge = challenges[challenge_index]
                    success, results = execute_python_code(code, challenge["test_cases"])
                    return results
                return "Challenge bulunamadı"

            run_btn.click(
                execute_code,
                inputs=[user_code, challenge_dropdown],
                outputs=test_results
            )

        return challenge_ui

def build_ui():
    with gr.Blocks() as demo:
        # Login/Register Page
        login_box = gr.Group(visible=True)
        with login_box:
            gr.Markdown("## Giriş Sayfası")
            username = gr.Textbox(label="Kullanıcı adı")
            password = gr.Textbox(label="Şifre", type="password")
            with gr.Row():
                signup_btn = gr.Button("Kayıt ol")
                login_btn = gr.Button("Giriş Yap")
            login_result = gr.Textbox(label="", interactive=False)
        
        # Deficiency Selection Page
        deficiency_box = gr.Group(visible=False)
        with deficiency_box:
            gr.Markdown("## Kullanıcının Eksik Olduğu Konular")
            user_label = gr.Textbox(label="Kullanıcı", interactive=False)
            gr.Markdown("**Diller**")
            lang_python = gr.Checkbox(label="Python")
            lang_javascript = gr.Checkbox(label="JavaScript")
            lang_java = gr.Checkbox(label="Java")
            gr.Markdown("**Alanlar**")
            field_variables = gr.Checkbox(label="Değişkenler")
            field_loops = gr.Checkbox(label="Döngüler")
            field_functions = gr.Checkbox(label="Fonksiyonlar")
            field_oop = gr.Checkbox(label="Nesne Yönelimli Programlama")
            save_btn = gr.Button("Kaydet")
            deficiency_result = gr.Textbox(label="", interactive=False)

        challenge_box = gr.Group(visible=False)
        with challenge_box:
            challenge_ui = build_challenge_ui()
            back_btn_challenge = gr.Button("Geri Dön")

        # Roadmap UI
        roadmap_box = gr.Group(visible=False)
        with roadmap_box:
            gr.Markdown("## Kişisel Öğrenme Yol Haritası (Gemini ile)")
            roadmap_accordion = gr.Accordion(label="Yol Haritası", open=True)
            with roadmap_accordion:
                roadmap_html = gr.HTML()
            back_btn = gr.Button("Geri Dön")

        # Registration logic
        def handle_signup(u, p):
            msg, _ = gr_register(u, p)
            return msg

        signup_btn.click(
            handle_signup,
            inputs=[username, password],
            outputs=login_result
        )

        # Login logic
        def handle_login(u, p):
            status, user, msg = gr_login(u, p)
            if status == "success":
                return (
                    gr.update(visible=False),  # Hide login box
                    gr.update(visible=True),   # Show deficiency box
                    user,                      # Set user_label
                    ""                         # Clear deficiency_result
                )
            else:
                return (
                    gr.update(visible=True),
                    gr.update(visible=False),
                    "",
                    msg
                )

        challenge_box = gr.Group(visible=False)
        with challenge_box:
            challenge_ui = build_challenge_ui()
            back_btn_challenge = gr.Button("Geri Dön")

        login_btn.click(
            handle_login,
            inputs=[username, password],
            outputs=[login_box, deficiency_box, user_label, deficiency_result]
        )

        # Deficiency save logic
        def handle_save(u, py, js, java, var, loops, funcs, oop):
            try:
                try:
                    with open("deficiencies.json", "r") as f:
                        data = json.load(f)
                except FileNotFoundError:
                    data = {}
                data[u] = {
                    "languages": [lang for lang, val in zip(["Python", "JavaScript", "Java"], [py, js, java]) if val],
                    "fields": [field for field, val in zip([
                        "Değişkenler", "Döngüler", "Fonksiyonlar", "Nesne Yönelimli Programlama"
                    ], [var, loops, funcs, oop]) if val]
                }
                with open("deficiencies.json", "w") as f:
                    json.dump(data, f)
                return "Kaydedildi!"
            except Exception as e:
                return f"Hata: {str(e)}"

        def after_save(u, py, js, java, var, loops, funcs, oop):
            msg = handle_save(u, py, js, java, var, loops, funcs, oop)
            roadmap, err = call_gemini_roadmap_api(u)
            if roadmap:
                roadmap_ui = render_simple_roadmap_from_file()
                return gr.update(visible=False), gr.update(visible=True), roadmap_ui, msg
            else:
                # Hata varsa, Gemini'nın ham çıktısını HTML olarak göster
                return gr.update(visible=True), gr.update(visible=False), err or "Yol haritası oluşturulamadı.", msg

        # Remove the old save_btn.click for handle_save
        # Connect save_btn to after_save only
        save_btn.click(
            after_save,
            inputs=[user_label, lang_python, lang_javascript, lang_java, field_variables, field_loops, field_functions, field_oop],
            outputs=[deficiency_box, roadmap_box, roadmap_html, deficiency_result]
        )
        back_btn.click(
            lambda: (gr.update(visible=True), gr.update(visible=False)),
            outputs=[deficiency_box, roadmap_box]
        )

        roadmap_btn = gr.Button("Challenge'ları Görüntüle", visible=False)

        def show_challenges():
            return (
                gr.update(visible=False),  # roadmap_box
                gr.update(visible=True)  # challenge_box
            )

        roadmap_btn.click(
            show_challenges,
            outputs=[roadmap_box, challenge_box]
        )

        back_btn_challenge.click(
            lambda: (gr.update(visible=True), gr.update(visible=False)),
            outputs=[roadmap_box, challenge_box]
        )


    return demo