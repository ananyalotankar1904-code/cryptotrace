import { useMemo, useState } from 'react'
import FilterBar from './FilterBar'
import TransactionTable from './TransactionTable'
import TransactionTimeline from './TransactionTimeline'
import {
  filterTransactions,
  sortTransactions,
  toDetailsTransaction,
  uniqueHops,
  uniqueTokens,
} from '../utils/transactionView'

const defaultFilters = {
  searchTerm: '',
  selectedToken: 'all',
  selectedHop: 'all',
  selectedRisk: 'all',
  selectedVasp: 'all',
}

function TransactionExplorer({
  investigation,
  selectedTransaction,
  onSelectTransaction,
}) {
  const [filters, setFilters] = useState(defaultFilters)
  const [sortField, setSortField] = useState('timestamp')
  const [sortDirection, setSortDirection] = useState('asc')
  const [timelineNewestFirst, setTimelineNewestFirst] = useState(false)

  const transactions = useMemo(
    () => investigation?.transactions || [],
    [investigation],
  )
  const vaspAddress = investigation.vasp?.address
  const tokens = useMemo(() => uniqueTokens(transactions), [transactions])
  const hops = useMemo(() => uniqueHops(transactions), [transactions])

  const filtered = useMemo(
    () => filterTransactions(transactions, filters, vaspAddress),
    [transactions, filters, vaspAddress],
  )

  const tableRows = useMemo(
    () => sortTransactions(filtered, sortField, sortDirection),
    [filtered, sortField, sortDirection],
  )

  const timelineRows = useMemo(
    () => sortTransactions(filtered, 'timestamp', timelineNewestFirst ? 'desc' : 'asc'),
    [filtered, timelineNewestFirst],
  )

  function clearFilters() {
    setFilters(defaultFilters)
    setSortField('timestamp')
    setSortDirection('asc')
    setTimelineNewestFirst(false)
  }

  function removeChip(key) {
    if (key === 'search') setFilters((prev) => ({ ...prev, searchTerm: '' }))
    if (key === 'token') setFilters((prev) => ({ ...prev, selectedToken: 'all' }))
    if (key === 'hop') setFilters((prev) => ({ ...prev, selectedHop: 'all' }))
    if (key === 'risk') setFilters((prev) => ({ ...prev, selectedRisk: 'all' }))
    if (key === 'vasp') setFilters((prev) => ({ ...prev, selectedVasp: 'all' }))
  }

  function handleSort(field) {
    if (sortField === field) {
      setSortDirection((prev) => (prev === 'asc' ? 'desc' : 'asc'))
      return
    }
    setSortField(field)
    setSortDirection(field === 'timestamp' ? 'asc' : 'desc')
  }

  function handleSelect(tx) {
    onSelectTransaction(toDetailsTransaction(tx, investigation.hops))
    document.querySelector('.graph-details')?.scrollIntoView({
      behavior: 'smooth',
      block: 'nearest',
    })
  }

  return (
    <div className="tx-explorer">
      <FilterBar
        searchTerm={filters.searchTerm}
        selectedToken={filters.selectedToken}
        selectedHop={filters.selectedHop}
        selectedRisk={filters.selectedRisk}
        selectedVasp={filters.selectedVasp}
        timelineNewestFirst={timelineNewestFirst}
        tokens={tokens}
        hops={hops}
        showVaspFilter={Boolean(vaspAddress)}
        filteredCount={filtered.length}
        totalCount={transactions.length}
        onSearchChange={(value) => setFilters((prev) => ({ ...prev, searchTerm: value }))}
        onTokenChange={(value) => setFilters((prev) => ({ ...prev, selectedToken: value }))}
        onHopChange={(value) => setFilters((prev) => ({ ...prev, selectedHop: value }))}
        onRiskChange={(value) => setFilters((prev) => ({ ...prev, selectedRisk: value }))}
        onVaspChange={(value) => setFilters((prev) => ({ ...prev, selectedVasp: value }))}
        onTimelineOrderChange={setTimelineNewestFirst}
        onClear={clearFilters}
        onRemoveChip={removeChip}
      />

      <TransactionTimeline
        transactions={timelineRows}
        selectedId={selectedTransaction?.id}
        onSelect={handleSelect}
      />

      <TransactionTable
        transactions={tableRows}
        selectedId={selectedTransaction?.id}
        onSelect={handleSelect}
        sortField={sortField}
        sortDirection={sortDirection}
        onSort={handleSort}
        onClearFilters={clearFilters}
      />
    </div>
  )
}

export default TransactionExplorer
