from enum import Enum, IntEnum
from typing import Dict, List, Set

APP_NAME = "SpendyWise"
APP_VERSION = "1.0.0"
API_VERSION = "v1"
GRPC_VERSION = "1.0"

DEFAULT_ENVIRONMENT = "development"
SUPPORTED_ENVIRONMENTS = ["development", "staging", "production"]


# gRPC config
DEFAULT_GRPC_PORT = 50051
MAX_WORKERS = 10
GRPC_MAX_MESSAGE_SIZE = 4 * 1024 * 1024  # 4MB
GRPC_KEEPALIVE_TIME_MS = 30000
GRPC_KEEPALIVE_TIMEOUT_MS = 5000


DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100
DEFAULT_TIMEOUT_SECONDS = 30
MAX_QUERY_LIMIT = 1000

# Authentication & Security
JWT_ALGORITHM = "HS256"
JWT_ACCESS_TOKEN_EXPIRE_MINUTES = 30
JWT_REFRESH_TOKEN_EXPIRE_DAYS = 7
PASSWORD_MIN_LENGTH = 6  # Simplified for mobile users
MAX_LOGIN_ATTEMPTS = 3  # Reduced for simplicity
SESSION_TIMEOUT_MINUTES = 60

# Supabase Auth Configuration 
SUPABASE_AUTH_SCHEMA = "auth"
SUPABASE_AUTH_USERS_TABLE = "users"
USER_METADATA_FIELDS = ["name", "phone_number", "date_of_birth"]
APP_METADATA_FIELDS = ["role", "subscription_tier", "onboarding_completed"]


# Currency & Localization
DEFAULT_CURRENCY = "VND"
SUPPORTED_CURRENCIES = ["VND", "USD", "EUR", "JPY", "GBP", "AUD", "CAD"]
DEFAULT_LOCALE = "vi_VN"
SUPPORTED_LOCALES = ["vi_VN", "en_US", "en_GB"]

# Financial Limits 
MAX_TRANSACTION_AMOUNT = 3_000_000  # 3M VND
MIN_TRANSACTION_AMOUNT = 5_000  # 5K VND 
MAX_BUDGET_AMOUNT = 100_000_000
MAX_SAVINGS_GOAL_AMOUNT = 50_000_000  # 50M VND savings goal 

# AI & ML Configuration 
AI_RESPONSE_MAX_LENGTH = 2000  
AI_CONFIDENCE_THRESHOLD = 0.7
MAX_CONVERSATION_HISTORY = 30  
EMOTION_TRACKING_ENABLED = True
IMPULSE_SPENDING_THRESHOLD = 100_000 









# =============================================================================
# USER & ENUMS
# =============================================================================

class TransactionType(str, Enum):
    """Transaction types"""
    INCOME = "income"
    EXPENSE = "expense"

class EmotionCheckin(str, Enum):   #which emotions best describe how you feel?
    HAPPY = "happy"
    NEUTRAL = "neutral"
    SAD = "sad"
    ANXIOUS = "anxious"
    STRESSED = "stressed"
    EXCITED = "excited"
    GRATEFUL = "grateful"
    MOTIVATED = "motivated"
    OVERWHELMED = "overwhelmed"
    CALM = "calm"
    CONTENT = "content"
    RELAXED = "relaxed"
    INDIFFERENT = "indifferent"
    RELIEVED = "relieved"
    SATISFIED = "satisfied"
    PEACEFUL = "peaceful"
    JOYFUL = "joyful"
    HOPEFUL = "hopeful"
    AMAZED = "amazed"
    CONFIDENT = "confident"
    ENTHUSIASTIC = "enthusiastic"
    CURIOUS = "curious"
    ANNOYED = "annoyed"
    ANGRY= "angry"
    GUILTY = "guilty"
    JEALOUS = "jealous"
    EMBARRASSED = "embarrassed"
    DISAPPOINTED = "disappointed"
    DISGUSTED = "disgusted"
    FURIOUS = "furious"
    DEPRESSED = "depressed"
    HOPELESS = "hopeless"
    LONELY = "lonely"
    TIRED = "tired"

