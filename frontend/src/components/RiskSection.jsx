import RiskScore from './RiskScore'
import { getInvestigationRisk } from '../utils/investigationView'

function RiskSection({ investigation }) {
  return <RiskScore risk={getInvestigationRisk(investigation)} />
}

export default RiskSection
