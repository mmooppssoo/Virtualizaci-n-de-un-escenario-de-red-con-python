from lib_mv import MV, Red
import logging
import sys
import json
import subprocess

# Configuración del logger
def init_log():
    logging.basicConfig(level=logging.DEBUG)
    log = logging.getLogger('auto_p2')
    ch = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', "%Y-%m-%d %H:%M:%S")
    ch.setFormatter(formatter)
    log.addHandler(ch)
    log.propagate = False
    return log

def pause():
    program_pause = input("Press the <ENTER> key to continue...")

def execute_operation(operation, num_servidores,log,num_lan_ad):
    if operation == 'crear':
        log.debug('Iniciando operación de creación de las mv...')
        for i in range(1, num_servidores + 1):
            # Ejecutar las operaciones de creación de las MV y red
            mv = MV(f's{i}.2')
            log.debug(f'Creando s{i}.2...')
            mv.crear_mv('cdps-vm-base-pc1.qcow2', 'if1', False, 2)
            log.debug(f's{i}.2 creado con exito')
        for j in range(3,num_lan_ad +3):
            for i in range(1, num_servidores + 1):
                # Ejecutar las operaciones de creación de las MV y red
                mv = MV(f's{i}.{j}')
                log.debug(f'Creando s{i}.{j}...')
                mv.crear_mv('cdps-vm-base-pc1.qcow2', 'if1', False, j)
                log.debug(f's{i}.{j} creado con exito')
        red = Red('Red')
        log.debug('Creando lb y c1...')
        red.crear_red(num_lan_ad)
        log.debug('lb y c1 creados con exito')
        log.debug('Operaciones de creación finalizadas')
    
    elif operation == 'arrancar':
        log.debug('Iniciando operación de arranque de las mv...')
        for i in range(1, num_servidores + 1):
            mv = MV(f's{i}.2')
            log.debug(f'Arrancando s{i}.2...')
            mv.arrancar_mv()
            log.debug(f's{i}.2 arrancado con exito')
        for j in range(3,num_lan_ad +3):
            for i in range(1, num_servidores + 1):
                mv = MV(f's{i}.{j}')
                log.debug(f'Arrancando s{i}.{j}...')
                mv.arrancar_mv()
                log.debug(f's{i}.{j} arrancado con exito')
                
        log.debug('Arrancando lb...')
        subprocess.call(f"sudo virsh start lb", shell=True)
        subprocess.call(f"xterm -e 'sudo virsh console lb' &", shell=True)
        log.debug('lb arrancado con exito')
        log.debug('Arrancando c1...')
        subprocess.call(f"sudo virsh start c1", shell=True)
        subprocess.call(f"xterm -e 'sudo virsh console c1' &", shell=True)
        log.debug('c1 arrancado con exito')
        log.debug('Operaciones de arranque finalizadas')

    elif operation == 'parar':
        log.debug('Parando maquinas virtuales...')
        for i in range(1, num_servidores + 1):
            mv = MV(f's{i}.2')
            log.debug(f'Parando s{i}.2...')
            mv.parar_mv()
            log.debug(f's{i}.2 parado con exito')
        for j in range(3,num_lan_ad +3):
            for i in range(1, num_servidores + 1):
                mv = MV(f's{i}.{j}')
                log.debug(f'Parando s{i}.{j}...')
                mv.parar_mv()
                log.debug(f's{i}.{j} parado con exito')
        log.debug('Parando lb...')
        subprocess.call(f"sudo virsh shutdown lb", shell=True)
        log.debug('lb parado con exito')
        log.debug('Parando c1...')
        subprocess.call(f"sudo virsh shutdown c1", shell=True)
        log.debug('c1 parado con exito')
        log.debug('Maquinas virtuales paradas con exito')

    elif operation == 'liberar':
        log.debug('Liberando maquinas virtuales y borrando todos los archivos...')
        for i in range(1, num_servidores + 1):
            mv = MV(f's{i}.2')
            log.debug(f'Liberando s{i}.2...')
            mv.liberar_mv()
            log.debug(f's{i}.2 liberado con exito')
        for j in range(3,num_lan_ad +3):
            for i in range(1, num_servidores + 1):
                mv = MV(f's{i}.{j}')
                log.debug(f'Liberando s{i}.{j}...')
                mv.liberar_mv()
                log.debug(f's{i}.{j} liberado con exito')
        red = Red('Red')
        log.debug('Liberando lb y c1...')
        red.liberar_red(num_lan_ad)
        log.debug('lb y c1 liberados con exito')
        log.debug('Maquinas virtuales liberadas con exito')
        
    elif operation == 'monitor':
        log.debug("Obteniendo información de las máquinas virtuales...")
        comando_mvs = "sudo virsh list --all"
        resultado_mvs = subprocess.run(comando_mvs, shell=True, capture_output=True, text=True)
        info_mvs = resultado_mvs.stdout
        log.info(f"Información de las máquinas virtuales:\n{info_mvs}")
        if len(info_mvs.strip().splitlines()) > 2:  # Verifica si hay más de dos líneas (indicando al menos una MV)
            log.debug("Verificando la conectividad con las máquinas virtuales...")
            for i in range(1, num_servidores + 1):
                ip = f"10.11.2.{30 + i}" 
                comando_ping = f"ping -c 4 {ip}"  # Prueba de ping con 4 paquetes
                respuesta_ping = subprocess.run(comando_ping, shell=True)
                if respuesta_ping.returncode == 0:
                    log.debug(f"Conexión exitosa con s{i}.2")
                else:
                    log.debug(f"No se pudo establecer conexión con s{i}.2")
            for j in range(3, num_lan_ad + 3):  # PING para servidores adicionales
                for i in range(1, num_servidores + 1):
                    ip = f"10.11.{j}.{30 + i}" 
                    comando_ping = f"ping -c 4 {ip}"  # Prueba de ping con 4 paquetes
                    respuesta_ping = subprocess.run(comando_ping, shell=True)
                    if respuesta_ping.returncode == 0:
                        log.debug(f"Conexión exitosa con s{i}.{j}")
                    else:
                        log.debug(f"No se pudo establecer conexión con s{i}.{j}")
            comando_ping = f"ping -c 4 10.11.1.2"  # Prueba de ping con 4 paquetes
            respuesta_ping = subprocess.run(comando_ping, shell=True)
            if respuesta_ping.returncode == 0:
                log.debug(f"Conexión exitosa con c1")
            else:
                log.debug(f"No se pudo establecer conexión con c1")
            comando_ping = f"ping -c 4 10.11.1.1"  # Prueba de ping con 4 paquetes
            respuesta_ping = subprocess.run(comando_ping, shell=True)
            if respuesta_ping.returncode == 0:
                log.debug(f"Conexión exitosa con lb")
            else:
                log.debug(f"No se pudo establecer conexión con lb")
        else:
            log.debug("No hay ninguna maquina virtual activa")
        

