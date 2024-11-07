from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount,Activity, Attachment
from botbuilder.schema.teams.additional_properties import ContentType
from assistant import Assistant
from azure.identity import DeviceCodeCredential
from msgraph import GraphServiceClient
import aiohttp, fitz, io, requests

class TeamsBot(ActivityHandler):
    def __init__(self):
        super().__init__()
        self.assistant = Assistant('chat_bbts_teste')  # Instância do assistente LLM

    async def on_message_activity(self, turn_context: TurnContext):
        # Verifica se há anexos enviados pelo usuário
        if turn_context.activity.attachments:
            # Processa o(s) anexo(s) e extrai o texto do(s) arquivo(s)
            file_texts = []
            for attachment in turn_context.activity.attachments:
                if attachment.content_type == "application/vnd.microsoft.teams.file.download.info":
                    download_url = attachment.content["downloadUrl"]
                    file_text = await self.download_and_extract_text(download_url)
                    file_texts.append(file_text)
                else:
                    await turn_context.send_activity("O tipo de arquivo não é suportado.")
            
            # Concatena o texto de todos os arquivos e envia para o assistente
            combined_text = "\n\n".join(file_texts)
            answer = self.assistant.invoke(combined_text)
            await turn_context.send_activity(f"Resposta com base no(s) arquivo(s):\n{answer}")
        
        else:
            # Caso não haja anexos, processa o texto da mensagem diretamente
            user_message = turn_context.activity.text
            answer = self.assistant.invoke(user_message)
            await turn_context.send_activity(f"{answer}")

    async def download_and_extract_text(self, url: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    content = await response.read()
                    # Usa PyMuPDF para extrair o texto do PDF
                    return self.extract_text_from_pdf(content)
                else:
                    return "Erro ao baixar o arquivo."

    def extract_text_from_pdf(self, pdf_bytes):
        pdf_text = ""
        # Carrega o PDF a partir dos bytes usando PyMuPDF
        with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf_document:
            for page in pdf_document:
                pdf_text += page.get_text("text")  # Extrai texto da página
        return pdf_text

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("Olá! Eu sou o assistente BBTS. No que posso ajudá-lo?")
