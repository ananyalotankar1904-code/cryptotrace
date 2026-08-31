import { useMemo } from 'react'
import TransactionGraph from './TransactionGraph'
import { buildGraphFromBackend, buildGraphFromInvestigation } from '../utils/graphUtils'

function FundFlowPanel({
  investigation,
  loading,
  selectedTransaction = null,
  onSelectTransaction,
}) {
  const graph = useMemo(() => {
    if (!investigation) {
      return { nodes: [], edges: [], moneyPathNodeIds: [], moneyPathEdgeIds: [] }
    }
    // Use the backend pre-computed graph when available (real analysis),
    // otherwise fall back to the transaction-derived graph (demo mode).
    if (investigation._backendGraph) {
      return buildGraphFromBackend(investigation)
    }
    return buildGraphFromInvestigation(investigation)
  }, [investigation])

  return (
    <section className="panel panel--graph">
      <h2 className="panel__title">Fund Flow Analysis</h2>
      <p className="panel__hint">
        Directed graph of fund movement. Click a wallet or transaction for
        details.{investigation && !investigation.isDemo
          ? ' Data sourced from real Ethereum on-chain analysis.'
          : ' Drag nodes to rearrange.'}
      </p>

      {!investigation && !loading ? (
        <p className="panel__empty">
          Trace a wallet to load a fund-flow graph.
        </p>
      ) : (
        <TransactionGraph
          key={investigation?.queriedAddress || investigation?.suspectWallet || 'empty'}
          nodes={graph.nodes}
          edges={graph.edges}
          moneyPathNodeIds={graph.moneyPathNodeIds}
          moneyPathEdgeIds={graph.moneyPathEdgeIds}
          loading={loading}
          selectedTransaction={selectedTransaction}
          onSelectTransaction={onSelectTransaction}
        />
      )}
    </section>
  )
}

export default FundFlowPanel
