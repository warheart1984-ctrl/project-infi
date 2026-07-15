#!/usr/bin/env python3
"""
Constitutional Freeze Enforcement
MANDATORY enforcement per Section 2.1.2 Immutability Doctrine
Aligned with UCDD S-003 Version Sovereignty Standard
Critical findings per S-005 for violations
"""

import os
import sys
import json
import hashlib
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ConstitutionalState:
    """State of constitutional freeze per Immutability Doctrine"""
    constitution_path: str
    frozen: bool
    frozen_at: Optional[str]  # ISO 8601 timestamp
    frozen_by: Optional[str]  # Authority tier
    hash: str  # SHA-256 content hash
    signature: Optional[str]  # Cryptographic signature
    registry_entry: Optional[str]  # Immutable Artifact Registry ID
    amendment_procedure: str = "UCDD S-006"


class ConstitutionalFreezeEnforcer:
    """Enforces constitutional freeze per Section 2.1.2 Immutability Doctrine"""
    
    def __init__(self, repo_path: str = "e:\\project-infi"):
        self.repo_path = Path(repo_path)
        self.freeze_file = self.repo_path / ".constitutional_freeze.json"
        self.constitution_files = [
            self.repo_path / "constitution.ulx",
            self.repo_path / "prime_architect_integration.py",  # Contains SAMPLE_CONSTITUTION
            self.repo_path / "ulx.py",  # ULX language implementation
        ]
        self.state = self._load_state()
        self.critical_findings = []
        
    def _load_state(self) -> Optional[ConstitutionalState]:
        """Load constitutional freeze state"""
        if not self.freeze_file.exists():
            return None
            
        try:
            with open(self.freeze_file, 'r') as f:
                data = json.load(f)
            return ConstitutionalState(**data)
        except Exception:
            return None
            
    def _save_state(self, state: ConstitutionalState):
        """Save constitutional freeze state per S-003"""
        with open(self.freeze_file, 'w') as f:
            json.dump({
                "constitution_path": str(state.constitution_path),
                "frozen": state.frozen,
                "frozen_at": state.frozen_at,
                "frozen_by": state.frozen_by,
                "hash": state.hash,
                "signature": state.signature,
                "registry_entry": state.registry_entry,
                "amendment_procedure": state.amendment_procedure
            }, f, indent=2)
            
    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA-256 hash of file"""
        if not file_path.exists():
            return ""
        with open(file_path, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()
            
    def is_frozen(self) -> bool:
        """Check if constitution is frozen"""
        return self.state is not None and self.state.frozen
        
    def freeze_constitution(self, authority: str = "PRIME-ARCHITECT") -> bool:
        """Freeze the constitution - MANDATORY per Section 2.1.2"""
        if self.is_frozen():
            print("Constitution is already frozen")
            return False
            
        # Verify authority tier (only PRIME can freeze)
        if authority != "PRIME-ARCHITECT":
            print("ERROR: Only PRIME-ARCHITECT authority can freeze constitution")
            self._record_critical_finding(
                "UNAUTHORIZED_FREEZE_ATTEMPT",
                f"Attempt to freeze by {authority} without PRIME authority"
            )
            return False
            
        # Compute hash of all constitution files
        hashes = {}
        for const_file in self.constitution_files:
            if const_file.exists():
                hashes[str(const_file)] = self._compute_hash(const_file)
            else:
                print(f"WARNING: Constitution file not found: {const_file}")
                
        # Create freeze state with ISO 8601 timestamp
        combined_hash = hashlib.sha256(json.dumps(hashes, sort_keys=True).encode()).hexdigest()
        timestamp = datetime.utcnow().isoformat() + "Z"
        
        # Generate registry entry ID per S-003
        registry_id = f"REG-CONST-{int(time.time())}"
        
        state = ConstitutionalState(
            constitution_path=str(self.repo_path),
            frozen=True,
            frozen_at=timestamp,
            frozen_by=authority,
            hash=combined_hash,
            signature=None,  # Would be HSM-signed in production
            registry_entry=registry_id,
            amendment_procedure="UCDD S-006"
        )
        
        self._save_state(state)
        print(f"✓ Constitution frozen by {authority}")
        print(f"✓ Timestamp: {timestamp}")
        print(f"✓ Registry Entry: {registry_id}")
        print(f"✓ Combined Hash: {combined_hash}")
        print(f"✓ Amendment Procedure: UCDD S-006")
        return True
        
    def _record_critical_finding(self, finding_type: str, description: str):
        """Record Critical finding per S-005"""
        finding = {
            "type": "CRITICAL",
            "finding_type": finding_type,
            "description": description,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "standard": "S-005",
            "severity": "CRITICAL"
        }
        self.critical_findings.append(finding)
        
        # Log to file
        findings_file = self.repo_path / ".constitutional_findings.json"
        try:
            existing = []
            if findings_file.exists():
                with open(findings_file, 'r') as f:
                    existing = json.load(f)
            existing.append(finding)
            with open(findings_file, 'w') as f:
                json.dump(existing, f, indent=2)
        except Exception:
            pass
            
    def verify_integrity(self) -> bool:
        """Verify constitutional integrity against frozen state per S-003"""
        if not self.is_frozen():
            print("Constitution is not frozen - cannot verify integrity")
            return False
            
        # Recompute hashes
        current_hashes = {}
        for const_file in self.constitution_files:
            if const_file.exists():
                current_hashes[str(const_file)] = self._compute_hash(const_file)
                
        # Compare with frozen state
        combined_hash = hashlib.sha256(json.dumps(current_hashes, sort_keys=True).encode()).hexdigest()
        
        if combined_hash != self.state.hash:
            print("=" * 60)
            print("CRITICAL FINDING - CONSTITUTIONAL INTEGRITY VIOLATION")
            print("=" * 60)
            print(f"Standard: S-005")
            print(f"Severity: CRITICAL")
            print(f"Expected hash: {self.state.hash}")
            print(f"Current hash:  {combined_hash}")
            print(f"Registry Entry: {self.state.registry_entry}")
            print("=" * 60)
            print("IMMEDIATE ESCALATION REQUIRED")
            print("=" * 60)
            
            self._record_critical_finding(
                "INTEGRITY_VIOLATION",
                f"Hash mismatch detected. Expected: {self.state.hash}, Current: {combined_hash}"
            )
            return False
            
        print("✓ Constitutional integrity verified")
        print(f"✓ Registry Entry: {self.state.registry_entry}")
        return True
        
    def check_modification(self) -> List[str]:
        """Check if constitution files have been modified since freeze"""
        if not self.is_frozen():
            return []
            
        violations = []
        for const_file in self.constitution_files:
            if const_file.exists():
                current_hash = self._compute_hash(const_file)
                # In production, we'd store per-file hashes in freeze state
                # For now, we use git to check modifications
                try:
                    result = subprocess.run(
                        ["git", "diff", "--name-only", str(const_file)],
                        cwd=self.repo_path,
                        capture_output=True,
                        text=True
                    )
                    if result.stdout.strip():
                        violations.append(str(const_file))
                except Exception:
                    pass
                    
        return violations
        
    def enforce_git_hook(self) -> bool:
        """Git pre-commit hook to enforce constitutional freeze per Section 2.1.2"""
        if not self.is_frozen():
            return True  # Allow commits if not frozen
            
        modifications = self.check_modification()
        
        if modifications:
            print("=" * 60)
            print("CRITICAL FINDING - CONSTITUTIONAL FREEZE VIOLATION")
            print("=" * 60)
            print("Standard: S-005")
            print("Severity: CRITICAL")
            print("Section: 2.1.2 Immutability Doctrine")
            print("\nThe following constitutional artifacts are frozen:")
            for mod in modifications:
                print(f"  - {mod}")
            print("\nUNILATERAL ENGINEERING MODIFICATION IS PROHIBITED")
            print("\nTo modify constitutional artifacts, you MUST:")
            print("  1. Unfreeze the constitution (requires PRIME-ARCHITECT authority)")
            print("  2. Make your changes")
            print("  3. Re-freeze the constitution (requires PRIME-ARCHITECT authority)")
            print("  4. Follow formal amendment procedure per UCDD S-006")
            print("  5. Update Immutable Artifact Registry per S-003")
            print("\nThis violation will be recorded as a Critical finding.")
            print("=" * 60)
            
            self._record_critical_finding(
                "FREEZE_VIOLATION",
                f"Attempted modification of frozen constitutional artifacts: {modifications}"
            )
            return False
            
        return True
        
    def unfreeze_constitution(self, authority: str) -> bool:
        """Unfreeze the constitution - requires PRIME authority per Section 2.1.2"""
        if not self.is_frozen():
            print("Constitution is not frozen")
            return False
            
        if authority != "PRIME-ARCHITECT":
            print("ERROR: Only PRIME-ARCHITECT authority can unfreeze the constitution")
            self._record_critical_finding(
                "UNAUTHORIZED_UNFREEZE_ATTEMPT",
                f"Attempt to unfreeze by {authority} without PRIME authority"
            )
            return False
            
        # Log the unfreeze event per S-006 amendment procedure
        print(f"✓ Constitution unfrozen by {authority}")
        print(f"⚠ Amendment procedure per UCDD S-006 must be followed")
        print(f"⚠ Immutable Artifact Registry must be updated per S-003")
        
        # Record unfreeze event
        self._record_critical_finding(
            "CONSTITUTION_UNFROZEN",
            f"Constitution unfrozen by {authority} for amendment"
        )
        
        # Remove freeze state
        self.freeze_file.unlink()
        self.state = None
        
        return True


def install_git_hooks(repo_path: str = "e:\\project-infi"):
    """Install git hooks to enforce constitutional freeze"""
    hooks_dir = Path(repo_path) / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)
    
    # Pre-commit hook
    pre_commit_hook = hooks_dir / "pre-commit"
    hook_content = """#!/usr/bin/env python3
