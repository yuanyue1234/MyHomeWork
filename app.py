from flask import Flask, jsonify, send_from_directory, request
from flask_cors import CORS
import os
import json

app = Flask(__name__)
CORS(app)

def get_courses():
    courses = []
    for course_dir in os.listdir('.'):
        if os.path.isdir(course_dir) and not course_dir.startswith('.'):
            course = {
                'id': course_dir,
                'title': course_dir,  # 可以根据需要修改标题
                'dates': []
            }
            for date_dir in os.listdir(course_dir):
                if os.path.isdir(os.path.join(course_dir, date_dir)):
                    date_info = {
                        'date': date_dir,
                        'description': f'{course_dir} - {date_dir}',  # 可以根据需要修改描述
                        'files': []
                    }
                    for file in os.listdir(os.path.join(course_dir, date_dir)):
                        if file.endswith('.html') and file.startswith('0'):
                            date_info['files'].append(file)
                    if date_info['files']:
                        course['dates'].append(date_info)
            if course['dates']:
                courses.append(course)
    return courses

@app.route('/courses', methods=['GET'])
def get_courses_route():
    return jsonify(get_courses())

@app.route('/courses', methods=['POST'])
def add_course():
    data = request.json
    course_id = data['id']
    course_title = data['title']
    dates = data['dates']

    if os.path.exists(course_id):
        return jsonify({"error": "Course already exists"}), 400

    os.makedirs(course_id)
    for date in dates:
        date_dir = os.path.join(course_id, date['date'])
        os.makedirs(date_dir)
        file_name = '01.html'  # 默认文件名
        file_path = os.path.join(date_dir, file_name)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(date['content'])

    return jsonify({"message": "Course added successfully"}), 201

@app.route('/<path:path>')
def serve_file(path):
    # 检查文件是否存在
    if os.path.isfile(path):
        return send_from_directory('.', path)
    else:
        # 如果文件不存在，返回 404 错误
        return "File not found", 404

# 添加一个新的路由来处理课程内容
@app.route('/course/<course_id>/<date>/<file>')
def serve_course_file(course_id, date, file):
    file_path = os.path.join(course_id, date, file)
    if os.path.isfile(file_path):
        return send_from_directory('.', file_path)
    else:
        return "File not found", 404

if __name__ == '__main__':
    app.run(debug=True)