# apps/common/pagination.py
# 自定义分页类

from collections import OrderedDict

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


class StandardPagination(PageNumberPagination):
    """标准分页类，统一分页响应格式。"""

    page_size = 10  # 默认每页数量
    page_size_query_param = 'page_size'  # 可通过请求参数动态调整每页数量
    max_page_size = 100  # 最大每页数量限制
    page_query_param = 'page'  # 页码参数名

    def get_paginated_response(self, data):
        """
        返回统一格式的分页响应数据。

        返回字段说明：
        - code: 状态码
        - message: 状态消息
        - data: 当前页数据列表
        - pagination: 分页信息（包含 total、page、page_size、total_pages）
        """
        return Response(
            OrderedDict(
                [
                    ('code', 0),
                    ('message', 'success'),
                    ('data', data),
                    (
                        'pagination',
                        OrderedDict(
                            [
                                ('total', self.page.paginator.count),  # 数据总条数
                                ('page', self.page.number),  # 当前页码
                                ('page_size', self.get_page_size(self.request)),  # 每页数量
                                ('total_pages', self.page.paginator.num_pages),  # 总页数
                            ]
                        ),
                    ),
                ]
            )
        )
