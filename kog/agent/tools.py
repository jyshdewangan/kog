import os
import smtplib
from email.message import EmailMessage
from typing import Optional, Type, Dict, Any
from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool
from langchain_ollama import ChatOllama
from kog.core.session import session_manager
from kog.core.context import context_manager

class SummarizeInput(BaseModel):
    pass # No input needed, it uses the current context

class SummarizeTool(BaseTool):
    name: str = "summarize_context"
    description: str = "Use this tool to summarize the currently loaded context."
    args_schema: Type[BaseModel] = SummarizeInput

    def _run(self) -> str:
        current_session = session_manager.get_current_session()
        if not current_session:
            return "Error: No active session. Please create or load a session first."
            
        contexts = session_manager.get_session_contexts(current_session)
        if not contexts:
            return "Error: No context loaded in the current session."
            
        try:
            retriever = context_manager.get_retriever(contexts)
            docs = retriever.invoke("everything") # a generic query to pull top docs
            if not docs:
                return "No content found in the current context."

            context_str = "\n\n".join(d.page_content for d in docs)
            llm = ChatOllama(model="qwen2.5:3b", temperature=0)
            prompt = f"Summarize the following documents:\n\n{context_str}\n\nSummary:"
            
            result = llm.invoke(prompt)
            return result.content
        except Exception as e:
            return f"Error during summarization: {str(e)}"

class AskInput(BaseModel):
    question: str = Field(description="The question to ask about the context")

class AskTool(BaseTool):
    name: str = "ask_question"
    description: str = "Use this tool to ask a specific question based on the currently loaded contexts."
    args_schema: Type[BaseModel] = AskInput

    def _run(self, question: str) -> str:
        current_session = session_manager.get_current_session()
        if not current_session:
            return "Error: No active session."
            
        contexts = session_manager.get_session_contexts(current_session)
        if not contexts:
            return "Error: No context loaded."
            
        try:
            retriever = context_manager.get_retriever(contexts)
            docs = retriever.invoke(question)
            if not docs:
                return "I couldn't find any relevant information in the context."

            context_str = "\n\n".join(d.page_content for d in docs)
            llm = ChatOllama(model="qwen2.5:3b", temperature=0)
            prompt = (
                "Answer the following question based ONLY on the provided context.\n\n"
                f"Context: {context_str}\n\n"
                f"Question: {question}\n\n"
                "Answer:"
            )
            
            result = llm.invoke(prompt)
            return result.content
        except Exception as e:
            return f"Error answering question: {str(e)}"

class SearchContextInput(BaseModel):
    query: str = Field(description="The search query to find relevant information in the currently loaded context")

class SearchContextTool(BaseTool):
    name: str = "search_context"
    description: str = "Use this tool to search the loaded documents/contexts for raw text chunks matching your query. Returns exact text excerpts."
    args_schema: Type[BaseModel] = SearchContextInput

    def _run(self, query: str) -> str:
        current_session = session_manager.get_current_session()
        if not current_session:
            return "Error: No active session."
            
        contexts = session_manager.get_session_contexts(current_session)
        if not contexts:
            return "Error: No context loaded."
            
        try:
            retriever = context_manager.get_retriever(contexts)
            docs = retriever.invoke(query)
            if not docs:
                return "No relevant text found matching your query."

            context_str = "\n\n---\n\n".join(f"Source Excerpt:\n{d.page_content}" for d in docs)
            return f"Raw text excerpts from your documents:\n\n{context_str}"
        except Exception as e:
            return f"Error retrieving text: {str(e)}"

class MailInput(BaseModel):
    to_email: str = Field(description="The recipient email address")
    subject: str = Field(description="The subject of the email")
    body: str = Field(description="The body content of the email")

class MailTool(BaseTool):
    name: str = "send_mail"
    description: str = "Use this tool to send an email. You must provide the recipient email address, subject, and body."
    args_schema: Type[BaseModel] = MailInput

    def _run(self, to_email: str, subject: str, body: str) -> str:
        # Load environment variables from .env
        from dotenv import load_dotenv
        load_dotenv()
        
        smtp_server = os.environ.get("SMTP_SERVER")
        smtp_port = os.environ.get("SMTP_PORT", 587)
        smtp_user = os.environ.get("SMTP_USER")
        smtp_pass = os.environ.get("SMTP_PASS")
        
        if not all([smtp_server, smtp_user, smtp_pass]):
            # Mock sending if no credentials
            print(f"\n[Mock Email Sent]")
            print(f"To: {to_email}")
            print(f"Subject: {subject}")
            print(f"Body:\n{body}\n")
            return f"Email successfully sent to {to_email} (Mock)"
            
        try:
            msg = EmailMessage()
            msg.set_content(body)
            msg['Subject'] = subject
            msg['From'] = smtp_user
            msg['To'] = to_email

            with smtplib.SMTP(smtp_server, int(smtp_port)) as server:
                server.starttls()
                server.login(smtp_user, smtp_pass)
                server.send_message(msg)
            return f"Email successfully sent to {to_email}"
        except Exception as e:
            return f"Failed to send email: {str(e)}"
