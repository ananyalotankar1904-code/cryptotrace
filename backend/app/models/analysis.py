from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field


class AnalysisCaseInfo(BaseModel):
    root_wallet: str = Field(description="Starting suspect wallet address.")
    blockchain: str = Field(default="ethereum", description="Target blockchain ecosystem.")
    network: str = Field(default="mainnet", description="Blockchain network name.")

class AnalysisSummary(BaseModel):
    transactions_analyzed: int = Field(description="Total number of transactions analyzed.")
    wallets_discovered: int = Field(description="Total number of unique wallets discovered.")
    max_hop: int = Field(description="Maximum hop distance reached.")

class AnalysisGraph(BaseModel):
    nodes: List[Dict[str, Any]] = Field(description="List of wallet nodes.")
    edges: List[Dict[str, Any]] = Field(description="List of transaction edges.")

class AnalysisRisk(BaseModel):
    risk_score: float = Field(description="Calculated risk score.")
    risk_level: str = Field(description="Risk level classification.")
    risk_indicators: List[str] = Field(description="List of risk indicators identified.")
    risk_indicator_details: Optional[List[Dict[str, Any]]] = Field(default=None, description="Detailed explanation of risk indicators.")

class VaspAttribution(BaseModel):
    """Structured VASP attribution result from the verified dataset."""
    identified: bool = Field(description="Whether a verified VASP match was found.")
    name: Optional[str] = Field(default=None, description="Name of the identified VASP (e.g., Binance).")
    type: Optional[str] = Field(default=None, description="Entity type (e.g., VASP).")
    address_type: Optional[str] = Field(default=None, description="Address classification (e.g., exchange_wallet, deposit_address).")
    matched_address: Optional[str] = Field(default=None, description="The exact verified address that matched.")
    match_type: str = Field(default="none", description="Match method used (exact_verified_address | none).")
    confidence: Optional[str] = Field(default=None, description="Confidence level from VASP dataset (high | medium | low | unknown).")
    confidence_score: Optional[float] = Field(default=None, description="Numeric confidence score (0-1) from the dataset record.")
    hop: Optional[int] = Field(default=None, description="Hop distance at which the VASP address was encountered.")
    evidence: Optional[str] = Field(default=None, description="Source evidence (e.g., Etherscan label URL).")
    source_name: Optional[str] = Field(default=None, description="Name of the attribution source.")
    notes: Optional[str] = Field(default=None, description="Additional notes from the dataset record.")
    status: str = Field(default="no_verified_dataset_match", description="Attribution status.")


class CombinedAnalysisResponse(BaseModel):
    case: AnalysisCaseInfo
    summary: AnalysisSummary
    transactions: List[Dict[str, Any]] = Field(description="List of normalized transaction records.")
    graph: AnalysisGraph
    risk_analysis: AnalysisRisk
    vasp_attribution: VaspAttribution = Field(description="VASP attribution result from the verified intelligence dataset.")
    known_entities: List[Dict[str, Any]] = Field(default_factory=list, description="List of identified VASP or known entities.")
    candidate_paths: List[Dict[str, Any]] = Field(default_factory=list, description="High-risk candidate transfer paths.")
    wallet_features: Optional[Dict[str, Any]] = Field(default=None, description="Extracted features per wallet.")
    disclaimer: str = Field(description="Investigation notice.")
