import { useEffect, useState } from 'react'
import { generateInvestigationReport } from '../services/reportService'

function ReportButton({ investigation = null, disabled = false }) {
  const [status, setStatus] = useState('idle') // 'idle' | 'generating' | 'success' | 'error'
  const [errorMessage, setErrorMessage] = useState('')
  const [successMessage, setSuccessMessage] = useState('')

  const isGenerating = status === 'generating'
  const isDisabled = disabled || !investigation || isGenerating

  // Auto-dismiss success notification after 4 seconds
  useEffect(() => {
    if (status === 'success') {
      const timer = setTimeout(() => {
        setStatus('idle')
        setSuccessMessage('')
      }, 4000)
      return () => clearTimeout(timer)
    }
  }, [status])

  async function handleGenerateReport() {
    if (isDisabled || isGenerating) return

    setStatus('generating')
    setErrorMessage('')
    setSuccessMessage('')

    try {
      await generateInvestigationReport(investigation)
      setStatus('success')
      setSuccessMessage('Investigation report generated successfully.')
    } catch (err) {
      setStatus('error')
      setErrorMessage(
        err?.message || 'Unable to generate the investigation report. Please try again.'
      )
    }
  }

  function handleDismissError() {
    setStatus('idle')
    setErrorMessage('')
  }

  return (
    <section className="report-bar" aria-label="Investigation Report Export">
      <div className="report-bar__actions">
        <button
          type="button"
          className={`btn ${investigation ? 'btn--primary' : 'btn--secondary'} report-bar__btn`}
          disabled={isDisabled}
          aria-busy={isGenerating}
          onClick={handleGenerateReport}
        >
          {isGenerating ? (
            <>
              <span className="report-bar__spinner" aria-hidden="true" />
              <span>GENERATING REPORT...</span>
            </>
          ) : (
            <>
              <svg
                className="report-bar__icon"
                viewBox="0 0 20 20"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
                aria-hidden="true"
              >
                <path
                  d="M4 14.5V15.5C4 16.0523 4.44772 16.5 5 16.5H15C15.5523 16.5 16 16.0523 16 15.5V14.5M10 3.5V12.5M10 12.5L6.5 9M10 12.5L13.5 9"
                  stroke="currentColor"
                  strokeWidth="1.75"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span>DOWNLOAD INVESTIGATION REPORT</span>
            </>
          )}
        </button>

        {!investigation ? (
          <p className="report-bar__hint">
            Load an investigation to generate and export an official PDF report.
          </p>
        ) : null}
      </div>

      {status === 'success' && successMessage ? (
        <div className="report-bar__status report-bar__status--success" role="status" aria-live="polite">
          <svg
            className="report-bar__status-icon"
            viewBox="0 0 20 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              d="M16.6667 5L7.5 14.1667L3.33334 10"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          <span>{successMessage}</span>
        </div>
      ) : null}

      {status === 'error' && errorMessage ? (
        <div className="report-bar__status report-bar__status--error" role="alert" aria-live="assertive">
          <svg
            className="report-bar__status-icon"
            viewBox="0 0 20 20"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <circle cx="10" cy="10" r="7.5" stroke="currentColor" strokeWidth="1.75" />
            <path d="M10 6.5V10.5M10 13.5H10.01" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
          <span className="report-bar__status-text">{errorMessage}</span>
          <button
            type="button"
            className="report-bar__dismiss-btn"
            onClick={handleDismissError}
            aria-label="Dismiss error message"
          >
            Dismiss
          </button>
        </div>
      ) : null}
    </section>
  )
}

export default ReportButton
