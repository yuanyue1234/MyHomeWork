from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime, timedelta

app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)

# 配置日志
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

DATA_FILE = 'courses.json'
COURSES_ROOT = '.'  # 课程文件根目录
last_update_time = None
last_scan_time = None
SCAN_INTERVAL = timedelta(minutes=5)  # 设置扫描间隔为5分钟
cached_courses = None

def should_scan():
    """判断是否需要重新扫描目录"""
    global last_scan_time
    if last_scan_time is None:
        return True
    return datetime.now() - last_scan_time > SCAN_INTERVAL

def scan_course_directory():
    """扫描课程目录获取实际的课程结构"""
    global last_scan_time, cached_courses
    
    # 如果缓存存在且不需要重新扫描，直接返回缓存
    if cached_courses and not should_scan():
        return cached_courses
    
    courses_dict = {}
    
    try:
        # 遍历根目录下的所有文件夹
        for course_id in os.listdir(COURSES_ROOT):
            course_path = os.path.join(COURSES_ROOT, course_id)
            
            # 检查是否为目录且不是特殊目录
            if os.path.isdir(course_path) and not course_id.startswith(('.', '_', 'static')):
                dates = []
                
                # 遍历课程目录下的日期文件夹
                for date_folder in os.listdir(course_path):
                    date_path = os.path.join(course_path, date_folder)
                    
                    if os.path.isdir(date_path):
                        files = [f for f in os.listdir(date_path) 
                               if os.path.isfile(os.path.join(date_path, f)) and f.endswith('.html')]
                        
                        if files:  # 只添加包含html文件的日期
                            dates.append({
                                'date': date_folder,
                                'description': f'第{len(dates) + 1}次作业',
                                'files': files
                            })
                
                if dates:  # 只添加包含作业的课程
                    courses_dict[course_id] = {
                        'id': course_id,
                        'title': f'{course_id} 课程',
                        'order': len(courses_dict) + 1,
                        'dates': sorted(dates, key=lambda x: x['date'])
                    }
        
        logger.info(f"扫描到 {len(courses_dict)} 个课程")
        last_scan_time = datetime.now()
        cached_courses = courses_dict
        return courses_dict
    
    except Exception as e:
        logger.error(f"扫描课程目录时出错: {str(e)}")
        return {}

def update_courses_json(courses_dict):
    """更新courses.json文件"""
    if not courses_dict:  # 如果数据为空，不更新文件
        return False
        
    try:
        # 读取现有的courses.json
        existing_courses = {}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                existing_courses = json.load(f)
        
        # 检查数据是否有变化
        if existing_courses == courses_dict:
            logger.info("课程数据没有变化，无需更新")
            return True
        
        # 合并现有数据和新数据
        for course_id, course_data in courses_dict.items():
            if course_id in existing_courses:
                # 保留现有的标题和顺序
                course_data['title'] = existing_courses[course_id].get('title', course_data['title'])
                course_data['order'] = existing_courses[course_id].get('order', course_data['order'])
        
        # 保存更新后的数据
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(courses_dict, f, ensure_ascii=False, indent=4)
            
        logger.info(f"已更新 {DATA_FILE}")
        return True
    except Exception as e:
        logger.error(f"更新 {DATA_FILE} 时出错: {str(e)}")
        return False

def get_courses():
    """获取课程数据，优先使用缓存"""
    global last_update_time
    
    try:
        # 检查是否需要扫描
        if should_scan():
            scanned_courses = scan_course_directory()
            if scanned_courses:
                update_courses_json(scanned_courses)
                last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                return list(scanned_courses.values()), last_update_time
        elif cached_courses:
            return list(cached_courses.values()), last_update_time
        
        # 如果没有缓存或扫描失败，从courses.json读取
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            courses_dict = json.load(f)
            
        if last_update_time is None:
            last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
        return list(courses_dict.values()), last_update_time
    
    except Exception as e:
        logger.error(f"获取课程数据时出错: {str(e)}")
        return [], None

@app.route('/courses', methods=['GET'])
def get_courses_route():
    courses, update_time = get_courses()
    return jsonify({
        'courses': courses,
        'lastUpdate': update_time
    })

