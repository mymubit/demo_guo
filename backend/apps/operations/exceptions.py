"""运营中心异常。"""
from __future__ import annotations


class OperationsError(Exception):
    """运营中心通用异常。"""

    code = 50000
    message = "运营中心错误"

    def __init__(self, message: str | None = None, *, code: int | None = None, extra: dict | None = None):
        self.message = message or self.message
        if code is not None:
            self.code = code
        self.extra = extra or {}
        super().__init__(self.message)


class CampaignError(OperationsError):
    code = 50101
    message = "活动配置错误"


class CampaignNotRunning(CampaignError):
    code = 50102
    message = "活动未在进行中"


class CouponExhausted(CampaignError):
    code = 50103
    message = "卡券已发完"


class CouponExpired(CampaignError):
    code = 50104
    message = "卡券已过期"


class CouponAlreadyClaimed(CampaignError):
    code = 50105
    message = "已领取过该卡券"


class RedemptionCodeInvalid(CampaignError):
    code = 50106
    message = "兑换码无效"


class TicketError(OperationsError):
    code = 50201
    message = "工单错误"


class TicketNotFound(TicketError):
    code = 50202
    message = "工单不存在"


class TicketSlaBreached(TicketError):
    code = 50203
    message = "工单 SLA 违约"


class ExperimentError(OperationsError):
    code = 50301
    message = "实验配置错误"


class ExperimentNotRunning(ExperimentError):
    code = 50302
    message = "实验未在进行中"


class ExperimentTrafficInvalid(ExperimentError):
    code = 50303
    message = "实验流量配比非法"


class TemplatePromotionError(OperationsError):
    code = 50401
    message = "模板沉淀错误"


class UgcTemplateError(OperationsError):
    code = 50501
    message = "UGC 模板错误"


class CreatorError(OperationsError):
    code = 50601
    message = "创作者激励错误"


class ComplianceRuleError(OperationsError):
    code = 50701
    message = "合规规则错误"
