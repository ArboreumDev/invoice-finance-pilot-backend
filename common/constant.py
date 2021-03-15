from common.risk import RiskParams

# ==================== LOG PARAMETERS ======================
# anyhting >0 will result in printed output
# TODO: Make logging to file optional
LOG_LEVEL = 1
LOG_FILE = "./risk.log"
TEST_LOG = "./test.log"

# ==================== RISK MODULE PARAMETERS ======================
# global variable trading off direct vs indirect reports of risk
W = 1
# scaling factor set by the network
GAMMA = 1
MAX_RECURSION_DEPTH = 10

# =================== DEFAULT VALUES FOR TESTING ==================
DEFAULT_PRECISION_MONEY = 2
DEFAULT_PRECISION_MATH_OPERATIONS = DEFAULT_PRECISION_MONEY * 3
DEFAULT_REPUTATION_RISK_PRIOR = [2, 1]  # changed name from UNKNOWN_RISK_PARAMS
DEFAULT_UNKNOWN_RISK_PARAMS = [2, 1]  # needed cause it breaks tests otherwise
DEFAULT_CENTRAL_SOURCE_REPUTATION = [15, 1]  # reputation of central source
DEFAULT_RECOMMENDATION_RISK = RiskParams(
    beta_params=[16.949847030201536, 8.553278883166213],
    kumr_params=[16.949847030201536, 8.553278883166213],
)
DEFAULT_RISK_FREE_APR = 0.075  # risk free rate
# this is the repayment probability=1-default probability
# ergo why i changed name from DEFAULT_RISK_FREE_DEFAULT_PROBABILITY
DEFAULT_RISK_FREE_REPAY_PROBABILITY = [
    100,
    1,
]
DEFAULT_DISCOUNT_APR = 0  # 0.055  # Discount Rate
DEFAULT_RISK_AVERSION = 0.05
DEFAULT_LOAN_TENOR = 6
DEFAULT_MAXIMUM_LOAN = 100000
DEFAULT_PENALTY_APR = 0.055  # penalty on late payments (not principal which is why this is way low
DEFAULT_SUPPORTER_LAG = 1  # periods supporter must wait to receive funds
DEFAULT_ANNUAL_COMPOUND_PERIODS = 12  # required as time is relative to number of compounding periods per year
DEFAULT_SUPPORTER_APR_DELTA = 1.1  # multiple that supporters enjoy of loan APR received by corpus
DEFAULT_SUPPORTER_MIN_DIRECT_LEND = 0.2  # min amount supporters directly lend to loan
DEFAULT_CORPUS_MIN_DIRECT_LEND = 0.2  # min amount corpus directly lends to laon
DEFUALT_MIN_COLLATERAL_FOR_CORPUS = 0  # min collateral required by corpus
DEFAULT_MAX_CORPUS_CASH_IN_ONE_LOAN = 0.25  # maximum cash corpus allows to go to any one loan
DEFAULT_MAX_CORPUS_PTFL_PCT_REPURCHASE = 0.1  # maximum amount corpus can repurchase of its portfolio from supporters
DEFAULT_MAX_SALARY_MULTIPLE_BORROWABLE = 3  # maximum of monthly salary borrowable by borrower
DEFAULT_CORPUS_APR_LIMITS = [0.12, 0.22]  # min and max APRs allowed for borrower
DEFAULT_LOAN_MIN_RATE = 10
DEFAULT_LOAN_MAX_RATE = 20

# =================== TYPES & Classes =============================
TRUSTOR = "trustor"
TRUSTEE = "trustee"


# =================== AUTHENTICATION =============================JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_TIME_MINUTES = 60 * 24 * 5

# ENDPOINT DESCRIPTIONS
TOKEN_DESCRIPTION = "It checks username and password if they are true, it returns JWT token to you."

# TODO load from dotenv
JWT_SECRET_KEY = "OHOc07e154e8067407c909be11132e7d1bcee77542afd6c26ba613e2ffd9c3375ea"

# DUMMY DB
USER_DB = {
    # pw = (get_hashed_password("rcArboreumTesting"))
    "rc_backend": {"hashed_password": "$2b$12$IpU.KSMJCELs5UOlOYnTUO80YBdXKFqR.vbKbGSJ/RcP4niC4ON5C", "role": "rc"},
}

USERS = list(USER_DB.keys())

