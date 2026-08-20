from flask import Flask, render_template, request, jsonify
from db_config import get_db_connection
from psycopg2.extras import Json
import time

app = Flask(__name__)

# ==========================================
# 1. PAGE ROUTES
# ==========================================
@app.route('/')
def customer_page():
    table_num = request.args.get('table', '1') 
    return render_template('index.html', table_num=table_num)

@app.route('/admin')
@app.route('/admin/orders')
@app.route('/admin/menus')
def admin_dashboard():
    return render_template('admin_dashboard.html')

# ==========================================
# 2. API FOR CUSTOMERS
# ==========================================
@app.route('/api/menus', methods=['GET'])
def get_customer_menus():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM menus WHERE is_available = TRUE ORDER BY id DESC")
        menus = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "data": menus}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/orders', methods=['POST'])
def create_order():
    try:
        data = request.json
        table_number = data.get('table_number')
        items = data.get('items')
        total_price = data.get('total_price')

        if not items or len(items) == 0:
            return jsonify({"success": False, "error": "ไม่มีรายการอาหารในตะกร้า"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO orders (table_number, items, total_price, status, created_at)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
            """,
            (table_number, Json(items), total_price, 'pending', time.time())
        )
        order_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "order_id": order_id, "message": "ส่งคำสั่งซื้อเรียบร้อยแล้ว!"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ==========================================
# 3. API FOR ADMIN - MENUS
# ==========================================
@app.route('/api/admin/menus', methods=['GET'])
def get_all_menus_admin():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM menus ORDER BY id DESC")
        menus = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "data": menus}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/menus', methods=['POST'])
def add_menu_admin():
    try:
        data = request.json if request.is_json else request.form
        name = data.get('name')
        price = float(data.get('price', 0))
        category = data.get('category')
        image_url = data.get('image_url', '')

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO menus (name, price, category, image_url, is_available, created_at)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id
            """,
            (name, price, category, image_url, True, time.time())
        )
        menu_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "id": menu_id, "message": "เพิ่มเมนูสำเร็จ"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/menus/<int:menu_id>', methods=['PUT'])
def update_menu_admin(menu_id):
    try:
        data = request.json if request.is_json else request.form
        name = data.get('name')
        price = float(data.get('price', 0))
        category = data.get('category')
        image_url = data.get('image_url')

        conn = get_db_connection()
        cur = conn.cursor()

        if image_url is not None:
            cur.execute(
                """
                UPDATE menus 
                SET name = %s, price = %s, category = %s, image_url = %s
                WHERE id = %s
                """,
                (name, price, category, image_url, menu_id)
            )
        else:
            cur.execute(
                """
                UPDATE menus 
                SET name = %s, price = %s, category = %s
                WHERE id = %s
                """,
                (name, price, category, menu_id)
            )

        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "อัปเดตเมนูสำเร็จ"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/menus/<int:menu_id>/toggle-status', methods=['PATCH'])
def toggle_menu_status(menu_id):
    try:
        data = request.json
        is_available = data.get('is_available')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE menus SET is_available = %s WHERE id = %s",
            (is_available, menu_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "เปลี่ยนสถานะสำเร็จ"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ลบเมนูเดี่ยว (แก้ไขให้ลบจริงใน Postgres)
@app.route('/api/admin/menus/<int:menu_id>', methods=['DELETE'])
def delete_menu_admin(menu_id):
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM menus WHERE id = %s", (menu_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "ลบเมนูสำเร็จ"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ลบเมนูหลายรายการพร้อมกัน (Batch Delete ใน Postgres)
@app.route('/api/admin/menus/batch-delete', methods=['DELETE'])
def batch_delete_menus():
    try:
        data = request.get_json()
        menu_ids = [int(i) for i in data.get('ids', [])]
        
        if menu_ids:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("DELETE FROM menus WHERE id = ANY(%s)", (menu_ids,))
            conn.commit()
            cur.close()
            conn.close()

        return jsonify({'success': True, 'message': f'ลบเมนูจำนวน {len(menu_ids)} รายการเรียบร้อย'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

# ==========================================
# 4. API FOR ADMIN - ORDERS
# ==========================================
@app.route('/api/admin/orders', methods=['GET'])
def get_admin_orders():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM orders ORDER BY created_at DESC")
        orders = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({"success": True, "data": orders}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/admin/orders/<int:order_id>/status', methods=['PATCH'])
def update_order_status(order_id):
    try:
        data = request.json
        new_status = data.get('status')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE orders SET status = %s WHERE id = %s",
            (new_status, order_id)
        )
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({"success": True, "message": "อัปเดตสถานะเรียบร้อย"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)