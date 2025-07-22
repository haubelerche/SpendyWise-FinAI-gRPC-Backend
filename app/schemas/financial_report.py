"""
Financial Reports Schemas
Pydantic schemas for financial reports validation and serialization
"""
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Any
from datetime import datetime, date
from uuid import UUID
from app.core.constants import ReportType, TimeRange, ChartType


class FinancialReportBase(BaseModel):
    """Base schema for financial reports"""
    report_type: ReportType = Field(..., description="Type of financial report")
    title: str = Field(..., min_length=1, max_length=200, description="Report title")
    time_range: TimeRange = Field(..., description="Time range for the report")
    start_date: Optional[date] = Field(default=None, description="Start date for custom time range")
    end_date: Optional[date] = Field(default=None, description="End date for custom time range")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="Additional filters")
    chart_type: Optional[ChartType] = Field(default=None, description="Chart type if applicable")

    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validate that end_date is after start_date"""
        if v and values.get('start_date') and v < values['start_date']:
            raise ValueError('End date must be after start date')
        return v


class FinancialReportCreate(FinancialReportBase):
    """Schema for creating financial reports"""
    data: Dict[str, Any] = Field(..., description="Report data")
    chart_config: Optional[Dict[str, Any]] = Field(default=None, description="Chart configuration")
    expires_at: Optional[datetime] = Field(default=None, description="Report expiry time")


class FinancialReportUpdate(BaseModel):
    """Schema for updating financial reports"""
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    data: Optional[Dict[str, Any]] = Field(default=None)
    chart_config: Optional[Dict[str, Any]] = Field(default=None)
    expires_at: Optional[datetime] = Field(default=None)
    file_url: Optional[str] = Field(default=None)


class FinancialReportResponse(FinancialReportBase):
    """Schema for financial report responses"""
    report_id: UUID = Field(..., description="Report unique identifier")
    user_id: UUID = Field(..., description="User who owns the report")
    data: Dict[str, Any] = Field(..., description="Report data")
    chart_config: Optional[Dict[str, Any]] = Field(default=None)
    generated_at: datetime = Field(..., description="When report was generated")
    expires_at: Optional[datetime] = Field(default=None)
    file_url: Optional[str] = Field(default=None)
    created_at: datetime = Field(..., description="Creation timestamp")
    is_expired: bool = Field(..., description="Whether report has expired")

    class Config:
        from_attributes = True


class ReportGenerationRequest(BaseModel):
    """Schema for report generation requests"""
    report_type: ReportType = Field(..., description="Type of report to generate")
    time_range: TimeRange = Field(..., description="Time range for analysis")
    start_date: Optional[date] = Field(default=None)
    end_date: Optional[date] = Field(default=None)
    filters: Optional[Dict[str, Any]] = Field(default={})
    include_chart: bool = Field(default=True, description="Whether to include chart data")
    chart_type: Optional[ChartType] = Field(default=None)
    export_format: Optional[str] = Field(default='json', description="Export format (json, pdf, csv)")


class ReportSummary(BaseModel):
    """Schema for report summary information"""
    report_id: UUID
    title: str
    report_type: ReportType
    time_range: TimeRange
    generated_at: datetime
    is_expired: bool
    has_chart: bool

    class Config:
        from_attributes = True


class ReportListResponse(BaseModel):
    """Schema for paginated report list responses"""
    reports: List[ReportSummary] = Field(..., description="List of report summaries")
    total_count: int = Field(..., description="Total number of reports")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")
    has_next: bool = Field(..., description="Whether there are more pages")


class ChartData(BaseModel):
    """Schema for chart data"""
    chart_type: ChartType = Field(..., description="Type of chart")
    title: str = Field(..., description="Chart title")
    data: Dict[str, Any] = Field(..., description="Chart data")
    config: Optional[Dict[str, Any]] = Field(default=None, description="Chart configuration")


class ReportMetrics(BaseModel):
    """Schema for report metrics and KPIs"""
    total_income: float = Field(default=0, description="Total income for period")
    total_expenses: float = Field(default=0, description="Total expenses for period")
    net_income: float = Field(default=0, description="Net income (income - expenses)")
    savings_rate: float = Field(default=0, description="Savings rate percentage")
    top_expense_category: Optional[str] = Field(default=None, description="Highest expense category")
    budget_adherence: float = Field(default=0, description="Budget adherence percentage")
    goal_progress: float = Field(default=0, description="Financial goals progress percentage")
