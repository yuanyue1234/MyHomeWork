from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import json
import logging
from datetime import datetime
import threading
import time

app = Flask(__name__, static_url_path='/static', static_folder='static')
CORS(app)

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

DATA_FILE = 'courses.json'
COURSES_ROOT = '.'  # 课程文件根目录
courses_data = None  # 全局变量存储课程数据
last_update_time = None
UPDATE_INTERVAL = 24 * 60 * 60  # 24小时的秒数

def scan_course_directory():
    """扫描课程目录获取实际的课程结构"""
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
        return courses_dict
    
    except Exception as e:
        logger.error(f"扫描课程目录时出错: {str(e)}")
        return {}

def update_courses_json(courses_dict):
    """更新courses.json文件"""
    if not courses_dict:
        return False
        
    try:
        # 读取现有的courses.json以保留自定义标题和顺序
        existing_courses = {}
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                existing_courses = json.load(f)
        
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

def initialize_courses():
    """初始化课程数据"""
    global courses_data, last_update_time
    
    # 扫描目录获取最新课程数据
    scanned_courses = scan_course_directory()
    if scanned_courses:
        update_courses_json(scanned_courses)
        courses_data = scanned_courses
        last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info("课程数据初始化完成")
    else:
        # 如果扫描失败，尝试从文件加载
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                courses_data = json.load(f)
                last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info("从文件加载课程数据成功")
        except Exception as e:
            logger.error(f"初始化课程数据失败: {str(e)}")
            courses_data = {}

def scheduled_update():
    """定时更新函数"""
    global courses_data, last_update_time
    while True:
        try:
            logger.info("执行定时更新...")
            # 扫描目录获取最新课程数据
            scanned_courses = scan_course_directory()
            if scanned_courses:
                update_courses_json(scanned_courses)
                courses_data = scanned_courses
                last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                logger.info(f"定时更新完成，更新时间：{last_update_time}")
            else:
                logger.warning("定时更新未发现新数据")
        except Exception as e:
            logger.error(f"定时更新出错: {str(e)}")
        
        # 休眠24小时
        time.sleep(UPDATE_INTERVAL)

@app.route('/courses', methods=['GET'])
def get_courses():
    """获取课程数据"""
    if courses_data is None:
        return jsonify({"error": "Courses data not initialized"}), 500
    
    return jsonify({
        'courses': list(courses_data.values()),
        'lastUpdate': last_update_time
    })

@app.route('/courses/reorder', methods=['PUT'])
def reorder_courses():
    """更新课程顺序"""
    global courses_data, last_update_time
    try:
        new_order = request.json
        
        # 更新顺序
        for item in new_order:
            if item['id'] in courses_data:
                courses_data[item['id']]['order'] = item['order']
        
        # 保存更新后的数据
        update_courses_json(courses_data)
        last_update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        return jsonify({
            "message": "Order updated successfully",
            "lastUpdate": last_update_time
        })
    except Exception as e:
        logger.error(f"更新课程顺序时出错: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/course/<course_id>/<date>/<file>')
def serve_course_file(course_id, date, file):
    """服务课程文件"""
    try:
        possible_paths = [
            os.path.join(course_id, date, file),
            os.path.join('courses', course_id, date, file),
            os.path.join('static', 'courses', course_id, date, file)
        ]
        
        for file_path in possible_paths:
            if os.path.isfile(file_path):
                directory = os.path.dirname(file_path)
                filename = os.path.basename(file_path)
                return send_from_directory(directory, filename)
        
        logger.error(f"找不到文件: {course_id}/{date}/{file}")
        return "File not found", 404
        
    except Exception as e:
        logger.error(f"访问课程文件时出错: {str(e)}")
        return str(e), 500

@app.route('/<path:path>')
def serve_file(path):
    """通用文件服务路由"""
    try:
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
    print("\n=== 课程作业展示系统 ===")
    print("正在初始化课程数据...")
    
    # 启动时初始化课程数据
    initialize_courses()
    
    # 创建并启动定时更新线程
    update_thread = threading.Thread(target=scheduled_update, daemon=True)
    update_thread.start()
    
    print("\n=== 服务器信息 ===")
    print(f"* 运行地址: http://localhost:5000")
    print(f"* 数据文件: {os.path.abspath(DATA_FILE)}")
    print(f"* 自动更新间隔: 24小时")
    print("* 按 Ctrl+C 停止服务器")
    print("\n=== 服务器日志 ===")
    
    app.run(host='0.0.0.0', port=5000, debug=False)