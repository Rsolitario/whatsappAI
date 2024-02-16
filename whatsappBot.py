from time import sleep
from selenium import webdriver
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import re
from unicodedata import normalize

from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.webdriver.firefox.options import Options

import yaml
# Importamos el paquete recien instalado
import google.generativeai as genai

filepath = './resource\whatsapp_session.txt'
driver = webdriver

yaml_file = open("config.yaml", 'r')
yaml_content = yaml.load(yaml_file, Loader=yaml.FullLoader)
GOOGLE_API_KEY = yaml_content.get("api_key")

# AI google
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-pro")

def crear_driver_session_v2():
    options = Options()
    options.add_argument("-profile")
    options.add_argument('C:\\Users\\anonimo\\AppData\\Roaming\\Mozilla\\Firefox\\Profiles\\p10ezzsn.default-release')

    #firefox_capabilities = DesiredCapabilities.FIREFOX
    #firefox_capabilities['marionette'] = True
    driver = webdriver.Firefox(options=options)
    return driver

def esperar_ser_clickeable(driver, time, selector, xpath):
        try:
            return WebDriverWait(driver, time).until(EC.element_to_be_clickable((xpath, selector)))
        except TimeoutException:
            pass
            # print(TimeoutException.with_traceback)
        return -1

def crear_driver_session():

    with open(filepath) as fp:
        for cnt, line in enumerate(fp):
            if cnt == 0:
                executor_url = line
            if cnt == 1:
                session_id = line

    def new_command_execute(self, command, params=None):
        if command == "newSession":
            # Mock the response
            return {'success': 0, 'value': None, 'sessionId': session_id}
        else:
            return org_command_execute(self, command, params)
                
    org_command_execute = RemoteWebDriver.execute

    RemoteWebDriver.execute = new_command_execute

    new_driver = webdriver.Remote(command_executor=executor_url, desired_capabilities={})
    new_driver.session_id = session_id

    RemoteWebDriver.execute = org_command_execute

    return new_driver

def buscar_chats():
    print("BUSCANDO CHATS")

    esperar_ser_clickeable(driver, 20, "_64p9p", By.CLASS_NAME)
    
    if len(driver.find_elements(By.CLASS_NAME, "_64p9P")) == 0:
        print("CHAT ABIERTO")
        message = identificar_mensaje()
        
        if message != None:
            return True

    # si no hay chats abierto comienza aquí
        # Lista de mensajes
    chats = driver.find_elements(By.CLASS_NAME, "_2A1R8")
    for chat in chats:
        
        print("DETECTANDO MENSAJES SIN LEER")

        # etiqueta de 1 mensaje pendiente
        chats_mensajes = chat.find_elements(By.CLASS_NAME, "_2H6nH")

        if len(chats_mensajes) == 0:
            print("CHATS ATENDIDOS")
            continue

        element_name = chat.find_element(By.CLASS_NAME, '_30scZ')
        name = element_name.text.upper().strip()
        
        print("IDENTIFICANDO CONTACTO")
        
        with open("./resource/contactos_autorizados.txt", mode='r', encoding='utf-8') as archivo:
            contactos = [linea.upper().rstrip() for linea in archivo]
            if name not in contactos:
                print("CONTACTO NO AUTORIZADO : ", name)
                continue
        
        print(name, "AUTORIZADO PARA SER ATENDIDO POR BOT")
        element_name.click()
        return True
    return False

def normalizar(message: str):
    # -> NFD y eliminar diacríticos
    message = re.sub(
        r"([^n\u0300-\u036f]|n(?!\u0303(?![\u0300-\u036f])))[\u0300-\u036f]+", r"\1", 
        normalize( "NFD", message), 0, re.I
    )

    # -> NFC
    return normalize( 'NFC', message)

def identificar_mensaje():
    element_box_message = driver.find_elements(By.CLASS_NAME, "_1BOF7")
    posicion = len(element_box_message) -1

    color =  element_box_message[posicion].value_of_css_property("background-color")

    if color == "rgb(217, 253, 211)" or color == "rgba(5, 97, 98, 1)": 
        print("CHAT ATENDIDO")
        return
    
    element_message = element_box_message[posicion]
    message = element_message.text.upper().strip()
    print("MENSAJE RECIBIDO :", message)
    return normalizar(message)

def preparar_respuesta(message :str):
    print("PREPARANDO RESPUESTA")

    response = model.generate_content(message)
    print("*** Respuesta: {response.text} ***")
    return response.text

def procesar_mensaje(message :str):
    chatbox = driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[1]")
    response = preparar_respuesta(message)
    print(response)
    chatbox.click()
    esperar_ser_clickeable(driver,5, "/html/body/div[1]/div/div[2]/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[1]/div/div[1]", By.XPATH)
    for i in response:
        chatbox.send_keys(i)
    # Enviar
    driver.find_element(By.XPATH, "/html/body/div[1]/div/div[2]/div[4]/div/footer/div[1]/div/span[2]/div/div[2]/div[2]/button").click()

def whatsapp_boot_init():
    global driver
    driver = crear_driver_session_v2()
    driver.get("https://web.whatsapp.com/")
    
    while True:
        if not buscar_chats():
            sleep(10)
            continue
        
        message = identificar_mensaje()

        if message == None:
            continue

        procesar_mensaje(message)


whatsapp_boot_init()
