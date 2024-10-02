import google.generativeai as genai
from integrations.ai import ArtifInteli

class Gemini(ArtifInteli.ArtifInteli):
    def __init__(self) -> None:
        genai.configure(api_key=self.env.get("F2B_GEMINI_IA_API_KEY"))
        self.ai_model = genai.GenerativeModel("gemini-1.5-flash")
        super().__init__()
    
    def suggest_email(self, subject: str,type:str):
        if type=="M":
            question = "Melhore o texto para que possa ser enviado um e-mail para cada cliente da minha lista de contatos.\n "+subject
        elif type=="A":
            question = "Crie um texto de apresentação de produtos para ser enviado por e-mail à cada cliente da minha lista de contatos. O texto será baseado no que já tenho logo abaixo.\n"+subject
        elif type=="P":
            question = "Crie uma proposta de venda de produtos para ser enviada por e-mail à cada cliente da minha lista. A proposta terá como premissas: "+subject
        elif type=="O":
            question = "Crie um exemplo de orçamento para que seja enviada por e-mail à cada cliente da minha lista com base nos seguintes dados: "+subject+ " coloque os produtos em uma tabela HTML sem bordas e com cabeçalho em negrito"
        
        content = self.ai_model.generate_content(question).text
        new_content = str(content).split("\n\n")
        subject = new_content[0].replace("##","").replace("Assunto: ","")
        content = "<br><br>".join(new_content[1:])
        content = content.replace("\n","")
        return {
            "subject": subject,
            "content": content
        }
    
    