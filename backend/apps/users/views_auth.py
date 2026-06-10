"""
用户认证视图
"""
from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from apps.users.models import User
from apps.users.serializers import UserRegisterSerializer, UserLoginSerializer


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        data = request.data
        nickname = data.get('nickname') or data.get('phone', '')[-4:]
        try:
            user = User.objects.create_user(
                phone=data.get('phone'),
                password=data.get('password'),
                nickname=nickname,
                email=data.get('email'),
            )
            tokens = get_tokens_for_user(user)
            return Response({
                'code': 0,
                'message': '注册成功',
                'data': {
                    'user': {
                        'id': str(user.id),
                        'nickname': user.nickname,
                        'phone': user.phone,
                        'is_staff': user.is_staff,
                        'is_superuser': user.is_superuser,
                    },
                    'tokens': tokens,
                }
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                'code': 400,
                'message': f'注册失败: {str(e)}',
            }, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        phone = request.data.get('phone')
        password = request.data.get('password')

        if not phone or not password:
            return Response({
                'code': 400,
                'message': '手机号和密码不能为空',
            }, status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(request, phone=phone, password=password)
        if user is None:
            # 尝试直接查询
            try:
                u = User.objects.filter(phone=phone).first()
                if u and u.check_password(password):
                    user = u
            except Exception:
                pass

        if user is None:
            # 演示环境：允许任何手机号+密码直接登录（快速体验）
            if not request.data.get('demo'):
                return Response({
                    'code': 401,
                    'message': '手机号或密码错误',
                }, status=status.HTTP_401_UNAUTHORIZED)
            # demo 模式：自动创建用户
            user, created = User.objects.get_or_create(
                phone=phone,
                defaults={'nickname': f'用户{phone[-4:]}'}
            )
            if created:
                user.set_password(password)
                user.save()

        tokens = get_tokens_for_user(user)
        return Response({
            'code': 0,
            'message': '登录成功',
            'data': {
                'user': {
                    'id': str(user.id),
                    'nickname': user.nickname,
                    'phone': user.phone,
                    'is_staff': user.is_staff,
                    'is_superuser': user.is_superuser,
                    'is_active': user.is_active,
                    'date_joined': user.date_joined.strftime('%Y-%m-%d') if user.date_joined else None,
                },
                'tokens': tokens,
            }
        })


class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({
                'code': 400,
                'message': 'refresh token is required',
            }, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            return Response({
                'code': 0,
                'message': 'success',
                'data': {
                    'access': str(token.access_token),
                    'refresh': str(token),
                }
            })
        except Exception as e:
            return Response({
                'code': 401,
                'message': f'Invalid token: {str(e)}',
            }, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                try:
                    token.blacklist()
                except Exception:
                    pass
        except Exception:
            pass
        return Response({
            'code': 0,
            'message': '退出成功',
        })
