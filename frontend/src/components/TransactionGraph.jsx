import { useEffect, useMemo, useRef, useState } from 'react'
import cytoscape from 'cytoscape'
import DetailsPanel from './DetailsPanel'
import TransactionDetails from './TransactionDetails'
import WalletDetails from './WalletDetails'

const graphStyle = [
  {
    selector: 'node',
    style: {
      'background-color': '#1b2433',
      'border-width': 2,
      'border-color': '#6b7c94',
      color: '#e8eef7',
      label: 'data(displayLabel)',
      'font-size': 10,
      'text-wrap': 'wrap',
      'text-valign': 'center',
      'text-halign': 'center',
      'text-max-width': 86,
      'line-height': 1.2,
      width: 58,
      height: 58,
      shape: 'ellipse',
    },
  },
  {
    selector: 'node[type = "suspect"]',
    style: {
      width: 78,
      height: 78,
      'background-color': '#243044',
      'border-width': 3,
      'border-color': '#c9a227',
      'font-weight': 700,
    },
  },
  {
    selector: 'node[type = "exchange"]',
    style: {
      shape: 'round-rectangle',
      width: 92,
      height: 52,
      'background-color': '#14301f',
      'border-color': '#5d9b73',
      'border-width': 3,
    },
  },
  {
    selector: 'node[type = "contract"]',
    style: {
      shape: 'diamond',
      width: 64,
      height: 64,
      'background-color': '#2a2230',
      'border-color': '#8d73a8',
      'border-width': 2,
    },
  },
  {
    selector: 'edge',
    style: {
      width: 2,
      'line-color': '#3d4f66',
      'target-arrow-color': '#3d4f66',
      'target-arrow-shape': 'triangle',
      'curve-style': 'bezier',
      'control-point-step-size': 36,
      label: 'data(label)',
      'font-size': 9,
      color: '#8b9bb4',
      'text-background-color': '#121924',
      'text-background-opacity': 0.9,
      'text-background-padding': 2,
      'arrow-scale': 1.1,
    },
  },
  {
    selector: '.dimmed',
    style: {
      opacity: 0.22,
    },
  },
  {
    selector: 'node.path-active',
    style: {
      'border-width': 4,
      'border-color': '#e0c36a',
    },
  },
  {
    selector: 'edge.path-active',
    style: {
      width: 4,
      'line-color': '#c9a227',
      'target-arrow-color': '#c9a227',
      color: '#e8eef7',
    },
  },
  {
    selector: 'edge.externally-selected',
    style: {
      width: 5,
      'line-color': '#4a91bd',
      'target-arrow-color': '#4a91bd',
      color: '#e8eef7',
    },
  },
  {
    selector: ':selected',
    style: {
      'border-color': '#4a91bd',
      'line-color': '#4a91bd',
      'target-arrow-color': '#4a91bd',
    },
  },
]

function toCyElements(nodes, edges) {
  return [
    ...nodes.map((node) => ({ data: { ...node } })),
    ...edges.map((edge) => ({ data: { ...edge } })),
  ]
}

function layoutOptions() {
  return {
    name: 'breadthfirst',
    directed: true,
    padding: 28,
    spacingFactor: 1.45,
    avoidOverlap: true,
    animate: false,
  }
}

