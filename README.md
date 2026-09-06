# 小区媒体分享平台

这是一个用 Python Flask 写的小区图片/视频分享网站。它可以让用户注册账号、登录、上传图片或视频、在首页查看大家分享的内容，并发表评论。

这份 README 面向非 Web 前后端背景的使用者，重点说明：这个工程怎么运行、页面怎么用、哪些文件很重要、以后怎么部署到阿里云服务器上。

## 1. 项目能做什么

当前项目支持：

- 用户注册
- 用户登录和退出登录
- 登录后首页显示当前账户名
- 上传图片
- 上传视频
- 非 MP4 视频自动尝试转成 MP4
- 首页展示图片/视频
- 登录后发表评论
- 提供 `/api/media` 接口返回媒体列表
- 后台定时检查服务器磁盘空间，空间不足时尝试发送邮件提醒

## 2. 项目目录说明

```text
.
├── app.py                  # Flask 主程序：路由、数据库模型、上传、转码、启动入口都在这里
├── requirements.txt        # Python 依赖列表
├── README.md               # 项目说明文档
├── templates/              # HTML 页面模板
│   ├── index.html          # 首页：展示媒体、登录状态、评论入口
│   ├── upload.html         # 上传页面
│   ├── login.html          # 登录页面
│   └── register.html       # 注册页面
├── static/                 # 静态文件目录
│   └── uploads/            # 用户上传的图片/视频保存在这里
└── instance/               # Flask 实例目录
    └── community.db        # SQLite 数据库文件，保存用户、媒体、评论数据
```

特别注意：

- `instance/community.db` 是数据库文件，不要随意删除。
- `static/uploads/` 里是用户上传的图片和视频，不要随意删除。
- 如果要备份网站数据，至少要备份 `instance/community.db` 和 `static/uploads/`。

## 3. 依赖要求

### Python 依赖

项目需要 Python 3，并依赖以下包：

- Flask
- Flask-SQLAlchemy
- psutil
- gunicorn（生产部署时使用）

这些依赖已经写在 `requirements.txt` 里。

### 系统依赖

如果只上传图片，不一定需要额外系统工具。

如果要上传 MOV、AVI、MKV、WMV、FLV 等非 MP4 视频，服务器必须安装：

- FFmpeg

FFmpeg 用来把非 MP4 视频转成浏览器更容易播放的 MP4。

### 前端依赖

当前项目没有 Node.js 构建步骤，不需要安装 Node.js。

页面使用 Bootstrap CDN 加载样式和脚本。如果服务器或浏览器网络无法访问 CDN，页面样式可能显示不完整。

## 4. 本地运行方法

以下命令需要在项目目录中执行。

### 第一步：创建 Python 虚拟环境

macOS / Linux：

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell：

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### 第二步：安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 第三步：如果要处理视频，安装 FFmpeg

macOS：

```bash
brew install ffmpeg
```

Ubuntu / Debian：

```bash
sudo apt update
sudo apt install -y ffmpeg
```

安装后可以检查：

```bash
ffmpeg -version
```

### 第四步：启动网站

```bash
python app.py
```

启动成功后，浏览器访问：

```text
http://localhost:5001
```

如果同一个局域网里的其他设备要访问，可以访问：

```text
http://你的电脑局域网IP:5001
```

## 5. 页面怎么使用

### 注册账号

1. 打开首页。
2. 点击右上角“注册”。
3. 输入用户名、邮箱、从下拉框选择小区、密码。
4. 注册成功后会跳转到登录页。

### 登录账号

1. 点击右上角“登录”。
2. 输入用户名和密码。
3. 登录成功后会回到首页。
4. 首页右上角会显示：`当前账号：你的用户名`。

### 退出登录

登录后，首页右上角会出现“退出登录”。点击后会退出当前账号，页面恢复显示“登录 / 注册”。

### 上传图片或视频

1. 先登录账号。
2. 点击首页的“上传图片或视频”。
3. 填写标题和描述。
4. 选择文件。
5. 点击“上传”。
6. 上传成功后会回到首页，并显示新内容。

### 发表评论

1. 先登录账号。
2. 在首页找到某个图片或视频。
3. 在评论框中输入内容。
4. 点击“发送”。

未登录用户可以查看首页内容，但不能上传和评论。

## 6. 工程规则

### 启动端口

本地开发默认监听：

```text
0.0.0.0:5001
```

本机访问地址：

```text
http://localhost:5001
```

### 数据库规则

当前使用 SQLite 数据库。

数据库配置在 `app.py` 中：

```python
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///community.db'
```

在 Flask 中，这个相对路径通常会落到 `instance/community.db`。

项目启动时会执行 `db.create_all()`，如果表不存在，会自动创建用户、媒体、评论相关数据表。

### 上传文件规则

上传目录：

```text
static/uploads/
```

最大上传大小：

```text
500MB
```

支持图片格式：

```text
png, jpg, jpeg, gif, webp
```

支持视频格式：

```text
mp4, mov, avi, mkv, wmv, flv
```

