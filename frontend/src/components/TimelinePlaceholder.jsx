function TimelinePlaceholder({ investigation }) {
  return (
    <section className="panel">
      <h2 className="panel__title">Fund Movement Timeline</h2>
      <p className="panel__hint">
        Transaction events will appear here in chronological order.
      </p>
      {investigation ? (
        <p className="panel__empty">{investigation.timelineNote}</p>
      ) : (
        <p className="panel__empty">No timeline loaded.</p>
      )}
    </section>
  )
}

export default TimelinePlaceholder
