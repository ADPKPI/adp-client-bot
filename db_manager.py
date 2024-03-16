from mysql.connector import pooling

class DBManager:
    _instance = None

    def __new__(cls, dbconfig):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls.pool = pooling.MySQLConnectionPool(pool_name="mypool", pool_size=5, **dbconfig)
        return cls._instance

    @staticmethod
    def get_connection():
        return DBManager._instance.pool.get_connection()

class MenuRepository:
    def get_menu(self):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT name FROM menu")
        rows = cursor.fetchall()
        cursor.close()
        cnx.close()
        return rows

    def get_pizza_details(self, pizza_name):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT name, description, photo_url, price, id FROM menu WHERE name = %s", (pizza_name,))
        row = cursor.fetchone()
        cursor.close()
        cnx.close()
        return row

    def get_pizza_details_by_id(self, product_id):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT id, name, price FROM menu WHERE id = %s", (product_id,))
        row = cursor.fetchone()
        cursor.close()
        cnx.close()
        return row

class CartRepository:
    def add_to_cart(self, user_id, product_id):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT quantity, total_price FROM user_cart WHERE user_id = %s AND product_id = %s", (user_id, product_id))
        cart_row = cursor.fetchone()

        if cart_row:
            new_quantity = cart_row[0] + 1
            new_total_price = new_quantity * (cart_row[1]/cart_row[0])
            cursor.execute("UPDATE user_cart SET quantity = %s, total_price = %s WHERE user_id = %s AND product_id = %s",
                           (new_quantity, new_total_price, user_id, product_id))
        else:
            menu_row = MenuRepository().get_pizza_details_by_id(product_id)
            if menu_row:
                cursor.execute(
                    "INSERT INTO user_cart (user_id, product_id, product_name, quantity, total_price) VALUES (%s, %s, %s, 1, %s)",
                    (user_id, product_id, menu_row[1], menu_row[2]))
        cnx.commit()
        cursor.close()
        cnx.close()

    def get_cart(self, user_id):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT product_name, quantity, total_price FROM user_cart WHERE user_id = %s", (user_id,))
        rows = cursor.fetchall()
        cursor.close()
        cnx.close()
        return rows

    def clear_cart(self, user_id):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("DELETE FROM user_cart WHERE user_id = %s", (user_id,))
        cnx.commit()
        cursor.close()
        cnx.close()


class UserRepository:
    def get_user(self, user_id):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = %s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        cnx.close()
        return row

    def add_user(self, user_id, username, firstname, lastname):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("INSERT INTO users (user_id, username, firstname, lastname) VALUES (%s, %s, %s, %s)",
                       (user_id, username, firstname, lastname))
        cnx.commit()
        cursor.close()
        cnx.close()

    def update_user_contact(self, user_id, phone_number=None, location=None):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        if phone_number:
            cursor.execute("UPDATE users SET phone_number=%s WHERE user_id = %s", (phone_number, user_id))
        if location:
            cursor.execute("UPDATE users SET saved_location=%s WHERE user_id = %s", (location, user_id))
        cnx.commit()
        cursor.close()
        cnx.close()

class OrderRepository:
    def create_order(self, user_id, phone_number, order_list, total_price, location):
        cnx = DBManager.get_connection()
        cursor = cnx.cursor()
        cursor.execute("SELECT order_id FROM orders ORDER BY order_id DESC LIMIT 1;")
        order_id = cursor.fetchall()[0][0] + 1

        cursor.execute("INSERT INTO orders (order_id, user_id, phone_number, order_list, total_price, order_time, location) VALUES (%s, %s, %s, %s, %s, NOW(), %s)",
                       (order_id, user_id, phone_number, str(order_list), total_price, location))

        cnx.commit()
        cursor.close()
        cnx.close()
        return order_id