视频处理规则：

- MP4 视频直接保存。
- 非 MP4 视频会调用 FFmpeg 转成 MP4。
- 转换成功后，原始视频文件会被删除，只保留 MP4。
- 转换失败时会提示“视频转换失败，请重试”。

### 登录规则

当前登录状态通过 Flask `session` 保存：

- 登录成功后保存用户 ID 和用户名。
- 首页根据登录状态显示“当前账号”或“登录 / 注册”。
- 上传和评论会使用当前登录用户 ID。
- 退出登录会清空 session。

### 磁盘空间告警规则

`app.py` 里有一个后台线程，每小时检查一次服务器 `/` 分区剩余空间。

如果剩余空间小于 5GB，会尝试发送邮件提醒。

但当前 SMTP 邮箱、密码、收件人仍写在代码中，且是示例/硬编码配置。正式部署前建议改成环境变量。

## 7. 当前限制和注意事项

这个项目可以本地运行和演示，但还不是完整的生产级系统。上线前需要特别注意：

1. `SECRET_KEY` 仍是占位值：
   - 当前代码中是 `your-secret-key-here`。
   - 生产环境应改为随机、安全、不公开的值。

2. 本地启动使用 `debug=True`：
   - 只适合本地开发。
   - 生产环境不要直接用 `python app.py` 对外提供服务。

3. 邮件告警配置仍是硬编码：
   - Gmail 邮箱和应用密码是占位值。
   - 生产环境建议用环境变量配置 SMTP。

4. 视频转码是同步执行：
   - 上传大视频时，请求会等待 FFmpeg 转码完成。
   - CPU-only 服务器可以运行，但转码速度取决于 CPU 性能。

5. 文件名可能冲突：
   - 当前使用 `secure_filename(file.filename)` 清理文件名。
   - 如果两个用户上传同名文件，后上传的文件可能覆盖先上传的文件。
   - 后续建议改成“时间戳 + 随机字符串”的唯一文件名。

6. 不支持的文件可能已经保存：
   - 当前上传逻辑先保存文件，再判断扩展名。
   - 如果是不支持格式，可能会有残留文件。
   - 后续建议先判断格式，再保存。

7. 部分静态资源引用缺失：
   - `login.html` 和 `register.html` 引用了 `/static/style.css`，当前项目中没有这个文件。
   - `upload.html` 引用了 `/static/images/community-bg.jpg`，当前项目中没有这个图片。
   - 这不影响核心功能，但可能影响页面样式或背景图。

## 8. 阿里云公网部署建议

你希望优先用阿里云，并且选择“均衡稳定”的 CPU-only 方案。这个项目不需要 GPU。

### 推荐服务器

优先推荐：

- 阿里云轻量应用服务器
- 系统选择 Ubuntu 22.04 LTS 或 Ubuntu 24.04 LTS
- 规格建议：2 核 CPU / 4GB 内存
- 磁盘建议：50GB 或以上 SSD
- 公网带宽：3M 到 5M

如果你更看重标准化运维和后续扩展，也可以选择阿里云 ECS：

- ECS 通用型或计算型实例
- 2 核 4GB 起步
- Ubuntu 22.04 LTS
- 40GB 到 80GB 云盘
- 3M 到 5M 公网带宽

### 为什么推荐 2 核 4GB

- Flask + SQLite 本身不重。
- 图片上传和浏览对 CPU 要求低。
- 视频转码会吃 CPU，1 核机器可能很慢。
- 2GB 内存也能跑，但 4GB 更稳。
- 上传图片/视频会占磁盘，磁盘不要太小。

### 安全组建议

只开放必要端口：

| 端口 | 用途 |
| --- | --- |
| 22 | SSH 登录服务器 |
| 80 | HTTP 公网访问 |
| 443 | HTTPS 公网访问 |

不要直接把 Flask 的 5001 端口开放到公网。生产环境建议让 Nginx 对外访问，再由 Nginx 转发到本机的 Gunicorn。

## 9. 阿里云部署步骤

下面以 Ubuntu 服务器为例。

### 第一步：购买服务器

1. 登录阿里云控制台。
2. 选择轻量应用服务器或 ECS。
3. 镜像选择 Ubuntu 22.04 LTS 或 24.04 LTS。
4. 规格选择 2 核 4GB。
5. 磁盘选择 50GB 或以上。
6. 公网带宽选择 3M 到 5M。
7. 设置登录密码或 SSH 密钥。
8. 安全组开放 22、80、443。

### 第二步：SSH 登录服务器

在本地终端执行：

```bash
ssh root@你的服务器公网IP
```

如果使用密钥：

```bash
ssh -i 你的密钥文件 root@你的服务器公网IP
```

### 第三步：安装系统依赖

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip ffmpeg nginx
```

### 第四步：上传代码

建议部署目录：

```text
/opt/community-media
```

可以用 `scp` 上传：

```bash
scp -r ./10_收集上传图片 root@你的服务器公网IP:/opt/community-media
```

也可以把代码推到 Git 仓库后，在服务器上 `git clone`。

### 第五步：创建虚拟环境并安装依赖

```bash
cd /opt/community-media
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 第六步：创建必要目录

