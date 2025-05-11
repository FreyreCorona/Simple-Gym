import platform
import time
from playwright.async_api import async_playwright
import logic.dbManager
import logic.config
import resend
from dateutil.parser import parse

def replace_texts(client_id,text):
    config = logic.config.load_config()
    client = logic.dbManager.show_client_by_id(client_id)
    variables = ['BUSSINES_NAME','PIX','MENSALITY','CLIENT_NAME','CLIENT_NUMBER','CLIENT_CPF','CLIENT_EMAIL','CLIENT_START_DATE','CLIENT_START_DATE_DAY','CLIENT_START_DATE_MONTH','CLIENT_DUE_DATE','CLIENT_DUE_DATE_DAY','CLIENT_DUE_DATE_MONTH','CLIENT_STATUS']
    values =[config['bussines_name'],config['pix_key'],config['default_payment'],client[1],client[2],client[3],client[4],client[5],parse(client[5]).day,parse(client[5]).month,client[6],parse(client[6]).day,parse(client[6]).month,client[8]]
    for i in range(len(variables)):
        text = text.replace(str(variables[i]),str(values[i]))
    print(text)
    return text

async def whatsapp_notification(id):
    client = logic.dbManager.show_client_by_id(id)
    config = logic.config.load_config()
    msg = replace_texts(id,str(config['notification_settings']['overdue_msg']))
    if client[8] == 'Vencido':
        msg = replace_texts(id,str(config['notification_settings']['due_msg']))
    
    async with async_playwright() as pl:
        user_data_dir = 'auth_session'
        if platform.system() == 'windows':
            browser = await pl.chromium.launch_persistent_context(channel='msedge',user_data_dir=user_data_dir,headless=False)
        else:
            browser = await pl.chromium.launch_persistent_context(executable_path='/opt/brave-bin/brave',headless=False,user_data_dir=user_data_dir)
        
        page = browser.pages[0] if browser.pages else await browser.new_page()
        msg = msg.replace(" ","%20")
        await page.goto(f"https://web.whatsapp.com/send/?phone=%2b55{client[2]}&text={msg}&type=phone_number&absent=0")
        await page.wait_for_selector("p.selectable-text.copyable-text",state='visible',timeout=1200000)
        time.sleep(5)
        await page.keyboard.press('Enter')
        time.sleep(5) 
        await browser.close()

def email_notification(id):
    resend.api_key = "re_2P8tNB5m_G9aad78UJT281bE1tuF8FVJB"
    client = logic.dbManager.show_client_by_id(id)
    config = logic.config.load_config()
    subject = f"Lembrete: Sua mensalidade da academia {str(config["bussines_name"])} vence em breve!"
    html = replace_texts(id,str(config['notification_settings']['overdue_msg']))
        
    if client[8] == "Vencido":
        subject = f"Atenção! Sua mensalidade da academia {str(config['bussines_name'])} está vencida!"
        html = replace_texts(id,str(config['notification_settings']['due_msg']))
       
    r = resend.Emails.send({
        "from": f"{str(config['bussines_name'])}@resend.dev",
        "to": str(client[4]),
        "subject": subject,
        "html": html
    })