# Función principal
def main():
    log = init_log()  # Inicializar el logger y asignarlo a la variable log
    print('CDPS - mensaje info1')

    # Lectura del archivo JSON para obtener el número de servidores
    with open('auto-p2.json', 'r') as json_file:
        config_data = json.load(json_file)
        num_servidores = config_data.get('num_serv')
        debug = config_data.get('debug', False)  # Obtener la configuración de depuración
        num_lan_ad = config_data.get('num_lan_adicional', 0)
        
    if not (1 <= num_servidores <= 5):
        log.error("Error: El número de servidores no está dentro del rango permitido (de 1 a 5).")
    else:
       log.info(f"Número de servidores a arrancar: {num_servidores}")
       
    if not (0 <= num_lan_ad <= 2):
        log.error("Error: El número de LANs no está dentro del rango permitido (de 0 a 2).")
    else:
       log.info(f"Número de LANs adicionales a arrancar: {num_lan_ad}")
       
    # Establecer el nivel de depuración según la configuración del archivo JSON
    if debug:
        log.setLevel(logging.DEBUG)
        log.debug("Modo de depuración activado")  # Mensaje de depuración
    elif not debug:
        log.setLevel(logging.INFO)  # Establecer el nivel a INFO si debug es False


    # Ejecución de las operaciones según el parámetro pasado
    execute_operation(sys.argv[1], num_servidores, log, num_lan_ad)
    pause()

if __name__ == "__main__":
    main()