```bash
mkdir -p static/uploads
mkdir -p instance
```

如果后续用 `www-data` 用户运行服务：

```bash
sudo chown -R www-data:www-data /opt/community-media/static/uploads /opt/community-media/instance
```

### 第七步：用 Gunicorn 手动验证

```bash
cd /opt/community-media
source .venv/bin/activate
gunicorn -w 2 --timeout 300 -b 127.0.0.1:5001 app:app
```

另开一个 SSH 窗口，在服务器上执行：

```bash
curl http://127.0.0.1:5001
```

如果能返回 HTML，说明 Flask 服务可以启动。

### 第八步：配置 systemd 开机自启

创建服务文件：

```bash
sudo nano /etc/systemd/system/community-media.service
```

写入以下内容，注意路径要和你的实际部署路径一致：

```ini
[Unit]
Description=Community Media Flask App
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/community-media
Environment="PATH=/opt/community-media/.venv/bin"
ExecStart=/opt/community-media/.venv/bin/gunicorn -w 2 --timeout 300 -b 127.0.0.1:5001 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

启用并启动服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable community-media
sudo systemctl start community-media
sudo systemctl status community-media
```

查看日志：

```bash
journalctl -u community-media -f
```

### 第九步：配置 Nginx 反向代理

创建 Nginx 配置：

```bash
sudo nano /etc/nginx/sites-available/community-media
```

写入：

```nginx
server {
    listen 80;
    server_name 你的域名或服务器公网IP;

    client_max_body_size 500M;

    location /static/ {
        alias /opt/community-media/static/;
    }

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

启用配置：

```bash
sudo ln -s /etc/nginx/sites-available/community-media /etc/nginx/sites-enabled/community-media
sudo nginx -t
sudo systemctl restart nginx
```

然后浏览器访问：

```text
http://你的服务器公网IP
```

### 第十步：配置域名和 HTTPS

如果你有域名：

1. 到域名 DNS 控制台添加 A 记录，指向服务器公网 IP。
2. 把 Nginx 配置里的 `server_name` 改为你的域名。
3. 使用 Certbot 配置 HTTPS。

Ubuntu 上可参考：

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d 你的域名
```

## 10. 备份建议

至少备份两个位置：

```text
/opt/community-media/instance/community.db
/opt/community-media/static/uploads/
```

建议频率：

- 数据库：每天备份一次。
- 上传文件：每周备份一次，或按上传量调整。
- 至少保留最近 7 天备份。

简单手动备份示例：

```bash
mkdir -p /opt/backups/community-media
cp /opt/community-media/instance/community.db /opt/backups/community-media/community-$(date +%F).db
tar -czf /opt/backups/community-media/uploads-$(date +%F).tar.gz /opt/community-media/static/uploads
```

## 11. 常见问题

### 启动时报 `ModuleNotFoundError`

说明 Python 依赖没装好。重新执行：

```bash
source .venv/bin/activate
pip install -r requirements.txt
```

### 上传非 MP4 视频失败

检查 FFmpeg 是否安装：

```bash
ffmpeg -version
```

如果没有安装：

```bash
sudo apt install -y ffmpeg
```

### 登录后首页还是显示“登录 / 注册”

请确认：

1. 登录时用户名和密码正确。
2. 浏览器没有禁用 Cookie。
3. `app.py` 中登录成功后会写入 `session['user_id']` 和 `session['username']`。
4. 首页模板根据 `session.get('user_id')` 判断显示内容。

### 公网 IP 打不开网站

依次检查：

1. 阿里云安全组是否开放 80 端口。
2. Nginx 是否运行：`sudo systemctl status nginx`。
3. Flask 服务是否运行：`sudo systemctl status community-media`。
4. Nginx 配置是否通过：`sudo nginx -t`。
5. 服务器本机能否访问：`curl http://127.0.0.1:5001`。

### 上传大文件失败

检查：

1. Flask 限制是 500MB。
2. Nginx 配置中是否有 `client_max_body_size 500M;`。
3. 服务器磁盘空间是否足够。
4. 上传视频转码可能需要较长时间，Gunicorn 已建议设置 `--timeout 300`。

## 12. 后续改进建议

如果后续继续增强项目，建议优先做：

1. 把 `SECRET_KEY`、SMTP、数据库路径改为环境变量。
2. 上传文件改成唯一文件名，避免同名覆盖。
3. 先检查文件类型，再保存文件，避免不支持文件残留。
4. 给登录、注册、上传页面统一一套导航和样式。
5. 给评论列表增加真实展示，而不是只显示新增评论。
6. 视频转码改成后台任务，避免请求长时间等待。
7. 增加管理员页面，用于删除不合适内容和清理上传文件。
8. 从 SQLite 升级到 PostgreSQL，以支持更多用户和并发访问。
