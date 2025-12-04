"""
Session Manager for Chatbox App
Manages chat sessions with CSV-based logging for messages and chunks
Stores only chunk IDs in logs, fetches chunk text from database when needed
"""
import os
import csv
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
import json


class SessionManager:
    """Manages chat sessions with CSV-based logging"""
    
    def __init__(self, sessions_dir: str = "./sessions", db_manager=None):
        """
        Initialize SessionManager
        
        Args:
            sessions_dir: Directory to store session files
            db_manager: Optional DatabaseManager instance for fetching chunk text
        """
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.db_manager = db_manager
        
        # Create subdirectories
        (self.sessions_dir / "logs").mkdir(exist_ok=True)
        (self.sessions_dir / "chunks").mkdir(exist_ok=True)
    
    def _ensure_session_files(self, session_id: str) -> None:
        """
        Ensure all session files exist (metadata, log, chunks)
        Creates them if they don't exist
        
        Args:
            session_id: Session ID
        """
        # Ensure metadata file exists
        metadata_path = self.sessions_dir / f"{session_id}.json"
        if not metadata_path.exists():
            created_at = datetime.utcnow().isoformat()
            metadata = {
                "session_id": session_id,
                "title": f"Session {session_id[:8]}",
                "created_at": created_at,
                "updated_at": created_at,
                "message_count": 0
            }
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            print(f"📝 Created missing metadata file for session {session_id[:8]}...")
        
        # Ensure log file exists
        log_path = self.sessions_dir / "logs" / f"{session_id}.csv"
        if not log_path.exists():
            log_path.parent.mkdir(parents=True, exist_ok=True)
            with open(log_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "message_id", "role", "content", 
                    "model", "has_attachments", "attachment_count"
                ])
            print(f"📝 Created missing log file for session {session_id[:8]}...")
        
        # Ensure chunks file exists
        chunks_path = self.sessions_dir / "chunks" / f"{session_id}.csv"
        if not chunks_path.exists():
            chunks_path.parent.mkdir(parents=True, exist_ok=True)
            with open(chunks_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([
                    "timestamp", "message_id", "chunk_id",
                    "document_id", "chunk_index", "score", "distance"
                ])
            print(f"📝 Created missing chunks file for session {session_id[:8]}...")
    
    def create_session(self, title: Optional[str] = None) -> str:
        """
        Create a new session
        
        Args:
            title: Optional title for the session
            
        Returns:
            Session ID (UUID string)
        """
        session_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        # Create session metadata file
        metadata = {
            "session_id": session_id,
            "title": title or f"Session {session_id[:8]}",
            "created_at": created_at,
            "updated_at": created_at,
            "message_count": 0
        }
        
        metadata_path = self.sessions_dir / f"{session_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        # Initialize CSV log files
        log_path = self.sessions_dir / "logs" / f"{session_id}.csv"
        chunks_path = self.sessions_dir / "chunks" / f"{session_id}.csv"
        
        # Create messages log with headers
        with open(log_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "message_id", "role", "content", 
                "model", "has_attachments", "attachment_count"
            ])
        
        # Create chunks log with headers (only IDs, no text to keep file size small)
        with open(chunks_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                "timestamp", "message_id", "chunk_id",
                "document_id", "chunk_index", "score", "distance"
            ])
        
        print(f"✅ Created session: {session_id}")
        return session_id
    
    def save_message(
        self, 
        session_id: str, 
        message_id: str,
        role: str, 
        content: str,
        model: Optional[str] = None,
        attachments: Optional[List[Dict]] = None
    ) -> None:
        """
        Save a message to session log
        
        Args:
            session_id: Session ID
            message_id: Unique message ID
            role: Message role (user/assistant)
            content: Message content
            model: Model used (for assistant messages)
            attachments: List of attachments
        """
        # Ensure all session files exist (creates them if missing)
        self._ensure_session_files(session_id)
        
        log_path = self.sessions_dir / "logs" / f"{session_id}.csv"
        timestamp = datetime.utcnow().isoformat()
        has_attachments = "true" if attachments else "false"
        attachment_count = len(attachments) if attachments else 0
        
        # Append to the session log file (all messages for this session go to same file)
        with open(log_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                timestamp,
                message_id,
                role,
                content,
                model or "",
                has_attachments,
                attachment_count
            ])
        
        print(f"💾 Saved {role} message to session {session_id[:8]}... (log: {log_path.name})")
        
        # Update session metadata
        self._update_session_metadata(session_id)
    
    def save_chunks(
        self,
        session_id: str,
        message_id: str,
        chunks: List[Dict[str, Any]]
    ) -> None:
        """
        Save chunks to session log
        
        Args:
            session_id: Session ID
            message_id: Associated message ID
            chunks: List of chunk dictionaries
        """
        # Ensure all session files exist
        self._ensure_session_files(session_id)
        
        chunks_path = self.sessions_dir / "chunks" / f"{session_id}.csv"
        
        timestamp = datetime.utcnow().isoformat()
        
        # Append to the session chunks file (only IDs, no text to keep file size small)
        with open(chunks_path, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            for chunk in chunks:
                chunk_id = str(chunk.get('id', '')).strip()
                if not chunk_id:
                    print(f"⚠️  Skipping chunk with empty ID for message {message_id}")
                    continue
                writer.writerow([
                    timestamp,
                    message_id,
                    chunk_id,  # Only store chunk ID (as string)
                    chunk.get('document_id', ''),
                    chunk.get('chunk_index', ''),
                    chunk.get('score', ''),
                    chunk.get('distance', '')
                    # Note: chunk text is NOT stored, will be fetched from database when needed
                ])
        
        print(f"💾 Saved {len(chunks)} chunk IDs to session {session_id[:8]}... (chunks: {chunks_path.name})")
    
    def get_chunks_for_message(
        self,
        session_id: str,
        message_id: str
    ) -> List[Dict[str, Any]]:
        """
        Retrieve chunks for a specific message from session log
        Fetches chunk text from database using chunk IDs
        
        Args:
            session_id: Session ID
            message_id: Message ID
            
        Returns:
            List of chunk dictionaries with full text from database
        """
        # Ensure session files exist (in case they're missing)
        self._ensure_session_files(session_id)
        
        chunks_path = self.sessions_dir / "chunks" / f"{session_id}.csv"
        
        if not chunks_path.exists():
            return []
        
        # Read chunk IDs from CSV
        chunk_ids_data = []
        with open(chunks_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['message_id'] == message_id:
                    chunk_id = row['chunk_id']
                    if not chunk_id or chunk_id.strip() == '':
                        print(f"⚠️  Empty chunk_id found for message {message_id}, skipping")
                        continue
                    chunk_ids_data.append({
                        'id': str(chunk_id).strip(),  # Ensure string and trim whitespace
                        'document_id': row['document_id'] or '',
                        'chunk_index': int(row['chunk_index']) if row['chunk_index'] and row['chunk_index'].strip() else None,
                        'score': float(row['score']) if row['score'] and row['score'].strip() else None,
                        'distance': float(row['distance']) if row['distance'] and row['distance'].strip() else None
                    })
        
        # Fetch chunk text from database if db_manager is available
        if self.db_manager and chunk_ids_data:
            chunks = []
            db = self.db_manager.get_session()
            try:
                # Import Chunk model from database module (same way as rag_system does)
                from database import Chunk
                for chunk_data in chunk_ids_data:
                    chunk_id = chunk_data['id']
                    # Try to fetch chunk from database using chunk_id (as string)
                    chunk_record = db.query(Chunk).filter(Chunk.id == chunk_id).first()
                    
                    # If not found, try with document_id + chunk_index as fallback
                    if not chunk_record and chunk_data['document_id'] and chunk_data['chunk_index'] is not None:
                        chunk_record = db.query(Chunk).filter(
                            Chunk.document_id == chunk_data['document_id'],
                            Chunk.chunk_index == chunk_data['chunk_index']
                        ).first()
                        if chunk_record:
                            # Update chunk_id to match database record
                            chunk_id = chunk_record.id
                            print(f"📝 Found chunk by document_id+index, updating ID: {chunk_id[:8]}...")
                    
                    if chunk_record:
                        chunk = {
                            'id': str(chunk_id),  # Ensure string format for consistency
                            'text': chunk_record.text,  # Fetched from database
                            'document_id': chunk_data['document_id'] or chunk_record.document_id,
                            'chunk_index': chunk_data['chunk_index'] if chunk_data['chunk_index'] is not None else chunk_record.chunk_index,
                            'score': chunk_data['score'],
                            'distance': chunk_data['distance']
                        }
                        chunks.append(chunk)
                    else:
                        # Chunk not found in database, use data from CSV without text
                        print(f"⚠️  Chunk {chunk_id} not found in database (doc: {chunk_data['document_id']}, idx: {chunk_data['chunk_index']})")
                        chunk = {
                            'id': str(chunk_id),  # Ensure string format
                            'text': '[Chunk text not available]',  # Fallback
                            'document_id': chunk_data['document_id'],
                            'chunk_index': chunk_data['chunk_index'],
                            'score': chunk_data['score'],
                            'distance': chunk_data['distance']
                        }
                        chunks.append(chunk)
            finally:
                db.close()
            
            return chunks
        
        # If no db_manager, return chunks without text
        return [
            {
                'id': chunk_data['id'],
                'text': '[Chunk text requires database access]',
                'document_id': chunk_data['document_id'],
                'chunk_index': chunk_data['chunk_index'],
                'score': chunk_data['score'],
                'distance': chunk_data['distance']
            }
            for chunk_data in chunk_ids_data
        ]
    
    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all messages for a session
        
        Args:
            session_id: Session ID
            
        Returns:
            List of message dictionaries
        """
        # Ensure session files exist (in case they're missing)
        self._ensure_session_files(session_id)
        
        log_path = self.sessions_dir / "logs" / f"{session_id}.csv"
        
        if not log_path.exists():
            return []
        
        messages = []
        with open(log_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                message = {
                    'id': row['message_id'],
                    'role': row['role'],
                    'content': row['content'],
                    'model': row['model'] if row['model'] else None,
                    'timestamp': row['timestamp']
                }
                messages.append(message)
        
        return messages
    
    def get_session_metadata(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get session metadata
        
        Args:
            session_id: Session ID
            
        Returns:
            Session metadata dictionary or None if not found
        """
        metadata_path = self.sessions_dir / f"{session_id}.json"
        
        if not metadata_path.exists():
            return None
        
        with open(metadata_path, 'r') as f:
            return json.load(f)
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all sessions
        
        Returns:
            List of session metadata dictionaries
        """
        sessions = []
        
        for metadata_file in self.sessions_dir.glob("*.json"):
            if metadata_file.name == "sessions.json":  # Skip index file if exists
                continue
            
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                sessions.append(metadata)
        
        # Sort by updated_at (most recent first)
        sessions.sort(key=lambda x: x.get('updated_at', ''), reverse=True)
        return sessions
    
    def update_session_title(self, session_id: str, title: str) -> None:
        """
        Update session title
        
        Args:
            session_id: Session ID
            title: New title
        """
        metadata = self.get_session_metadata(session_id)
        if not metadata:
            raise ValueError(f"Session {session_id} does not exist")
        
        metadata['title'] = title
        metadata['updated_at'] = datetime.utcnow().isoformat()
        
        metadata_path = self.sessions_dir / f"{session_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def delete_session(self, session_id: str) -> None:
        """
        Delete a session and all its files
        
        Args:
            session_id: Session ID
        """
        # Delete metadata
        metadata_path = self.sessions_dir / f"{session_id}.json"
        if metadata_path.exists():
            metadata_path.unlink()
        
        # Delete log file
        log_path = self.sessions_dir / "logs" / f"{session_id}.csv"
        if log_path.exists():
            log_path.unlink()
        
        # Delete chunks file
        chunks_path = self.sessions_dir / "chunks" / f"{session_id}.csv"
        if chunks_path.exists():
            chunks_path.unlink()
        
        print(f"✅ Deleted session: {session_id}")
    
    def _update_session_metadata(self, session_id: str) -> None:
        """Update session metadata (message count, updated_at)"""
        # Ensure session files exist first
        self._ensure_session_files(session_id)
        
        metadata = self.get_session_metadata(session_id)
        if not metadata:
            # Create metadata if it doesn't exist (shouldn't happen after _ensure_session_files)
            created_at = datetime.utcnow().isoformat()
            metadata = {
                "session_id": session_id,
                "title": f"Session {session_id[:8]}",
                "created_at": created_at,
                "updated_at": created_at,
                "message_count": 0
            }
        
        # Count messages
        messages = self.get_messages(session_id)
        metadata['message_count'] = len(messages)
        metadata['updated_at'] = datetime.utcnow().isoformat()
        
        metadata_path = self.sessions_dir / f"{session_id}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