class EmotionTrigger(str, Enum):
    WORK = "work"
    HOME = "home"
    SCHOOL = "school"
    OUTDOORS = "outdoors"
    TRAVEL = "travel"
    WEATHER = "weather"
    IDENTITY = "identity"
    PARTNER = "partner"
    FRIENDS = "friends"
    PET = "pet"
    FAMILY = "family"
    COLLEAGUES = "colleagues"
    DATING = "dating"
    HEALTH = "health"
    SLEEP = "sleep"
    EXERCISES = "exercises"
    FOODS = "foods"
    HOBBY = "hobby"
    MONEY = "money"

class AchievementType(str, Enum): #link with gooogle play achievements
    ROOKIE_STARTER = "rookie_starter"  # First transaction
    READY_TO_BE_THE_SAVER = "ready_to_be_the_saver"  # First savings goal # First budget created
    SAVING_SAGE = "saving_sage"  # First savings goal achieved, more than 1M VND saved
    SAVINGS_CHAMPION = "savings_champion"  # saving more than 10M VND successfully
    SAVINGS_PRO = "savings_pro"  # saving more than 50M VND successfully
    SAVINGS_MASTER = "savings_master"  # saving more than 100M VND successfully
    SAVINGS_GURU = "savings_guru"  # saving more than 200M VND successfully
    SAVINGS_GOD = "savings_god"  # saving more than 500M VND successfully
    THE_BILLIONAIRE = "the_billionaire"  # savings more than 1 billion VND successfully



    BUDGET_WIZARD = "budget_wizard"  # First budget completed
    BUDGET_SENSEI = "budget_sensei"  # more than 5 budgets economically spent, no overspending
    BUDGET_PRO = "budget_pro"  # more than 10 budgets economically spent, no overspending
    BUDGET_MASTER = "budget_master"  # more than 20 budgets economically spent, no overspending
    BUDGET_GURU = "budget_guru"  # more than 50 budgets completed successfully

    SPENDING_WIZARD = "spending_wizard"  # spending under budget for 1 week
    SPENDING_SENSEI = "spending_sensei" # spending under budget for 1 month
    SPENDING_PRO = "spending_pro"  # spending under budget for 3 months
    SPENDING_MASTER = "spending_master"  # spending under budget for 6 months
    SPENDING_GURU = "spending_guru"# spending under budget for 1 year

    DEBT_NEWBIE = "debt_newbie"  # have more than 1M VND in debt
    DEBT_SLAVE = "debt_slave"  # have more than 5M VND in debt
    DEEP_IN_DEBT = "deep_in_debt"  #have more than 20M VND in debt
    WRESTLER_WITH_DEBT = "wrestler_with_debt"  # have more than 50M VND in debt
    FALL_INTO_DEBT_SPIRAL = "fall_into_debt_spiral"  # have more than 100M VND in debt
    DEBT_VETERAN = "debt_veteran" #save yourself out of debt, more than 10M VND paid off
    DEBT_WARRIOR = "debt_warrior"  # save yourself out of debt, more than 50M VND paid off
    NO_LONGER_MISERABLE = "no_longer_miserable"  # pay all the debts



    FINANCIAL_GURU = "financial_guru"  # using the app for 1 month
    FINANCIAL_MASTER = "financial_master"  # using the app for 3 months
    MONEY_GOD = "money_god"  # using the app for 6 months
    UNBEATABLE_MONEY_SAVER = "unbeatable_money_saver" # using the app for 1 year

#will continue to add more achievements soon



