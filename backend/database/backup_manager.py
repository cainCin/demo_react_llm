"""
Database Backup and Restore Manager
Handles automatic backup and restore of PostgreSQL and Milvus Lite databases
"""
import os
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Optional, Tuple, Dict, Any
import json

from config import (
    POSTGRES_HOST, POSTGRES_PORT, POSTGRES_DB, POSTGRES_USER, POSTGRES_PASSWORD,
    MILVUS_LITE_PATH
)


class BackupManager:
    """
    Manages database backups and restores for PostgreSQL and Milvus Lite
    Uses Docker exec for PostgreSQL backups when container is available
    """
    
    def __init__(self, backup_dir: str = "./backups", postgres_container: str = "chatbox-postgres"):
        """
        Initialize BackupManager
        
        Args:
            backup_dir: Directory to store backup files
            postgres_container: Docker container name for PostgreSQL (default: chatbox-postgres)
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.postgres_container = postgres_container
        
        # Ensure backup directory exists
        (self.backup_dir / "postgres").mkdir(exist_ok=True)
        (self.backup_dir / "milvus").mkdir(exist_ok=True)
        (self.backup_dir / "metadata").mkdir(exist_ok=True)
    
    def _check_docker_container(self) -> bool:
        """
        Check if PostgreSQL Docker container exists and is running
        
        Returns:
            True if container exists and is running, False otherwise
        """
        try:
            result = subprocess.run(
                ['docker', 'ps', '--filter', f'name={self.postgres_container}', '--format', '{{.Names}}'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0 and self.postgres_container in result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False
    
    def _cleanup_old_backups(self, backup_type: str) -> None:
        """
        Delete old backups, keeping only the latest one
        
        Args:
            backup_type: 'postgres' or 'milvus'
        """
        backup_type_dir = self.backup_dir / backup_type
        if not backup_type_dir.exists():
            return
        
        # Get all backup files
        if backup_type == 'postgres':
            backup_files = list(backup_type_dir.glob("*.sql"))
        else:  # milvus
            backup_files = list(backup_type_dir.glob("*.db"))
        
        if len(backup_files) <= 1:
            return  # Keep the only backup or no backups
        
        # Sort by modification time (newest first)
        backup_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        
        # Delete all except the latest
        for old_backup in backup_files[1:]:
            try:
                old_backup.unlink()
                # Also delete corresponding metadata if exists
                metadata_file = self.backup_dir / "metadata" / f"{old_backup.stem}.json"
                if metadata_file.exists():
                    metadata_file.unlink()
            except Exception as e:
                print(f"⚠️  Warning: Could not delete old backup {old_backup.name}: {e}")
    
    def backup_postgres(self, backup_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Backup PostgreSQL database using pg_dump via Docker exec
        Deletes old backups, keeping only the latest one
        
        Args:
            backup_name: Optional custom backup name (default: timestamp-based)
            
        Returns:
            Tuple of (success: bool, backup_path: str)
        """
        # Clean up old backups before creating new one
        self._cleanup_old_backups('postgres')
        
        if not backup_name:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"postgres_backup_{timestamp}.sql"
        
        backup_path = self.backup_dir / "postgres" / backup_name
        
        try:
            # Check if Docker container is available
            use_docker = self._check_docker_container()
            
            if use_docker:
                # Use Docker exec to run pg_dump inside container
                # This ensures version compatibility
                container_backup_path = f"/tmp/{backup_name}"
                
                cmd = [
                    'docker', 'exec',
                    self.postgres_container,
                    'pg_dump',
                    '-U', POSTGRES_USER,
                    '-d', POSTGRES_DB,
                    '-F', 'c',  # Custom format (compressed)
                    '-f', container_backup_path
                ]
                
                # Set PGPASSWORD via environment in docker exec
                env = os.environ.copy()
                env['PGPASSWORD'] = POSTGRES_PASSWORD
                
                result = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode == 0:
                    # Copy backup file from container to host
                    copy_cmd = [
                        'docker', 'cp',
                        f'{self.postgres_container}:{container_backup_path}',
                        str(backup_path)
                    ]
                    
                    copy_result = subprocess.run(
                        copy_cmd,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if copy_result.returncode != 0:
                        error_msg = f"Failed to copy backup from container: {copy_result.stderr}"
                        print(f"❌ {error_msg}")
                        return False, error_msg
                    
                    # Clean up backup file in container
                    subprocess.run(
                        ['docker', 'exec', self.postgres_container, 'rm', container_backup_path],
                        capture_output=True,
                        timeout=10
                    )
                else:
                    error_msg = result.stderr or result.stdout
                    print(f"❌ PostgreSQL backup failed: {error_msg}")
                    return False, error_msg
            else:
                # Fallback to local pg_dump (if Docker not available)
                env = os.environ.copy()
                env['PGPASSWORD'] = POSTGRES_PASSWORD
                
                cmd = [
                    'pg_dump',
                    '-h', POSTGRES_HOST,
                    '-p', str(POSTGRES_PORT),
                    '-U', POSTGRES_USER,
                    '-d', POSTGRES_DB,
                    '-F', 'c',  # Custom format (compressed)
                    '-f', str(backup_path)
                ]
                
                result = subprocess.run(
                    cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr or result.stdout
                    print(f"❌ PostgreSQL backup failed: {error_msg}")
                    return False, error_msg
            
            # Save metadata
            metadata = {
                "backup_type": "postgres",
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "created_at": datetime.utcnow().isoformat(),
                "database": POSTGRES_DB,
                "host": POSTGRES_HOST,
                "port": POSTGRES_PORT,
                "method": "docker" if use_docker else "local"
            }
            self._save_metadata(backup_name, metadata)
            
            method_str = "Docker" if use_docker else "local"
            print(f"✅ PostgreSQL backup created via {method_str}: {backup_name}")
            return True, str(backup_path)
                
        except subprocess.TimeoutExpired:
            error_msg = "Backup operation timed out (exceeded 5 minutes)"
            print(f"❌ {error_msg}")
            return False, error_msg
        except FileNotFoundError as e:
            if 'docker' in str(e).lower():
                error_msg = "Docker not found. Please install Docker or use local pg_dump."
            else:
                error_msg = "pg_dump not found. Please install PostgreSQL client tools.\n"
                error_msg += "   Linux: sudo apt-get install postgresql-client\n"
                error_msg += "   macOS: brew install postgresql\n"
                error_msg += "   Windows: Install PostgreSQL (client tools included)"
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"PostgreSQL backup error: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def restore_postgres(self, backup_name: str, drop_existing: bool = False) -> Tuple[bool, str]:
        """
        Restore PostgreSQL database from backup using Docker exec
        
        Args:
            backup_name: Name of backup file to restore
            drop_existing: If True, drop existing database before restore
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        backup_path = self.backup_dir / "postgres" / backup_name
        
        if not backup_path.exists():
            error_msg = f"Backup file not found: {backup_path}"
            print(f"❌ {error_msg}")
            return False, error_msg
        
        try:
            # Check if Docker container is available
            use_docker = self._check_docker_container()
            
            env = os.environ.copy()
            env['PGPASSWORD'] = POSTGRES_PASSWORD
            
            # If drop_existing, we need to drop and recreate the database
            if drop_existing:
                if use_docker:
                    # Drop and create database using Docker exec
                    drop_cmd = [
                        'docker', 'exec',
                        self.postgres_container,
                        'psql',
                        '-U', POSTGRES_USER,
                        '-d', 'postgres',
                        '-c', f'DROP DATABASE IF EXISTS {POSTGRES_DB};'
                    ]
                    
                    drop_result = subprocess.run(
                        drop_cmd,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if drop_result.returncode != 0:
                        print(f"⚠️  Warning: Could not drop database: {drop_result.stderr}")
                    
                    create_cmd = [
                        'docker', 'exec',
                        self.postgres_container,
                        'psql',
                        '-U', POSTGRES_USER,
                        '-d', 'postgres',
                        '-c', f'CREATE DATABASE {POSTGRES_DB};'
                    ]
                    
                    create_result = subprocess.run(
                        create_cmd,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if create_result.returncode != 0:
                        error_msg = f"Could not create database: {create_result.stderr}"
                        print(f"❌ {error_msg}")
                        return False, error_msg
                else:
                    # Fallback to local psql
                    drop_cmd = [
                        'psql',
                        '-h', POSTGRES_HOST,
                        '-p', str(POSTGRES_PORT),
                        '-U', POSTGRES_USER,
                        '-d', 'postgres',
                        '-c', f'DROP DATABASE IF EXISTS {POSTGRES_DB};'
                    ]
                    
                    drop_result = subprocess.run(
                        drop_cmd,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if drop_result.returncode != 0:
                        print(f"⚠️  Warning: Could not drop database: {drop_result.stderr}")
                    
                    create_cmd = [
                        'psql',
                        '-h', POSTGRES_HOST,
                        '-p', str(POSTGRES_PORT),
                        '-U', POSTGRES_USER,
                        '-d', 'postgres',
                        '-c', f'CREATE DATABASE {POSTGRES_DB};'
                    ]
                    
                    create_result = subprocess.run(
                        create_cmd,
                        env=env,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    if create_result.returncode != 0:
                        error_msg = f"Could not create database: {create_result.stderr}"
                        print(f"❌ {error_msg}")
                        return False, error_msg
            
            # Restore from backup
            if use_docker:
                # Copy backup file to container
                container_backup_path = f"/tmp/{backup_name}"
                copy_cmd = [
                    'docker', 'cp',
                    str(backup_path),
                    f'{self.postgres_container}:{container_backup_path}'
                ]
                
                copy_result = subprocess.run(
                    copy_cmd,
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if copy_result.returncode != 0:
                    error_msg = f"Failed to copy backup to container: {copy_result.stderr}"
                    print(f"❌ {error_msg}")
                    return False, error_msg
                
                # Restore using Docker exec
                restore_cmd = [
                    'docker', 'exec',
                    self.postgres_container,
                    'pg_restore',
                    '-U', POSTGRES_USER,
                    '-d', POSTGRES_DB,
                    '-c',  # Clean (drop) existing objects
                    container_backup_path
                ]
                
                result = subprocess.run(
                    restore_cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                # Clean up backup file in container
                subprocess.run(
                    ['docker', 'exec', self.postgres_container, 'rm', container_backup_path],
                    capture_output=True,
                    timeout=10
                )
            else:
                # Fallback to local pg_restore
                restore_cmd = [
                    'pg_restore',
                    '-h', POSTGRES_HOST,
                    '-p', str(POSTGRES_PORT),
                    '-U', POSTGRES_USER,
                    '-d', POSTGRES_DB,
                    '-c',  # Clean (drop) existing objects
                    str(backup_path)
                ]
                
                result = subprocess.run(
                    restore_cmd,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
            
            if result.returncode == 0:
                method_str = "Docker" if use_docker else "local"
                print(f"✅ PostgreSQL restore completed via {method_str}: {backup_name}")
                return True, f"Successfully restored from {backup_name}"
            else:
                error_msg = result.stderr or result.stdout
                print(f"❌ PostgreSQL restore failed: {error_msg}")
                return False, error_msg
                
        except subprocess.TimeoutExpired:
            error_msg = "Restore operation timed out (exceeded 10 minutes)"
            print(f"❌ {error_msg}")
            return False, error_msg
        except FileNotFoundError as e:
            if 'docker' in str(e).lower():
                error_msg = "Docker not found. Please install Docker or use local pg_restore."
            else:
                error_msg = "pg_restore not found. Please install PostgreSQL client tools."
            print(f"❌ {error_msg}")
            return False, error_msg
        except Exception as e:
            error_msg = f"PostgreSQL restore error: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def backup_milvus(self, backup_name: Optional[str] = None) -> Tuple[bool, str]:
        """
        Backup Milvus Lite database by copying the .db file
        Deletes old backups, keeping only the latest one
        
        Args:
            backup_name: Optional custom backup name (default: timestamp-based)
            
        Returns:
            Tuple of (success: bool, backup_path: str)
        """
        # Clean up old backups before creating new one
        self._cleanup_old_backups('milvus')
        
        if not backup_name:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            backup_name = f"milvus_backup_{timestamp}.db"
        
        backup_path = self.backup_dir / "milvus" / backup_name
        
        try:
            # Convert relative path to absolute
            milvus_path = Path(MILVUS_LITE_PATH)
            if not milvus_path.is_absolute():
                # Assume relative to backend directory
                backend_dir = Path(__file__).parent.parent
                milvus_path = backend_dir / MILVUS_LITE_PATH
            
            if not milvus_path.exists():
                # Milvus file doesn't exist yet (first run), create empty backup metadata
                print(f"ℹ️  Milvus database file doesn't exist yet: {milvus_path}")
                metadata = {
                    "backup_type": "milvus",
                    "backup_name": backup_name,
                    "backup_path": str(backup_path),
                    "created_at": datetime.utcnow().isoformat(),
                    "source_path": str(milvus_path),
                    "note": "Source file did not exist at backup time"
                }
                self._save_metadata(backup_name, metadata)
                return True, str(backup_path)
            
            # Copy the database file
            shutil.copy2(milvus_path, backup_path)
            
            # Save metadata
            metadata = {
                "backup_type": "milvus",
                "backup_name": backup_name,
                "backup_path": str(backup_path),
                "created_at": datetime.utcnow().isoformat(),
                "source_path": str(milvus_path),
                "file_size": milvus_path.stat().st_size
            }
            self._save_metadata(backup_name, metadata)
            
            print(f"✅ Milvus backup created: {backup_name}")
            return True, str(backup_path)
            
        except Exception as e:
            error_msg = f"Milvus backup error: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def restore_milvus(self, backup_name: str) -> Tuple[bool, str]:
        """
        Restore Milvus Lite database from backup
        
        Args:
            backup_name: Name of backup file to restore
            
        Returns:
            Tuple of (success: bool, message: str)
        """
        backup_path = self.backup_dir / "milvus" / backup_name
        
        if not backup_path.exists():
            error_msg = f"Backup file not found: {backup_path}"
            print(f"❌ {error_msg}")
            return False, error_msg
        
        try:
            # Convert relative path to absolute
            milvus_path = Path(MILVUS_LITE_PATH)
            if not milvus_path.is_absolute():
                backend_dir = Path(__file__).parent.parent
                milvus_path = backend_dir / MILVUS_LITE_PATH
            
            # Ensure parent directory exists
            milvus_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy backup file to Milvus location
            shutil.copy2(backup_path, milvus_path)
            
            print(f"✅ Milvus restore completed: {backup_name}")
            return True, f"Successfully restored from {backup_name}"
            
        except Exception as e:
            error_msg = f"Milvus restore error: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def backup_all(self, backup_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Backup both PostgreSQL and Milvus databases
        
        Args:
            backup_name: Optional base name for backups (timestamp will be appended)
            
        Returns:
            Dictionary with backup results
        """
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        base_name = backup_name or "full_backup"
        
        results = {
            "timestamp": timestamp,
            "postgres": {},
            "milvus": {},
            "success": False
        }
        
        # Backup PostgreSQL
        pg_success, pg_path = self.backup_postgres(f"{base_name}_postgres_{timestamp}.sql")
        results["postgres"] = {
            "success": pg_success,
            "path": pg_path if pg_success else None,
            "error": None if pg_success else pg_path
        }
        
        # Backup Milvus
        milvus_success, milvus_path = self.backup_milvus(f"{base_name}_milvus_{timestamp}.db")
        results["milvus"] = {
            "success": milvus_success,
            "path": milvus_path if milvus_success else None,
            "error": None if milvus_success else milvus_path
        }
        
        results["success"] = pg_success and milvus_success
        
        # Save combined metadata
        combined_metadata = {
            "backup_type": "full",
            "base_name": base_name,
            "timestamp": timestamp,
            "created_at": datetime.utcnow().isoformat(),
            "postgres": results["postgres"],
            "milvus": results["milvus"],
            "success": results["success"]
        }
        self._save_metadata(f"{base_name}_{timestamp}", combined_metadata)
        
        if results["success"]:
            print(f"✅ Full backup completed: {base_name}_{timestamp}")
        else:
            print(f"⚠️  Full backup completed with errors: {base_name}_{timestamp}")
        
        return results
    
    def restore_all(self, backup_timestamp: str, drop_existing: bool = False) -> Dict[str, Any]:
        """
        Restore both PostgreSQL and Milvus databases from a full backup
        
        Args:
            backup_timestamp: Timestamp of the backup to restore
            drop_existing: If True, drop existing PostgreSQL database before restore
            
        Returns:
            Dictionary with restore results
        """
        results = {
            "postgres": {},
            "milvus": {},
            "success": False
        }
        
        # Find backup files with this timestamp
        pg_backups = list((self.backup_dir / "postgres").glob(f"*{backup_timestamp}*.sql"))
        milvus_backups = list((self.backup_dir / "milvus").glob(f"*{backup_timestamp}*.db"))
        
        if not pg_backups:
            results["postgres"] = {
                "success": False,
                "error": f"No PostgreSQL backup found with timestamp: {backup_timestamp}"
            }
        else:
            pg_success, pg_msg = self.restore_postgres(pg_backups[0].name, drop_existing)
            results["postgres"] = {
                "success": pg_success,
                "message": pg_msg
            }
        
        if not milvus_backups:
            results["milvus"] = {
                "success": False,
                "error": f"No Milvus backup found with timestamp: {backup_timestamp}"
            }
        else:
            milvus_success, milvus_msg = self.restore_milvus(milvus_backups[0].name)
            results["milvus"] = {
                "success": milvus_success,
                "message": milvus_msg
            }
        
        results["success"] = results["postgres"].get("success", False) and results["milvus"].get("success", False)
        
        return results
    
    def list_backups(self) -> Dict[str, Any]:
        """
        List all available backups
        
        Returns:
            Dictionary with lists of PostgreSQL and Milvus backups
        """
        pg_backups = []
        milvus_backups = []
        
        # List PostgreSQL backups
        for backup_file in (self.backup_dir / "postgres").glob("*.sql"):
            pg_backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": backup_file.stat().st_size,
                "created": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
            })
        
        # List Milvus backups
        for backup_file in (self.backup_dir / "milvus").glob("*.db"):
            milvus_backups.append({
                "name": backup_file.name,
                "path": str(backup_file),
                "size": backup_file.stat().st_size,
                "created": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat()
            })
        
        # Sort by creation time (newest first)
        pg_backups.sort(key=lambda x: x["created"], reverse=True)
        milvus_backups.sort(key=lambda x: x["created"], reverse=True)
        
        return {
            "postgres": pg_backups,
            "milvus": milvus_backups
        }
    
    def _save_metadata(self, backup_name: str, metadata: Dict[str, Any]) -> None:
        """Save backup metadata to JSON file"""
        metadata_path = self.backup_dir / "metadata" / f"{backup_name}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    def get_latest_backup(self) -> Optional[Dict[str, Any]]:
        """
        Get the most recent full backup
        
        Returns:
            Dictionary with latest backup info or None
        """
        backups = self.list_backups()
        
        if not backups["postgres"] or not backups["milvus"]:
            return None
        
        # Find matching timestamps
        pg_timestamps = {}
        milvus_timestamps = {}
        
        for pg in backups["postgres"]:
            # Extract timestamp from filename (format: *_YYYYMMDD_HHMMSS.sql)
            parts = pg["name"].split("_")
            if len(parts) >= 3:
                timestamp = "_".join(parts[-2:]).replace(".sql", "")
                pg_timestamps[timestamp] = pg
        
        for milvus in backups["milvus"]:
            parts = milvus["name"].split("_")
            if len(parts) >= 3:
                timestamp = "_".join(parts[-2:]).replace(".db", "")
                milvus_timestamps[timestamp] = milvus
        
        # Find common timestamps
        common_timestamps = set(pg_timestamps.keys()) & set(milvus_timestamps.keys())
        
        if not common_timestamps:
            return None
        
        # Get the most recent
        latest_timestamp = max(common_timestamps)
        
        return {
            "timestamp": latest_timestamp,
            "postgres": pg_timestamps[latest_timestamp],
            "milvus": milvus_timestamps[latest_timestamp]
        }

