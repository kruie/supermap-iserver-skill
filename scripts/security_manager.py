"""
SuperMap iServer 安全管理工具

提供令牌认证、用户管理、角色权限管理、SSL 配置等安全功能。
"""

import requests
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class User:
    """用户数据类"""
    username: str
    display_name: str
    email: str
    roles: List[str]


@dataclass
class Role:
    """角色数据类"""
    name: str
    description: str
    permissions: List[str]


class SecurityManager:
    """iServer 安全管理器"""

    def __init__(
        self,
        server_url: str,
        username: Optional[str] = None,
        password: Optional[str] = None,
        token: Optional[str] = None,
        timeout: int = 30
    ):
        """
        初始化安全管理器

        Args:
            server_url: iServer 服务器地址
            username: 管理员用户名
            password: 管理员密码
            token: 访问令牌 (可选,如果已获取)
            timeout: 请求超时时间 (秒)
        """
        self.server_url = server_url.rstrip('/')
        self.username = username
        self.password = password
        self.timeout = timeout
        self.session = requests.Session()

        if token:
            self.token = token
            self.session.headers.update({'token': token})
        elif username and password:
            self.token = self.get_token(username, password)
            self.session.headers.update({'token': self.token})
        else:
            self.token = None

    def _get(self, endpoint: str, params: Optional[Dict] = None) -> requests.Response:
        """发送 GET 请求"""
        url = f"{self.server_url}{endpoint}"
        response = self.session.get(url, params=params, timeout=self.timeout)
        response.raise_for_status()
        return response

    def _post(self, endpoint: str, json_data: Optional[Dict] = None) -> requests.Response:
        """发送 POST 请求"""
        url = f"{self.server_url}{endpoint}"
        response = self.session.post(url, json=json_data, timeout=self.timeout)
        response.raise_for_status()
        return response

    # ========== 令牌认证 ==========

    def get_token(self, username: str, password: str) -> str:
        """
        获取访问令牌

        Args:
            username: 用户名
            password: 密码

        Returns:
            访问令牌
        """
        response = self._post(
            '/iserver/security/token',
            json_data={
                'username': username,
                'password': password
            }
        )
        return response.json()['token']

    def validate_token(self, token: str) -> bool:
        """
        验证令牌是否有效

        Args:
            token: 访问令牌

        Returns:
            是否有效
        """
        try:
            response = self._get('/iserver/security/token/validate', params={'token': token})
            return response.json()['valid']
        except Exception:
            return False

    def revoke_token(self, token: str) -> Dict:
        """
        撤销令牌

        Args:
            token: 访问令牌

        Returns:
            撤销结果
        """
        return self._post('/iserver/security/token/revoke', json_data={'token': token}).json()

    def enable_token_auth(
        self,
        token_enabled: bool = True,
        token_expire_hours: int = 24,
        max_token_count: int = 100
    ) -> Dict:
        """
        启用/禁用令牌认证

        Args:
            token_enabled: 是否启用令牌认证
            token_expire_hours: 令牌过期时间 (小时)
            max_token_count: 最大令牌数量

        Returns:
            配置结果
        """
        return self._post(
            '/iserver/security/token/config',
            json_data={
                'tokenEnabled': token_enabled,
                'tokenExpireHours': token_expire_hours,
                'maxTokenCount': max_token_count
            }
        ).json()

    # ========== 用户管理 ==========

    def create_user(
        self,
        username: str,
        password: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> Dict:
        """
        创建用户

        Args:
            username: 用户名
            password: 密码
            display_name: 显示名称
            email: 邮箱
            roles: 角色列表

        Returns:
            创建结果
        """
        data = {
            'username': username,
            'password': password
        }

        if display_name:
            data['displayName'] = display_name
        if email:
            data['email'] = email
        if roles:
            data['roles'] = roles

        return self._post('/iserver/security/users', json_data=data).json()

    def update_user(
        self,
        username: str,
        display_name: Optional[str] = None,
        email: Optional[str] = None,
        roles: Optional[List[str]] = None
    ) -> Dict:
        """
        更新用户信息

        Args:
            username: 用户名
            display_name: 显示名称
            email: 邮箱
            roles: 角色列表

        Returns:
            更新结果
        """
        data = {'username': username}

        if display_name:
            data['displayName'] = display_name
        if email:
            data['email'] = email
        if roles:
            data['roles'] = roles

        return self._post(f'/iserver/security/users/{username}', json_data=data).json()

    def delete_user(self, username: str) -> Dict:
        """
        删除用户

        Args:
            username: 用户名

        Returns:
            删除结果
        """
        return self._post(f'/iserver/security/users/{username}/delete', json_data={}).json()

    def get_user(self, username: str) -> User:
        """
        获取用户信息

        Args:
            username: 用户名

        Returns:
            用户对象
        """
        response = self._get(f'/iserver/security/users/{username}')
        data = response.json()

        return User(
            username=data['username'],
            display_name=data.get('displayName', ''),
            email=data.get('email', ''),
            roles=data.get('roles', [])
        )

    def list_users(self) -> List[User]:
        """
        获取所有用户

        Returns:
            用户列表
        """
        response = self._get('/iserver/security/users')
        data = response.json()

        return [
            User(
                username=u['username'],
                display_name=u.get('displayName', ''),
                email=u.get('email', ''),
                roles=u.get('roles', [])
            )
            for u in data.get('users', [])
        ]

    # ========== 角色管理 ==========

    def create_role(
        self,
        name: str,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None
    ) -> Dict:
        """
        创建角色

        Args:
            name: 角色名称
            description: 角色描述
            permissions: 权限列表

        Returns:
            创建结果
        """
        data = {'name': name}

        if description:
            data['description'] = description
        if permissions:
            data['permissions'] = permissions

        return self._post('/iserver/security/roles', json_data=data).json()

    def update_role(
        self,
        name: str,
        description: Optional[str] = None,
        permissions: Optional[List[str]] = None
    ) -> Dict:
        """
        更新角色

        Args:
            name: 角色名称
            description: 角色描述
            permissions: 权限列表

        Returns:
            更新结果
        """
        data = {'name': name}

        if description:
            data['description'] = description
        if permissions:
            data['permissions'] = permissions

        return self._post(f'/iserver/security/roles/{name}', json_data=data).json()

    def delete_role(self, name: str) -> Dict:
        """
        删除角色

        Args:
            name: 角色名称

        Returns:
            删除结果
        """
        return self._post(f'/iserver/security/roles/{name}/delete', json_data={}).json()

    def get_role(self, name: str) -> Role:
        """
        获取角色信息

        Args:
            name: 角色名称

        Returns:
            角色对象
        """
        response = self._get(f'/iserver/security/roles/{name}')
        data = response.json()

        return Role(
            name=data['name'],
            description=data.get('description', ''),
            permissions=data.get('permissions', [])
        )

    def list_roles(self) -> List[Role]:
        """
        获取所有角色

        Returns:
            角色列表
        """
        response = self._get('/iserver/security/roles')
        data = response.json()

        return [
            Role(
                name=r['name'],
                description=r.get('description', ''),
                permissions=r.get('permissions', [])
            )
            for r in data.get('roles', [])
        ]

    # ========== SSL/TLS 配置 ==========

    def enable_ssl(
        self,
        certificate_path: str,
        private_key_path: str,
        ssl_port: int = 8443
    ) -> Dict:
        """
        启用 SSL/TLS

        Args:
            certificate_path: 证书文件路径
            private_key_path: 私钥文件路径
            ssl_port: SSL 端口

        Returns:
            配置结果
        """
        return self._post(
            '/iserver/security/ssl/enable',
            json_data={
                'certificatePath': certificate_path,
                'privateKeyPath': private_key_path,
                'sslPort': ssl_port
            }
        ).json()

    def disable_ssl(self) -> Dict:
        """
        禁用 SSL/TLS

        Returns:
            配置结果
        """
        return self._post('/iserver/security/ssl/disable', json_data={}).json()

    # ========== 访问控制 ==========

    def set_service_access_control(
        self,
        service_name: str,
        allowed_roles: List[str],
        denied_roles: Optional[List[str]] = None
    ) -> Dict:
        """
        设置服务访问控制

        Args:
            service_name: 服务名称
            allowed_roles: 允许访问的角色列表
            denied_roles: 拒绝访问的角色列表

        Returns:
            配置结果
        """
        data = {
            'serviceName': service_name,
            'allowedRoles': allowed_roles
        }

        if denied_roles:
            data['deniedRoles'] = denied_roles

        return self._post(
            '/iserver/security/accesscontrol',
            json_data=data
        ).json()

    def get_service_access_control(self, service_name: str) -> Dict:
        """
        获取服务访问控制配置

        Args:
            service_name: 服务名称

        Returns:
            访问控制配置
        """
        return self._get(
            '/iserver/security/accesscontrol',
            params={'serviceName': service_name}
        ).json()


# ========== 使用示例 ==========

if __name__ == "__main__":
    # 示例 1: 初始化安全管理器
    security = SecurityManager(
        server_url="http://localhost:8090",
        username="admin",
        password="supermap"
    )

    # 示例 2: 获取令牌
    token = security.get_token("analyst", "password123")
    print(f"访问令牌: {token}")

    # 示例 3: 创建用户
    result = security.create_user(
        username="analyst",
        password="password123",
        display_name="数据分析师",
        email="analyst@example.com",
        roles=["analyst_role"]
    )
    print(f"创建用户: {result}")

    # 示例 4: 创建角色
    result = security.create_role(
        name="analyst_role",
        description="数据分析师角色",
        permissions=["read", "query", "analyze"]
    )
    print(f"创建角色: {result}")

    # 示例 5: 列出所有用户
    users = security.list_users()
    print("用户列表:")
    for user in users:
        print(f"  - {user.username} ({user.display_name})")

    # 示例 6: 列出所有角色
    roles = security.list_roles()
    print("角色列表:")
    for role in roles:
        print(f"  - {role.name}: {role.description}")

    # 示例 7: 启用令牌认证
    result = security.enable_token_auth(
        token_enabled=True,
        token_expire_hours=24,
        max_token_count=100
    )
    print(f"启用令牌认证: {result}")

    # 示例 8: 设置服务访问控制
    result = security.set_service_access_control(
        service_name="map-world",
        allowed_roles=["analyst_role", "admin_role"]
    )
    print(f"设置访问控制: {result}")
