#coding=utf-8
"""
# Author: Wenbing.Wang
# Created Time : 二  9/23 08:01:54 2025

# File Name: app.py
# Description:

"""

 #coding=utf-8
"""
# Author: Wenbing.Wang
# Created Time : 一  9/22 20:52:13 2025

# File Name: app.py
# Description: 小区媒体分享平台 - 完整版

"""

import os
import subprocess
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
import psutil
import smtplib
from email.mime.text import MIMEText
from email.header import Header
import threading
import time

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///community.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# 允许的文件扩展名
ALLOWED_IMAGE_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
ALLOWED_VIDEO_EXTENSIONS = {'mp4', 'mov', 'avi', 'mkv', 'wmv', 'flv'}

# 预置小区列表：上线前请替换为你实际要服务的小区名称
COMMUNITY_OPTIONS = [
    '朝阳花园',
    '幸福家园',
    '阳光丽景',
    '锦绣雅苑',
    '绿城小区',
    '清风里',
]

db = SQLAlchemy(app)

# 数据库模型 - 增加媒体类型字段
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    community = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    media_items = db.relationship('Media', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

class Media(db.Model):  # 重命名Image为Media以支持多种类型
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    media_type = db.Column(db.String(10), nullable=False)  # 'image' 或 'video'
    comments = db.relationship('Comment', backref='media', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    media_id = db.Column(db.Integer, db.ForeignKey('media.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 创建数据库
with app.app_context():
    db.create_all()

# 辅助函数
def allowed_file(filename, file_type='image'):
    """检查文件扩展名是否允许"""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    if file_type == 'image':
        return ext in ALLOWED_IMAGE_EXTENSIONS
    elif file_type == 'video':
        return ext in ALLOWED_VIDEO_EXTENSIONS
    return False

def convert_to_mp4(input_path, output_path):
    """使用FFmpeg将视频转换为MP4格式"""
    try:
        cmd = [
            'ffmpeg', '-i', input_path,
            '-c:v', 'libx264', '-c:a', 'aac',
            '-strict', 'experimental', output_path
        ]
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"视频转换错误: {e}")
        return False

def check_disk_space():
    """检查磁盘空间，不足时发送邮件"""
    disk = psutil.disk_usage('/')
    free_gb = disk.free / (1024**3)
    
    # 如果剩余空间小于5GB，发送警告邮件
    if free_gb < 5:
        send_disk_alert(free_gb)

def send_disk_alert(free_gb):
    """发送磁盘空间警告邮件"""
    mail_host = "smtp.gmail.com"  # 使用Gmail SMTP服务器
    mail_user = "your-bot-email@gmail.com"  # 发送邮件的机器人邮箱
    mail_pass = "your-app-password"  # 应用专用密码
    
    sender = mail_user
    receivers = ['wangwenbingood1988@gmail.com']  # 您的邮箱
    
    content = f"""
    小区媒体分享平台磁盘空间警告：
    
    服务器磁盘剩余空间仅剩 {free_gb:.2f} GB。
    请及时清理磁盘空间，避免服务中断。
    
    此邮件由系统自动发送，请勿回复。
    """
    
    message = MIMEText(content, 'plain', 'utf-8')
    message['From'] = Header("小区媒体平台监控", 'utf-8')
    message['To'] = Header("管理员", 'utf-8')
    message['Subject'] = Header("磁盘空间不足警告", 'utf-8')
    
    try:
        smtp_obj = smtplib.SMTP_SSL(mail_host, 465)
        smtp_obj.login(mail_user, mail_pass)
        smtp_obj.sendmail(sender, receivers, message.as_string())
        print("磁盘空间警告邮件发送成功")
    except Exception as e:
        print(f"邮件发送失败: {e}")

# 后台磁盘监控线程
def disk_monitor():
    """后台线程，定期检查磁盘空间"""
    while True:
        check_disk_space()
        time.sleep(3600)  # 每小时检查一次

# 启动磁盘监控线程
monitor_thread = threading.Thread(target=disk_monitor)
monitor_thread.daemon = True
monitor_thread.start()

# 路由定义
@app.route('/')
def index():
    media_list = Media.query.order_by(Media.created_at.desc()).all()
    return render_template('index.html', media_list=media_list)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        community = request.form['community']

        # 检查用户是否已存在
        if User.query.filter_by(username=username).first():
            flash('用户名已存在')
            return redirect(url_for('register'))

        if User.query.filter_by(email=email).first():
            flash('邮箱已存在')
            return redirect(url_for('register'))

        if community not in COMMUNITY_OPTIONS:
            flash('请选择列表中的小区')
            return redirect(url_for('register'))

        # 创建新用户
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, email=email, community=community)
        db.session.add(new_user)
        db.session.commit()

        flash('注册成功，请登录')
        return redirect(url_for('login'))

    return render_template('register.html', community_options=COMMUNITY_OPTIONS)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            flash('登录成功')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误')

    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('已退出登录')
    return redirect(url_for('index'))

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'user_id' not in session:
        flash('请先登录后再上传文件')
        return redirect(url_for('login'))

    if request.method == 'POST':
        # 检查文件是否在请求中
        if 'file' not in request.files:
            flash('没有选择文件')
            return redirect(url_for('upload'))
        
        file = request.files['file']
        
        # 检查文件名是否为空
        if file.filename == '':
            flash('没有选择文件')
            return redirect(url_for('upload'))
        
        title = request.form.get('title', '')
        description = request.form.get('description', '')
        
        if file and file.filename:
            filename = secure_filename(file.filename)
            file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            # 确定媒体类型并处理
            media_type = 'image'
            final_filename = filename
            
            # 检查是否为视频文件
            if file_ext in ALLOWED_VIDEO_EXTENSIONS:
                media_type = 'video'
                # 如果不是MP4格式，进行转换
                if file_ext != 'mp4':
                    mp4_filename = f"{filename.rsplit('.', 1)[0]}.mp4"
                    mp4_path = os.path.join(app.config['UPLOAD_FOLDER'], mp4_filename)
                    if convert_to_mp4(file_path, mp4_path):
                        os.remove(file_path)  # 删除原始文件
                        final_filename = mp4_filename
                    else:
                        flash('视频转换失败，请重试')
                        return redirect(url_for('upload'))
            # 检查是否为图片文件
            elif file_ext in ALLOWED_IMAGE_EXTENSIONS:
                media_type = 'image'
            else:
                flash('不支持的文件类型')
                return redirect(url_for('upload'))
            
            # 保存到数据库
            user_id = session['user_id']
            
            new_media = Media(
                filename=final_filename, 
                title=title, 
                description=description, 
                user_id=user_id,
                media_type=media_type
            )
            db.session.add(new_media)
            db.session.commit()
            
            # 检查磁盘空间
            check_disk_space()
            
            flash('文件上传成功')
            return redirect(url_for('index'))
    
    return render_template('upload.html')

@app.route('/comment', methods=['POST'])
def add_comment():
    if 'user_id' not in session:
        return jsonify({
            'success': False,
            'message': '请先登录后再发表评论'
        }), 401

    content = request.form['content']
    media_id = request.form['media_id']
    user_id = session['user_id']
    
    new_comment = Comment(content=content, user_id=user_id, media_id=media_id)
    db.session.add(new_comment)
    db.session.commit()
    
    # 获取评论作者的用户名
    author = User.query.get(user_id).username
    
    return jsonify({
        'success': True,
        'comment': {
            'content': content,
            'author': author,
            'created_at': new_comment.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })

@app.route('/api/media')
def get_media():
    """API接口，返回所有媒体数据"""
    media_list = Media.query.order_by(Media.created_at.desc()).all()
    result = []
    
    for media in media_list:
        result.append({
            'id': media.id,
            'filename': media.filename,
            'title': media.title,
            'description': media.description,
            'author': media.author.username,
            'created_at': media.created_at.strftime('%Y-%m-%d %H:%M'),
            'comment_count': len(media.comments),
            'media_type': media.media_type
        })
    
    return jsonify(result)

# 应用启动入口 - 这是之前遗漏的关键部分！
if __name__ == '__main__':
    # 确保上传目录存在
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
        print(f"创建上传目录: {app.config['UPLOAD_FOLDER']}")
    
    print("启动小区媒体分享平台...")
    print("访问地址: http://localhost:5001")
    print("局域网访问: http://<您的IP地址>:5001")
    
    # 启动Flask应用，使用5001端口避免与系统服务冲突
    app.run(debug=True, host='0.0.0.0', port=5001)
