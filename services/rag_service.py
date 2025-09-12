import chromadb
from chromadb.config import Settings as ChromaSettings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import Document
import openai
import os
import uuid
from typing import List, Dict, Any
import asyncio
from config.settings import get_settings

class RAGService:
    def __init__(self):
        self.settings = get_settings()
        self.client = None
        self.collection = None
        self.embeddings = None
        self.llm = None
        self.text_splitter = None
        
    async def initialize(self):
        """Initialize ChromaDB, embeddings, and LLM"""
        try:
            # Initialize ChromaDB
            self.client = chromadb.PersistentClient(
                path=self.settings.chroma_db_path,
                settings=ChromaSettings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            try:
                self.collection = self.client.get_collection(name=self.settings.chroma_collection_name)
            except:
                self.collection = self.client.create_collection(name=self.settings.chroma_collection_name)
            
            # Initialize OpenAI components
            openai.api_key = self.settings.openai_api_key
            
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=self.settings.openai_api_key,
                model=self.settings.embedding_model
            )
            
            self.llm = ChatOpenAI(
                openai_api_key=self.settings.openai_api_key,
                model_name=self.settings.openai_model,
                temperature=self.settings.temperature,
                max_tokens=self.settings.max_tokens
            )
            
            # Initialize text splitter
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.settings.chunk_size,
                chunk_overlap=self.settings.chunk_overlap,
                separators=["\n\n", "\n", ".", "!", "?", ",", " ", ""]
            )
            
            # Load HR data if collection is empty
            if self.collection.count() == 0:
                await self._load_hr_data()
                
        except Exception as e:
            print(f"Error initializing RAG service: {e}")
            raise
    
    async def _load_hr_data(self):
        """Load HR data from hr_data.txt into ChromaDB"""
        try:
            hr_data_path = "hr_data.txt"
            if os.path.exists(hr_data_path):
                with open(hr_data_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                
                await self.add_document(content, "hr_data.txt")
                print("HR data loaded successfully")
            else:
                print("HR data file not found")
        except Exception as e:
            print(f"Error loading HR data: {e}")
    
    async def add_document(self, content: str, filename: str) -> str:
        """Add a document to the vector database"""
        try:
            # Split text into chunks
            documents = self.text_splitter.create_documents([content])
            
            # Generate embeddings and add to ChromaDB
            texts = [doc.page_content for doc in documents]
            embeddings = await asyncio.to_thread(self.embeddings.embed_documents, texts)
            
            # Create unique IDs for each chunk
            ids = [f"{filename}_{i}_{uuid.uuid4()}" for i in range(len(texts))]
            
            # Prepare metadata
            metadatas = [{
                "source": filename,
                "chunk_id": i,
                "content_length": len(text)
            } for i, text in enumerate(texts)]
            
            # Add to ChromaDB
            self.collection.add(
                embeddings=embeddings,
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            
            return f"Added {len(texts)} chunks from {filename}"
            
        except Exception as e:
            print(f"Error adding document: {e}")
            raise
    
    async def query(self, question: str, n_results: int = 5) -> Dict[str, Any]:
        """Query the RAG system"""
        try:
            # Check if it's a casual greeting or friendly question
            casual_greetings = [
                "how are you", "كيف حالك", "كيفك", "شلونك", "ازيك", 
                "hello", "hi", "مرحبا", "أهلا", "السلام عليكم",
                "good morning", "good evening", "صباح الخير", "مساء الخير"
            ]
            
            question_lower = question.lower().strip()
            is_casual = any(greeting in question_lower for greeting in casual_greetings)
            
            if is_casual:
                # Handle casual greetings directly with a friendly response
                friendly_responses = {
                    "ar": "مرحباً! أنا بخير، شكراً لسؤالك. أنا مساعدك الذكي في AgentX AI وأنا هنا لمساعدتك في أي استفسارات تتعلق بالشركة أو سياسات الموارد البشرية. كيف يمكنني مساعدتك اليوم؟",
                    "en": "Hello! I'm doing great, thank you for asking! I'm your AI assistant at AgentX AI, and I'm here to help you with any questions about the company or HR policies. How can I assist you today?"
                }
                
                # Detect language and respond accordingly
                if any(ar_word in question_lower for ar_word in ["كيف", "شلون", "ازي", "مرحبا", "أهلا", "السلام"]):
                    response_text = friendly_responses["ar"]
                else:
                    response_text = friendly_responses["en"]
                
                return {
                    "answer": response_text,
                    "sources": []
                }
            
            # Generate embedding for the question
            question_embedding = await asyncio.to_thread(
                self.embeddings.embed_query, question
            )
            
            # Search for relevant documents
            results = self.collection.query(
                query_embeddings=[question_embedding],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            if not results['documents'][0]:
                return {
                    "answer": "عذراً، لم أتمكن من العثور على معلومات ذات صلة بسؤالك في قاعدة البيانات. هل يمكنك إعادة صياغة السؤال أو تقديم المزيد من التفاصيل؟",
                    "sources": []
                }
            
            # Prepare context from retrieved documents
            context = "\n\n".join(results['documents'][0])
            
            # Create improved prompt for GPT-3.5-turbo
            prompt = f"""
أنت مساعد ذكي ودود متخصص في الإجابة على الأسئلة المتعلقة بشركة AgentX AI وسياسات الموارد البشرية.

تعليمات مهمة:
1. كن ودوداً ومفيداً في جميع إجاباتك
2. إذا سُئلت أسئلة عامة أو ودية، جاوب بشكل طبيعي وودود
3. ركز على تقديم معلومات دقيقة ومفيدة
4. إذا لم تكن المعلومات كافية، اقترح طرق للحصول على مزيد من المساعدة

المعلومات المتاحة:
{context}

السؤال: {question}

الإجابة: قدم إجابة شاملة ودقيقة وودية باللغة العربية بناءً على المعلومات المتاحة أعلاه.
"""
            
            # Get response from GPT-3.5-turbo
            response = await asyncio.to_thread(
                self.llm.invoke, prompt
            )
            
            # Prepare sources information
            sources = []
            for i, metadata in enumerate(results['metadatas'][0]):
                sources.append({
                    "source": metadata.get('source', 'Unknown'),
                    "chunk_id": metadata.get('chunk_id', i),
                    "relevance_score": 1 - results['distances'][0][i]  # Convert distance to similarity
                })
            
            return {
                "answer": response.content,
                "sources": sources
            }
            
        except Exception as e:
            print(f"Error querying RAG system: {e}")
            return {
                "answer": f"حدث خطأ أثناء معالجة السؤال: {str(e)}",
                "sources": []
            }
    
    async def list_documents(self) -> List[Dict[str, Any]]:
        """List all documents in the collection"""
        try:
            # Get all documents
            results = self.collection.get(include=["metadatas"])
            
            # Group by source
            documents = {}
            for metadata in results['metadatas']:
                source = metadata.get('source', 'Unknown')
                if source not in documents:
                    documents[source] = {
                        "name": source,
                        "chunks": 0
                    }
                documents[source]["chunks"] += 1
            
            return list(documents.values())
            
        except Exception as e:
            print(f"Error listing documents: {e}")
            return []