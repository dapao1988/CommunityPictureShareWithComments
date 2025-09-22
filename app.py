#coding=utf-8
"""
# Author: Wenbing.Wang
# Created Time : 一  9/22 20:52:13 2025

# File Name: app.py
# Description:

"""

# app.py
import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///community.db'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

db = SQLAlchemy(app)

# 数据库模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    community = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    images = db.relationship('Image', backref='author', lazy=True)
    comments = db.relationship('Comment', backref='author', lazy=True)

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('Comment', backref='image', lazy=True)

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# 创建数据库
with app.app_context():
    db.create_all()

# 路由定义
@app.route('/')
def index():
    images = Image.query.order_by(Image.created_at.desc()).all()
    return render_template('index.html', images=images)

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
        
        # 创建新用户
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password, email=email, community=community)
        db.session.add(new_user)
        db.session.commit()
        
        flash('注册成功，请登录')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        
        if user and check_password_hash(user.password, password):
            # 这里应该设置session或使用Flask-Login
            flash('登录成功')
            return redirect(url_for('index'))
        else:
            flash('用户名或密码错误')
    
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    # 这里应该检查用户是否已登录
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        file = request.files['image']
        
        if file:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 这里应该获取当前登录用户的ID
            user_id = 1  # 临时值，实际应从session获取
            
            new_image = Image(filename=filename, title=title, description=description, user_id=user_id)
            db.session.add(new_image)
            db.session.commit()
            
            flash('图片上传成功')
            return redirect(url_for('index'))
    
    return render_template('upload.html')

@app.route('/comment', methods=['POST'])
def add_comment():
    content = request.form['content']
    image_id = request.form['image_id']
    
    # 这里应该获取当前登录用户的ID
    user_id = 1  # 临时值，实际应从session获取
    
    new_comment = Comment(content=content, user_id=user_id, image_id=image_id)
    db.session.add(new_comment)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'comment': {
            'content': content,
            'author': User.query.get(user_id).username,
            'created_at': new_comment.created_at.strftime('%Y-%m-%d %H:%M')
        }
    })

@app.route('/api/images')
def get_images():
    images = Image.query.order_by(Image.created_at.desc()).all()
    image_list = []
    
    for image in images:
        image_list.append({
            'id': image.id,
            'filename': image.filename,
            'title': image.title,
            'description': image.description,
            'author': image.author.username,
            'created_at': image.created_at.strftime('%Y-%m-%d %H:%M'),
            'comment_count': len(image.comments)
        })
    
    return jsonify(image_list)

if __name__ == '__main__':
    # 确保上传目录存在
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    app.run(debug=True)
