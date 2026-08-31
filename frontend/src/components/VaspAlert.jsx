import AddressDisplay from './AddressDisplay'
import { confidenceBand, confidencePercent, getVaspState } from '../utils/investigationView'

function Meter({ value, label }) {
  const width = Math.max(0, Math.min(100, value))
  return (
    <div
      className="meter"
      role="progressbar"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={100}
      aria-valuenow={width}
    >
      <span className="meter__fill" style={{ width: `${width}%` }} />
    </div>
  )
}

function statusMark(status) {
  const text = String(status || '')
  if (/known/i.test(text)) return `✓ ${text}`
  if (/verification|possible/i.test(text)) return `⚠ ${text}`
  return text || 'Unknown'
}

function VaspAlert({ vasp, path = [], hops }) {
  const state = getVaspState(vasp)

  if (state === 'none') {
    return (
      <section className="panel vasp-alert vasp-alert--none">
        <h2 className="panel__title">No known VASP identified</h2>
        <p className="panel__empty">
          No known exchange or VASP was identified in the currently traced path.
        </p>
        <p className="details-footnote">
          VASP identification indicates a potential service destination and does
          not by itself identify an individual or establish criminal wrongdoing.
        </p>
      </section>
    )
  }

  const percent = confidencePercent(vasp.confidence)
  const band = confidenceBand(percent)
  const hop = vasp.hop ?? vasp.finalDestinationHop
  const heading = state === 'possible' ? 'Possible VASP' : 'VASP identified'

  return (
    <section className={`panel vasp-alert vasp-alert--${state}`}>
      <h2 className="panel__title">{heading}</h2>
      <p className="vasp-alert__name">{vasp.name || 'Details unavailable'}</p>
      <p className="vasp-alert__type">{vasp.type || 'Exchange / VASP'}</p>
      <p className="vasp-alert__status">{statusMark(vasp.status)}</p>

      <p className="detail-row__label">Attribution confidence</p>
      {percent == null ? (
        <p className="panel__empty">Confidence unavailable.</p>
      ) : (
        <>
          <Meter value={percent} label="Attribution confidence" />
          <p className="vasp-alert__confidence">
            {percent}% · {band} confidence
          </p>
        </>
      )}

      {hop != null ? (
        <p className="vasp-alert__hop">
          VASP detected at hop {hop}
          {hops != null ? ` of ${hops}` : ''}
        </p>
      ) : null}

      {vasp.address ? (
        <div className="vasp-alert__address">
          <p className="detail-row__label">VASP address</p>
          <AddressDisplay address={vasp.address} />
        </div>
      ) : null}

      {path.length > 0 ? (
        <ol className="vasp-path" aria-label="Fund path">
          {path.map((node) => (
            <li key={node.address || node.label}>{node.label}</li>
          ))}
        </ol>
      ) : null}

      <p className="details-footnote">
        VASP identification indicates a potential service destination and does
        not by itself identify an individual or establish criminal wrongdoing.
      </p>
    </section>
  )
}

export default VaspAlert
