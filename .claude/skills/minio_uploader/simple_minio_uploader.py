#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化版 MinIO 上传工具
只专注于基本的文件上传功能
"""

import os
import urllib.parse
import mimetypes
import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

# 添加对常见文件类型的MIME类型支持
mimetypes.add_type('text/markdown', '.md')
mimetypes.add_type('text/markdown', '.markdown')
mimetypes.add_type('text/plain', '.txt')
mimetypes.add_type('text/html', '.html')
mimetypes.add_type('text/html', '.htm')

import os
from pathlib import Path
from typing import Dict, Any, Optional

# 主项目环境变量文件路径（相对于技能目录）
PROJECT_ENV_PATH = Path(__file__).parent.parent.parent / "ai_chat_backend_fastapi" / ".env"

def load_project_env() -> None:
    """加载主项目的环境变量配置"""
    if not PROJECT_ENV_PATH.exists():
        return  # 主项目.env文件不存在时使用默认值

    for raw_line in PROJECT_ENV_PATH.read_text(encoding='utf-8').splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        cleaned = value.strip().strip('"').strip("'")
        os.environ[key] = cleaned

load_project_env() 

class SimpleMinIOUploader:
    """简化版 MinIO 上传器"""

    def __init__(self, endpoint_url=None, access_key=None, secret_key=None):
        """
        初始化MinIO客户端

        Args:
            endpoint_url: MinIO服务地址，优先使用环境变量 MINIO_ENDPOINT
            access_key: 访问密钥，优先使用环境变量 MINIO_ACCESS_KEY
            secret_key: 密钥，优先使用环境变量 MINIO_SECRET_KEY
        """
        # 从环境变量读取配置，如果提供了参数则使用参数值
        self.endpoint_url = endpoint_url or os.getenv('MINIO_ENDPOINT', 'http://localhost:9000')
        access_key = access_key or os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
        secret_key = secret_key or os.getenv('MINIO_SECRET_KEY', 'minioadmin')

        # 读取其他可选配置
        self.region = os.getenv('MINIO_REGION', 'us-east-1')
        self.secure = os.getenv('MINIO_SECURE', 'false').lower() == 'true'

        # 初始化客户端
        self.client = boto3.client(
            's3',
            endpoint_url=self.endpoint_url,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=self.region,
            config=Config(signature_version='s3v4'),
            verify=self.secure
        )

        print(f"🚀 MinIO客户端初始化成功: {self.endpoint_url} ({'HTTPS' if self.secure else 'HTTP'})")

    def upload_file(self, file_path, bucket_name=None, object_name=None, force_download=False, content_type=None):
        """
        上传文件到MinIO

        Args:
            file_path: 本地文件路径
            bucket_name: 存储桶名称，优先使用环境变量 MINIO_BUCKET_NAME，默认为 cc-reslut
            object_name: 对象名称，如果不提供则使用文件名
            force_download: 是否强制下载（添加 download 参数）
            content_type: 文件MIME类型，如果不提供则自动检测

        Returns:
            str: 上传成功返回public文件地址，失败返回None
        """
        # 使用环境变量或默认值
        if bucket_name is None:
            bucket_name = os.getenv('MINIO_BUCKET_NAME', 'agentic')
        if not os.path.exists(file_path):
            print(f"❌ 文件不存在: {file_path}")
            return None

        # 如果没有指定对象名称，使用文件名
        if object_name is None:
            object_name = os.path.basename(file_path)

        # 如果没有指定content_type，自动检测
        if content_type is None:
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'application/octet-stream'

        # 对于文本文件，确保设置UTF-8编码
        if content_type.startswith('text/'):
            if 'charset=' not in content_type:
                content_type += '; charset=utf-8'

        try:
            # 上传文件，设置Content-Type
            self.client.upload_file(
                Bucket=bucket_name,
                Key=object_name,
                Filename=file_path,
                ExtraArgs={'ContentType': content_type}
            )

            # 返回public文件地址，对文件名进行URL编码
            encoded_object_name = urllib.parse.quote(object_name)
            public_url = f"{self.endpoint_url}/{bucket_name}/{encoded_object_name}"

            # 如果强制下载，添加 download 参数
            if force_download:
                public_url += "?download=1"

            print(f"✅ 文件上传成功: {file_path} -> {public_url} ({content_type})")
            return public_url

        except ClientError as e:
            print(f"❌ 上传失败: {e}")
            return None

    def get_file_url(self, object_name, bucket_name=None, expires_in=3600):
        """
        获取文件的访问链接

        Args:
            object_name: 对象名称
            bucket_name: 存储桶名称，优先使用环境变量 MINIO_BUCKET_NAME
            expires_in: 链接过期时间(秒)

        Returns:
            str: 访问链接
        """
        # 使用环境变量或默认值
        if bucket_name is None:
            bucket_name = os.getenv('MINIO_BUCKET_NAME', 'agentic')
        try:
            url = self.client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expires_in
            )
            return url
        except ClientError as e:
            print(f"❌ 生成链接失败: {e}")
            return None

    def get_public_url(self, object_name, bucket_name=None, force_download=False):
        """
        获取文件的public访问链接（需要存储桶设置为公开访问）

        Args:
            object_name: 对象名称
            bucket_name: 存储桶名称，优先使用环境变量 MINIO_BUCKET_NAME
            force_download: 是否强制下载（添加 download 参数）

        Returns:
            str: public访问链接
        """
        # 使用环境变量或默认值
        if bucket_name is None:
            bucket_name = os.getenv('MINIO_BUCKET_NAME', 'agentic')
        try:
            # 对文件名进行URL编码
            encoded_object_name = urllib.parse.quote(object_name)
            public_url = f"{self.endpoint_url}/{bucket_name}/{encoded_object_name}"

            # 如果强制下载，添加 download 参数
            if force_download:
                public_url += "?download=1"

            return public_url
        except Exception as e:
            print(f"❌ 生成public链接失败: {e}")
            return None

    def list_files(self, bucket_name=None, prefix="", max_keys=100):
        """
        列出存储桶中的文件

        Args:
            bucket_name: 存储桶名称，优先使用环境变量 MINIO_BUCKET_NAME
            prefix: 对象名前缀
            max_keys: 最大返回数量

        Returns:
            list: 文件列表
        """
        # 使用环境变量或默认值
        if bucket_name is None:
            bucket_name = os.getenv('MINIO_BUCKET_NAME', 'agentic')

        try:
            response = self.client.list_objects_v2(
                Bucket=bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            files = response.get('Contents', [])

            if files:
                print(f"📄 存储桶 '{bucket_name}' 中的文件:")
                for file in files:
                    size_mb = file['Size'] / (1024 * 1024)
                    print(f"   - {file['Key']} ({file['Size']} bytes, {size_mb:.2f} MB)")
            else:
                print(f"📄 存储桶 '{bucket_name}' 中没有文件")

            return files
        except ClientError as e:
            print(f"❌ 列出文件失败: {e}")
            return []

    def delete_file(self, object_name, bucket_name=None):
        """
        删除文件

        Args:
            object_name: 对象名称
            bucket_name: 存储桶名称，优先使用环境变量 MINIO_BUCKET_NAME

        Returns:
            bool: 删除是否成功
        """
        # 使用环境变量或默认值
        if bucket_name is None:
            bucket_name = os.getenv('MINIO_BUCKET_NAME', 'agentic')
        try:
            self.client.delete_object(Bucket=bucket_name, Key=object_name)
            print(f"✅ 文件删除成功: {bucket_name}/{object_name}")
            return True
        except ClientError as e:
            print(f"❌ 文件删除失败: {e}")
            return False

    def bucket_exists(self, bucket_name):
        """
        检查存储桶是否存在

        Args:
            bucket_name: 存储桶名称

        Returns:
            bool: 存储桶是否存在
        """
        try:
            self.client.head_bucket(Bucket=bucket_name)
            return True
        except ClientError:
            return False

    def create_bucket(self, bucket_name):
        """
        创建存储桶

        Args:
            bucket_name: 存储桶名称

        Returns:
            bool: 创建是否成功
        """
        try:
            if not self.bucket_exists(bucket_name):
                self.client.create_bucket(Bucket=bucket_name)
                print(f"✅ 存储桶 '{bucket_name}' 创建成功")
            else:
                print(f"⚠️  存储桶 '{bucket_name}' 已存在")
            return True
        except ClientError as e:
            print(f"❌ 创建存储桶失败: {e}")
            return False


def main():
    """主函数 - 命令行使用"""
    import sys

    if len(sys.argv) < 2:
        print("使用方法: python simple_minio_uploader.py <文件路径> [对象名称] [force_download] [存储桶]")
        print("示例: python simple_minio_uploader.py ./test.txt")
        print("示例: python simple_minio_uploader.py ./test.txt folder/test.txt true")
        print("示例: python simple_minio_uploader.py ./test.txt folder/test.txt true my-bucket")
        print()
        print("环境变量配置:")
        print("  MINIO_ENDPOINT: MinIO服务地址 (默认: http://localhost:9000)")
        print("  MINIO_ACCESS_KEY: 访问密钥 (默认: minioadmin)")
        print("  MINIO_SECRET_KEY: 密钥 (默认: minioadmin)")
        print("  MINIO_BUCKET_NAME: 默认存储桶 (默认: agentic)")
        print("  MINIO_SECURE: 是否使用HTTPS (默认: false)")
        print("  MINIO_REGION: AWS区域 (默认: us-east-1)")
        return

    file_path = sys.argv[1]
    object_name = sys.argv[2] if len(sys.argv) > 2 else None
    force_download = len(sys.argv) > 3 and sys.argv[3].lower() == 'true'
    bucket_name = sys.argv[4] if len(sys.argv) > 4 else None

    print(f"🔧 配置信息:")
    print(f"   端点: {os.getenv('MINIO_ENDPOINT', 'http://localhost:9000')}")
    print(f"   存储桶: {bucket_name or os.getenv('MINIO_BUCKET_NAME', 'agentic')}")
    print(f"   安全模式: {os.getenv('MINIO_SECURE', 'false')}")
    print()

    # 创建上传器
    uploader = SimpleMinIOUploader()

    # 确保存储桶存在
    target_bucket = bucket_name or os.getenv('MINIO_BUCKET_NAME', 'agentic')
    uploader.create_bucket(target_bucket)

    # 上传文件并获取public地址
    public_url = uploader.upload_file(file_path, object_name=object_name, force_download=force_download, bucket_name=bucket_name)
    if public_url:
        print(f"🔗 Public访问地址: {public_url}")
    else:
        print("❌ 文件上传失败")
        import sys
        sys.exit(1)

    # 返回 URL（用于模块导入时的返回值，但 Bash 工具只能捕获 print 输出）
    return public_url


if __name__ == "__main__":
    main()

