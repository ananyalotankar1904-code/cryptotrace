"""
End-to-End Pipeline Demo for Graph Analytics & Risk Layer
Project: Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges
"""

import json
import matplotlib.pyplot as plt
import networkx as nx
from graph_engine import BlockchainGraphBuilder
from analytics_service import analyze_transaction_graph
from mock_data import MOCK_ROOT_WALLET, MOCK_TRANSFERS, MOCK_VASP_DIRECTORY


def render_graph_image(graph: nx.MultiDiGraph, output_file: str = "transaction_graph_prototype.png"):
    """Visualizes the transaction graph with distinct entity color coding."""
    plt.figure(figsize=(11, 5), dpi=300)
    pos = nx.spring_layout(graph, seed=42, k=1.5)

    color_map = []
    labels = {}
    for node, data in graph.nodes(data=True):
        ntype = data.get("type")
        entity_type = data.get("entity_type")
        known_entity = data.get("known_entity")

        if ntype == "suspect":
            color_map.append("#E63946")  # Alert Red
            labels[node] = f"SUSPECT\n{node[:8]}..."
        elif entity_type == "KNOWN_VASP" or known_entity:
            color_map.append("#2A9D8F")  # VASP Emerald
            labels[node] = f"VASP: {known_entity or 'Exchange'}\n{node[:8]}..."
        else:
            color_map.append("#F4A261")  # Intermediary Orange
            labels[node] = f"HOP {data.get('hop', '?')}\n{node[:8]}..."

    nx.draw_networkx_nodes(graph, pos, node_color=color_map, node_size=3000, edgecolors="#1D3557", linewidths=1.5)
    nx.draw_networkx_labels(graph, pos, labels=labels, font_size=8, font_weight="bold")
    nx.draw_networkx_edges(graph, pos, arrows=True, arrowstyle="-|>", arrowsize=18, width=2.0, edge_color="#333333")

    edge_labels = {}
    for u, v, k, d in graph.edges(keys=True, data=True):
        edge_labels[(u, v)] = f"{d.get('value')} {d.get('asset')}"
    nx.draw_networkx_edge_labels(graph, pos, edge_labels=edge_labels, font_size=7)

    plt.title("Cryptocurrency Multi-Hop Fund Flow & VASP Attribution Graph", fontsize=12, fontweight="bold", pad=15)
    plt.axis("off")
    plt.tight_layout()
    plt.savefig(output_file, bbox_inches="tight")
    plt.close()
    print(f"[+] Saved graph visualization to: {output_file}")


def run_pipeline_demo():
    print("=" * 75)
    print("SIH BLOCKCHAIN FORENSIC PIPELINE: AI/ML + GRAPH ANALYTICS DEMO")
    print("=" * 75)

    # 1. Execute Unified Analytics Service
    print("\n[1] Running Analytics Service on Synthetic Transaction Ingestion Payload...")
    analysis_result = analyze_transaction_graph(
        root_wallet=MOCK_ROOT_WALLET,
        transfers=MOCK_TRANSFERS,
        vasp_directory=MOCK_VASP_DIRECTORY
    )

    print(f" -> Root Suspect Wallet: {analysis_result['root_wallet']}")
    print(f" -> Total Wallets (Nodes): {analysis_result['wallet_count']}")
    print(f" -> Total Transfers (Edges): {analysis_result['transaction_count']}")
    print(f" -> Max Hop Distance: {analysis_result['max_hop']} hops")
    print(f" -> Risk Score: {analysis_result['risk_score']} / 100 ({analysis_result['risk_level']})")

    print("\n[2] Risk Indicators (Why this score was assigned):")
    for ind in analysis_result["risk_indicators"]:
        print(f"    * {ind}")

    print("\n[3] Identified VASP Entities (Member 2 Intelligence Match):")
    for vasp in analysis_result["known_entities"]:
        print(f"    * {vasp['entity']} ({vasp['entity_type']}) at Hop {vasp['hop']} (Address: {vasp['address']})")

    print("\n[4] Discovered Candidate Paths:")
    for idx, path_data in enumerate(analysis_result["paths"], 1):
        print(f"    Path #{idx}: {' -> '.join(path_data['path'])} ({path_data['hops']} hops)")

    # 2. Render Graph Image
    builder = BlockchainGraphBuilder(MOCK_VASP_DIRECTORY)
    graph = builder.build_transaction_graph(MOCK_TRANSFERS, root_wallet=MOCK_ROOT_WALLET)
    render_graph_image(graph, "transaction_graph_prototype.png")

    # 3. Export JSON Payload for Member 6's Frontend
    with open("dashboard_sample_payload.json", "w") as f:
        json.dump(analysis_result, f, indent=2)
    print("[+] Exported Member 6 dashboard payload to: dashboard_sample_payload.json")
    print("\nPipeline execution completed successfully.")


if __name__ == "__main__":
    run_pipeline_demo()
