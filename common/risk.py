from typing import Any, List, Tuple

from pydantic import BaseModel

BetaParams = Tuple[Any, Any]  # TODO put in float
KumrParams = Tuple[float, float]

ExternalRiskInfo = List[Any]


class RiskParams(BaseModel):
    kumr_params: KumrParams
    beta_params: BetaParams


# recommenation risk of central authority (pls confirm @dju)
class RiskInput(BaseModel):
    # recommendation_risks: AgentInfoTable
    central_risk_info: RiskParams
