from typing import Optional, List
from fastapi import APIRouter, HTTPException, Query, Path, status

from app.models.transfer import (
    TransferResponse,
    TransferDirection,
    TransferCategory,
    ErrorResponse,
)
from app.models.trace import TraceResponse
from app.models.analysis import CombinedAnalysisResponse
from app.services.analytics.analytics_service import analyze_transaction_graph
from app.services.vasp_service import attribute_vasp_from_graph_nodes, attribute_vasp_from_transfers
from app.utils.validation import validate_ethereum_address
from app.services.alchemy import (
    AlchemyService,
    AlchemyConfigError,
    AlchemyAuthError,
    AlchemyRateLimitError,
    AlchemyNetworkError,
    AlchemyError,
)
from app.services.tracer import MultiHopTracer
from app.config import get_settings

settings = get_settings()

router = APIRouter(prefix="/wallet", tags=["Wallet Transfers & Tracing"])


@router.get(
    "/{address}/transfers",
    response_model=TransferResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Ethereum Wallet Asset Transfers",
    description=(
        "Retrieve historical Ethereum asset transfers (native ETH and ERC-20 tokens) "
        "for a specified Ethereum wallet address using Alchemy Transfers API."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Ethereum wallet address format."},
        429: {"model": ErrorResponse, "description": "Alchemy API rate limit exceeded."},
        500: {"model": ErrorResponse, "description": "Server configuration error (e.g., missing API key)."},
        502: {"model": ErrorResponse, "description": "Alchemy upstream API error or invalid authentication."},
        504: {"model": ErrorResponse, "description": "Gateway timeout connecting to Alchemy."},
    },
)
async def get_wallet_transfers(
    address: str = Path(
        ...,
        description="Target 42-character hex Ethereum address (e.g., 0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe)",
    ),
    direction: TransferDirection = Query(
        default=TransferDirection.ALL,
        description="Filter transfer direction: 'all' (both incoming and outgoing), 'from' (outgoing only), or 'to' (incoming only).",
    ),
    categories: Optional[str] = Query(
        default="external,erc20",
        description="Comma-separated list of transfer categories: external (native ETH), erc20 (tokens), internal, erc721, erc1155.",
    ),
    max_count: int = Query(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of transfer items to return per request (1 - 1000).",
    ),
    page_key: Optional[str] = Query(
        default=None,
        description="Pagination cursor token to fetch the subsequent page of transfers.",
    ),
) -> TransferResponse:
    """Retrieve structured transfer records for a validated Ethereum wallet."""
    # 1. Validate Ethereum address format
    is_valid, validated_address_or_error = validate_ethereum_address(address)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_ETHEREUM_ADDRESS",
                "message": validated_address_or_error,
                "input_address": address,
            },
        )

    normalized_address = validated_address_or_error

    # 2. Parse category filters
    category_list: List[str] = []
    if categories:
        valid_cats = {c.value for c in TransferCategory}
        raw_cats = [c.strip().lower() for c in categories.split(",") if c.strip()]
        for c in raw_cats:
            if c in valid_cats:
                category_list.append(c)
    if not category_list:
        category_list = [TransferCategory.EXTERNAL.value, TransferCategory.ERC20.value]

    # 3. Query Alchemy Service
    service = AlchemyService()
    try:
        response = await service.get_wallet_transfers(
            address=normalized_address,
            direction=direction,
            categories=category_list,
            max_count=max_count,
            page_key=page_key,
        )
        return response

    except AlchemyConfigError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "CONFIGURATION_ERROR",
                "message": err.message,
            },
        )
    except AlchemyAuthError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "ALCHEMY_AUTH_ERROR",
                "message": err.message,
            },
        )
    except AlchemyRateLimitError as err:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": err.message,
            },
        )
    except AlchemyNetworkError as err:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error": "NETWORK_TIMEOUT",
                "message": err.message,
            },
        )
    except AlchemyError as err:
        raise HTTPException(
            status_code=err.status_code if err.status_code >= 400 else status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "ALCHEMY_API_ERROR",
                "message": err.message,
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred while processing transfer data.",
            },
        )

