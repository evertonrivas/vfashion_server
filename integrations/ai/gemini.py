import google.generativeai as genai
from integrations.ai import ArtifInteli

class Gemini(ArtifInteli.ArtifInteli):
    def __init__(self) -> None:
        genai.configure(api_key=self.env.get("F2B_GEMINI_IA_API_KEY"))
        self.ai_model = genai.GenerativeModel("gemini-1.5-flash")
        super().__init__()
    
    def suggest_email(self, subject: str):
        content = self.ai_model.generate_content("Melhore o texto para que possa ser enviado um e-mail para cada cliente da minha lista de contatos.\n "+subject)
        return content.text.replace("\n","<br>")
    
    