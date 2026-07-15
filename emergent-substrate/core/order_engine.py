"""
Order Engine - Copilot's side
shape() → govern() → integrate()
"""

import re
from typing import List, Dict, Optional
from .models import (
    StructuredModel,
    GovernedSpec,
    ValidationResult,
    GovernanceStatus,
    PacketType
)


class OrderEngine:
    """
    Copilot's order engine
    Shapes raw entropy into structured models, governs them, and integrates into memory
    """

    def __init__(self):
        self._structure_type_counts: Dict[str, int] = {}

    def shape(self, packet) -> StructuredModel:
        """
        Transform raw entropy packet into structured model
        - Invariant extraction
        - Cross-domain decomposition
        - Constraint derivation
        """
        # Extract title from content
        title = self._extract_title(packet.raw_content)
        
        # Generate abstract
        abstract = self._generate_abstract(packet.raw_content)
        
        # Extract invariants (heuristic regex - swap with LLM in production)
        invariants = self._extract_invariants(packet.raw_content, packet.cross_domain)
        
        # Decompose by cross-domain
        cross_domain_decomposition = self._decompose_cross_domain(
            packet.raw_content, 
            packet.cross_domain
        )
        
        # Derive constraints
        constraints = self._derive_constraints(packet.raw_content, invariants)
        
        # Determine structure type
        structure_type = self._determine_structure_type(packet.packet_type, invariants)
        
        # Track structure type for GPS homogenization check
        self._structure_type_counts[structure_type] = self._structure_type_counts.get(structure_type, 0) + 1
        
        # Calculate confidence score (heuristic)
        confidence_score = self._calculate_confidence(packet, invariants, constraints)
        
        return StructuredModel(
            source_packet_id=packet.packet_id,
            title=title,
            abstract=abstract,
            invariants=invariants,
            cross_domain_decomposition=cross_domain_decomposition,
            constraints=constraints,
            structure_type=structure_type,
            confidence_score=confidence_score
        )

    def govern(self, model: StructuredModel, validation_results: List[ValidationResult]) -> GovernedSpec:
        """
        Apply governance validation results to produce governed spec
        """
        # Determine overall governance status
        overall_status = self._determine_governance_status(validation_results)
        
        # Generate content from model
        content = self._generate_spec_content(model, validation_results)
        
        return GovernedSpec(
            source_model_id=model.model_id,
            title=model.title,
            content=content,
            validation_results=validation_results,
            governance_status=overall_status,
            integrated=False
        )

    def integrate(self, spec: GovernedSpec, memory_layer) -> None:
        """
        Integrate governed spec into memory layer
        """
        # Mark as integrated
        spec.integrated = True
        
        # Append evolution event
        memory_layer.append_evolution_event(
            event_type="spec_integrated",
            description=f"Integrated spec: {spec.title}",
            related_ids=[spec.spec_id, spec.source_model_id]
        )

    def _extract_title(self, content: str) -> str:
        """Extract title from content"""
        # Take first sentence or first 50 chars
        first_sentence = re.split(r'[.!?]', content)[0].strip()
        if len(first_sentence) > 50:
            return first_sentence[:50] + "..."
        return first_sentence

    def _generate_abstract(self, content: str) -> str:
        """Generate abstract from content"""
        # Take first 200 chars
        if len(content) > 200:
            return content[:200] + "..."
        return content

    def _extract_invariants(self, content: str, cross_domains: List[str]) -> List[str]:
        """
        Extract invariants from content
        Heuristic regex - swap with LLM call in production
        """
        invariants = []
        
        # Look for patterns like "must", "should", "requires", "ensures"
        patterns = [
            r'(?:must|should|requires|ensures)\s+(?:be|have|include|maintain)\s+\w+',
            r'(?:no|never)\s+\w+\s+(?:allowed|permitted)',
            r'(?:always|never)\s+\w+',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            invariants.extend(matches)
        
        # Add domain-specific invariants
        for domain in cross_domains:
            invariants.append(f"Domain invariant: {domain}")
        
        return invariants[:10]  # Limit to 10 invariants

    def _decompose_cross_domain(self, content: str, cross_domains: List[str]) -> Dict[str, List[str]]:
        """Decompose content by cross-domain"""
        decomposition = {}
        
        for domain in cross_domains:
            # Simple heuristic - look for domain keywords in content
            domain_keywords = self._get_domain_keywords(domain)
            found = [kw for kw in domain_keywords if kw.lower() in content.lower()]
            decomposition[domain] = found
        
        return decomposition

    def _get_domain_keywords(self, domain: str) -> List[str]:
        """Get keywords for a domain"""
        domain_keywords = {
            "biology": ["cell", "organism", "evolution", "genetic", "membrane", "system"],
            "constitutional law": ["law", "right", "amendment", "constitution", "governance", "authority"],
            "systems theory": ["feedback", "loop", "emergence", "network", "dynamics", "equilibrium"],
            "computer science": ["algorithm", "data", "interface", "protocol", "architecture", "system"],
            "philosophy": ["ethics", "logic", "reason", "truth", "meaning", "consciousness"],
        }
        return domain_keywords.get(domain.lower(), [])

    def _derive_constraints(self, content: str, invariants: List[str]) -> List[str]:
        """Derive constraints from invariants"""
        constraints = []
        
        for invariant in invariants:
            # Simple heuristic - convert invariant to constraint
            if "must" in invariant.lower():
                constraints.append(f"Constraint: {invariant}")
            elif "never" in invariant.lower() or "no" in invariant.lower():
                constraints.append(f"Prohibition: {invariant}")
        
        return constraints

    def _determine_structure_type(self, packet_type: PacketType, invariants: List[str]) -> str:
        """Determine structure type based on packet type and invariants"""
        type_mapping = {
            PacketType.IDEA: "concept",
            PacketType.FEELING: "affective",
            PacketType.METAPHOR: "analogical",
            PacketType.CHALLENGE: "problem",
            PacketType.EXTENSION: "expansion",
            PacketType.MUTATION: "variant",
        }
        
        base_type = type_mapping.get(packet_type, "generic")
        
        # Refine based on invariants
        if len(invariants) > 5:
            base_type += "_complex"
        
        return base_type

    def _calculate_confidence(self, packet, invariants: List[str], constraints: List[str]) -> float:
        """Calculate confidence score (heuristic)"""
        # Base confidence from intensity
        confidence = packet.intensity * 0.5
        
        # Boost from invariants
        confidence += len(invariants) * 0.03
        
        # Boost from constraints
        confidence += len(constraints) * 0.02
        
        # Boost from cross-domain
        confidence += len(packet.cross_domain) * 0.05
        
        # Clamp to [0, 1]
        return min(max(confidence, 0.0), 1.0)

    def _determine_governance_status(self, validation_results: List[ValidationResult]) -> GovernanceStatus:
        """Determine overall governance status from validation results"""
        if any(r.status == GovernanceStatus.BLOCK for r in validation_results):
            return GovernanceStatus.BLOCK
        elif any(r.status == GovernanceStatus.WARN for r in validation_results):
            return GovernanceStatus.WARN
        return GovernanceStatus.PASS

    def _generate_spec_content(self, model: StructuredModel, validation_results: List[ValidationResult]) -> str:
        """Generate spec content from model and validation results"""
        content = f"# {model.title}\n\n"
        content += f"## Abstract\n{model.abstract}\n\n"
        
        if model.invariants:
            content += "## Invariants\n"
            for inv in model.invariants:
                content += f"- {inv}\n"
            content += "\n"
        
        if model.constraints:
            content += "## Constraints\n"
            for cons in model.constraints:
                content += f"- {cons}\n"
            content += "\n"
        
        if model.cross_domain_decomposition:
            content += "## Cross-Domain Decomposition\n"
            for domain, items in model.cross_domain_decomposition.items():
                content += f"### {domain}\n"
                for item in items:
                    content += f"- {item}\n"
            content += "\n"
        
        content += f"## Governance Status: {model.governance_status}\n"
        
        return content

    def get_structure_type_count(self, structure_type: str) -> int:
        """Get count of a specific structure type (for GPS homogenization check)"""
        return self._structure_type_counts.get(structure_type, 0)

    def reset_structure_type_counts(self):
        """Reset structure type counts"""
        self._structure_type_counts.clear()