function TransactionGraph({
  nodes = [],
  edges = [],
  moneyPathNodeIds = [],
  moneyPathEdgeIds = [],
  loading = false,
  selectedTransaction = null,
  onSelectTransaction,
}) {
  const containerRef = useRef(null)
  const cyRef = useRef(null)
  const [pathOn, setPathOn] = useState(false)
  const [selectedWallet, setSelectedWallet] = useState(null)
  const [internalTransaction, setInternalTransaction] = useState(null)
  const [tooltip, setTooltip] = useState(null)
  const isControlled = typeof onSelectTransaction === 'function'
  const activeTransaction = isControlled ? selectedTransaction : internalTransaction
  const nodesRef = useRef(nodes)
  const edgesRef = useRef(edges)
  const onSelectTransactionRef = useRef(onSelectTransaction)

  useEffect(() => {
    nodesRef.current = nodes
    edgesRef.current = edges
    onSelectTransactionRef.current = onSelectTransaction
  }, [nodes, edges, onSelectTransaction])

  const graphKey = useMemo(() => {
    const nodeKey = nodes.map((node) => node.id).join('|')
    const edgeKey = edges.map((edge) => edge.id).join('|')
    return `${nodeKey}::${edgeKey}`
  }, [nodes, edges])

  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) {
      return undefined
    }

    const cy = cytoscape({
      container: containerRef.current,
      elements: toCyElements(nodes, edges),
      style: graphStyle,
      layout: layoutOptions(),
      minZoom: 0.35,
      maxZoom: 2.4,
      wheelSensitivity: 0.25,
      pixelRatio: 'auto',
    })

    cyRef.current = cy

    cy.ready(() => {
      cy.resize()
      cy.fit(undefined, 28)
    })

    cy.on('tap', 'node', (event) => {
      const id = event.target.id()
      const wallet = nodesRef.current.find((node) => node.id === id)
      setSelectedWallet(wallet || { missing: true })
      if (typeof onSelectTransactionRef.current === 'function') {
        onSelectTransactionRef.current(null)
      } else {
        setInternalTransaction(null)
      }
    })

    cy.on('tap', 'edge', (event) => {
      const id = event.target.id()
      const transaction = edgesRef.current.find((edge) => edge.id === id)
      setSelectedWallet(null)
      if (typeof onSelectTransactionRef.current === 'function') {
        onSelectTransactionRef.current(transaction || { missing: true })
      } else {
        setInternalTransaction(transaction || { missing: true })
      }
    })

    cy.on('tap', (event) => {
      if (event.target === cy) {
        setSelectedWallet(null)
        if (typeof onSelectTransactionRef.current === 'function') {
          onSelectTransactionRef.current(null)
        } else {
          setInternalTransaction(null)
        }
        cy.elements().unselect()
      }
    })

    cy.on('mouseover', 'edge', (event) => {
      const data = event.target.data()
      const pos = event.renderedPosition
      setTooltip({
        x: pos.x,
        y: pos.y,
        text: `${data.amount} ${data.token} · Hop ${data.hop}`,
      })
    })

    cy.on('mouseout', 'edge', () => {
      setTooltip(null)
    })

    const observer = new ResizeObserver(() => {
      cy.resize()
    })
    observer.observe(containerRef.current)

    return () => {
      observer.disconnect()
      cy.destroy()
      cyRef.current = null
    }
  }, [graphKey, nodes, edges])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy || cy.destroyed()) {
      return
    }

    cy.elements().removeClass('dimmed path-active')

    if (!pathOn) {
      return
    }

    cy.elements().addClass('dimmed')
    moneyPathNodeIds.forEach((id) => {
      cy.getElementById(id).removeClass('dimmed').addClass('path-active')
    })
    moneyPathEdgeIds.forEach((id) => {
      cy.getElementById(id).removeClass('dimmed').addClass('path-active')
    })
  }, [pathOn, moneyPathNodeIds, moneyPathEdgeIds, graphKey])

  useEffect(() => {
    const cy = cyRef.current
    if (!cy || cy.destroyed()) {
      return
    }

    cy.edges().removeClass('externally-selected')

    if (!activeTransaction) {
      return
    }

    const targetId = activeTransaction.id
      ? (String(activeTransaction.id).startsWith('tx-')
          ? activeTransaction.id
          : `tx-${activeTransaction.id}`)
      : null

    let edge = targetId ? cy.getElementById(targetId) : null
    if (!edge || edge.length === 0) {
      const src = activeTransaction.source || activeTransaction.from
      const tgt = activeTransaction.target || activeTransaction.to
      if (src && tgt) {
        edge = cy
          .edges()
          .filter((e) => e.data('source') === src && e.data('target') === tgt)
      }
    }

    if (edge && edge.length > 0) {
      edge.addClass('externally-selected')
      setSelectedWallet(null)
    }
  }, [activeTransaction, graphKey])

  function getCy() {
    const cy = cyRef.current
    if (!cy || cy.destroyed()) {
      return null
    }
    return cy
  }

  function zoomBy(factor) {
    const cy = getCy()
    if (!cy) {
      return
    }
    cy.zoom({
      level: cy.zoom() * factor,
      renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 },
    })
  }

  function fitGraph() {
    const cy = getCy()
    if (!cy) {
      return
    }
    cy.fit(undefined, 28)
  }

  function resetGraph() {
    const cy = getCy()
    if (!cy) {
      return
    }
    cy.layout(layoutOptions()).run()
    cy.fit(undefined, 28)
  }

  function closeDetails() {
    setSelectedWallet(null)
    if (isControlled) {
      onSelectTransaction(null)
    } else {
      setInternalTransaction(null)
    }
    const cy = getCy()
    if (cy) {
      cy.elements().unselect()
      cy.edges().removeClass('externally-selected')
    }
  }

  if (loading) {
    return (
      <p className="panel__empty" role="status">
        Building transaction graph...
      </p>
    )
  }

  if (!nodes.length) {
    return (
      <p className="panel__empty">
        No transaction data available for visualization.
      </p>
    )
  }

  return (
    <div className="graph-shell">
      <div className="graph-toolbar">
        <div className="graph-toolbar__group" aria-label="Graph controls">
          <button type="button" className="graph-ctrl" onClick={() => zoomBy(1.2)}>
            +
          </button>
          <button type="button" className="graph-ctrl" onClick={() => zoomBy(1 / 1.2)}>
            −
          </button>
          <button type="button" className="graph-ctrl" onClick={fitGraph}>
            FIT
          </button>
          <button type="button" className="graph-ctrl" onClick={resetGraph}>
            RESET
          </button>
        </div>
        <button
          type="button"
          className={`btn btn--secondary graph-path-btn ${pathOn ? 'is-active' : ''}`}
          onClick={() => setPathOn((value) => !value)}
        >
          {pathOn ? 'CLEAR MONEY PATH' : 'HIGHLIGHT MONEY PATH'}
        </button>
      </div>

      <ul className="graph-legend" aria-label="Graph legend">
        <li>
          <span className="legend-mark legend-mark--suspect" />
          Suspect Wallet
        </li>
        <li>
          <span className="legend-mark legend-mark--wallet" />
          Wallet
        </li>
        <li>
          <span className="legend-mark legend-mark--exchange" />
          Exchange / VASP
        </li>
        <li>
          <span className="legend-mark legend-mark--contract" />
          Smart Contract
        </li>
        <li>
          <span className="legend-mark legend-mark--edge" />
          Transaction
        </li>
      </ul>

      <div className="graph-layout">
        <div className="graph-canvas-wrap">
          <div ref={containerRef} className="graph-canvas" />
          {tooltip ? (
            <div
              className="graph-tooltip"
              style={{ left: tooltip.x, top: tooltip.y }}
            >
              {tooltip.text}
            </div>
          ) : null}
        </div>
        <div className="graph-details">
          {activeTransaction ? (
            <TransactionDetails
              transaction={
                activeTransaction.missing ? {} : activeTransaction
              }
              onClose={closeDetails}
            />
          ) : selectedWallet ? (
            <WalletDetails
              wallet={selectedWallet.missing ? {} : selectedWallet}
              onClose={closeDetails}
            />
          ) : (
            <DetailsPanel title="Select an item">
              <p className="panel__empty">
                Click a wallet or transaction in the graph to view detailed
                information.
              </p>
            </DetailsPanel>
          )}
        </div>
      </div>
    </div>
  )
}

export default TransactionGraph
