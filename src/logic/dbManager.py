import sqlite3
from datetime import datetime,timedelta
from dateutil.parser import parse
import resend
from logic.config import *
import os

def connect_db():
    return sqlite3.connect(os.getcwd() +'/resources/gym.db')
def db_initialize():
    con = connect_db()
    cursor = con.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS  clients(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            number INTEGER,
            cpf TEXT, 
            email TEXT,
            start_date DATE,
            end_date DATE,
            amount INTEGER,
            payment_status TEXT
                )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments(
            ID INTEGER PRIMARY KEY AUTOINCREMENT,
            client_ID INTEGER,
            payment_date DATE,
            amount INTEGER,
            payment_status TEXT,
            FOREIGN KEY (client_ID) REFERENCES clients(ID)
                )           
    ''')
    cursor.execute('''
        CREATE TRIGGER IF NOT EXISTS actualize_clients
        AFTER INSERT ON payments
        BEGIN UPDATE clients
        SET start_date = NEW.payment_date,
        end_date = DATE(NEW.payment_date,"+30 days"),
        payment_status = NEW.payment_status
        WHERE ID = NEW.client_ID;
        END;''')
    cursor.execute('''
                   CREATE TABLE IF NOT EXISTS trial(
                   ID INTEGER PRIMARY KEY,
                   first_execution DATE,
                   last_execution DATE,
                   end_trial DATE,
                   is_active BOOLEAN)
                   ''')
    con.commit()
    con.close()
    #actualiza el estado de pago de los clientes
    change_client_status()

    print('Base de datos inicializada correctamente')
def change_client_status():
    con = connect_db()
    cursor = con.cursor()
    cursor.execute('''UPDATE clients SET payment_status = 'Vencido' WHERE end_date < DATE('now') AND payment_status = 'Pago' ''')
    con.commit()
    con.close()        

def check_trial():
    con = connect_db()
    cursor = con.cursor()

    cursor.execute("SELECT * FROM trial")
    trial = cursor.fetchone()
    if trial: #a tabla ja existe
        cursor.execute("""UPDATE trial SET last_execution = DATE('now')""")    
        if not trial[4]: #la aplicacion esta en periodo de prueba o inactiva
            if datetime.now().date() <= parse(trial[3]).date(): #esta en periodo de prueba
                print("Dias del Periodo de prueba restante: ",parse(trial[3]).date() - datetime.now().date())
                con.commit()
                con.close()
                return True
            elif datetime.now().date() < parse(trial[2]).date(): #el sistema de base de datos fue modificado externamente
                print("Detectado modificacion de la base de datos de manera externa")
                conf = load_config()        
                resend.Emails.send({
                    "from": "Vulnerability@resend.dev",
                    "to": "einierfreyre60@gmail.com",
                    "subject": "La base de datos fue modificada externamente",
                    "html": f"Modificacion por parte de {conf["bussines_name"]}"
                })
                cursor.execute('DROP TABLE clients,payment')
                con.commit()
                con.close()
                return False
            else:# el periodo de prueba expiro
                print("periodo de prueba expirado")
                return False
        else: #la aplicacion esta activa
            print("La aplicacion esta activa")        
            return True

    else: #a tabla no existe
        print("creando la informacion del periodo de prueba")
        cursor.execute("""INSERT INTO trial(ID,first_execution,last_execution,end_trial,is_active) 
                       VALUES(1,DATE('now'),DATE('now'),DATE('now','+15 days'),false)""")
        con.commit()
        con.close()
        return True
def active_application(KEY):
    con = connect_db()
    cursor = con.cursor()
    if KEY == "LICENCE-DJFKAL-3.13.2":
        cursor.execute("UPDATE trial SET is_active = true WHERE ID = 1")
        con.commit()
        con.close()
        print("Activacion exitosa")
        return True
    con.close()
    return False
def regist_client(name,number,cpf,email,start_date,amount):
    '''Registra clientes en la base de datos'''
    try:
        date = parse(start_date,dayfirst=True).date()
        end_date = date + timedelta(days=30)
        payment_status= 'Pago' if datetime.now().date() <= end_date else 'Vencido'

        con = connect_db()
        cursor = con.cursor()
        cursor.execute('''
            INSERT INTO clients(name,number,cpf,email,start_date,end_date,amount,payment_status)
            VALUES (?,?,?,?,?,?,?,?)''',
            (name,number,cpf,email,date,end_date,amount,payment_status)
        )
        con.commit()
        con.close()
        print('Cliente registrado exitosamente')
    
    except ValueError:
        print('ERROR: ValueError>regist_client')
def regist_payment(client_id,payment_date,amount,payment_status):
    con = connect_db()
    cursor = con.cursor()
    cursor.execute('''
        INSERT INTO payments(client_ID,payment_date,amount,payment_status)
        VALUES (?,?,?,?)''',(client_id,payment_date,amount,payment_status))
    con.commit()
    con.close()
def edit_client(ID,name,number,cpf,email,start_date,amount):
    try:
        date = parse(start_date).date()
        end_date = date + timedelta(days=30)
        payment_status= 'Pago' if datetime.now().date() <= end_date else 'Vencido'
        con = connect_db()
        cursor = con.cursor()
        cursor.execute('''
        UPDATE clients
        SET name = ?,number = ?,cpf = ? ,email = ?, start_date = ?, end_date = ?,amount = ?,payment_status = ?
        WHERE ID = ?''',
        (name,number,cpf,email,start_date,end_date,amount,payment_status,ID))
        con.commit()
        con.close()
    except ValueError:
        print('Error al intentar actualizar la base de datos')

def delete_client(ID):
    try:
        con = connect_db()
        cursor = con.cursor()
        cursor.execute('DELETE FROM clients WHERE ID = ?',(ID,))
        con.commit()
        con.close()
    except ValueError:
        print('Value error al intentar eliminar el cliente')
def delete_payment(ID):
    try:
        con = connect_db()
        cursor = con.cursor()
        cursor.execute('DELETE FROM payments WHERE ID = ?',(ID,))
        con.commit()
        con.close()
    except ValueError:
        print('Value error al intentar eliminar el cliente')
def show_clients(start_from,quantity):
    try:
        con = connect_db()
        cursor = con.cursor()
        cursor.execute('''
        SELECT * FROM clients LIMIT ? OFFSET ? ''',
        (quantity,start_from))
        clients = cursor.fetchall()
        con.close()
        return clients
    except ValueError:
        print('ERROR al intentar mostrar los clientes')
def show_payments(id):
    con = connect_db()
    cursor = con.cursor()
    cursor.execute('SELECT * FROM payments WHERE client_ID = ?',(id,))
    data = cursor.fetchall()
    con.close()
    return data
def show_client_by_id(id):
    try:
        con = connect_db()
        cursor = con.cursor()
        cursor.execute('SELECT * FROM clients WHERE ID = ?',(id,))
        client = cursor.fetchone()
        con.close()
        return client
    except ValueError:
        print('Error al devolver por id')

def client_exist(id):
    con = connect_db()
    cursor = con.cursor()
    cursor.execute('Select 1 FROM clients WHERE ID = ?',(id,))
    if cursor.fetchone():
        con.close()
        return True
    else:
        con.close()
        return False

def search_db(filter):
    con = connect_db()
    cursor = con.cursor()
    cursor.execute('SELECT * FROM clients WHERE name LIKE ? OR number LIKE ? OR cpf LIKE ? OR email LIKE ?',(f'%{filter}%',f'%{filter}%',f'%{filter}%',f'%{filter}%'))
    result = cursor.fetchall()
    con.close()
    return result

def client_count(start_date = None):
    con = connect_db()
    
    cursor = con.cursor()
    if not start_date:
        cursor.execute('SELECT COUNT(*) FROM clients')
    else:
        cursor.execute('SELECT COUNT(*) FROM clients WHERE start_date >= ?', (start_date.isoformat(),))   
    data = cursor.fetchone()[0]
    con.close()
    return data

def search_payment(status,start_date = None):
    con = connect_db()
    cursor = con.cursor()
    if not start_date:
        cursor.execute("SELECT * FROM clients WHERE payment_status = ?",(status,))
    else:
        cursor.execute("SELECT * FROM clients WHERE payment_status = ? AND payment_date >= ?",(status,start_date.isoformat()))
    data = cursor.fetchall()
    con.close()
    return data

def get_group_of_payments(start_date,end_date): 
        con = connect_db()
        cursor = con.cursor()
        cursor.execute('''SELECT strftime("%m",payment_date) AS month,
                        SUM(amount) AS total_amount
                       FROM payments WHERE payment_status == "Pago" AND payment_date BETWEEN ? AND ?
                       GROUP BY month 
                       ORDER BY month''',(start_date.isoformat(),end_date.isoformat()))
        data = cursor.fetchall()
        con.close()
        print(data)
        return data
def total_income(start_date = None):
    con = connect_db()
    cursor = con.cursor()
    if not start_date:
        cursor.execute('SELECT SUM(amount) FROM payments WHERE payment_status = "Pago"')
    else:
        cursor.execute('SELECT SUM(amount) FROM payments WHERE payment_date >= ? AND payment_status = "Pago"', (start_date.isoformat(),))
    data = cursor.fetchone()[0]
    con.close()
    if data:
        return data
    else:
        return 0

def get_expiring_memberships(days_threshold=5):
    con = connect_db()
    cursor = con.cursor()
    
    # Calcula la fecha futura basada en el umbral de días
    future_date = datetime.now().date() + timedelta(days=days_threshold)
    
    cursor.execute('''
        SELECT ID, name, end_date 
        FROM clients 
        WHERE end_date BETWEEN DATE('now') AND DATE(?)
        AND payment_status = 'Pago'
    ''', (future_date,))
    
    expiring = cursor.fetchall()
    con.close()
    return expiring
def get_expired_memberships():
    con = connect_db()
    cursor = con.cursor()
    
    cursor.execute('''
        SELECT ID, name, end_date 
        FROM clients 
        WHERE payment_status = 'Vencido'
    ''')
    
    expired = cursor.fetchall()
    con.close()
    return expired

if __name__ == '__main__':
    db_initialize()