class RecurrenceFrequency(str, Enum):
    """Frequency for recurring transactions"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"


class SubCategories(str, Enum):
    FOOD_DINING = "food_dining"
    GROCERIES = "groceries"
    TRANSPORTATION = "transportation"
    FUEL = "fuel"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    HOBBIES = "hobbies"
    SPORTS_FITNESS = "sports_fitness"
    BILLS_UTILITIES = "bills_utilities"
    RENT_MORTGAGE = "rent_mortgage"
    INSURANCE = "insurance"
    TELECOMMUNICATIONS = "telecommunications"
    HEALTHCARE = "healthcare"
    PHARMACY = "pharmacy"
    WELLNESS = "wellness"
    EDUCATION = "education"
    BOOKS = "books"
    COURSES = "courses"
    TRAVEL = "travel"
    ACCOMMODATION = "accommodation"
    INVESTMENT = "investment"
    SAVINGS = "savings"
    DEBT_PAYMENT = "debt_payment"
    BANK_FEES = "bank_fees"
    GIFTS = "gifts"
    CHARITY = "charity"
    FAMILY_SUPPORT = "family_support"
    BUSINESS_EXPENSE = "business_expense"
    OFFICE_SUPPLIES = "office_supplies"
    TAXES = "taxes"
    GOVERNMENT_FEES = "government_fees"
    OTHER = "other"
    SALARY = "salary"
    FREELANCE = "freelance"
    BUSINESS_INCOME = "business_income"
    INVESTMENT_RETURN = "investment_return"
    RENTAL_INCOME = "rental_income"
    PENSION = "pension"
    GOVERNMENT_BENEFIT = "government_benefit"
    BONUS = "bonus"
    COMMISSION = "commission"
    GIFT_RECEIVED = "gift_received"
    REFUND = "refund"
    INSURANCE_CLAIM = "insurance_claim"
    LOAN = "loan"


class BudgetStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    ARCHIVED = "archived"

class BudgetPeriod(str, Enum):
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    CUSTOM = "custom"



class SavingsStatus(str, Enum):
    ACTIVE = "active"
    IN_PROGRESS = "in_progress"
    ACHIEVED = "achieved"
    PAUSED = "paused"
    CANCELLED = "cancelled"
    OVERDUE = "overdue"

class SavingsPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"



class SupabaseAuthField(str, Enum):
    ID = "id"
    EMAIL = "email"
    EMAIL_CONFIRMED_AT = "email_confirmed_at"
    LAST_SIGN_IN_AT = "last_sign_in_at"
    RAW_USER_META_DATA = "raw_user_meta_data"
    RAW_APP_META_DATA = "raw_app_meta_data"
    PHONE = "phone"
    CREATED_AT = "created_at"
    UPDATED_AT = "updated_at"
    DELETED_AT = "deleted_at"  



class NotificationType(str, Enum):
    
    BUDGET_ALERT = "budget_alert"
    BUDGET_EXCEEDED = "budget_exceeded"
    SPENDING_WARNING = "spending_warning"
    SAVINGS_OPPORTUNITY = "savings_opportunity"

    # Goal & Achievement
    GOAL_REMINDER = "goal_reminder"
    GOAL_ACHIEVED = "goal_achieved"
    SAVINGS_MILESTONE = "savings_milestone"
    
    # Educational & Behavioral
    DAILY_SAVINGS_TIP = "daily_savings_tip"
    SPENDING_REFLECTION = "spending_reflection"
    IMPULSE_CONTROL = "impulse_control"

    # AI & Insights
    AI_INSIGHT = "ai_insight"
    FINANCIAL_ADVICE = "financial_advice"
    SPENDING_PATTERN_ALERT = "spending_pattern_alert"
    
    # Engagement
    DAILY_CHECK_IN = "daily_check_in"
    WEEKLY_REVIEW = "weekly_review"
    CHALLENGE_INVITATION = "challenge_invitation"

    # System
    SYSTEM_UPDATE = "system_update"
    ACCOUNT_SECURITY = "account_security"

class RelationshipStatus(str, Enum):
    SINGLE = "single"
    IN_A_RELATIONSHIP = "in_a_relationship"
    ENGAGED = "engaged"
    MARRIED = "married"
    DIVORCED = "divorced"
    WIDOWED = "widowed"
    SEPARATED = "separated"

class ConversationContext(str, Enum):
    """AI conversation contexts for financial education"""
    GENERAL = "general"
    BUDGETING_BASICS = "budgeting_basics"
    SAVING_STRATEGIES = "saving_strategies"
    SPENDING_ANALYSIS = "spending_analysis"
    EXPENSE_REDUCTION = "expense_reduction"  # How to cut costs
    FINANCIAL_GOALS = "financial_goals"
    MONEY_MINDSET = "money_mindset"  # Psychology of spending
    FRUGAL_LIVING = "frugal_living"  # Living below means
    STUDENT_FINANCE = "student_finance"  # For students/young adults
    EMERGENCY_FUND = "emergency_fund"
    INVESTMENT_BASICS = "investment_basics"  # Simple investing
    DEBT_AVOIDANCE = "debt_avoidance"  # Preventing debt
    SMART_SHOPPING = "smart_shopping"  # Getting best deals
    MENTAL_HEALTH = "mental_health"  # Financial stress management


class AIResponseType(str, Enum):
    """Types of AI responses"""
    ADVICE = "advice"
    ANALYSIS = "analysis"
    RECOMMENDATION = "recommendation"
    WARNING = "warning"
    ENCOURAGEMENT = "encouragement"
    QUESTION = "question"
    CLARIFICATION = "clarification"


class InsightType(str, Enum):
    """Types of financial insights generated by AI for user financial behavior analysis"""
    # Positive Insights
    SAFE_ZONE = "safe_zone"
    GOAL_ACHIEVER = "goal_achiever"
    SMART_SAVER = "smart_saver"
    REDUCED_DEBT = "reduced_debt"
    HEALTHY_SPENDING = "healthy_spending"
    
    # Warning Insights
    OVERSPENDING = "overspending"
    ON_VERGE_OF_BANKRUPTCY = "on_verge_of_bankruptcy"
    INCONSISTENT_TRACKING = "inconsistent_tracking"
    UNEXPECTED_EXPENSE_SPIKE = "unexpected_expense_spike"
    IRREGULAR_INCOME = "irregular_income"
    RECURRING_OVERSPENDING = "recurring_overspending"
    BELOW_MINIMUM_BALANCE = "below_minimum_balance"
    
    # Critical Insights
    DEBT_INCREASING = "debt_increasing"
    FINANCIAL_INSTABILITY = "financial_instability"
    URGENT_FINANCIAL_ATTENTION_NEEDED = "urgent_financial_attention_needed"
    NO_EMERGENCY_FUND = "no_emergency_fund"


# =============================================================================
# REPORTING & ANALYTICS ENUMS
# =============================================================================

class ReportType(str, Enum):

    EXPENSE_SUMMARY = "expense_summary"
    INCOME_SUMMARY = "income_summary"
    BUDGET_ANALYSIS = "budget_analysis"
    GOAL_PROGRESS = "goal_progress"
    CATEGORY_BREAKDOWN = "category_breakdown"
    MONTHLY_TREND = "monthly_trend"
    YEARLY_OVERVIEW = "yearly_overview"
    CASH_FLOW = "cash_flow"
    NET_WORTH = "net_worth"
    SPENDING_PATTERN = "spending_pattern"

class TimeRange(str, Enum):
    TODAY = "today"
    YESTERDAY = "yesterday"
    THIS_WEEK = "this_week"
    LAST_WEEK = "last_week"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_QUARTER = "this_quarter"
    LAST_QUARTER = "last_quarter"
    THIS_YEAR = "this_year"
    LAST_YEAR = "last_year"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    LAST_90_DAYS = "last_90_days"
    LAST_365_DAYS = "last_365_days"
    CUSTOM = "custom"
    ALL_TIME = "all_time"

class ChartType(str, Enum):
    LINE = "line"
    BAR = "bar"
    PIE = "pie"
    DOUGHNUT = "doughnut"
    SCATTER = "scatter"
 










# =============================================================================
# SYSTEM & TECHNICAL ENUMS
# =============================================================================

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

class LogLevel(str, Enum):
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class CacheKeys(str, Enum):
    USER_PREFERENCES = "user_prefs"
    TRANSACTION_CACHE = "trans_cache"
    BUDGET_CACHE = "budget_cache"
    AI_CONVERSATION = "ai_conv"





# =============================================================================
# HTTP & gRPC STATUS CODES
# =============================================================================

class HTTPStatusCode(IntEnum):
    OK = 200
    CREATED = 201
    ACCEPTED = 202
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    METHOD_NOT_ALLOWED = 405
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    TOO_MANY_REQUESTS = 429
    INTERNAL_SERVER_ERROR = 500
    BAD_GATEWAY = 502
    SERVICE_UNAVAILABLE = 503
    GATEWAY_TIMEOUT = 504

class GRPCStatusCode(IntEnum):
    OK = 0
    CANCELLED = 1
    UNKNOWN = 2
    INVALID_ARGUMENT = 3
    DEADLINE_EXCEEDED = 4
    NOT_FOUND = 5
    ALREADY_EXISTS = 6
    PERMISSION_DENIED = 7
    RESOURCE_EXHAUSTED = 8
    FAILED_PRECONDITION = 9
    ABORTED = 10
    OUT_OF_RANGE = 11
    UNIMPLEMENTED = 12
    INTERNAL = 13
    UNAVAILABLE = 14
    DATA_LOSS = 15
    UNAUTHENTICATED = 16

# =============================================================================
# ERROR CODES
# =============================================================================

class ErrorCode(str, Enum):
    """Application-specific error codes for financial education app"""
    # Authentication & Authorization
    INVALID_CREDENTIALS = "AUTH001"
    TOKEN_EXPIRED = "AUTH002"
    TOKEN_INVALID = "AUTH003"
    EMAIL_NOT_VERIFIED = "AUTH004"
    ACCOUNT_DEACTIVATED = "AUTH005"  # User deactivated their account
    ACCOUNT_DELETED = "AUTH006"  # Account was permanently deleted
    
    # Validation Errors
    INVALID_INPUT = "VAL001"
    MISSING_REQUIRED_FIELD = "VAL002"
    INVALID_FORMAT = "VAL003"
    VALUE_OUT_OF_RANGE = "VAL004"
    INVALID_CURRENCY = "VAL005"
    INVALID_DATE_RANGE = "VAL006"
    DUPLICATE_ENTRY = "VAL007"
    INVALID_EMAIL = "VAL008"
    
    # Business Logic Errors (Financial Education Focus)
    BUDGET_LIMIT_EXCEEDED = "BIZ001"  # 2M VND budget limit
    TRANSACTION_TOO_LARGE = "BIZ002"  # Encourage smaller spending
    SAVINGS_GOAL_TOO_HIGH = "BIZ003"  # Keep goals realistic
    CATEGORY_NOT_FOUND = "BIZ004"
    BUDGET_NOT_FOUND = "BIZ005"
    GOAL_NOT_FOUND = "BIZ006"
    SPENDING_PATTERN_UNHEALTHY = "BIZ007"  # AI detected poor spending habits
    
    # System Errors
    DATABASE_ERROR = "SYS001"
    EXTERNAL_SERVICE_ERROR = "SYS002"
    SERVICE_UNAVAILABLE = "SYS004"
    TIMEOUT_ERROR = "SYS005"
    
    # File & Media Errors
    FILE_TOO_LARGE = "FILE001"
    INVALID_FILE_TYPE = "FILE002"
    FILE_UPLOAD_FAILED = "FILE003"
    FILE_NOT_FOUND = "FILE004"
    
    # AI & ML Errors
    AI_SERVICE_ERROR = "AI001"
    AI_RESPONSE_INVALID = "AI002"
    AI_MODEL_ERROR = "AI004"

# =============================================================================
# CONFIGURATION MAPPINGS
# =============================================================================



# Currency Symbols and Formatting
CURRENCY_SYMBOLS: Dict[str, str] = {
    "VND": "₫",
    "USD": "$",
    "EUR": "€",
    "JPY": "¥",
    "GBP": "£",
    "AUD": "A$",
    "CAD": "C$"
}

CURRENCY_DECIMALS: Dict[str, int] = {
    "VND": 0,
    "USD": 2,
    "EUR": 2,
    "JPY": 0,
    "GBP": 2,
    "AUD": 2,
    "CAD": 2
}

# Budget Alert Thresholds (Stricter for financial education)
BUDGET_ALERT_THRESHOLDS: List[int] = [25, 50, 75, 90, 100]  # Earlier warnings
#TODO:???arange these thresholds to be more suitable for financial education focus

# Supported Date Formats
DATE_FORMATS: List[str] = [
    "%Y-%m-%d",
    "%d/%m/%Y",
    "%m/%d/%Y",
    "%Y-%m-%d %H:%M:%S",
    "%d/%m/%Y %H:%M:%S"
]

# Default Pagination Settings
DEFAULT_PAGINATION: Dict[str, int] = {
    "page": 1,
    "page_size": DEFAULT_PAGE_SIZE,
    "max_page_size": MAX_PAGE_SIZE
}


# Default Financial Advice Topics
AI_ADVICE_TOPICS: Set[str] = {
    "budgeting_for_beginners", "saving_strategies", "expense_reduction", 
    "frugal_living", "smart_shopping", "financial_discipline",
    "emergency_fund_basics", "avoiding_debt", "student_budgeting",
    "money_mindset", "delayed_gratification", "investment_basics",
    "living_below_means", "financial_goals_setting"
}

# Spending Analysis Thresholds (Stricter for financial education)
SPENDING_ANALYSIS: Dict[str, Dict[str, float]] = {
    "high_expense_warning": {"amount": 2_000_000},  # 500K VND - warn for large expenses
    "daily_limit_suggestion": {"amount": 200_000},
    "impulse_buy_detection": {"time_threshold": 180},  # 3 minutes between add to cart and buy
    "category_overspend": {"threshold": 1.1},   # 110% of budget (stricter)
    "savings_rate_low": {"threshold": 0.1},  # Less than 10% savings rate
}
#TODO: need further adjustments based on age



# Financial Education Constants
#Savings Rate = (Monthly Savings/Monthly Income) × 100
SAVINGS_RATE_TARGETS = {
    "minimum": 0.1,  # 10% minimum savings rate
    "good": 0.2,     # 20% good savings rate  
    "excellent": 0.3 # 30% excellent savings rate
}


# Session Management (Simple mobile app)
SESSION_CONFIG: Dict[str, int] = {
    "session_timeout_minutes": SESSION_TIMEOUT_MINUTES,  # Local session timeout
    "remember_me_days": 60  # How long to remember login preference, 2 months
}

# Supabase Auth Helper Constants (Simplified)
DEFAULT_USER_ROLE = "user"  # Default role for new users
SUPABASE_USER_FIELDS = {
    "required": ["id", "email", "created_at"],
    "optional": ["phone", "email_confirmed_at", "last_sign_in_at"],
    "metadata": ["raw_user_meta_data", "raw_app_meta_data"]
}

# User Metadata Schema (stored in raw_user_meta_data) - Financial Education Focus
USER_PROFILE_FIELDS = {
    "name": str,
    "date_of_birth": str,
    "preferred_currency": str,
    "preferred_locale": str,
    "onboarding_completed": bool,
    "notification_preferences": dict,
    "financial_education_level": str,  # beginner, intermediate, advanced
    "savings_goals": list,
    "monthly_income": float,  # For calculating savings rate
    "financial_challenges_completed": list
}

# App Metadata Schema (stored in raw_app_meta_data) - Financial Education Focus
APP_SETTINGS_FIELDS = {
    "role": str,  # UserRole value
    "subscription_tier": str,
    "features_enabled": list,
    "ai_personality_type": str,
    "spending_alerts_enabled": bool,
    "savings_reminders_enabled": bool,
    "financial_education_progress": dict,
    "account_deletion_requested": bool,  # For soft deletion process
    "deletion_requested_at": str  # ISO timestamp
}
