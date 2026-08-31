function DetailsPanel({ title, onClose, children }) {
  return (
    <section className="panel details-panel">
      <header className="details-panel__header">
        <h2 className="panel__title">{title}</h2>
        {onClose ? (
          <button
            type="button"
            className="details-panel__close"
            onClick={onClose}
            aria-label="Close details"
          >
            ×
          </button>
        ) : null}
      </header>
      {children}
    </section>
  )
}

export default DetailsPanel
