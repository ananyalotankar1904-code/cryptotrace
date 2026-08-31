function FilterBar({
  searchTerm,
  selectedToken,
  selectedHop,
  selectedRisk,
  selectedVasp,
  timelineNewestFirst,
  tokens,
  hops,
  showVaspFilter,
  filteredCount,
  totalCount,
  onSearchChange,
  onTokenChange,
  onHopChange,
  onRiskChange,
  onVaspChange,
  onTimelineOrderChange,
  onClear,
  onRemoveChip,
}) {
  const chips = []
  if (searchTerm.trim()) {
    chips.push({ key: 'search', label: `Search: ${searchTerm.trim()}` })
  }
  if (selectedToken !== 'all') {
    chips.push({ key: 'token', label: selectedToken })
  }
  if (selectedHop !== 'all') {
    chips.push({ key: 'hop', label: `Hop ${selectedHop}` })
  }
  if (selectedRisk !== 'all') {
    chips.push({ key: 'risk', label: `${selectedRisk} risk` })
  }
  if (selectedVasp === 'vasp') {
    chips.push({ key: 'vasp', label: 'VASP transactions' })
  }

  return (
    <div className="filter-bar">
      <label className="filter-field filter-field--search">
        <span>Search</span>
        <input
          type="search"
          value={searchTerm}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Search wallet address or transaction hash..."
        />
      </label>

      <label className="filter-field">
        <span>Token</span>
        <select
          value={selectedToken}
          onChange={(event) => onTokenChange(event.target.value)}
        >
          <option value="all">All Tokens</option>
          {tokens.map((token) => (
            <option key={token} value={token}>
              {token}
            </option>
          ))}
        </select>
      </label>

      <label className="filter-field">
        <span>Hop</span>
        <select
          value={selectedHop}
          onChange={(event) => onHopChange(event.target.value)}
        >
          <option value="all">All Hops</option>
          {hops.map((hop) => (
            <option key={hop} value={String(hop)}>
              Hop {hop}
            </option>
          ))}
        </select>
      </label>

      <label className="filter-field">
        <span>Risk</span>
        <select
          value={selectedRisk}
          onChange={(event) => onRiskChange(event.target.value)}
        >
          <option value="all">All</option>
          <option value="Low">Low</option>
          <option value="Medium">Medium</option>
          <option value="High">High</option>
          <option value="Critical">Critical</option>
        </select>
      </label>

      {showVaspFilter ? (
        <label className="filter-field">
          <span>VASP</span>
          <select
            value={selectedVasp}
            onChange={(event) => onVaspChange(event.target.value)}
          >
            <option value="all">All</option>
            <option value="vasp">VASP Transactions</option>
          </select>
        </label>
      ) : null}

      <label className="filter-field">
        <span>Timeline sort</span>
        <select
          value={timelineNewestFirst ? 'newest' : 'oldest'}
          onChange={(event) => onTimelineOrderChange(event.target.value === 'newest')}
        >
          <option value="oldest">Oldest First</option>
          <option value="newest">Newest First</option>
        </select>
      </label>

      <button type="button" className="btn btn--secondary" onClick={onClear}>
        CLEAR FILTERS
      </button>

      <p className="filter-count">
        Showing {filteredCount} of {totalCount} transactions
      </p>

      {chips.length > 0 ? (
        <div className="filter-chips" aria-label="Active filters">
          <span className="filter-chips__label">Active filters:</span>
          {chips.map((chip) => (
            <button
              key={chip.key}
              type="button"
              className="filter-chip"
              onClick={() => onRemoveChip(chip.key)}
            >
              {chip.label} ×
            </button>
          ))}
        </div>
      ) : null}
    </div>
  )
}

export default FilterBar