import sys
sys.path.insert(0, 'e:\\\\project-infi')
from constitutional_freeze import ConstitutionalFreezeEnforcer

enforcer = ConstitutionalFreezeEnforcer()
if not enforcer.enforce_git_hook():
    sys.exit(1)
"""
    
    with open(pre_commit_hook, 'w') as f:
        f.write(hook_content)
        
    # Make hook executable (on Unix-like systems)
    try:
        os.chmod(pre_commit_hook, 0o755)
    except Exception:
        pass  # Windows doesn't support chmod
        
    print(f"Git hooks installed in {hooks_dir}")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Constitutional Freeze Enforcement")
    parser.add_argument("command", choices=["freeze", "unfreeze", "verify", "check", "install-hooks"])
    parser.add_argument("--authority", default="PRIME-ARCHITECT", help="Authority tier")
    parser.add_argument("--repo", default="e:\\project-infi", help="Repository path")
    
    args = parser.parse_args()
    
    enforcer = ConstitutionalFreezeEnforcer(args.repo)
    
    if args.command == "freeze":
        success = enforcer.freeze_constitution(args.authority)
        sys.exit(0 if success else 1)
        
    elif args.command == "unfreeze":
        success = enforcer.unfreeze_constitution(args.authority)
        sys.exit(0 if success else 1)
        
    elif args.command == "verify":
        success = enforcer.verify_integrity()
        sys.exit(0 if success else 1)
        
    elif args.command == "check":
        modifications = enforcer.check_modification()
        if modifications:
            print("Modified files:")
            for mod in modifications:
                print(f"  - {mod}")
            sys.exit(1)
        else:
            print("No modifications detected")
            sys.exit(0)
            
    elif args.command == "install-hooks":
        install_git_hooks(args.repo)
        sys.exit(0)


if __name__ == "__main__":
    main()
