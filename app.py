from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime, timedelta

app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
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

@app.route('/health')
def health_check():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    # 启动时读取一次数据以初始化更新时间
    courses, _ = get_courses()
    # app.run(debug=True)
    app.run(host='0.0.0.0', port=5000, debug=False)
