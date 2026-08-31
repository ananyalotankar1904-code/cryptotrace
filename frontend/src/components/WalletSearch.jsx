import { useState } from 'react'
import { DEMO_WALLET, NO_VASP_DEMO_WALLET, POSSIBLE_VASP_DEMO_WALLET } from '../services/api'

function WalletSearch({
  onTrace,
  onDemo,
  loading,
  error,
}) {
  const [address, setAddress] = useState('')

  function handleSubmit(event) {
    event.preventDefault()
    onTrace(address)
  }

  return (
    <section className="panel search-panel">
      <h2 className="panel__title">Investigate a Wallet</h2>
      <p className="panel__hint">
        Enter a wallet address to load a demonstration investigation. No live
        blockchain lookup is performed in this phase.
      </p>

      <form className="search-form" onSubmit={handleSubmit}>
        <label className="sr-only" htmlFor="wallet-address">
          Wallet address
        </label>
        <input
          id="wallet-address"
          className="search-form__input"
          type="text"
          value={address}
          onChange={(event) => setAddress(event.target.value)}
          placeholder="Enter Ethereum or Polygon wallet address"
          autoComplete="off"
          spellCheck="false"
          disabled={loading}
        />
        <button className="btn btn--primary" type="submit" disabled={loading}>
          {loading ? 'TRACING…' : 'TRACE WALLET'}
        </button>
      </form>

      {error ? <p className="search-form__error">{error}</p> : null}

      <button
        type="button"
        className="btn btn--link"
        onClick={onDemo}
        disabled={loading}
      >
        Try Demo Investigation
      </button>

      <p className="search-form__demo-hint">
        Demo (VASP identified): <code>{DEMO_WALLET}</code>
      </p>
      <p className="search-form__demo-hint">
        Demo (no VASP): <code>{NO_VASP_DEMO_WALLET}</code>
      </p>
      <p className="search-form__demo-hint">
        Demo (possible VASP): <code>{POSSIBLE_VASP_DEMO_WALLET}</code>
      </p>
    </section>
  )
}

export default WalletSearch
