from flask import Flask, request, jsonify
from flask_cors import CORS
import json

app = Flask(__name__)
CORS(app)

# 读取课程数据
def read_courses():
    try:
        with open('courses.json', 'r', encoding='utf-8') as f:  # 添加 encoding='utf-8'
            return json.load(f)
    except FileNotFoundError:
        return {}

# 保存课程数据
def save_courses(courses):
    with open('courses.json', 'w', encoding='utf-8') as f:  # 添加 encoding='utf-8'
        json.dump(courses, f, ensure_ascii=False, indent=4)  # 添加 ensure_ascii=False 和 indent=4

# 获取所有课程
@app.route('/courses', methods=['GET'])
def get_courses():
    return jsonify(read_courses())

# 添加新课程
@app.route('/courses', methods=['POST'])
def add_course():
    courses = read_courses()
    new_course = request.json
    courses[new_course['id']] = new_course
    save_courses(courses)
    return jsonify({"message": "Course added successfully"}), 201

# 删除课程
@app.route('/courses/<course_id>', methods=['DELETE'])
def delete_course(course_id):
    courses = read_courses()
    if course_id in courses:
        del courses[course_id]
        save_courses(courses)
        return jsonify({"message": "Course deleted successfully"}), 200
    return jsonify({"message": "Course not found"}), 404

# 更新课程顺序
@app.route('/courses/<course_id>/order', methods=['PUT'])
def update_course_order(course_id):
    courses = read_courses()
    if course_id in courses:
        new_order = request.json['order']
        old_order = courses[course_id]['order']
        
        # 更新所有受影响的课程顺序
        for cid, course in courses.items():
            if old_order < new_order and old_order < course['order'] <= new_order:
                course['order'] -= 1
            elif new_order < old_order and new_order <= course['order'] < old_order:
                course['order'] += 1
        
        courses[course_id]['order'] = new_order
        save_courses(courses)
        return jsonify({"message": "Course order updated successfully"}), 200
    return jsonify({"message": "Course not found"}), 404

# 添加新的路由来处理批量更新课程顺序
@app.route('/courses/reorder', methods=['PUT'])
def reorder_courses():
    new_order = request.json
    courses = read_courses()
    
    for item in new_order:
        if item['id'] in courses:
            courses[item['id']]['order'] = item['order']
    
    save_courses(courses)
    return jsonify({"message": "Courses reordered successfully"}), 200

if __name__ == '__main__':
    app.run(debug=True)
    print("hello world!!!")