@router.get(
    "/{address}/analyze",
    response_model=CombinedAnalysisResponse,
    status_code=status.HTTP_200_OK,
    summary="Analyze Ethereum Wallet (Graph & Risk)",
    description="Retrieves multi-hop transfers and passes them to the AIML analytics module for graph features and risk scoring.",
)
async def analyze_wallet(
    address: str = Path(..., description="Target 42-character hex Ethereum address"),
    max_depth: int = Query(3, description="Maximum hop depth for tracing."),
    max_transfers_per_wallet: int = Query(25, description="Max transfers per wallet node."),
) -> CombinedAnalysisResponse:
    # 1. Validate
    is_valid, validated_address_or_error = validate_ethereum_address(address)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "INVALID_ETHEREUM_ADDRESS", "message": validated_address_or_error}
        )
    normalized_address = validated_address_or_error

    # 2. Trace
    tracer = MultiHopTracer()
    try:
        trace_result = await tracer.trace_wallet(
            root_address=normalized_address,
            max_depth=max_depth,
            max_transfers_per_wallet=max_transfers_per_wallet,
            categories=["external", "erc20"]
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "TRACE_FAILED", "message": str(exc)}
        )
    
    # 3. Analytics
    # Convert trace paths to dicts for the analytics service
    transfers = [p.model_dump(by_alias=False) for p in trace_result.paths]
    
    try:
        analysis = analyze_transaction_graph(
            root_wallet=normalized_address,
            transfers=transfers,
            vasp_directory=None,
            max_path_depth=max_depth
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": "ANALYTICS_FAILED", "message": str(exc)}
        )

    # 4. VASP Attribution — exact verified address matching from dataset
    graph_nodes = analysis.get("nodes", [])
    vasp_attribution = attribute_vasp_from_graph_nodes(
        graph_nodes=graph_nodes,
        blockchain=trace_result.blockchain or "ethereum"
    )
    # Fallback: if no match from nodes, try raw transfers
    if not vasp_attribution["identified"]:
        vasp_attribution = attribute_vasp_from_transfers(
            transfers=transfers,
            blockchain=trace_result.blockchain or "ethereum"
        )

    # 5. Construct response
    return CombinedAnalysisResponse(
        case={"root_wallet": analysis["root_wallet"], "blockchain": trace_result.blockchain, "network": trace_result.network},
        summary={
            "transactions_analyzed": analysis["transaction_count"],
            "wallets_discovered": analysis["wallet_count"],
            "max_hop": analysis["max_hop"]
        },
        transactions=transfers,
        graph={"nodes": analysis["nodes"], "edges": analysis["edges"]},
        risk_analysis={
            "risk_score": analysis["risk_score"],
            "risk_level": analysis["risk_level"],
            "risk_indicators": analysis["risk_indicators"],
            "risk_indicator_details": analysis["risk_indicator_details"]
        },
        vasp_attribution=vasp_attribution,
        known_entities=analysis["known_entities"],
        candidate_paths=analysis["paths"],
        wallet_features=analysis["wallet_features"],
        disclaimer=analysis["disclaimer"]
    )
@router.get(
    "/{address}/trace",
    response_model=TraceResponse,
    status_code=status.HTTP_200_OK,
    summary="Multi-Hop Ethereum Fund-Flow Tracing",
    description=(
        "Recursively traces outgoing fund-flow relationships from a starting suspect Ethereum wallet "
        "up to max_depth hops using Breadth-First Search (BFS). Discovers transaction paths, prevents "
        "infinite loops, handles native ETH and ERC-20 tokens, and computes traversal summary metrics."
    ),
    responses={
        400: {"model": ErrorResponse, "description": "Invalid Ethereum wallet address format."},
        429: {"model": ErrorResponse, "description": "Alchemy API rate limit exceeded."},
        500: {"model": ErrorResponse, "description": "Server configuration error (e.g., missing API key)."},
        502: {"model": ErrorResponse, "description": "Alchemy upstream API error or invalid authentication."},
        504: {"model": ErrorResponse, "description": "Gateway timeout connecting to Alchemy."},
    },
)
async def trace_wallet_fund_flow(
    address: str = Path(
        ...,
        description="Starting suspect Ethereum wallet address (e.g., 0xde0B295669a9FD93d5F28D9Ec85E40f4cb697BAe)",
    ),
    max_depth: int = Query(
        default=3,
        ge=1,
        le=5,
        description="Maximum hop depth for multi-hop graph exploration (1 to 5, default 3).",
    ),
    max_transfers_per_wallet: int = Query(
        default=25,
        ge=1,
        le=100,
        description="Maximum outgoing transfers to evaluate per wallet node (1 to 100, default 25).",
    ),
    categories: Optional[str] = Query(
        default="external,erc20",
        description="Comma-separated list of transfer categories: external (native ETH), erc20 (tokens), internal.",
    ),
) -> TraceResponse:
    """Trace outgoing multi-hop transaction trails from a starting suspect wallet."""
    # 1. Validate Ethereum address format
    is_valid, validated_address_or_error = validate_ethereum_address(address)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_ETHEREUM_ADDRESS",
                "message": validated_address_or_error,
                "input_address": address,
            },
        )

    normalized_address = validated_address_or_error

    # 2. Parse category filters
    category_list: List[str] = []
    if categories:
        valid_cats = {c.value for c in TransferCategory}
        raw_cats = [c.strip().lower() for c in categories.split(",") if c.strip()]
        for c in raw_cats:
            if c in valid_cats:
                category_list.append(c)
    if not category_list:
        category_list = [TransferCategory.EXTERNAL.value, TransferCategory.ERC20.value]

    # 3. Execute Multi-Hop BFS Tracing
    tracer = MultiHopTracer()
    try:
        response = await tracer.trace_wallet(
            root_address=normalized_address,
            max_depth=max_depth,
            max_transfers_per_wallet=max_transfers_per_wallet,
            categories=category_list,
        )
        return response

    except AlchemyConfigError as err:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "CONFIGURATION_ERROR",
                "message": err.message,
            },
        )
    except AlchemyAuthError as err:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "ALCHEMY_AUTH_ERROR",
                "message": err.message,
            },
        )
    except AlchemyRateLimitError as err:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": err.message,
            },
        )
    except AlchemyNetworkError as err:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail={
                "error": "NETWORK_TIMEOUT",
                "message": err.message,
            },
        )
    except AlchemyError as err:
        raise HTTPException(
            status_code=err.status_code if err.status_code >= 400 else status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "ALCHEMY_API_ERROR",
                "message": err.message,
            },
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_SERVER_ERROR",
                "message": f"An unexpected error occurred while executing multi-hop trace: {str(exc)}",
            },
        )

