import { useState } from 'react'
import InvestigationSummary from '../components/InvestigationSummary'
import Disclaimer from '../components/Disclaimer'
import FundFlowPanel from '../components/FundFlowPanel'
import Navbar from '../components/Navbar'
import PageHeader from '../components/PageHeader'
import ReportButton from '../components/ReportButton'
import RiskSection from '../components/RiskSection'
import SummaryCards from '../components/SummaryCards'
import TransactionExplorer from '../components/TransactionExplorer'
import VaspSection from '../components/VaspSection'
import WalletSearch from '../components/WalletSearch'
import { DEMO_WALLET, traceWallet } from '../services/api'
import AddressDisplay from '../components/AddressDisplay'

function Dashboard() {
  const [investigation, setInvestigation] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [selectedTransaction, setSelectedTransaction] = useState(null)

  async function loadInvestigation(address) {
    if (!address || !address.trim()) {
      setError('Please enter a wallet address.')
      return
    }

    setError('')
    setSelectedTransaction(null)
    setLoading(true)

    try {
      const result = await traceWallet(address)
      setInvestigation(result)
    } catch (err) {
      setInvestigation(null)
      setError(err.message || 'Unable to load investigation.')
    } finally {
      setLoading(false)
    }
  }

  function handleDemo() {
    loadInvestigation(DEMO_WALLET)
  }

  return (
    <div className="app-shell">
      <Navbar />
      <main className="app-main">
        <PageHeader />
        <WalletSearch
          onTrace={loadInvestigation}
          onDemo={handleDemo}
          loading={loading}
          error={error}
        />

        {loading ? (
          <p className="loading-banner" role="status">
            Tracing wallet activity on Ethereum Mainnet… This may take a few seconds.
          </p>
        ) : null}

        {investigation ? (
          <>
            <section className="subject-bar">
              <p className="subject-bar__label">Wallet under investigation</p>
              <p className="subject-bar__chain">{investigation.chain}</p>
              <AddressDisplay address={investigation.suspectWallet} />
              {investigation.isDemo ? (
                <span className="badge">Mock data</span>
              ) : null}
            </section>

            <SummaryCards investigation={investigation} />

            <FundFlowPanel
              investigation={investigation}
              loading={loading}
              selectedTransaction={selectedTransaction}
              onSelectTransaction={setSelectedTransaction}
            />

            <InvestigationSummary investigation={investigation} />

            <div className="two-column">
              <VaspSection
                vasp={investigation.vasp}
                path={investigation.path}
                hops={investigation.hops}
              />
              <RiskSection investigation={investigation} />
            </div>

            <ReportButton investigation={investigation} disabled={loading} />

            <TransactionExplorer
              investigation={investigation}
              selectedTransaction={selectedTransaction}
              onSelectTransaction={setSelectedTransaction}
            />
          </>
        ) : (
          <>
            <FundFlowPanel investigation={null} loading={loading} />
            <p className="empty-dashboard">
              No investigation loaded. Enter an address or start the demo to
              populate the dashboard.
            </p>
            <ReportButton investigation={null} disabled />
          </>
        )}

        <Disclaimer />
      </main>
    </div>
  )
}

export default Dashboard
