"""
用户资料视图
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response({
            'code': 0,
            'message': 'success',
            'data': {
                'id': str(user.id),
                'nickname': user.nickname,
                'phone': user.phone,
                'email': getattr(user, 'email', ''),
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'is_active': user.is_active,
                'date_joined': user.date_joined.strftime('%Y-%m-%d') if user.date_joined else None,
            }
        })

    def put(self, request):
        user = request.user
        nickname = request.data.get('nickname')
        if nickname:
            user.nickname = nickname
            user.save()
        return Response({
            'code': 0,
            'message': '更新成功',
            'data': {
                'id': str(user.id),
                'nickname': user.nickname,
            }
        })
