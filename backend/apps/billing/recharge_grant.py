# -*- coding: utf-8 -*-
"""充值到账币数：会员享档位额外赠送，普通用户仅基础币。"""


def resolve_recharge_grant_coins(package, user) -> dict:
    from apps.membership.services import MembershipService

    base = int(package.base_coins or 0)
    configured_bonus = int(package.bonus_coins or 0)
    is_member = MembershipService.get_current_membership(user) is not None
    bonus = configured_bonus if is_member else 0
    return {
        "base_coins": base,
        "bonus_coins": bonus,
        "configured_bonus_coins": configured_bonus,
        "total_coins": base + bonus,
        "member_bonus_eligible": is_member,
    }
