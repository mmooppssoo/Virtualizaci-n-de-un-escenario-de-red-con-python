import logging
from lxml import etree
import json
import subprocess
import shutil
import os


log = logging.getLogger('auto_p2')

class MV:
    def __init__(self, nombre):
        self.nombre = nombre
        log.debug('init MV ' + self.nombre)


    def crear_mv(self, imagen, interfaces_red, router,indice_lan):
        log.debug("crear_mv " + self.nombre)
        # Crear máquinas virtuales s1-sN según el número especificado
        subprocess.call(f"qemu-img create -f qcow2 -b {imagen} {self.nombre}.qcow2", shell=True)
        
        # Copiar el archivo XML base
        shutil.copy('plantilla-vm-pc1.xml', f'{self.nombre}.xml')
        
        # Cargar la copia del archivo XML para realizar modificaciones
        tree = etree.parse(f"{self.nombre}.xml")
        root = tree.getroot()
        # Realizar las modificaciones en la copia del archivo XML
        name = root.find("name")
        name.text = self.nombre  # Usar el self.nombre proporcionado
        interface = root.find("./devices/interface/source")
        interface.set("bridge", f"LAN{indice_lan}")
        source = root.find("./devices/disk/source")
        source.set("file", f"/mnt/tmp/alvaro/{self.nombre}.qcow2")  # Modificar la ruta del archivo qcow2
        # Guardar la copia modificada del archivo XML
        with open(f'{self.nombre}.xml', 'wb') as file:
              file.write(etree.tostring(tree, pretty_print=True))
        subprocess.call(f"sudo virsh define {self.nombre}.xml", shell=True)
        # Modificacion de la pagina web
        with open(f'index.html', 'w') as file:
            file.write(f"<h1>Pagina web del servidor {self.nombre}</h1>")
        # Copiar el archivo HTML modificado a la máquina virtual
        subprocess.call(f"sudo virt-copy-in -a {self.nombre}.qcow2 index.html /var/www/html/", shell=True)
        # Eliminar el archivo HTML local
        subprocess.call(f"rm index.html", shell=True)
        
    def arrancar_mv(self):
        log.debug("arrancar_mv " + self.nombre)
        subprocess.call(f"sudo virsh start {self.nombre}", shell=True)
        subprocess.call(f"xterm -e 'sudo virsh console {self.nombre}' &", shell=True)
        
         
    def parar_mv(self):
        log.debug("parar_mv " + self.nombre)
        # Aquí debes implementar la lógica para detener la máquina virtual
        subprocess.call(f"sudo virsh shutdown {self.nombre}", shell=True)
                

    def liberar_mv(self):
        log.debug("liberar_mv " + self.nombre)
    
        # Verificar si la máquina virtual está en ejecución
        running = subprocess.run(f"sudo virsh list --all | grep {self.nombre}", shell=True, stdout=subprocess.PIPE, text=True)
        if 'running' in running.stdout:
            # Detener la máquina virtual si está en ejecución
            subprocess.call(f"sudo virsh destroy {self.nombre}", shell=True)
    
        # Eliminar la definición de la máquina virtual
        subprocess.call(f"sudo virsh undefine {self.nombre}", shell=True)
        # Borrar archivos creados durante el arranque de la MV
        subprocess.call(f"rm {self.nombre}.qcow2", shell=True)
        subprocess.call(f"rm {self.nombre}.xml", shell=True)
        



