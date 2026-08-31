from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class ReportRiskIndicator(BaseModel):
    title: str
    severity: str
    description: Optional[str] = ""

class ReportRisk(BaseModel):
    score: Optional[float] = None
    level: Optional[str] = None
    summary: Optional[str] = ""
    indicators: List[ReportRiskIndicator] = Field(default_factory=list)
    breakdown: List[Any] = Field(default_factory=list)

class ReportVasp(BaseModel):
    identified: bool
    possible: bool
    name: str
    type: str
    confidence: Optional[float] = None
    address: Optional[str] = None
    hop: Optional[int] = None
    finalDestinationHop: Optional[int] = None
    status: Optional[str] = ""

class ReportPathNode(BaseModel):
    label: str
    address: str

class ReportTransaction(BaseModel):
    id: Any
    from_addr: Optional[str] = Field(default=None, alias="from")
    to: Optional[str] = None
    amount: Any = None
    token: Optional[str] = None
    timestamp: Optional[str] = None
    hop: Optional[int] = None
    risk: Optional[Dict[str, Any]] = None
    status: Optional[str] = None
    txHash: Optional[str] = None
    block: Any = None

    class Config:
        populate_by_name = True

class ReportPayload(BaseModel):
    investigationId: str
    suspectWallet: Optional[str] = None
    queriedAddress: str
    chain: str
    hops: int = 0
    totalValue: Optional[float] = None
    totalValueToken: str = "ETH"
    transactionsCount: int = 0
    risk: ReportRisk
    vasp: Optional[ReportVasp] = None
    path: List[ReportPathNode] = Field(default_factory=list)
    transactions: List[ReportTransaction] = Field(default_factory=list)
    entityMeta: Dict[str, Any] = Field(default_factory=dict)
    isDemo: bool = False
    generatedAt: str
