#!/usr/bin/python
import shlex
import sys
import telebot
import subprocess
from telebot import types

#se inicializa el bot
bot = telebot.TeleBot("BOT_TOKEN")
machine = "MY VM BOX MACHINE"
cid_list=[]

# Funcion simple para identificar las conexiones a nuestro bot, cid es el codigo unico de cada conversacion
# establecida

def knowYou(cid):
 if cid in cid_list:
  return True
 else:
  return False

# Por seguridad nuestro bot implementara un sencillo mecanismo de identifiacion con un password
# esta funcion extrae el texto como resultado de un mensaje tipo "/start password"

def extract_unique_code(text): 
 n = len(text.split())
 if n==2:
  return text.split()[1]
 else:
  None

# Para evitar problemas, nos aseguramos que cada mensaje recibido sea de tipo texto
# esta solucion quizas no es la ideal, puede que exista otra más elegante.. 

def extract_message_text(message):
 try:
  texto = message.text
  return texto
 except:
  texto=""
  return texto
  
# Una funcion listener que interceptará todos los mensajes recibidos por el bot, funciona como un log
# y tambien nos permite manejar algunos casos en los que el usuario aun no se ha identificado

def listener(messages): 
 for message in messages: 
  cid = message.chat.id
  texto = extract_message_text(message)
  if not knowYou(cid) and '/start' not in texto:
   print "[" + str(cid) + "]: " + texto
   bot.reply_to(message, "Presentate, intenta /start")
  else:
   print "[" + str(cid) + "]: " + texto

# Asi, le decimos al bot que utilice como funcion escuchadora nuestra funcion 'listener' declarada arriba.
bot.set_update_listener(listener) 

# esta será que la función que maneje el comando "/start"
@bot.message_handler(commands=['start'])
def send_welcome(message):
 unique_code = extract_unique_code(message.text) # extraemos el password
 cid = message.chat.id # Guardamos el ID de la conversacion para poder responder.
 #aqui denifimos el teclado que se le presentara la usuario
 markup = types.ReplyKeyboardMarkup(row_width=2)
 markup.add('Start', 'PowerOff', 'Restart', 'ShowInfo')
 # si ya el usuario es conococido por el bot
 # bot_register_next_step será la funcion que maneje los mensajes que envie el usuario apartir de ahora
 if cid in cid_list:
   bot.reply_to(message, "Ya hemos iniciado nuestra conversacion anteriormente..")
   msg = bot.send_message(cid, "Selecciona una accion:", reply_markup=markup)
   bot.register_next_step_handler(msg, process_next_step)
 else:
  if unique_code == "MY_BOT_PASSWORD":
   cid_list.append(cid)
   bot.reply_to(message, "Bienvenido...")
   msg = bot.send_message(cid, "Selecciona una accion:", reply_markup=markup)
   bot.register_next_step_handler(msg, process_next_step)
  else:
   bot.reply_to(message, "[-] Password incorrecto..")

# esta será que la función que maneje el comando "/stop"
@bot.message_handler(commands=['stop'])
def send_goodbye(message):
 unique_code = extract_unique_code(message.text)
 cid = message.chat.id # Guardamos el ID de la conversacion para poder responder.
 if cid in cid_list:
   bot.reply_to(message, "OK, fue un placer servirte jefe..")
   cid_list.remove(cid)
 else:
   bot.reply_to(message, "No te conozco, presentate con /start y tu password..")

# sencilla funcion que indica si la vm esta corriendo o no 

def isVmRunning():
 comando="vboxmanage showvminfo " + machine + " | grep -i state"
 print comando
 proc=subprocess.check_output(comando, shell=True)
 if "running" in proc:
  return True
 else:
  return False

# Funcion que manejara todos los mensajes a partir de que el usuario se indentifique

def process_next_step(message):
 texto = extract_message_text(message)
 print "[+] Mensaje: " + texto
 cid = message.chat.id # Guardamos el ID de la conversacion para poder responder.
 #evitamos manejar equivocadamente los comandos "/start y /stop"
 if '/start' not in texto and '/stop' not in texto:
  if texto=="Start":
    if isVmRunning():
     msg = bot.send_message(cid,"Aparentemente la vm ya esta corriendo...")
     bot.register_next_step_handler(msg, process_next_step)     
    else:
     comando="vboxmanage startvm " + machine + " --type=headless"
     print comando
     proc=subprocess.check_call(shlex.split(comando))
     if proc==0:
      msg = bot.send_message(cid,"La vm se inicio correctamente...")
      bot.register_next_step_handler(msg, process_next_step)
  else:
   if texto=="PowerOff":
    msg = bot.send_message(cid, "OK, intentare apagar la vm...")
    if isVmRunning():
     comando="vboxmanage controlvm " + machine + " poweroff"
     print comando
     proc=subprocess.check_call(shlex.split(comando))
     if proc==0:
      msg = bot.send_message(cid,"La vm se apago correctamente")
      bot.register_next_step_handler(msg, process_next_step)
    else:
     msg = bot.send_message(cid,"Aparentemente la vm no esta corriendo...")
     bot.register_next_step_handler(msg, process_next_step)     
   else:
    if texto=="Restart":
     msg = bot.send_message(cid, "OK, intentare reiniciar la vm...")
     if isVmRunning():
      comando="vboxmanage controlvm " + machine + " reset"
      print comando
      proc=subprocess.check_call(shlex.split(comando))
      if proc==0:
       msg = bot.send_message(cid,"Ready, la vm se reinicio correctamente..")
       bot.register_next_step_handler(msg, process_next_step)
     else:
      msg = bot.send_message(cid,"Aparentemente la vm no esta corriendo...")
      bot.register_next_step_handler(msg, process_next_step)     
    else:
     if texto=="ShowInfo":
      msg = bot.send_message(cid, "OK, este es el status de la vm...")
      comando="vboxmanage showvminfo " + machine + " | grep -i state"
      print comando
      proc=subprocess.check_output(comando, shell=True)
      #proc=subprocess.Popen(shlex.split(comando))
      msg = bot.send_message(cid,proc)
      bot.register_next_step_handler(msg, process_next_step)  
     else:
      msg = bot.send_message(cid, "No se como interpretar lo que pides, intenta alguna opcion del menu..")
      bot.register_next_step_handler(msg, process_next_step)  
bot.polling()
