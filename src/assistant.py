import time
import re
from openai import AzureOpenAI
from config import Config

config = Config()

class Assistant:
    def __init__(self, name):
        # Configura o cliente do Azure OpenAI
        self.client = AzureOpenAI(
            azure_endpoint=config.AZURE_OPENAI_ENDPOINT,
            api_key=config.AZURE_OPENAI_API_KEY,
            api_version="2024-08-01-preview",
        )
        # Obtém o assistente especificado pelo nome
        self.assistant = self.get_assistant_by_name(name)

    def get_assistant_by_name(self, name):
        """Recupera o assistente com o nome especificado."""
        try:
            return next(
                filter(lambda x: x.name == name, self.client.beta.assistants.list().data)
            )
        except StopIteration:
            raise ValueError(f"Assistant '{name}' not found.")

    def invoke(self, input_text):
        """Chama a API com o texto do usuário e retorna a resposta."""
        if not input_text:
            return ''

        try:
            thread = self.create_thread()
            message = self.create_user_message(thread.id, input_text)
            run = self.initiate_run(thread.id)

            return self.retrieve_response(thread.id, run)
        except Exception as e:
            return f"Erro de comunicação com o chatbot: {e}"

    def create_thread(self):
        """Cria um novo thread para a conversa."""
        return self.client.beta.threads.create()

    def create_user_message(self, thread_id, input_text):
        """Envia a mensagem do usuário para o thread."""
        return self.client.beta.threads.messages.create(
            thread_id=thread_id,
            role="user",
            content=input_text,
        )

    def initiate_run(self, thread_id):
        """Inicia uma execução do assistente no thread especificado."""
        return self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant.id,
            instructions="Responda o usuário.",
        )

    def retrieve_response(self, thread_id, run):
        """Recupera a resposta do assistente e limpa o texto."""
        while run.status in ['queued', 'in_progress', 'cancelling']:
            time.sleep(0.5)
            run = self.client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run.id)

        if run.status == 'completed':
            messages = self.client.beta.threads.messages.list(thread_id=thread_id)
            answer = messages.data[0].content[0].text.value
            self.client.beta.threads.delete(thread_id=thread_id)
            return self.clean_text(answer)
        else:
            self.client.beta.threads.delete(thread_id=thread_id)
            return "A execução do assistente falhou."

    @staticmethod
    def clean_text(text):
        """Limpa o texto da resposta, removendo padrões específicos."""
        return re.sub(r'【.*?†source】', '', text)
