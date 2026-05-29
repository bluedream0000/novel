# -*- coding: utf-8 -*-
"""
七牛云管理器 - 使用官方 qiniu 包
"""
import json
import time
import urllib.request
import ssl

try:
    from qiniu import Auth, put_data
    HAS_QINIU = True
except ImportError:
    HAS_QINIU = False


class QiniuManager:
    """七牛云管理器 - 使用官方 SDK"""
    
    def __init__(self, access_key, secret_key, bucket, domain):
        self.access_key = access_key
        self.secret_key = secret_key
        self.bucket = bucket
        self.domain = domain
        
        if HAS_QINIU:
            self.auth = Auth(access_key, secret_key)
        else:
            self.auth = None
    
    def generate_upload_token(self, key=None, expires=3600):
        """
        生成上传 Token
        
        Args:
            key: 文件 key（可选）
            expires: Token 有效期（秒），默认 1 小时
        
        Returns:
            str: 上传 Token
        """
        if self.auth:
            # 使用官方 SDK 生成 Token
            return self.auth.upload_token(self.bucket, key, expires)
        else:
            # 回退到手动实现（备用）
            return self._manual_generate_token(key, expires)
    
    def _manual_generate_token(self, key=None, expires=3600):
        """手动生成 Token（备用方案，当 qiniu 包不可用时）"""
        import hmac
        import hashlib
        import base64
        
        # 上传策略
        scope = f'{self.bucket}:{key}' if key else self.bucket
        policy = {
            'scope': scope,
            'deadline': int(time.time()) + expires,
        }
        
        # JSON 编码
        policy_json = json.dumps(policy, separators=(',', ':'))
        
        # URL 安全 Base64 编码
        def urlsafe_b64encode(data):
            if isinstance(data, str):
                data = data.encode('utf-8')
            return base64.urlsafe_b64encode(data).rstrip(b'=').decode('utf-8')
        
        encoded_policy = urlsafe_b64encode(policy_json)
        
        # HMAC-SHA1 签名
        sign = hmac.new(
            self.secret_key.encode('utf-8'),
            encoded_policy.encode('utf-8'),
            hashlib.sha1
        ).digest()
        encoded_sign = urlsafe_b64encode(sign)
        
        # 组合 Token
        token = f'{self.access_key}:{encoded_sign}:{encoded_policy}'
        return token
    
    def generate_download_url(self, key, expires=3600, is_public=True):
        """
        生成下载 URL
        
        Args:
            key: 文件 key
            expires: 有效期（秒）
            is_public: 是否公开空间
        
        Returns:
            str: 下载 URL
        """
        # 清理 domain：去掉协议前缀和末尾斜杠
        domain = self.domain.strip()
        if domain.startswith('http://'):
            domain = domain[7:]
        elif domain.startswith('https://'):
            domain = domain[8:]
        domain = domain.rstrip('/')

        # 使用 HTTPS
        base_url = f'https://{domain}/{key}'
        
        if is_public:
            # 公开空间直接返回 URL
            return base_url
        else:
            # 私有空间需要签名
            if self.auth:
                return self.auth.private_download_url(base_url, expires=expires)
            else:
                return base_url
    
    def upload_file(self, key, data, is_public=True):
        """
        上传文件
        
        Args:
            key: 文件 key（存储路径）
            data: 文件内容（bytes 或 str）
            is_public: 是否公开空间
        
        Returns:
            dict: 上传结果
        """
        # 确保数据是 bytes
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        # 生成 Token
        token = self.generate_upload_token(key, expires=3600 * 24)
        
        # 使用官方 SDK 上传
        if HAS_QINIU:
            try:
                ret, info = put_data(token, key, data)
                if info.status_code == 200:
                    return {
                        'success': True,
                        'key': ret.get('key'),
                        'hash': ret.get('hash'),
                        'url': self.generate_download_url(key, is_public=is_public)
                    }
                else:
                    return {
                        'success': False,
                        'error': f'上传失败: {info.status_code} - {info.text_body}'
                    }
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }
        
        # 回退到手动上传（备用）
        return self._manual_upload(key, data, token, is_public)
    
    def _manual_upload(self, key, data, token, is_public=True):
        """手动上传（备用方案）"""
        import uuid
        
        # 上传地址（华东区）
        upload_url = 'https://upload.qiniup.com'
        
        # 构建 multipart form data
        boundary = uuid.uuid4().hex
        body = b''
        
        # Token（必须在 file 之前）
        body += f'--{boundary}\r\n'.encode('utf-8')
        body += b'Content-Disposition: form-data; name="token"\r\n\r\n'
        body += token.encode('utf-8')
        body += b'\r\n'
        
        # Key
        body += f'--{boundary}\r\n'.encode('utf-8')
        body += b'Content-Disposition: form-data; name="key"\r\n\r\n'
        body += key.encode('utf-8')
        body += b'\r\n'
        
        # 文件内容
        body += f'--{boundary}\r\n'.encode('utf-8')
        body += f'Content-Disposition: form-data; name="file"; filename="{key}"\r\n'.encode('utf-8')
        body += b'Content-Type: application/octet-stream\r\n\r\n'
        body += data
        body += b'\r\n'
        
        body += f'--{boundary}--\r\n'.encode('utf-8')
        
        # 发送请求
        req = urllib.request.Request(upload_url, data=body, method='POST')
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
        
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            response = urllib.request.urlopen(req, context=ctx, timeout=60)
            result = json.loads(response.read().decode('utf-8'))
            
            return {
                'success': True,
                'key': result.get('key'),
                'hash': result.get('hash'),
                'url': self.generate_download_url(key, is_public=is_public)
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def download_file(self, key, save_path=None):
        """
        下载文件
        
        Args:
            key: 文件 key
            save_path: 保存路径，None 则返回内容
        
        Returns:
            dict: 下载结果
        """
        # 清理 domain
        domain = self.domain.strip()
        if domain.startswith('http://'):
            domain = domain[7:]
        elif domain.startswith('https://'):
            domain = domain[8:]
        domain = domain.rstrip('/')

        # 七牛测试域名（clouddn.com / qiniudn.com）通常不支持 HTTPS，先尝试 HTTP
        urls_to_try = [
            f'http://{domain}/{key}',
            f'https://{domain}/{key}',
        ]

        last_error = None
        for url in urls_to_try:
            try:
                ctx = ssl.create_default_context()
                ctx.check_hostname = False
                ctx.verify_mode = ssl.CERT_NONE
                
                response = urllib.request.urlopen(url, context=ctx, timeout=30)
                data = response.read()
                
                if save_path:
                    with open(save_path, 'wb') as f:
                        f.write(data)
                    return {'success': True, 'path': save_path, 'url': url}
                else:
                    return {'success': True, 'data': data, 'url': url}
            except urllib.error.HTTPError as e:
                last_error = e
                if e.code == 404:
                    return {'success': False, 'error': '文件不存在'}
                # 421 / 403 等可能是协议问题，继续尝试下一个URL
                continue
            except Exception as e:
                last_error = e
                continue

        if last_error:
            if isinstance(last_error, urllib.error.HTTPError):
                return {'success': False, 'error': f'HTTP {last_error.code}: {last_error.reason}'}
            return {'success': False, 'error': str(last_error)}
        return {'success': False, 'error': '所有下载尝试均失败'}
    
    def upload_json(self, key, data_dict, is_public=True):
        """上传 JSON 数据"""
        content = json.dumps(data_dict, ensure_ascii=False, indent=2)
        return self.upload_file(key, content.encode('utf-8'), is_public=is_public)
    
    def download_json(self, key):
        """下载 JSON 数据"""
        result = self.download_file(key)
        if result['success']:
            data = result['data']
            if isinstance(data, bytes):
                data = data.decode('utf-8')
            return {'success': True, 'data': json.loads(data)}
        return result


# 测试代码
if __name__ == '__main__':
    print(f'qiniu 包可用: {HAS_QINIU}')
    
    if not HAS_QINIU:
        print('请安装: pip install qiniu')