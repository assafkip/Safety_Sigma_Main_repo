"""
Safety Sigma Audit Logger

Append-only JSONL logging with tamper-evident chain for LLM integration.
Records inputs, model prompts, responses, spans used, decisions, and validation scores.
"""

import json
import hashlib
import time
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
import threading


class AuditLogger:
    """
    Tamper-evident append-only audit logger
    
    Each log entry includes:
    - Hash of previous entry (tamper-evident chain)
    - Timestamp and run context
    - Input data and model interactions
    - Decisions made and validation results
    """
    
    def __init__(self, log_file: Path, redact_sensitive: bool = True):
        self.log_file = Path(log_file)
        self.redact_sensitive = redact_sensitive
        self.lock = threading.Lock()
        
        # Ensure log directory exists
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize log if it doesn't exist
        if not self.log_file.exists():
            self._initialize_log()
    
    def _initialize_log(self):
        """Initialize audit log with genesis entry"""
        genesis_entry = {
            "event": "audit_log_initialized",
            "timestamp": time.time(),
            "iso_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "schema_version": "v0.4",
            "previous_hash": "genesis",
            "entry_hash": ""
        }
        
        # Compute hash for genesis entry  
        genesis_entry["entry_hash"] = self._compute_entry_hash(genesis_entry)
        
        # Write genesis entry
        with self.log_file.open('w', encoding='utf-8') as f:
            f.write(json.dumps(genesis_entry, ensure_ascii=False) + '\n')
    
    def append(self, event: Dict[str, Any]) -> str:
        """
        Append event to audit log with tamper-evident chain
        
        Args:
            event: Event data to log
            
        Returns:
            Hash of the logged entry
        """
        with self.lock:
            # Get hash of previous entry
            previous_hash = self._get_last_entry_hash()
            
            # Build complete log entry
            log_entry = {
                "event": event.get("event", "unknown"),
                "timestamp": time.time(),
                "iso_timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "run_id": event.get("run_id", "unknown"),
                "previous_hash": previous_hash,
                "data": self._sanitize_event_data(event)
            }
            
            # Compute hash including previous hash
            entry_hash = self._compute_entry_hash(log_entry)
            log_entry["entry_hash"] = entry_hash
            
            # Append to log file
            with self.log_file.open('a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
            
            return entry_hash
    
    def _get_last_entry_hash(self) -> str:
        """Get hash of the last entry in the log"""
        if not self.log_file.exists():
            return "genesis"
        
        try:
            # Read last line of log file
            with self.log_file.open('r', encoding='utf-8') as f:
                lines = f.readlines()
                
            if not lines:
                return "genesis"
            
            last_line = lines[-1].strip()
            if last_line:
                last_entry = json.loads(last_line)
                return last_entry.get("entry_hash", "genesis")
                
        except (json.JSONDecodeError, IOError):
            # If log is corrupted, note this in hash
            return "corrupted_log"
        
        return "genesis"
    
    def _compute_entry_hash(self, entry: Dict[str, Any]) -> str:
        """Compute SHA-256 hash of entry for tamper evidence"""
        # Create stable string representation
        entry_copy = entry.copy()
        entry_copy.pop("entry_hash", None)  # Remove hash field from computation
        
        # Sort keys for deterministic hashing
        entry_str = json.dumps(entry_copy, sort_keys=True, ensure_ascii=False)
        
        return hashlib.sha256(entry_str.encode('utf-8')).hexdigest()
    
    def _sanitize_event_data(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize event data, redacting sensitive information if configured"""
        sanitized = event.copy()
        
        if self.redact_sensitive:
            # List of sensitive fields to redact
            sensitive_fields = [
                "api_key",
                "token", 
                "password",
                "secret",
                "credential"
            ]
            
            # Redact model responses that might contain sensitive data
            if "model_response" in sanitized:
                sanitized["model_response"] = self._redact_model_response(
                    sanitized["model_response"]
                )
            
            # Redact any fields with sensitive names
            for field in sensitive_fields:
                if field in sanitized:
                    sanitized[field] = "[REDACTED]"
            
            # Redact nested sensitive data
            sanitized = self._redact_nested_sensitive(sanitized, sensitive_fields)
        
        return sanitized
    
    def _redact_model_response(self, response: Any) -> Any:
        """Redact potentially sensitive content from model responses"""
        if isinstance(response, str):
            # Redact patterns that look like credentials
            import re
            
            # Redact API keys (long alphanumeric strings)
            response = re.sub(r'[a-zA-Z0-9]{32,}', '[REDACTED_KEY]', response)
            
            # Redact email addresses in responses
            response = re.sub(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', 
                            '[REDACTED_EMAIL]', response)
            
        return response
    
    def _redact_nested_sensitive(self, data: Any, sensitive_fields: list) -> Any:
        """Recursively redact sensitive fields in nested structures"""
        if isinstance(data, dict):
            result = {}
            for key, value in data.items():
                if key.lower() in [f.lower() for f in sensitive_fields]:
                    result[key] = "[REDACTED]"
                else:
                    result[key] = self._redact_nested_sensitive(value, sensitive_fields)
            return result
        elif isinstance(data, list):
            return [self._redact_nested_sensitive(item, sensitive_fields) for item in data]
        else:
            return data
    
    def verify_chain_integrity(self) -> Dict[str, Any]:
        """
        Verify the integrity of the audit chain
        
        Returns:
            Verification report with chain status
        """
        report = {
            "intact": True,
            "total_entries": 0,
            "verified_entries": 0,
            "issues": []
        }
        
        if not self.log_file.exists():
            report["intact"] = False
            report["issues"].append("Audit log file does not exist")
            return report
        
        try:
            with self.log_file.open('r', encoding='utf-8') as f:
                lines = f.readlines()
            
            previous_hash = "genesis"
            
            for line_num, line in enumerate(lines, 1):
                try:
                    entry = json.loads(line.strip())
                    report["total_entries"] += 1
                    
                    # Verify previous hash matches
                    if entry.get("previous_hash") != previous_hash:
                        report["intact"] = False
                        report["issues"].append(
                            f"Line {line_num}: Previous hash mismatch. "
                            f"Expected: {previous_hash}, Got: {entry.get('previous_hash')}"
                        )
                        continue
                    
                    # Verify entry hash
                    expected_hash = self._compute_entry_hash(entry)
                    if entry.get("entry_hash") != expected_hash:
                        report["intact"] = False
                        report["issues"].append(
                            f"Line {line_num}: Entry hash mismatch. "
                            f"Expected: {expected_hash}, Got: {entry.get('entry_hash')}"
                        )
                        continue
                    
                    report["verified_entries"] += 1
                    previous_hash = entry["entry_hash"]
                    
                except json.JSONDecodeError as e:
                    report["intact"] = False
                    report["issues"].append(f"Line {line_num}: Invalid JSON - {str(e)}")
                    
        except IOError as e:
            report["intact"] = False
            report["issues"].append(f"Failed to read audit log: {str(e)}")
        
        return report
    
    def get_entries_by_run_id(self, run_id: str) -> List[Dict[str, Any]]:
        """Get all audit entries for a specific run ID"""
        entries = []
        
        if not self.log_file.exists():
            return entries
        
        try:
            with self.log_file.open('r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        if entry.get("data", {}).get("run_id") == run_id:
                            entries.append(entry)
                    except json.JSONDecodeError:
                        continue
                        
        except IOError:
            pass
        
        return entries
    
    def get_recent_entries(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get the most recent audit entries"""
        entries = []
        
        if not self.log_file.exists():
            return entries
        
        try:
            with self.log_file.open('r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Get last N lines
            recent_lines = lines[-limit:] if len(lines) > limit else lines
            
            for line in recent_lines:
                try:
                    entries.append(json.loads(line.strip()))
                except json.JSONDecodeError:
                    continue
                    
        except IOError:
            pass
        
        return entries


class AuditContext:
    """
    Context manager for audit logging with automatic cleanup
    """
    
    def __init__(self, logger: AuditLogger, run_id: str, operation: str):
        self.logger = logger
        self.run_id = run_id
        self.operation = operation
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        self.logger.append({
            "event": f"{self.operation}_start",
            "run_id": self.run_id,
            "start_time": self.start_time
        })
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        end_time = time.time()
        duration = end_time - self.start_time if self.start_time else 0
        
        if exc_type is None:
            # Success
            self.logger.append({
                "event": f"{self.operation}_success",
                "run_id": self.run_id,
                "duration_seconds": duration,
                "end_time": end_time
            })
        else:
            # Error occurred
            self.logger.append({
                "event": f"{self.operation}_error",
                "run_id": self.run_id,
                "duration_seconds": duration,
                "end_time": end_time,
                "error_type": exc_type.__name__ if exc_type else None,
                "error_message": str(exc_val) if exc_val else None
            })
        
        return False  # Don't suppress exceptions