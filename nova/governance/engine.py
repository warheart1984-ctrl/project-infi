from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import List

from nova.law_kernel.law_ledger import LawLedger
from nova.law_kernel.models import LawStatus


class ProposalStatus(str, Enum):
    OPEN = "open"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class LawProposal:
    id: str
    code: str
    text: str
    status: ProposalStatus
    votes_for: float
    votes_against: float


class GovernanceEngine:
    def __init__(self, ledger: LawLedger) -> None:
        self.ledger = ledger
        self._proposals: List[LawProposal] = []

    def propose_law(self, code: str, text: str) -> LawProposal:
        proposal = LawProposal(
            id=f"prop:{len(self._proposals)}",
            code=code,
            text=text,
            status=ProposalStatus.OPEN,
            votes_for=0.0,
            votes_against=0.0,
        )
        self._proposals.append(proposal)
        return proposal

    def vote(self, proposal_id: str, weight: float, approve: bool) -> None:
        proposal = next(item for item in self._proposals if item.id == proposal_id)
        if approve:
            proposal.votes_for += weight
        else:
            proposal.votes_against += weight

    def finalize(self, proposal_id: str, threshold: float = 0.6) -> LawProposal:
        proposal = next(item for item in self._proposals if item.id == proposal_id)
        total = proposal.votes_for + proposal.votes_against
        if total == 0:
            proposal.status = ProposalStatus.REJECTED
            return proposal
        if proposal.votes_for / total >= threshold:
            proposal.status = ProposalStatus.ACCEPTED
            self.ledger.add_law(
                code=proposal.code,
                text=proposal.text,
                status=LawStatus.EXPERIMENTAL,
                fitness=0.5,
                epoch="EPOCH:GOV",
            )
        else:
            proposal.status = ProposalStatus.REJECTED
        return proposal
