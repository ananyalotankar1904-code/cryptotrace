function DetailRow({ label, children }) {
  if (children == null || children === '') {
    return null
  }

  return (
    <div className="detail-row">
      <dt>{label}</dt>
      <dd>{children}</dd>
    </div>
  )
}

export default DetailRow
