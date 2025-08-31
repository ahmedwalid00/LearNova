"""
PDF processing and text chunking utilities for lesson content.
"""

import io
from typing import List, Dict, Any, Tuple
from uuid import UUID
import PyPDF2
from langchain.text_splitter import RecursiveCharacterTextSplitter, TokenTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain.schema import Document


class PDFProcessor:
    """Handles PDF and TXT content extraction and processing."""
    
    @classmethod
    async def extract_text_from_file(cls, file_content: bytes, file_extension: str) -> str:
        """
        Extract text content from PDF or TXT file bytes.
        
        Args:
            file_content: File content as bytes
            file_extension: File extension (.pdf or .txt)
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If file processing fails
        """
        try:
            if file_extension.lower() == '.pdf':
                return await cls.extract_text_from_pdf(file_content)
            elif file_extension.lower() == '.txt':
                return await cls.extract_text_from_txt(file_content)
            else:
                raise ValueError(f"Unsupported file type: {file_extension}")
        except Exception as e:
            raise ValueError(f"Failed to extract text from {file_extension} file: {str(e)}")
    
    @classmethod
    async def extract_text_from_txt(cls, txt_content: bytes) -> str:
        """
        Extract text content from TXT file bytes.
        
        Args:
            txt_content: TXT file content as bytes
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If TXT processing fails
        """
        try:
            text_content = txt_content.decode('utf-8')
            
            if not text_content.strip():
                raise ValueError("No readable text found in TXT file")
            
            return text_content.strip()
            
        except UnicodeDecodeError as e:
            raise ValueError(f"Failed to decode TXT file: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to extract text from TXT: {str(e)}")
    
    @classmethod
    async def extract_text_from_pdf(cls, pdf_content: bytes) -> str:
        """
        Extract text content from PDF bytes.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Extracted text content
            
        Raises:
            ValueError: If PDF processing fails
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            text_content = []
            
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text.strip():  # Only add non-empty pages
                        text_content.append(f"--- Page {page_num + 1} ---\\n{page_text}")
                except Exception as e:
                    # Skip problematic pages but continue processing
                    text_content.append(f"--- Page {page_num + 1} (Error reading page) ---\\n")
                    continue
            
            if not text_content:
                raise ValueError("No readable text found in PDF")
            
            return "\\n\\n".join(text_content)
            
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")
    
    @classmethod
    def get_pdf_metadata(cls, pdf_content: bytes) -> Dict[str, Any]:
        """
        Extract metadata from PDF.
        
        Args:
            pdf_content: PDF file content as bytes
            
        Returns:
            Dictionary containing PDF metadata
        """
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(pdf_content))
            metadata = {
                'page_count': len(pdf_reader.pages),
                'size_bytes': len(pdf_content),
                'size_mb': round(len(pdf_content) / (1024 * 1024), 2)
            }
            
            # Try to get PDF metadata
            if pdf_reader.metadata:
                metadata.update({
                    'title': pdf_reader.metadata.get('/Title', ''),
                    'author': pdf_reader.metadata.get('/Author', ''),
                    'subject': pdf_reader.metadata.get('/Subject', ''),
                    'creator': pdf_reader.metadata.get('/Creator', ''),
                    'producer': pdf_reader.metadata.get('/Producer', ''),
                    'creation_date': str(pdf_reader.metadata.get('/CreationDate', '')),
                    'modification_date': str(pdf_reader.metadata.get('/ModDate', ''))
                })
            
            return metadata
            
        except Exception as e:
            return {
                'page_count': 0,
                'size_bytes': len(pdf_content),
                'size_mb': round(len(pdf_content) / (1024 * 1024), 2),
                'error': str(e)
            }


class TextChunker:
    """Handles text chunking strategies for lesson content."""
    
    # Default chunking parameters
    DEFAULT_CHUNK_SIZE = 700
    DEFAULT_CHUNK_OVERLAP = 150
    MAX_CHUNK_SIZE = 1500
    MIN_CHUNK_SIZE = 100
    
    @classmethod
    def create_recursive_splitter(
        cls, 
        chunk_size: int = None, 
        chunk_overlap: int = None
    ) -> RecursiveCharacterTextSplitter:
        """
        Create a recursive character text splitter.
        
        Args:
            chunk_size: Target size for each chunk
            chunk_overlap: Overlap between chunks
            
        Returns:
            Configured text splitter
        """
        chunk_size = chunk_size or cls.DEFAULT_CHUNK_SIZE
        chunk_overlap = chunk_overlap or cls.DEFAULT_CHUNK_OVERLAP
        
        # Ensure chunk overlap is not too large
        chunk_overlap = min(chunk_overlap, chunk_size // 4)
        
        return RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\\n\\n", "\\n", ". ", "! ", "? ", ", ", " ", ""]
        )
    
    @classmethod
    def create_token_splitter(
        cls, 
        chunk_size: int = None, 
        chunk_overlap: int = None
    ) -> TokenTextSplitter:
        """
        Create a token-based text splitter.
        
        Args:
            chunk_size: Target number of tokens per chunk
            chunk_overlap: Overlap between chunks in tokens
            
        Returns:
            Configured token splitter
        """
        chunk_size = chunk_size or (cls.DEFAULT_CHUNK_SIZE // 4)  # Roughly 4 chars per token
        chunk_overlap = chunk_overlap or (cls.DEFAULT_CHUNK_OVERLAP // 4)
        
        return TokenTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
    
    @classmethod
    async def chunk_text(
        cls, 
        text: str, 
        strategy: str = "recursive",
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> List[str]:
        """
        Chunk text using specified strategy.
        
        Args:
            text: Text content to chunk
            strategy: Chunking strategy ("recursive" or "token")
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            
        Returns:
            List of text chunks
            
        Raises:
            ValueError: If chunking fails or invalid strategy
        """
        if not text or not text.strip():
            return []
        
        try:
            if strategy == "recursive":
                splitter = cls.create_recursive_splitter(chunk_size, chunk_overlap)
            elif strategy == "token":
                splitter = cls.create_token_splitter(chunk_size, chunk_overlap)
            else:
                raise ValueError(f"Unknown chunking strategy: {strategy}")
            
            # Create a document and split it
            doc = Document(page_content=text, metadata={})
            chunks = splitter.split_documents([doc])
            
            # Extract text from documents and filter out empty chunks
            chunk_texts = [chunk.page_content for chunk in chunks if chunk.page_content.strip()]
            
            # Filter chunks by size
            filtered_chunks = []
            for chunk_text in chunk_texts:
                if len(chunk_text.strip()) >= cls.MIN_CHUNK_SIZE:
                    # Truncate if too long
                    if len(chunk_text) > cls.MAX_CHUNK_SIZE:
                        chunk_text = chunk_text[:cls.MAX_CHUNK_SIZE] + "..."
                    filtered_chunks.append(chunk_text.strip())
            
            return filtered_chunks
            
        except Exception as e:
            raise ValueError(f"Text chunking failed: {str(e)}")
    
    @classmethod
    def create_chunk_metadata(
        cls, 
        chunk_index: int, 
        total_chunks: int, 
        lesson_metadata: Dict[str, Any],
        chunk_text: str
    ) -> Dict[str, Any]:
        """
        Create metadata for a text chunk.
        
        Args:
            chunk_index: Index of the chunk (0-based)
            total_chunks: Total number of chunks
            lesson_metadata: Metadata from the lesson/PDF
            chunk_text: The actual chunk text
            
        Returns:
            Chunk metadata dictionary
        """
        return {
            'chunk_index': chunk_index,
            'chunk_number': chunk_index + 1,  # 1-based for display
            'total_chunks': total_chunks,
            'char_count': len(chunk_text),
            'word_count': len(chunk_text.split()),
            'lesson_metadata': lesson_metadata,
            'chunk_type': 'text',
            'processing_strategy': 'recursive_split'
        }


class LessonProcessor:
    """Orchestrates the complete lesson processing workflow."""
    
    @classmethod
    async def process_lesson_file(
        cls,
        file_content: bytes,
        file_extension: str,
        lesson_id: UUID,
        chunking_strategy: str = "recursive",
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Complete processing of a lesson file (PDF or TXT).
        
        Args:
            file_content: File content as bytes
            file_extension: File extension (.pdf or .txt)
            lesson_id: UUID of the lesson
            chunking_strategy: Text chunking strategy
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            
        Returns:
            Tuple of (full_text, chunk_data_list, file_metadata)
            
        Raises:
            ValueError: If processing fails
        """
        try:
            # Extract text from file
            full_text = await PDFProcessor.extract_text_from_file(file_content, file_extension)
            
            # Get file metadata
            if file_extension.lower() == '.pdf':
                file_metadata = PDFProcessor.get_pdf_metadata(file_content)
            else:  # TXT file
                file_metadata = {
                    'file_type': 'txt',
                    'size_bytes': len(file_content),
                    'size_mb': round(len(file_content) / (1024 * 1024), 2),
                    'char_count': len(full_text),
                    'word_count': len(full_text.split()),
                    'line_count': len(full_text.split('\n'))
                }
            
            file_metadata['lesson_id'] = str(lesson_id)
            file_metadata['file_extension'] = file_extension
            
            # Chunk the text
            chunks = await TextChunker.chunk_text(
                text=full_text,
                strategy=chunking_strategy,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap
            )
            
            if not chunks:
                raise ValueError(f"No valid chunks created from {file_extension} content")
            
            # Create chunk data with metadata
            chunk_data_list = []
            for i, chunk_text in enumerate(chunks):
                chunk_metadata = TextChunker.create_chunk_metadata(
                    chunk_index=i,
                    total_chunks=len(chunks),
                    lesson_metadata=file_metadata,
                    chunk_text=chunk_text
                )
                
                chunk_data_list.append({
                    'chunk_number': i + 1,
                    'chunk_text': chunk_text,
                    'chunk_metadata': chunk_metadata
                })
            
            return full_text, chunk_data_list, file_metadata
            
        except Exception as e:
            raise ValueError(f"Lesson processing failed: {str(e)}")
    
    @classmethod
    async def process_lesson_pdf(
        cls,
        pdf_content: bytes,
        lesson_id: UUID,
        chunking_strategy: str = "recursive",
        chunk_size: int = None,
        chunk_overlap: int = None
    ) -> Tuple[str, List[Dict[str, Any]], Dict[str, Any]]:
        """
        Backward compatibility method for PDF processing.
        
        Args:
            pdf_content: PDF file content as bytes
            lesson_id: UUID of the lesson
            chunking_strategy: Text chunking strategy
            chunk_size: Target chunk size
            chunk_overlap: Overlap between chunks
            
        Returns:
            Tuple of (full_text, chunk_data_list, pdf_metadata)
        """
        return await cls.process_lesson_file(
            file_content=pdf_content,
            file_extension='.pdf',
            lesson_id=lesson_id,
            chunking_strategy=chunking_strategy,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