@app.route('/courses', methods=['POST'])
def add_course():
    global last_update_time
    try:
        data = request.json
        course_id = data['id']
        dates = data['dates']

        # 读取现有数据
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                courses_dict = json.load(f)
        except:
            courses_dict = {}

        if course_id in courses_dict:
            return jsonify({"error": "Course already exists"}), 400

        # 添加新课程
        courses_dict[course_id] = {
            'id': course_id,
            'title': data['title'],
            'order': len(courses_dict) + 1,
            'dates': dates
        }

        # 保存更新后的数据
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(courses_dict, f, ensure_ascii=False, indent=4)
            
        # 更新时间戳
        last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"添加了新课程，更新时间：{last_update_time}")

        return jsonify({
            "message": "Course added successfully",
            "lastUpdate": last_update_time
        }), 201
    except Exception as e:
        logger.error(f"添加课程时出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/courses/reorder', methods=['PUT'])
def reorder_courses():
    global last_update_time
    try:
        new_order = request.json
        
        # 读取现有数据
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            courses_dict = json.load(f)
        
        # 更新顺序
        for item in new_order:
            if item['id'] in courses_dict:
                courses_dict[item['id']]['order'] = item['order']
        
        # 保存更新后的数据
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(courses_dict, f, ensure_ascii=False, indent=4)
            
        # 更新时间戳
        last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"更新了课程顺序，更新时间：{last_update_time}")
        
        return jsonify({
            "message": "Order updated successfully",
            "lastUpdate": last_update_time
        })
    except Exception as e:
        logger.error(f"更新课程顺序时出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/course/<course_id>/<date>/<file>')
def serve_course_file(course_id, date, file):
    """服务课程文件，支持多级目录结构"""
    try:
        # 构建可能的文件路径
        possible_paths = [
            os.path.join(course_id, date, file),  # 直接路径
            os.path.join('courses', course_id, date, file),  # courses子目录
            os.path.join('static', 'courses', course_id, date, file)  # static/courses子目录
        ]
        
        # 尝试所有可能的路径
        for file_path in possible_paths:
            if os.path.isfile(file_path):
                directory = os.path.dirname(file_path)
                filename = os.path.basename(file_path)
                return send_from_directory(directory, filename)
        
        # 如果找不到文件，记录错误并返回404
        logger.error(f"找不到文件: {course_id}/{date}/{file}")
        logger.error(f"尝试过的路径: {possible_paths}")
        return "File not found", 404
        
    except Exception as e:
        logger.error(f"访问课程文件时出错: {str(e)}")
        return str(e), 500

@app.route('/<path:path>')
def serve_file(path):
    """通用文件服务路由"""
    try:
        # 检查文件是否存在于根目录或static目录
        if os.path.isfile(path):
            directory = os.path.dirname(path)
            filename = os.path.basename(path)
            return send_from_directory(directory or '.', filename)
        elif os.path.isfile(os.path.join('static', path)):
            return send_from_directory('static', path)
        else:
            logger.error(f"找不到文件: {path}")
            return "File not found", 404
    except Exception as e:
        logger.error(f"访问文件时出错: {str(e)}")
        return str(e), 500
    
def update_jquery_paths():
    jquery_dir = 'jquery'  # Changed from 'JQuery' to 'jquery' for consistency
    updated_files = []
    
    # Walk through all HTML files in jquery directory
    for root, dirs, files in os.walk(jquery_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check and update jQuery reference path
                if '<script src="../../static/js/jquery-3.4.1.min.js"></script>' not in content:
                    # Replace old jQuery references with new path
                    replacements = [
                        ('<script src="js/jquery-1.12.4.js"></script>', 
                         '<script src="../../static/js/jquery-3.4.1.min.js"></script>'),
                        ('<script src="../static/jquery-3.4.1.min.js"></script>', 
                         '<script src="../../static/js/jquery-3.4.1.min.js"></script>'),
                        # Add more patterns if needed
                    ]
                    
                    new_content = content
                    for old_path, new_path in replacements:
                        if old_path in new_content:
                            new_content = new_content.replace(old_path, new_path)
                            updated_files.append(file_path)
                    
                    # If no existing jQuery reference found, add it after <head>
                    if all(old_path not in content for old_path, _ in replacements):
                        new_content = new_content.replace(
                            '<head>',
                            '<head>\n\t<script src="../../static/js/jquery-3.4.1.min.js"></script>'
                        )
                        updated_files.append(file_path)
                    
                    # Write back if content changed
                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)

    # Log results
    if updated_files:
        print('Updated jQuery reference paths in the following files:')
        for file_path in sorted(set(updated_files)):  # Remove duplicates and sort
            print(f'Updated: {file_path}')
    else:
        print('No files needed updating.')
    jquery_dir = 'JQuery'
    updated_files = []  # 用于存储更新的文件路径
    
    # 遍历JQuery目录下的所有HTML文件
    for root, dirs, files in os.walk(jquery_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 检查是否已经有jQuery路径
                if '<script src="../static/js/jquery-3.4.1.min.js"></script>' not in content:
                    # 如果没有jQuery路径，添加正确的路径
                    content = content.replace(
                        '<head>',
                        '<head>\n\t<script src="../static/js/jquery-3.4.1.min.js"></script>'
                    )
                    updated_files.append(file_path)  # 记录更新的文件路径
                
                # 替换旧的jQuery引用路径
                new_content = content.replace(
                    '<script src="js/jquery-1.12.4.js"></script>',
                    '<script src="../static/jquery-3.4.1.min.js"></script>'
                )
                
                # 如果内容有变化，写回文件
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    updated_files.append(file_path)  # 记录更新的文件路径

    # 仅显示更新的文件路径
    if updated_files:
        print('替换不正常jQuery引用路径的文件路径：') 
        for updated_file in updated_files:
            print(f'Updated: {updated_file}')
    else:
        print('没有需要更新的文件。')
def update_bootstrap_paths():
    bootstrap_dir = 'Bootstrap'  # Bootstrap 目录
    updated_files = []
    
    # 遍历 Bootstrap 目录下的所有 HTML 文件
    for root, dirs, files in os.walk(bootstrap_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                # 读取文件内容
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                new_bootstrap_path = '../../static/bootstrap-5.3.3-dist/js/bootstrap.min.js'
                new_script_tag = f'<script src="{new_bootstrap_path}"></script>'
                
                # 需要替换的可能的旧路径模式
                old_patterns = [
                    '<script src="js/bootstrap.min.js"></script>',
                    '<script src="../js/bootstrap.min.js"></script>',
                    '<script src="bootstrap/js/bootstrap.min.js"></script>',
                    '<script src="../bootstrap/js/bootstrap.min.js"></script>',
                    '<script src="dist/js/bootstrap.min.js"></script>',
                    '<script src="bootstrap.min.js"></script>'
                ]
                
                # 检查是否需要更新
                needs_update = True
                if new_script_tag in content:
                    needs_update = False
                
                new_content = content
                if needs_update:
                    # 替换所有旧的 Bootstrap 引用
                    for old_pattern in old_patterns:
                        if old_pattern in new_content:
                            new_content = new_content.replace(old_pattern, new_script_tag)
                            updated_files.append(file_path)
                    
                    # 如果没有找到任何 Bootstrap 引用，在 </head> 标签前添加
                    if new_content == content and all(pattern not in content for pattern in old_patterns):
                        head_end_pos = new_content.find('</head>')
                        if head_end_pos != -1:
                            new_content = new_content[:head_end_pos] + f'\n\t{new_script_tag}\n' + new_content[head_end_pos:]
                            updated_files.append(file_path)
                
                # 如果内容有变化，写回文件
                if new_content != content:
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(new_content)

    # 输出更新结果
    if updated_files:
        print('更新了以下文件的 Bootstrap 引用路径：')
        for file_path in sorted(set(updated_files)):  # 去重并排序
            print(f'已更新: {file_path}')
    else:
        print('没有需要更新的文件。')

# 查看app.py是否正常正常运行
@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    update_jquery_paths()  # 更新JQuery目录下的所有HTML文件的jQuery引用路径
    update_bootstrap_paths()  # 更新 Bootstrap 路径
    # 启动时读取一次数据以初始化更新时间
    courses, _ = get_courses()
    app.run(host='0.0.0.0', port=5000, debug=False)

    jquery_dir = 'jquery'  # Changed from 'JQuery' to 'jquery' for consistency
    updated_files = []
    
    # Walk through all HTML files in jquery directory
    for root, dirs, files in os.walk(jquery_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                # Read file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check and update jQuery reference path
                if '<script src="../../static/js/jquery-3.4.1.min.js"></script>' not in content:
                    # Replace old jQuery references with new path
                    replacements = [
                        ('<script src="js/jquery-1.12.4.js"></script>', 
                         '<script src="../../static/js/jquery-3.4.1.min.js"></script>'),
                        ('<script src="../static/jquery-3.4.1.min.js"></script>', 
                         '<script src="../../static/js/jquery-3.4.1.min.js"></script>'),
                        # Add more patterns if needed
                    ]
                    
                    new_content = content
                    for old_path, new_path in replacements:
                        if old_path in new_content:
                            new_content = new_content.replace(old_path, new_path)
                            updated_files.append(file_path)
                    
                    # If no existing jQuery reference found, add it after <head>
                    if all(old_path not in content for old_path, _ in replacements):
                        new_content = new_content.replace(
                            '<head>',
                            '<head>\n\t<script src="../../static/js/jquery-3.4.1.min.js"></script>'
                        )
                        updated_files.append(file_path)
                    
                    # Write back if content changed
                    if new_content != content:
                        with open(file_path, 'w', encoding='utf-8') as f:
                            f.write(new_content)

    # Log results
    if updated_files:
        print('Updated jQuery reference paths in the following files:')
        for file_path in sorted(set(updated_files)):  # Remove duplicates and sort
            print(f'Updated: {file_path}')
    else:
        print('No files needed updating.')