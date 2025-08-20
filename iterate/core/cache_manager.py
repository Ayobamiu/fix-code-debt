"""
Smart caching system for codebase intelligence.
Implements Git-based change detection, file system monitoring, and intelligent caching.
"""

import os
import json
import hashlib
import time
from typing import Dict, List, Set, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import subprocess


@dataclass
class FileCache:
    """Cache information for a single file."""
    file_path: str
    last_modified: float
    content_hash: str
    chunk_count: int
    dependencies: List[str]
    last_analyzed: float


@dataclass
class CacheState:
    """Overall cache state."""
    last_git_commit: str
    last_analysis_time: float
    total_files: int
    total_chunks: int
    cache_version: str = "1.0"


class SmartCacheManager:
    """Manages intelligent caching for codebase analysis."""
    
    def __init__(self, cache_dir: str = ".iterate_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache files
        self.files_cache_file = self.cache_dir / "files_cache.json"
        self.state_cache_file = self.cache_dir / "cache_state.json"
        
        # Load existing cache
        self.files_cache: Dict[str, FileCache] = {}
        self.cache_state: CacheState = self._load_cache_state()
        
        # Initialize caches
        self._load_files_cache()
    
    def _load_cache_state(self) -> CacheState:
        """Load the overall cache state."""
        if self.state_cache_file.exists():
            try:
                with open(self.state_cache_file, 'r') as f:
                    data = json.load(f)
                    return CacheState(**data)
            except:
                pass
        
        # Default state
        return CacheState(
            last_git_commit="",
            last_analysis_time=0,
            total_files=0,
            total_chunks=0
        )
    
    def _save_cache_state(self):
        """Save the overall cache state."""
        try:
            with open(self.state_cache_file, 'w') as f:
                json.dump(asdict(self.cache_state), f, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Could not save cache state: {e}")
    
    def _load_files_cache(self):
        """Load the files cache."""
        if self.files_cache_file.exists():
            try:
                with open(self.files_cache_file, 'r') as f:
                    data = json.load(f)
                    self.files_cache = {
                        path: FileCache(**file_data) 
                        for path, file_data in data.items()
                    }
            except:
                self.files_cache = {}
        else:
            self.files_cache = {}
    
    def _save_files_cache(self):
        """Save the files cache."""
        try:
            with open(self.files_cache_file, 'w') as f:
                data = {
                    path: asdict(file_cache) 
                    for path, file_cache in self.files_cache.items()
                }
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"⚠️  Warning: Could not save files cache: {e}")
    
    def _get_git_commit_hash(self, directory: str) -> Optional[str]:
        """Get the current Git commit hash."""
        try:
            result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except:
            pass
        return None
    
    def _get_git_changed_files(self, directory: str, since_commit: str) -> List[str]:
        """Get files changed since a specific commit."""
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', since_commit],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return [line.strip() for line in result.stdout.splitlines() if line.strip()]
        except:
            pass
        return []
    
    def _calculate_file_hash(self, file_path: str) -> str:
        """Calculate SHA256 hash of file content."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except:
            return ""
    
    def _get_file_dependencies(self, file_path: str) -> List[str]:
        """Get file dependencies (simplified - can be enhanced later)."""
        # For now, return empty list - can be enhanced with actual dependency analysis
        return []
    
    def get_files_to_process(self, directory: str, all_files: List[str]) -> Tuple[List[str], List[str]]:
        """
        Get files that need processing and files that can be skipped.
        Returns: (files_to_process, files_to_skip)
        """
        print("🔍 Checking cache for changes...")
        
        # Check Git changes first (most reliable)
        git_changes = self._check_git_changes(directory)
        
        # Check file system changes
        file_system_changes = self._check_file_system_changes(all_files)
        
        # Combine changes
        all_changes = set(git_changes + file_system_changes)
        
        # Determine what to process
        files_to_process = []
        files_to_skip = []
        
        for file_path in all_files:
            if file_path in all_changes:
                files_to_process.append(file_path)
                print(f"  📝 {file_path} - changed, will process")
            else:
                files_to_skip.append(file_path)
                print(f"  ✅ {file_path} - unchanged, skipping")
        
        print(f"📊 Cache analysis: {len(files_to_process)} files to process, {len(files_to_skip)} files to skip")
        
        return files_to_process, files_to_skip
    
    def _check_git_changes(self, directory: str) -> List[str]:
        """Check for Git-based changes."""
        current_commit = self._get_git_commit_hash(directory)
        if not current_commit:
            print("  ⚠️  Not a Git repository, skipping Git change detection")
            return []
        
        # If this is a new repository or first run
        if not self.cache_state.last_git_commit:
            print(f"  🆕 First run, will process all files")
            self.cache_state.last_git_commit = current_commit
            return []
        
        # If commit hasn't changed, no Git changes
        if current_commit == self.cache_state.last_git_commit:
            print(f"  ✅ Git commit unchanged: {current_commit[:8]}")
            return []
        
        # Get changed files
        print(f"  🔄 Git commit changed: {self.cache_state.last_git_commit[:8]} → {current_commit[:8]}")
        changed_files = self._get_git_changed_files(directory, self.cache_state.last_git_commit)
        
        # Update cache state
        self.cache_state.last_git_commit = current_commit
        
        return changed_files
    
    def _check_file_system_changes(self, all_files: List[str]) -> List[str]:
        """Check for file system changes."""
        changed_files = []
        
        for file_path in all_files:
            if not os.path.exists(file_path):
                # File was deleted
                if file_path in self.files_cache:
                    del self.files_cache[file_path]
                    changed_files.append(file_path)
                continue
            
            # Check if file is in cache
            if file_path not in self.files_cache:
                # New file
                changed_files.append(file_path)
                continue
            
            # Check modification time
            current_mtime = os.path.getmtime(file_path)
            cached_mtime = self.files_cache[file_path].last_modified
            
            if current_mtime > cached_mtime:
                # File modified, check content hash
                current_hash = self._calculate_file_hash(file_path)
                cached_hash = self.files_cache[file_path].content_hash
                
                if current_hash != cached_hash:
                    changed_files.append(file_path)
        
        return changed_files
    
    def update_file_cache(self, file_path: str, chunk_count: int, dependencies: List[str] = None):
        """Update cache for a processed file."""
        try:
            if not os.path.exists(file_path):
                return
            
            mtime = os.path.getmtime(file_path)
            content_hash = self._calculate_file_hash(file_path)
            
            self.files_cache[file_path] = FileCache(
                file_path=file_path,
                last_modified=mtime,
                content_hash=content_hash,
                chunk_count=chunk_count,
                dependencies=dependencies or [],
                last_analyzed=time.time()
            )
            
        except Exception as e:
            print(f"⚠️  Warning: Could not update cache for {file_path}: {e}")
    
    def finalize_analysis(self, total_files: int, total_chunks: int):
        """Finalize the analysis and update cache state."""
        self.cache_state.last_analysis_time = time.time()
        self.cache_state.total_files = total_files
        self.cache_state.total_chunks = total_chunks
        
        # Save caches
        self._save_cache_state()
        self._save_files_cache()
        
        print(f"💾 Cache updated: {len(self.files_cache)} files, {total_chunks} chunks")
    
    def get_cache_stats(self) -> Dict[str, any]:
        """Get cache statistics."""
        return {
            "cached_files": len(self.files_cache),
            "last_analysis": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.cache_state.last_analysis_time)),
            "last_git_commit": self.cache_state.last_git_commit[:8] if self.cache_state.last_git_commit else "None",
            "total_files_analyzed": self.cache_state.total_files,
            "total_chunks_generated": self.cache_state.total_chunks,
            "cache_size_mb": self._get_cache_size_mb()
        }
    
    def _get_cache_size_mb(self) -> float:
        """Get cache size in MB."""
        try:
            total_size = 0
            for file_path in [self.files_cache_file, self.state_cache_file]:
                if file_path.exists():
                    total_size += file_path.stat().st_size
            
            # Add ChromaDB size
            chromadb_dir = self.cache_dir / "chromadb"
            if chromadb_dir.exists():
                for root, dirs, files in os.walk(chromadb_dir):
                    for file in files:
                        file_path = Path(root) / file
                        total_size += file_path.stat().st_size
            
            return round(total_size / (1024 * 1024), 2)
        except:
            return 0.0
    
    def clear_cache(self):
        """Clear all cache data."""
        try:
            # Remove cache files
            if self.files_cache_file.exists():
                self.files_cache_file.unlink()
            if self.state_cache_file.exists():
                self.state_cache_file.unlink()
            
            # Clear ChromaDB
            chromadb_dir = self.cache_dir / "chromadb"
            if chromadb_dir.exists():
                import shutil
                shutil.rmtree(chromadb_dir)
            
            # Reset caches
            self.files_cache = {}
            self.cache_state = CacheState(
                last_git_commit="",
                last_analysis_time=0,
                total_files=0,
                total_chunks=0
            )
            
            print("🗑️  Cache cleared successfully")
            
        except Exception as e:
            print(f"❌ Error clearing cache: {e}")
    
    def is_cache_valid(self, max_age_hours: int = 24) -> bool:
        """Check if cache is still valid based on age."""
        if self.cache_state.last_analysis_time == 0:
            return False
        
        age_hours = (time.time() - self.cache_state.last_analysis_time) / 3600
        return age_hours < max_age_hours