class Red:
    def __init__(self, nombre):
        self.nombre = nombre
        log.debug('init Red ' + self.nombre)

    def crear_red(self,num_lan_ad):
        log.debug('crear_red ' + self.nombre)
        # Aquí debes implementar la lógica para crear la red
        # Crear y configurar LAN1 y LAN2
        subprocess.call("sudo brctl addbr LAN1", shell=True)
        subprocess.call("sudo ifconfig LAN1 up", shell=True)
        subprocess.call(f"sudo brctl addbr LAN2", shell=True)
        subprocess.call(f"sudo ifconfig LAN2 up", shell=True)
            
        #Crar y configurar LANs de servidores
        for j in range(3, num_lan_ad + 3):  # Crear LANs adicionales
            subprocess.call(f"sudo brctl addbr LAN{j}", shell=True)
            subprocess.call(f"sudo ifconfig LAN{j} up", shell=True)
            
        #Configurar host
        subprocess.call(f"sudo ifconfig LAN1 10.11.1.3/24", shell=True)
        subprocess.call(f"sudo ip route add 10.11.0.0/16 via 10.11.1.1", shell=True)
        
        #Crear maquina c1
        subprocess.call(f"qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 c1.qcow2", shell=True)
        # Copiar el archivo XML base
        shutil.copy('plantilla-vm-pc1.xml', f'c1.xml')
        # Cargar la copia del archivo XML para realizar modificaciones
        tree = etree.parse(f"c1.xml")
        root = tree.getroot()
        # Realizar las modificaciones en la copia del archivo XML
        name = root.find("name")
        name.text = 'c1'  
        interface = root.find("./devices/interface/source")
        interface.set("bridge", "LAN1")
        source = root.find("./devices/disk/source")
        source.set("file", f"/mnt/tmp/alvaro/c1.qcow2")  # Modificar la ruta del archivo qcow2
        # Guardar la copia modificada del archivo XML
        with open(f'c1.xml', 'wb') as file:
              file.write(etree.tostring(tree, pretty_print=True))
        subprocess.call(f"sudo virsh define c1.xml", shell=True)
        with open(f"hostname", "w") as hostname_file:
            hostname_file.write('c1')
        with open('interfaces', 'w') as interfaces_file:
            interfaces_file.write(f"""
               auto lo
               iface lo inet loopback
                       
               auto eth0
               iface eth0 inet static
               address 10.11.1.2
               netmask 255.255.255.0
               gateway 10.11.1.1""")
        subprocess.call(f"sudo virt-copy-in -a c1.qcow2 hostname /etc/", shell=True)
        subprocess.call(f"sudo virt-copy-in -a c1.qcow2 interfaces /etc/network/", shell=True)	
        subprocess.call(f"sudo virt-edit -a c1.qcow2 /etc/hosts -e 's/127.0.1.1.*/127.0.1.1 c1/'", shell=True)
        subprocess.call(f"rm hostname", shell=True)
        subprocess.call(f"rm interfaces", shell=True)   

        def generar_xml_balanceador():
            # Crear el XML para el balanceador
            tree = etree.parse('plantilla-vm-pc1.xml')  # Usar la plantilla XML proporcionada
            # Realizar las modificaciones para el balanceador
            root = tree.getroot()
            # Cambiar el nombre de la máquina virtual
            name = root.find("name")
            name.text = 'lb'
            # Modificar la interfaz de red LAN1
            interface = root.find("./devices/interface/source")
            interface.set("bridge", "LAN1")
            source = root.find("./devices/disk/source")
            source.set("file", f"/mnt/tmp/alvaro/lb.qcow2")  # Modificar la ruta del archivo qcow2
            # Agregar una segunda interfaz de red para LAN2
            # Crear la interfaz de red para LAN2 similar a la de LAN1
            interface2 = etree.SubElement(root.find("devices"), "interface", type="bridge")
            source2 = etree.SubElement(interface2, "source", bridge=f"LAN2")
            model2 = etree.SubElement(interface2, "model", type="virtio")
            #Crear la interfaz de red para LAN adicional
            for j in range(3,num_lan_ad +3):
                interface_j = etree.SubElement(root.find("devices"), "interface", type="bridge")
                source_j = etree.SubElement(interface_j, "source", bridge=f"LAN{j}")
                model_j = etree.SubElement(interface_j, "model", type="virtio")
            # Guardar el XML generado en un archivo para el balanceador
            with open('lb.xml', 'wb') as file:
                file.write(etree.tostring(tree, pretty_print=True))
                
        # Crear el balanceador de carga (lb)
        subprocess.call("qemu-img create -f qcow2 -b cdps-vm-base-pc1.qcow2 lb.qcow2", shell=True)
        subprocess.call("cp plantilla-vm-pc1.xml lb.xml", shell=True)
        generar_xml_balanceador()  # Generar el XML para el balanceador
        subprocess.call("sudo virt-edit -a lb.qcow2 /etc/sysctl.conf -e 's/#net.ipv4.ip_forward=1/net.ipv4.ip_forward=1/'", shell=True)
        subprocess.call(f"sudo virsh define lb.xml", shell=True)
        with open(f"hostname", "w") as hostname_file:
            hostname_file.write('lb')
        with open('interfaces', 'w') as interfaces_file:
            interfaces_file.write(f"""
               auto eth0
               iface eth0 inet static
               address 10.11.1.1
               netmask 255.255.255.0

               auto eth1
               iface eth1 inet static
               address 10.11.2.1
               netmask 255.255.255.0""")
            for i in range(2, num_lan_ad + 2):
                interfaces_file.write(f"""
                    auto eth{i}
                    iface eth{i} inet static
                    address 10.11.{i + 1}.1
                    netmask 255.255.255.0 """)               
        subprocess.call(f"sudo virt-copy-in -a lb.qcow2 hostname /etc/", shell=True)
        subprocess.call(f"sudo virt-copy-in -a lb.qcow2 interfaces /etc/network/", shell=True)	
        subprocess.call(f"sudo virt-edit -a lb.qcow2 /etc/hosts -e 's/127.0.1.1.*/127.0.1.1 lb/'", shell=True)
        subprocess.call(f"rm hostname", shell=True)
        subprocess.call(f"rm interfaces", shell=True)   
        
        
        #Configurar archivos servidores
        with open('auto-p2.json', 'r') as json_file:
            config_data = json.load(json_file)
            num_servidores = config_data.get('num_serv')
            for i in range(1, num_servidores + 1):
                  nombre_vm = f"s{i}.2"
                  direccion_ip = f"10.11.2.{30 + i}"  # Asignar direcciones IP
                  with open(f"hostname", "w") as hostname_file:
                     hostname_file.write(nombre_vm)
                  with open(f"interfaces", "w") as interfaces_file:
                     interfaces_file.write(f"""
                       auto lo
                       iface lo inet loopback
                       
                       auto eth0
                       iface eth0 inet static
                         address {direccion_ip}
                         netmask 255.255.255.0
                         gateway 10.11.2.1""")
                  subprocess.call(f"sudo virt-copy-in -a {nombre_vm}.qcow2 hostname /etc/", shell=True)
                  subprocess.call(f"sudo virt-copy-in -a {nombre_vm}.qcow2 interfaces /etc/network/", shell=True)	
                  subprocess.call(f"sudo virt-edit -a {nombre_vm}.qcow2 /etc/hosts -e 's/127.0.1.1.*/127.0.1.1 {nombre_vm}/'", shell=True)
                  subprocess.call(f"rm hostname", shell=True)
                  subprocess.call(f"rm interfaces", shell=True)
            #Configurar archivos servidores adicionales
            for j in range(3,num_lan_ad +3):
                for i in range(1, num_servidores + 1):
                  nombre_vm = f"s{i}.{j}"
                  direccion_ip = f"10.11.{j}.{30 + i}"  # Asignar direcciones IP
                  with open(f"hostname", "w") as hostname_file:
                     hostname_file.write(nombre_vm)
                  with open(f"interfaces", "w") as interfaces_file:
                     interfaces_file.write(f"""
                       auto lo
                       iface lo inet loopback
                       
                       auto eth0
                       iface eth0 inet static
                         address {direccion_ip}
                         netmask 255.255.255.0
                         gateway 10.11.{j}.1""")
                  subprocess.call(f"sudo virt-copy-in -a {nombre_vm}.qcow2 hostname /etc/", shell=True)
                  subprocess.call(f"sudo virt-copy-in -a {nombre_vm}.qcow2 interfaces /etc/network/", shell=True)	
                  subprocess.call(f"sudo virt-edit -a {nombre_vm}.qcow2 /etc/hosts -e 's/127.0.1.1.*/127.0.1.1 {nombre_vm}/'", shell=True)
                  subprocess.call(f"rm hostname", shell=True)
                  subprocess.call(f"rm interfaces", shell=True)
            
    def liberar_red(self,num_lan_ad):
        log.debug('liberar_red ' + self.nombre)
        # Aquí debes implementar la lógica para liberar la red
        # Eliminar las interfaces de red LAN1 y LAN2
        # Verificar si la máquina virtual está en ejecución
        running = subprocess.run(f"sudo virsh list --all | grep lb", shell=True, stdout=subprocess.PIPE, text=True)
        if 'running' in running.stdout:
            # Detener la máquina virtual si está en ejecución
            subprocess.call(f"sudo virsh destroy lb", shell=True)
            subprocess.call(f"sudo virsh destroy c1", shell=True)
    
        # Eliminar la definición de la máquina virtual
        subprocess.call(f"sudo virsh undefine lb", shell=True)
        subprocess.call(f"sudo virsh undefine c1", shell=True)
        subprocess.call("sudo ifconfig LAN1 down", shell=True)
        subprocess.call("sudo ifconfig LAN2 down", shell=True)
        subprocess.call("sudo brctl delbr LAN1", shell=True)
        subprocess.call("sudo brctl delbr LAN2", shell=True)
        for j in range(3,num_lan_ad +3):
            subprocess.call(f"sudo ifconfig LAN{j} down", shell=True)
            subprocess.call(f"sudo brctl delbr LAN{j}", shell=True)
        subprocess.call(f"rm lb.qcow2", shell=True)
        subprocess.call(f"rm lb.xml", shell=True)
        subprocess.call(f"rm c1.qcow2", shell=True)
        subprocess.call(f"rm c1.xml", shell=True)
        



