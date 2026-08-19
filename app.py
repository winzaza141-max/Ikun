from flask import Flask, render_template, request, jsonify
from firebase_config import db
import time
from firebase_admin import firestore

app = Flask(__name__)

# ==========================================
# 1. PAGE ROUTES (หน้าเว็บต่างๆ)
# ==========================================

# หน้าลูกค้าสั่งอาหาร
@app.route('/')
def customer_page():
    table_num = request.args.get('table', '1') 
    return render_template('index.html', table_num=table_num)

# หน้า Admin รวม (รองรับ Sidebar สลับหน้ารับออเดอร์ & จัดการเมนู)
@app.route('/admin')
@app.route('/admin/orders')
@app.route('/admin/menus')
def admin_dashboard():
    return render_template('admin_dashboard.html')


# ==========================================
# 2. API FOR CUSTOMERS (ระบบสั่งอาหาร)
# ==========================================

# ดึงเฉพาะเมนูที่พร้อมขาย (is_available == True)
@app.route('/api/menus', methods=['GET'])
def get_customer_menus():
    try:
        docs = db.collection('menus').where('is_available', '==', True).stream()
        menus = [doc.to_dict() | {"id": doc.id} for doc in docs]
        return jsonify({"success": True, "data": menus}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ส่งคำสั่งซื้อ (Create Order)
@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        table_number = data.get('table_number')
        items = data.get('items')
        total_price = data.get('total_price')

        if not items or len(items) == 0:
            return jsonify({"success": False, "error": "ไม่มีรายการอาหารในตะกร้า"}), 400

        order_data = {
            "table_number": table_number,
            "items": items,
            "total_price": total_price,
            "status": "pending",  # pending, cooking, served, cancelled
            "created_at": time.time()
        }

        doc_ref = db.collection('orders').add(order_data)
        return jsonify({"success": True, "order_id": doc_ref[1].id, "message": "ส่งคำสั่งซื้อเรียบร้อยแล้ว!"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================
# 3. API FOR ADMIN - MENUS (จัดการเมนู)
# ==========================================

# ดึงเมนูทั้งหมด (รวมทั้งเปิดและปิดการขาย)
@app.route('/api/admin/menus', methods=['GET'])
def get_all_menus_admin():
    try:
        docs = db.collection('menus').stream()
        menus = [doc.to_dict() | {"id": doc.id} for doc in docs]
        return jsonify({"success": True, "data": menus}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# เพิ่มเมนูใหม่ (รับ URL รูปภาพแทนการอัปโหลดไฟล์)
@app.route('/api/admin/menus', methods=['POST'])
def add_menu_admin():
    try:
        # รองรับทั้งแบบ JSON และ Form-data
        data = request.json if request.is_json else request.form
        
        name = data.get('name')
        price = float(data.get('price', 0))
        category = data.get('category')
        image_url = data.get('image_url', '')

        menu_data = {
            "name": name,
            "price": price,
            "category": category,
            "image_url": image_url,
            "is_available": True,
            "created_at": time.time()
        }
        
        doc_ref = db.collection('menus').add(menu_data)
        return jsonify({"success": True, "id": doc_ref[1].id, "message": "เพิ่มเมนูสำเร็จ"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# แก้ไขข้อมูลเมนู
@app.route('/api/admin/menus/<menu_id>', methods=['PUT'])
def update_menu_admin(menu_id):
    try:
        data = request.json if request.is_json else request.form
        
        name = data.get('name')
        price = float(data.get('price', 0))
        category = data.get('category')
        image_url = data.get('image_url')

        update_data = {
            "name": name,
            "price": price,
            "category": category
        }

        if image_url is not None:
            update_data["image_url"] = image_url

        db.collection('menus').document(menu_id).update(update_data)
        return jsonify({"success": True, "message": "อัปเดตเมนูสำเร็จ"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# สลับสถานะ เปิด/ปิด การขาย
@app.route('/api/admin/menus/<menu_id>/toggle-status', methods=['PATCH'])
def toggle_menu_status(menu_id):
    try:
        data = request.json
        is_available = data.get('is_available')
        
        db.collection('menus').document(menu_id).update({"is_available": is_available})
        return jsonify({"success": True, "message": "เปลี่ยนสถานะสำเร็จ"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ลบเมนู
@app.route('/api/admin/menus/<menu_id>', methods=['DELETE'])
def delete_menu_admin(menu_id):
    try:
        db.collection('menus').document(menu_id).delete()
        return jsonify({"success": True, "message": "ลบเมนูสำเร็จ"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================
# 4. API FOR ADMIN - ORDERS (จัดการออเดอร์ร้านค้า)
# ==========================================

# ดึงรายการออเดอร์ทั้งหมด เรียงจากใหม่อยู่บน
@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    try:
        docs = db.collection('orders').order_by('created_at', direction=firestore.Query.DESCENDING).stream()
        orders = []
        for doc in docs:
            data = doc.to_dict()
            data['id'] = doc.id
            orders.append(data)
        return jsonify({"success": True, "data": orders}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# อัปเดตสถานะออเดอร์
@app.route('/api/admin/orders/<order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    try:
        data = request.json
        new_status = data.get('status')
        
        db.collection('orders').document(order_id).update({"status": new_status})
        return jsonify({"success": True, "message": "อัปเดตสถานะเรียบร้อย"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ==========================================
# START SERVER
# ==========================================
if __name__ == '__main__':
    app.run(debug=True, port=5000)
    