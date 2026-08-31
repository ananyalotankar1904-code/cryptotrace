import AddressDisplay from './AddressDisplay'
import { formatTimestamp } from '../utils/formatTimestamp'
import { displayRiskLevel, riskTone } from '../utils/riskDisplay'

function SortButton({ field, currentField, direction, onSort, children }) {
  const active = currentField === field
  const arrow = active ? (direction === 'asc' ? ' ↑' : ' ↓') : ''

  return (
    <button
      type="button"
      className={`sort-btn ${active ? 'is-active' : ''}`}
      onClick={() => onSort(field)}
    >
      {children}
      {arrow}
    </button>
  )
}

function TransactionTable({
  transactions,
  selectedId,
  onSelect,
  sortField,
  sortDirection,
  onSort,
  onClearFilters,
}) {
  return (
    <section className="panel">
      <h2 className="panel__title">Transaction History</h2>
      <p className="panel__hint">
        Demonstration transaction subset. Click a row to inspect details in the
        graph panel. Addresses are shortened; use Copy for the full value.
      </p>

      {transactions.length === 0 ? (
        <div className="empty-filter-state">
          <p className="empty-filter-state__title">No transactions found</p>
          <p className="panel__empty">
            No transactions match the current filters.
          </p>
          <button type="button" className="btn btn--secondary" onClick={onClearFilters}>
            CLEAR FILTERS
          </button>
        </div>
      ) : (
        <div className="table-wrap">
          <table className="data-table">
            <thead>
              <tr>
                <th>#</th>
                <th>
                  <SortButton
                    field="timestamp"
                    currentField={sortField}
                    direction={sortDirection}
                    onSort={onSort}
                  >
                    Timestamp
                  </SortButton>
                </th>
                <th>From</th>
                <th>To</th>
                <th>
                  <SortButton
                    field="amount"
                    currentField={sortField}
                    direction={sortDirection}
                    onSort={onSort}
                  >
                    Amount
                  </SortButton>
                </th>
                <th>Token</th>
                <th>
                  <SortButton
                    field="hop"
                    currentField={sortField}
                    direction={sortDirection}
                    onSort={onSort}
                  >
                    Hop
                  </SortButton>
                </th>
                <th>
                  <SortButton
                    field="risk"
                    currentField={sortField}
                    direction={sortDirection}
                    onSort={onSort}
                  >
                    Risk
                  </SortButton>
                </th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {transactions.map((tx) => {
                const when = formatTimestamp(tx.timestamp)
                const risk = displayRiskLevel(tx.risk)
                const selected =
                  selectedId === `tx-${tx.id}` ||
                  selectedId === String(tx.id) ||
                  selectedId === tx.id

                return (
                  <tr
                    key={tx.id}
                    className={`data-table__row ${selected ? 'is-selected' : ''}`}
                    onClick={() => onSelect(tx)}
                    tabIndex={0}
                    onKeyDown={(event) => {
                      if (event.key === 'Enter' || event.key === ' ') {
                        event.preventDefault()
                        onSelect(tx)
                      }
                    }}
                  >
                    <td>{tx.id}</td>
                    <td>
                      {when ? (
                        <>
                          {when.date}
                          {when.time ? (
                            <>
                              <br />
                              {when.time}
                            </>
                          ) : null}
                        </>
                      ) : (
                        tx.timestamp
                      )}
                    </td>
                    <td>
                      <AddressDisplay address={tx.from} />
                    </td>
                    <td>
                      <AddressDisplay address={tx.to} />
                    </td>
                    <td>{tx.amount}</td>
                    <td>{tx.token}</td>
                    <td>{tx.hop}</td>
                    <td>
                      {risk ? (
                        <span className={`risk-chip risk-chip--${riskTone(risk)}`}>
                          {risk}
                        </span>
                      ) : (
                        '—'
                      )}
                    </td>
                    <td>{tx.status || '—'}</td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}

export default TransactionTable
