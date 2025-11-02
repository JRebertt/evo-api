#!/usr/bin/env python3
"""
Evolution API CLI - Gerenciador de Instâncias com Personas
"""

import os
import sys
import json
import time
import requests
import random
import shutil
import socket
from pathlib import Path
from typing import Dict, List, Optional
from openai import OpenAI

# Cores para o terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

class Storage:
    """Gerenciador de storage local"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.storage_dir = base_dir / 'storage'
        self.storage_dir.mkdir(exist_ok=True)
        
        self.config_file = self.storage_dir / 'config.json'
        self.instances_file = self.storage_dir / 'instances.json'
        self.photos_dir = self.storage_dir / 'photos'
        self.photos_dir.mkdir(exist_ok=True)
        
    def load_config(self) -> Dict:
        """Carrega configurações do storage"""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_config(self, config: Dict):
        """Salva configurações no storage"""
        with open(self.config_file, 'w') as f:
            json.dump(config, f, indent=2)
    
    def load_instances(self) -> Dict:
        """Carrega instâncias do storage"""
        if self.instances_file.exists():
            with open(self.instances_file, 'r') as f:
                return json.load(f)
        return {}
    
    def save_instances(self, instances: Dict):
        """Salva instâncias no storage"""
        with open(self.instances_file, 'w') as f:
            json.dump(instances, f, indent=2)
    
    def get_photo_path(self, photo_id: str) -> Path:
        """Retorna caminho da foto no storage"""
        return self.photos_dir / f"{photo_id}.jpg"
    
    def copy_photo_to_storage(self, source: Path, photo_id: str) -> Path:
        """Copia foto para o storage com novo nome"""
        dest = self.get_photo_path(photo_id)
        shutil.copy2(source, dest)
        return dest

class EvolutionCLI:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.storage = Storage(self.base_dir)
        
        # Detectar IP local
        self.local_ip = self.get_local_ip()
        
        # Carregar ou solicitar configurações
        self.config = self.load_or_request_config()
        
        # Verificar mudança de IP
        self.check_ip_change()
        
        # Configurar URLs e keys
        self.base_url = self.config['evolution_api']['base_url']
        self.global_apikey = self.config['evolution_api']['global_apikey']
        
        # Carregar instâncias
        self.instances = self.storage.load_instances()
        
        # Inicializar cliente Gemini
        self.setup_gemini_client()
        
        # Organizar fotos da pasta models/
        self.organize_model_photos()
        
        # Testar conexão e sincronizar instâncias
        self.test_connection_and_sync()
        
    def organize_model_photos(self):
        """Organiza fotos da pasta models/ renomeando para modelo1, modelo2, etc."""
        models_dir = self.base_dir / 'models'
        
        # Buscar todas as imagens (exceto README.md)
        image_extensions = ['.jpg', '.jpeg', '.png', '.webp']
        photos = []
        
        for file in models_dir.iterdir():
            if file.is_file() and file.suffix.lower() in image_extensions:
                # Ignorar se já está no formato modeloX
                if not file.stem.startswith('modelo'):
                    photos.append(file)
        
        if not photos:
            return  # Nenhuma foto para organizar
        
        # Renomear fotos para modelo1, modelo2, etc.
        for i, photo in enumerate(photos, 1):
            new_name = f"modelo{i}{photo.suffix}"
            new_path = models_dir / new_name
            
            # Se já existe, pular
            if new_path.exists():
                continue
            
            try:
                photo.rename(new_path)
                self.print_success(f"Foto organizada: {photo.name} → {new_name}")
            except Exception as e:
                self.print_warning(f"Erro ao renomear {photo.name}: {e}")
    
    def get_local_ip(self) -> str:
        """Detecta o IP local da máquina"""
        try:
            # Criar socket para detectar IP
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "localhost"
    
    def check_ip_change(self):
        """Verifica se o IP mudou e oferece atualização"""
        saved_ip = self.config.get('last_detected_ip')
        
        if saved_ip and saved_ip != self.local_ip:
            self.print_warning(f"IP mudou! Anterior: {saved_ip} → Atual: {self.local_ip}")
            
            current_url = self.config['evolution_api']['base_url']
            
            # Verificar se a URL usa o IP antigo
            if saved_ip in current_url:
                new_url = current_url.replace(saved_ip, self.local_ip)
                
                print(f"\n{Colors.WARNING}URL atual: {current_url}{Colors.ENDC}")
                print(f"{Colors.OKGREEN}URL sugerida: {new_url}{Colors.ENDC}\n")
                
                update = input(f"{Colors.OKCYAN}Atualizar URL automaticamente? (S/n): {Colors.ENDC}").strip().lower()
                
                if update != 'n':
                    self.config['evolution_api']['base_url'] = new_url
                    self.config['last_detected_ip'] = self.local_ip
                    self.storage.save_config(self.config)
                    self.base_url = new_url
                    self.print_success(f"URL atualizada para: {new_url}")
                else:
                    self.print_info("URL não foi alterada")
            else:
                # IP mudou mas não está na URL (pode ser localhost ou domínio)
                self.config['last_detected_ip'] = self.local_ip
                self.storage.save_config(self.config)
        elif not saved_ip:
            # Primeira vez, salvar IP
            self.config['last_detected_ip'] = self.local_ip
            self.storage.save_config(self.config)
    
    def test_connection_and_sync(self):
        """Testa conexão com a API e sincroniza instâncias"""
        self.print_info("Testando conexão com Evolution API...")
        
        try:
            # Buscar instâncias da API
            result = self.make_request('GET', 'instance/fetchInstances')
            
            if result:
                self.print_success("Conexão com Evolution API estabelecida!")
                
                # Debug (comentado para produção)
                # self.print_warning(f"[DEBUG] Tipo da resposta: {type(result)}")
                # self.print_warning(f"[DEBUG] Conteúdo: {str(result)[:200]}")
                # debug_file = self.storage.storage_dir / 'debug_api_response.json'
                # with open(debug_file, 'w') as f:
                #     json.dump(result, f, indent=2)
                # self.print_info(f"Resposta completa salva em: {debug_file}")
                
                # Sincronizar instâncias
                if isinstance(result, list) and len(result) > 0:
                    self.print_info(f"Encontradas {len(result)} instância(s) na API")
                    self.sync_instances(result)
                elif isinstance(result, list):
                    self.print_info("Nenhuma instância encontrada na API")
                else:
                    self.print_warning("Formato de resposta inesperado da API")
            else:
                self.print_error("Não foi possível conectar à Evolution API")
                self.print_warning("Verifique se a API está rodando e a URL está correta")
        except Exception as e:
            self.print_error(f"Erro ao testar conexão: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def sync_instances(self, api_instances: list):
        """Sincroniza instâncias da API com o storage local"""
        synced = 0
        
        # self.print_warning(f"[DEBUG] Iniciando sync de {len(api_instances)} instâncias")
        
        for i, instance in enumerate(api_instances):
            # self.print_warning(f"[DEBUG] Instância {i}: {str(instance)[:100]}")
            
            # A API retorna 'name' diretamente, não dentro de 'instance'
            instance_name = instance.get('name')
            # self.print_warning(f"[DEBUG] Nome extraído: {instance_name}")
            
            if not instance_name:
                continue
            
            # Se não existe no storage local, adicionar
            if instance_name not in self.instances:
                # connectionStatus também está direto na raiz
                connection_status = instance.get('connectionStatus')
                is_connected = connection_status == 'open'
                
                self.instances[instance_name] = {
                    "name": instance_name,
                    "apikey": "",
                    "created_at": time.time(),
                    "connected": is_connected,
                    "persona": None,
                    "photo_id": None,
                    "synced_from_api": True
                }
                
                synced += 1
                status = "🟢 Conectada" if is_connected else "🔴 Desconectada"
                self.print_info(f"Sincronizada: {instance_name} - {status}")
            else:
                # Atualizar status de conexão
                connection_status = instance.get('connectionStatus')
                is_connected = connection_status == 'open'
                
                if self.instances[instance_name]['connected'] != is_connected:
                    self.instances[instance_name]['connected'] = is_connected
                    status = "🟢 Conectada" if is_connected else "🔴 Desconectada"
                    self.print_info(f"Status atualizado: {instance_name} - {status}")
        
        if synced > 0:
            self.storage.save_instances(self.instances)
            self.print_success(f"{synced} instância(s) sincronizada(s) com sucesso!")
    
    def setup_gemini_client(self):
        """Configura cliente Gemini com as credenciais"""
        try:
            # Configurar variáveis de ambiente
            os.environ['OPENAI_API_KEY'] = self.config['gemini']['api_key']
            os.environ['OPENAI_BASE_URL'] = self.config['gemini'].get('base_url', 
                'https://generativelanguage.googleapis.com/v1beta/openai/')
            
            self.gemini_client = OpenAI()
            self.print_success("Cliente Gemini configurado com sucesso!")
        except Exception as e:
            self.print_error(f"Erro ao configurar Gemini: {str(e)}")
            self.gemini_client = None
    
    def load_or_request_config(self) -> Dict:
        """Carrega configurações ou solicita ao usuário"""
        config = self.storage.load_config()
        
        # Verificar se tem todas as configurações necessárias
        needs_config = False
        
        if not config.get('evolution_api', {}).get('base_url'):
            needs_config = True
        if not config.get('evolution_api', {}).get('global_apikey'):
            needs_config = True
        if not config.get('gemini', {}).get('api_key'):
            needs_config = True
        
        if needs_config:
            self.print_header("CONFIGURAÇÃO INICIAL")
            self.print_info("Algumas configurações estão faltando. Vamos configurar agora!")
            print()
            
            # Evolution API
            if not config.get('evolution_api'):
                config['evolution_api'] = {}
            
            if not config['evolution_api'].get('base_url'):
                # Sugerir URL com IP detectado
                suggested_url = f"http://{self.local_ip}:8080"
                
                print(f"{Colors.OKGREEN}IP detectado: {self.local_ip}{Colors.ENDC}")
                print(f"{Colors.OKGREEN}URL sugerida: {suggested_url}{Colors.ENDC}\n")
                
                while True:
                    base_url = input(f"{Colors.OKCYAN}URL da Evolution API [Enter para usar sugerida]: {Colors.ENDC}").strip()
                    
                    # Se vazio, usar sugerida
                    if not base_url:
                        base_url = suggested_url
                        self.print_info(f"Usando URL sugerida: {base_url}")
                    
                    # Adicionar http:// se não tiver protocolo
                    if not base_url.startswith('http://') and not base_url.startswith('https://'):
                        base_url = 'http://' + base_url
                        self.print_info(f"URL ajustada para: {base_url}")
                    
                    # Remover barra final se tiver
                    base_url = base_url.rstrip('/')
                    
                    config['evolution_api']['base_url'] = base_url
                    config['last_detected_ip'] = self.local_ip
                    break
            
            if not config['evolution_api'].get('global_apikey'):
                while True:
                    apikey = input(f"{Colors.OKCYAN}Global API Key da Evolution: {Colors.ENDC}").strip()
                    
                    if not apikey:
                        self.print_error("API Key não pode ser vazia!")
                        continue
                    
                    config['evolution_api']['global_apikey'] = apikey
                    break
            
            # Gemini
            if not config.get('gemini'):
                config['gemini'] = {}
            
            if not config['gemini'].get('api_key'):
                while True:
                    gemini_key = input(f"{Colors.OKCYAN}API Key do Gemini: {Colors.ENDC}").strip()
                    
                    if not gemini_key:
                        self.print_error("API Key do Gemini não pode ser vazia!")
                        continue
                    
                    config['gemini']['api_key'] = gemini_key
                    break
            
            if not config['gemini'].get('model'):
                config['gemini']['model'] = 'gemini-2.5-flash'
            
            if not config['gemini'].get('base_url'):
                config['gemini']['base_url'] = 'https://generativelanguage.googleapis.com/v1beta/openai/'
            
            # Webhook
            if not config.get('webhook'):
                config['webhook'] = {
                    'url': '',
                    'enabled': False
                }
            
            # Settings
            if not config.get('settings'):
                config['settings'] = {
                    'reject_call': False,
                    'msg_call': '',
                    'groups_ignore': True,
                    'always_online': False,
                    'read_messages': False,
                    'read_status': False,
                    'sync_full_history': False
                }
            
            # Salvar configurações
            self.storage.save_config(config)
            self.print_success("Configurações salvas com sucesso!")
        
        return config
    
    def print_header(self, text: str):
        """Imprime cabeçalho colorido"""
        print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
        print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")
    
    def print_success(self, text: str):
        """Imprime mensagem de sucesso"""
        print(f"{Colors.OKGREEN}✓ {text}{Colors.ENDC}")
    
    def print_error(self, text: str):
        """Imprime mensagem de erro"""
        print(f"{Colors.FAIL}✗ {text}{Colors.ENDC}")
    
    def print_info(self, text: str):
        """Imprime mensagem informativa"""
        print(f"{Colors.OKCYAN}ℹ {text}{Colors.ENDC}")
    
    def print_warning(self, text: str):
        """Imprime mensagem de aviso"""
        print(f"{Colors.WARNING}⚠ {text}{Colors.ENDC}")
    
    def make_request(self, method: str, endpoint: str, **kwargs) -> Optional[Dict]:
        """Faz requisição para a API"""
        url = f"{self.base_url}/{endpoint}"
        headers = kwargs.get('headers', {})
        
        # Adicionar apikey global se não houver apikey específica
        if 'apikey' not in headers:
            headers['apikey'] = self.global_apikey
        
        kwargs['headers'] = headers
        
        # Debug (comentado para produção)
        # self.print_warning(f"[DEBUG] Request: {method} {url}")
        # self.print_warning(f"[DEBUG] Headers: {headers}")
        
        try:
            response = requests.request(method, url, **kwargs)
            # self.print_warning(f"[DEBUG] Status Code: {response.status_code}")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            self.print_error(f"Erro na requisição: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    self.print_error(f"Status: {e.response.status_code}")
                    self.print_error(f"Resposta: {e.response.text}")
                except:
                    pass
            return None
    
    def generate_photo_id(self) -> str:
        """Gera ID único para foto"""
        import uuid
        return str(uuid.uuid4())[:8]
    
    def get_available_photos(self) -> List[Path]:
        """Retorna lista de fotos disponíveis na pasta models"""
        models_dir = self.base_dir / 'models'
        photos = []
        
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            photos.extend(models_dir.glob(ext))
        
        # Filtrar README
        photos = [p for p in photos if p.name.lower() != 'readme.md']
        
        return photos
    
    def get_used_photo_ids(self) -> List[str]:
        """Retorna lista de IDs de fotos já utilizadas por instâncias ativas"""
        used = []
        for instance in self.instances.values():
            # Apenas contar instâncias conectadas
            if instance.get('connected') and instance.get('photo_id'):
                used.append(instance['photo_id'])
        return used
    
    def select_and_copy_photo(self) -> Optional[tuple]:
        """Seleciona foto aleatória e copia para storage"""
        available = self.get_available_photos()
        
        if not available:
            self.print_warning("Nenhuma foto encontrada na pasta 'models'!")
            self.print_info("Por favor, adicione fotos na pasta 'models'")
            return None
        
        # Selecionar foto aleatória
        selected = random.choice(available)
        
        # Gerar ID único
        photo_id = self.generate_photo_id()
        
        # Copiar para storage
        storage_path = self.storage.copy_photo_to_storage(selected, photo_id)
        
        self.print_success(f"Foto selecionada: {selected.name} → {photo_id}.jpg")
        
        return (photo_id, storage_path)
    
    def create_instance(self, instance_name: str) -> Optional[Dict]:
        """Cria uma nova instância"""
        self.print_info(f"Criando instância: {instance_name}")
        
        payload = {
            "instanceName": instance_name,
            "qrcode": True,
            "integration": "WHATSAPP-BAILEYS",
            **self.config['settings']
        }
        
        # Adicionar webhook se configurado
        if self.config['webhook']['enabled'] and self.config['webhook']['url']:
            payload['webhook'] = {
                "url": self.config['webhook']['url'],
                "byEvents": False,
                "base64": True
            }
        
        result = self.make_request('POST', 'instance/create', json=payload)
        
        if result:
            self.print_success(f"Instância '{instance_name}' criada com sucesso!")
            
            # Salvar informações da instância
            self.instances[instance_name] = {
                "name": instance_name,
                "apikey": result.get('hash', ''),
                "created_at": time.time(),
                "connected": False,
                "persona": None,
                "photo_id": None
            }
            self.storage.save_instances(self.instances)
            
            return result
        
        return None
    
    def connect_instance(self, instance_name: str) -> Optional[Dict]:
        """Conecta a instância e retorna QR code"""
        self.print_info(f"Conectando instância: {instance_name}")
        
        result = self.make_request('GET', f'instance/connect/{instance_name}')
        
        if result:
            # Debug (comentado para produção)
            # self.print_warning(f"[DEBUG] Chaves da resposta: {list(result.keys())}")
            # debug_file = self.storage.storage_dir / 'debug_qr_response.json'
            # with open(debug_file, 'w') as f:
            #     json.dump(result, f, indent=2)
            # self.print_info(f"Resposta completa salva em: {debug_file}")
            
            if 'base64' in result:
                self.print_success("QR Code gerado!")
                self.print_info("Escaneie o QR Code com seu WhatsApp")
                
                # Exibir QR Code no terminal
                self.display_qr_code(result)
                
                return result
        
        return None
    
    def display_qr_code(self, qr_response: Dict):
        """Exibe QR Code no terminal"""
        try:
            import qrcode
            
            # A API pode retornar o código em diferentes formatos
            qr_data = None
            
            # Tentar pegar o código direto (algumas APIs retornam assim)
            if 'code' in qr_response:
                qr_data = qr_response['code']
                # self.print_warning(f"[DEBUG] Usando 'code' da resposta")
            elif 'qrcode' in qr_response and isinstance(qr_response['qrcode'], dict):
                if 'code' in qr_response['qrcode']:
                    qr_data = qr_response['qrcode']['code']
                    self.print_warning(f"[DEBUG] Usando 'qrcode.code' da resposta")
            
            # Se não encontrou o código direto, tentar extrair da imagem base64
            if not qr_data and 'base64' in qr_response:
                self.print_warning(f"[DEBUG] Tentando extrair da imagem base64")
                try:
                    import base64
                    import io
                    from PIL import Image
                    from pyzbar.pyzbar import decode
                    
                    base64_qr = qr_response['base64']
                    
                    # Remover prefixo data:image se houver
                    if ',' in base64_qr:
                        base64_qr = base64_qr.split(',')[1]
                    
                    # Decodificar imagem
                    img_data = base64.b64decode(base64_qr)
                    img = Image.open(io.BytesIO(img_data))
                    
                    # Ler QR Code da imagem
                    decoded = decode(img)
                    if decoded:
                        qr_data = decoded[0].data.decode('utf-8')
                        self.print_warning(f"[DEBUG] Extraído da imagem com pyzbar")
                except ImportError:
                    self.print_warning("[DEBUG] pyzbar não instalado, não pode ler da imagem")
                except Exception as e:
                    self.print_warning(f"[DEBUG] Erro ao ler imagem: {str(e)}")
            
            # Se conseguiu o código, exibir
            if qr_data:
                # Configurar QR Code menor
                qr = qrcode.QRCode(
                    version=1,  # Versão menor
                    box_size=1,  # Tamanho de cada "pixel"
                    border=2     # Borda menor
                )
                qr.add_data(qr_data)
                qr.make(fit=True)
                
                print("\n" + "="*50)
                qr.print_ascii(invert=True)
                print("="*50 + "\n")
            else:
                self.print_warning("Não foi possível extrair dados do QR Code")
                self.print_info("Visualize o QR Code na interface web da Evolution API")
            
        except ImportError:
            self.print_warning("Biblioteca 'qrcode' não instalada")
            self.print_info("Instale com: pip3 install qrcode[pil]")
            self.print_info("Ou visualize o QR Code na interface web da Evolution API")
        except Exception as e:
            self.print_warning(f"Erro ao exibir QR Code: {str(e)}")
            self.print_info("Visualize o QR Code na interface web da Evolution API")
    
    def check_connection_status(self, instance_name: str) -> bool:
        """Verifica status de conexão da instância"""
        result = self.make_request('GET', f'instance/connectionState/{instance_name}')
        
        # A API retorna 'instance' com 'state' dentro
        if result:
            # Tentar diferentes formatos de resposta
            state = None
            
            # Formato 1: state direto
            if 'state' in result:
                state = result['state']
            # Formato 2: dentro de 'instance'
            elif 'instance' in result and isinstance(result['instance'], dict):
                state = result['instance'].get('state')
            
            if state == 'open':
                return True
        
        return False
    
    def wait_for_connection(self, instance_name: str, timeout: int = 120) -> bool:
        """Aguarda conexão da instância"""
        self.print_info("Aguardando conexão do WhatsApp...")
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.check_connection_status(instance_name):
                self.print_success("WhatsApp conectado!")
                self.instances[instance_name]['connected'] = True
                self.storage.save_instances(self.instances)
                return True
            
            print(".", end="", flush=True)
            time.sleep(3)
        
        print()  # Nova linha
        self.print_warning("Timeout: WhatsApp não foi conectado")
        return False
    
    def generate_persona(self) -> Optional[Dict]:
        """Gera uma persona usando Gemini"""
        if not self.gemini_client:
            self.print_error("Cliente Gemini não está configurado!")
            return None
        
        self.print_info("Gerando persona com Gemini...")
        
        # Carregar prompt
        prompt_file = self.base_dir / 'ai' / 'prompt.txt'
        with open(prompt_file, 'r') as f:
            prompt = f.read()
        
        try:
            response = self.gemini_client.chat.completions.create(
                model=self.config['gemini']['model'],
                messages=[
                    {"role": "system", "content": "Você é um gerador de personas. Sempre responda APENAS com JSON válido, sem texto adicional."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9
            )
            
            content = response.choices[0].message.content.strip()
            
            # Remover markdown se presente
            if content.startswith('```json'):
                content = content.split('```json')[1].split('```')[0].strip()
            elif content.startswith('```'):
                content = content.split('```')[1].split('```')[0].strip()
            
            persona = json.loads(content)
            self.print_success(f"Persona criada: {persona['nome']}")
            
            return persona
            
        except Exception as e:
            self.print_error(f"Erro ao gerar persona: {str(e)}")
            return None
    
    def update_profile_name(self, instance_name: str, name: str) -> bool:
        """Atualiza nome do perfil do WhatsApp"""
        import time
        
        self.print_info(f"Atualizando nome do perfil para: {name}")
        
        # Tentar 3 vezes com delay
        for attempt in range(3):
            payload = {"name": name}
            result = self.make_request('POST', f'chat/updateProfileName/{instance_name}', json=payload)
            
            if result:
                self.print_success("✓ Nome do perfil atualizado!")
                self.print_info("📝 Nota: Verifique no WhatsApp se o nome foi realmente alterado")
                self.print_info("⚠️  Contas Business podem ter limitações de atualização de nome")
                return True
            
            if attempt < 2:
                self.print_warning(f"Tentativa {attempt + 1} falhou, aguardando 3s...")
                time.sleep(3)
        
        self.print_error("✗ Não foi possível atualizar o nome após 3 tentativas")
        self.print_warning("📝 Configure o nome MANUALMENTE no WhatsApp")
        return False
    
    def update_profile_status(self, instance_name: str, status: str) -> bool:
        """Atualiza bio/status do perfil do WhatsApp"""
        import time
        
        # Validar tamanho (WhatsApp limita a 139 caracteres)
        if len(status) > 139:
            self.print_warning(f"Bio muito longa ({len(status)} caracteres), truncando para 139")
            status = status[:139]
        
        self.print_info(f"Atualizando bio do perfil: {status}")
        
        # Tentar 3 vezes com delay
        for attempt in range(3):
            payload = {"status": status}
            result = self.make_request('POST', f'chat/updateProfileStatus/{instance_name}', json=payload)
            
            if result:
                self.print_success("Bio do perfil atualizada!")
                return True
            
            if attempt < 2:
                self.print_warning(f"Tentativa {attempt + 1} falhou, aguardando 2s...")
                time.sleep(2)
        
        self.print_error("Não foi possível atualizar a bio após 3 tentativas")
        return False
    
    def update_profile_picture(self, instance_name: str, photo_path: Path) -> bool:
        """Atualiza foto do perfil do WhatsApp"""
        self.print_info(f"Atualizando foto do perfil")
        
        try:
            import base64
            
            # Ler imagem e converter para base64
            with open(photo_path, 'rb') as f:
                img_data = f.read()
                img_base64 = base64.b64encode(img_data).decode('utf-8')
            
            # Tentar sem prefixo data URI (apenas base64)
            # A API pode aceitar base64 puro
            payload = {"picture": img_base64}
            result = self.make_request('POST', f'chat/updateProfilePicture/{instance_name}', json=payload)
            
            if result:
                self.print_success("Foto do perfil atualizada!")
                return True
            return False
                
        except Exception as e:
            self.print_error(f"Erro ao atualizar foto: {str(e)}")
            return False
    
    def setup_persona(self, instance_name: str) -> bool:
        """Configura persona completa para a instância"""
        self.print_header("CONFIGURANDO PERSONA")
        
        # Verificar se é WhatsApp Business
        is_business = self.check_if_business(instance_name)
        if is_business:
            self.print_warning("⚠️  WhatsApp Business detectado!")
            self.print_info("ℹ️  Limitação: Nome não pode ser atualizado via API em contas Business")
            self.print_info("✓ Foto e bio serão atualizadas normalmente")
            self.print_info("📝 Configure o nome manualmente no aplicativo WhatsApp Business")
            print()
        
        # Verificar se já tem persona
        if self.instances[instance_name].get('persona'):
            self.print_warning("Esta instância já possui uma persona configurada!")
            return True
        
        # Selecionar e copiar foto
        photo_result = self.select_and_copy_photo()
        if not photo_result:
            return False
        
        photo_id, photo_path = photo_result
        
        # Gerar persona
        persona = self.generate_persona()
        if not persona:
            return False
        
        # Atualizar perfil do WhatsApp
        import time
        success = True
        
        # Atualizar foto
        success &= self.update_profile_picture(instance_name, photo_path)
        self.print_info("Aguardando 5s para estabilizar...")
        time.sleep(5)  # Aguardar 5s para WhatsApp processar
        
        # Atualizar nome
        success &= self.update_profile_name(instance_name, persona['nome'])
        self.print_info("Aguardando 5s para estabilizar...")
        time.sleep(5)  # Aguardar 5s para WhatsApp processar
        
        # Atualizar bio
        success &= self.update_profile_status(instance_name, persona['bio'])
        
        if success:
            # Salvar persona
            self.instances[instance_name]['persona'] = persona
            self.instances[instance_name]['photo_id'] = photo_id
            self.instances[instance_name]['is_business'] = is_business
            self.storage.save_instances(self.instances)
            
            self.print_success("Persona configurada com sucesso!")
            self.print_info(f"Nome: {persona['nome']}")
            if is_business:
                self.print_warning("  ⚠️  Configure este nome MANUALMENTE no WhatsApp Business!")
            self.print_info(f"Idade: {persona['idade']} anos")
            self.print_info(f"Cidade: {persona['cidade']}")
            self.print_info(f"Profissão: {persona['profissao']}")
            self.print_info(f"Bio: {persona['bio']}")
            self.print_info(f"Foto ID: {photo_id}")
            
            return True
        
        return False
    
    def create_and_connect(self):
        """Fluxo completo: criar instância e conectar"""
        self.print_header("CRIAR NOVA INSTÂNCIA")
        
        instance_name = input(f"{Colors.OKCYAN}Nome da instância: {Colors.ENDC}").strip()
        
        if not instance_name:
            self.print_error("Nome da instância não pode ser vazio!")
            return
        
        if instance_name in self.instances:
            self.print_error("Instância já existe!")
            return
        
        # Criar instância
        result = self.create_instance(instance_name)
        if not result:
            return
        
        # Conectar e gerar QR code
        qr_result = self.connect_instance(instance_name)
        if not qr_result:
            return
        
        # Aguardar conexão
        if self.wait_for_connection(instance_name):
            # Configurar persona automaticamente
            self.setup_persona(instance_name)
    
    def list_instances(self):
        """Lista todas as instâncias"""
        self.print_header("INSTÂNCIAS CADASTRADAS")
        
        if not self.instances:
            self.print_info("Nenhuma instância cadastrada")
            return
        
        # Contar instâncias por status
        connected_count = sum(1 for i in self.instances.values() if i.get('connected'))
        total_count = len(self.instances)
        
        print(f"{Colors.BOLD}Total: {total_count} instâncias | Conectadas: {connected_count} | Desconectadas: {total_count - connected_count}{Colors.ENDC}\n")
        
        for name, data in self.instances.items():
            status = "🟢 Conectado" if data.get('connected') else "🔴 Desconectado"
            persona_status = "✓ Configurada" if data.get('persona') else "✗ Não configurada"
            
            print(f"\n{Colors.BOLD}━━━ {name} ━━━{Colors.ENDC}")
            print(f"  Status: {status}")
            print(f"  Persona: {persona_status}")
            
            if data.get('persona'):
                print(f"  Nome: {data['persona']['nome']}")
                print(f"  Idade: {data['persona']['idade']} anos")
                print(f"  Cidade: {data['persona']['cidade']}")
                print(f"  Foto ID: {data.get('photo_id', 'N/A')}")
    
    def delete_instance(self):
        """Deleta uma instância"""
        self.print_header("DELETAR INSTÂNCIA")
        
        if not self.instances:
            self.print_info("Nenhuma instância cadastrada")
            return
        
        # Listar instâncias
        print(f"{Colors.BOLD}Instâncias disponíveis:{Colors.ENDC}")
        for i, name in enumerate(self.instances.keys(), 1):
            status = "🟢" if self.instances[name].get('connected') else "🔴"
            print(f"  {i}. {status} {name}")
        
        instance_name = input(f"\n{Colors.OKCYAN}Nome da instância para deletar: {Colors.ENDC}").strip()
        
        if instance_name not in self.instances:
            self.print_error("Instância não encontrada!")
            return
        
        # Confirmar
        confirm = input(f"{Colors.WARNING}Tem certeza? (s/N): {Colors.ENDC}").strip().lower()
        if confirm != 's':
            self.print_info("Operação cancelada")
            return
        
        # Deletar da API
        result = self.make_request('DELETE', f'instance/delete/{instance_name}')
        
        # Deletar foto do storage se existir
        photo_id = self.instances[instance_name].get('photo_id')
        if photo_id:
            photo_path = self.storage.get_photo_path(photo_id)
            if photo_path.exists():
                photo_path.unlink()
                self.print_info(f"Foto {photo_id}.jpg deletada do storage")
        
        # Remover do registro
        del self.instances[instance_name]
        self.storage.save_instances(self.instances)
        
        self.print_success(f"Instância '{instance_name}' deletada com sucesso!")
    
    def extract_invite_code(self, link: str) -> Optional[str]:
        """Extrai código de convite de 22 caracteres do link"""
        import re
        
        # Padrão: https://chat.whatsapp.com/CODIGO_22_CHARS
        pattern = r'chat\.whatsapp\.com/([A-Za-z0-9]{22})'
        match = re.search(pattern, link)
        
        if match:
            return match.group(1)
        
        # Se o usuário colou apenas o código
        if re.match(r'^[A-Za-z0-9]{22}$', link.strip()):
            return link.strip()
        
        return None
    
    def check_if_business(self, instance_name: str) -> bool:
        """Verifica se a instância é WhatsApp Business"""
        try:
            # Buscar informações da instância
            result = self.make_request('GET', f'instance/fetchInstances', timeout=10)
            
            if result and isinstance(result, list):
                for inst in result:
                    if inst.get('name') == instance_name:
                        # Verificar se tem campo isBusiness ou businessProfile
                        return inst.get('isBusiness', False)
            
            return False
        except Exception as e:
            self.print_warning(f"Não foi possível verificar tipo de conta: {str(e)}")
            return False
    
    def join_groups(self):
        """Entra em grupos via links de convite"""
        self.print_header("ENTRAR EM GRUPOS")
        
        # Listar instâncias conectadas
        connected = {name: data for name, data in self.instances.items() if data.get('connected')}
        
        if not connected:
            self.print_error("Nenhuma instância conectada!")
            self.print_info("Conecte uma instância primeiro (opção 1)")
            return
        
        # Mostrar instâncias
        print(f"{Colors.BOLD}Instâncias conectadas:{Colors.ENDC}")
        for i, name in enumerate(connected.keys(), 1):
            print(f"  {i}. 🟢 {name}")
        
        instance_name = input(f"\n{Colors.OKCYAN}Nome da instância: {Colors.ENDC}").strip()
        
        if instance_name not in connected:
            self.print_error("Instância não encontrada ou não está conectada!")
            return
        
        # Verificar se é Business
        is_business = self.check_if_business(instance_name)
        if is_business:
            self.print_warning("⚠️  WhatsApp Business detectado!")
            self.print_info("Grupos podem exigir aprovação do administrador")
        
        # Solicitar links
        print(f"\n{Colors.BOLD}Cole os links de convite (um por linha){Colors.ENDC}")
        print(f"{Colors.OKBLUE}Formato: https://chat.whatsapp.com/CODIGO{Colors.ENDC}")
        print(f"{Colors.OKBLUE}Digite 'fim' quando terminar{Colors.ENDC}\n")
        
        links = []
        while True:
            link = input(f"{Colors.OKCYAN}Link {len(links)+1}: {Colors.ENDC}").strip()
            
            if link.lower() == 'fim':
                break
            
            if link:
                # Extrair código
                code = self.extract_invite_code(link)
                if code:
                    links.append(code)
                    self.print_success(f"✓ Código extraído: {code}")
                else:
                    self.print_error("✗ Link inválido! Use o formato correto")
        
        if not links:
            self.print_warning("Nenhum link válido fornecido")
            return
        
        # Confirmar
        print(f"\n{Colors.BOLD}Total de grupos: {len(links)}{Colors.ENDC}")
        confirm = input(f"{Colors.OKCYAN}Confirmar entrada? (S/n): {Colors.ENDC}").strip().lower()
        
        if confirm == 'n':
            self.print_info("Operação cancelada")
            return
        
        # Entrar nos grupos
        success_count = 0
        failed_count = 0
        
        for i, code in enumerate(links, 1):
            self.print_info(f"[{i}/{len(links)}] Entrando no grupo...")
            
            try:
                result = self.make_request(
                    'GET',
                    f'group/acceptInviteCode/{instance_name}',
                    params={'inviteCode': code},
                    timeout=20
                )
                
                if result and result.get('accepted'):
                    self.print_success(f"✓ Grupo {i}: Entrada aceita!")
                    success_count += 1
                else:
                    self.print_warning(f"✗ Grupo {i}: Resposta inesperada")
                    failed_count += 1
                
            except Exception as e:
                self.print_error(f"✗ Grupo {i}: Erro - {str(e)}")
                failed_count += 1
            
            # Delay entre grupos (exceto no último)
            if i < len(links):
                self.print_info("Aguardando 10 segundos...")
                time.sleep(10)
        
        # Resumo
        print(f"\n{Colors.BOLD}{'='*50}{Colors.ENDC}")
        self.print_success(f"✓ Sucessos: {success_count}")
        if failed_count > 0:
            self.print_error(f"✗ Falhas: {failed_count}")
        
        # Listar grupos
        if success_count > 0:
            print(f"\n{Colors.BOLD}Listando grupos...{Colors.ENDC}")
            try:
                groups = self.make_request(
                    'GET',
                    f'group/fetchAllGroups/{instance_name}',
                    params={'getParticipants': 'false'},
                    timeout=15
                )
                
                if groups and isinstance(groups, list):
                    self.print_success(f"Total de grupos: {len(groups)}")
                    for group in groups[-success_count:]:  # Mostrar últimos grupos
                        name = group.get('subject', 'Sem nome')
                        size = group.get('size', 0)
                        print(f"  • {name} ({size} membros)")
            except Exception as e:
                self.print_warning(f"Não foi possível listar grupos: {str(e)}")
    
    def join_groups_auto(self):
        """Entrada automática em grupos via scraping"""
        self.print_header("ENTRADA AUTOMÁTICA EM GRUPOS")
        
        # Listar instâncias conectadas
        connected = {name: inst for name, inst in self.instances.items() if inst.get('connected')}
        
        if not connected:
            self.print_error("Nenhuma instância conectada!")
            self.print_info("Use a opção 1 para criar e conectar uma instância")
            return
        
        print(f"\n{Colors.BOLD}Instâncias conectadas:{Colors.ENDC}")
        for i, name in enumerate(connected.keys(), 1):
            print(f"  {i}. {name}")
        
        instance_name = input(f"\n{Colors.OKCYAN}Nome da instância: {Colors.ENDC}").strip()
        
        if instance_name not in connected:
            self.print_error("Instância não encontrada ou não está conectada!")
            return
        
        # Verificar se é Business
        is_business = self.check_if_business(instance_name)
        if is_business:
            self.print_warning("⚠️  WhatsApp Business detectado!")
            self.print_info("Grupos podem exigir aprovação do administrador")
        
        # Buscar grupos automaticamente
        self.print_info("\n🔍 Buscando grupos automaticamente...")
        self.print_info("Categorias: Amizade (5) + Amor e Romance (5)")
        self.print_info("Isso pode levar 1-2 minutos...\n")
        
        try:
            # Importar scraper
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent))
            from scraper import GruposWhatsScraper
            
            # Executar scraping
            scraper = GruposWhatsScraper()
            codigos = scraper.coletar_codigos(verbose=True)
            
            if not codigos:
                self.print_error("\nNenhum código foi coletado!")
                return
            
            # Confirmar
            print(f"\n{Colors.BOLD}Total de grupos encontrados: {len(codigos)}{Colors.ENDC}")
            confirm = input(f"{Colors.OKCYAN}Confirmar entrada em todos? (S/n): {Colors.ENDC}").strip().lower()
            
            if confirm == 'n':
                self.print_info("Operação cancelada")
                return
            
            # Entrar nos grupos
            success_count = 0
            failed_count = 0
            
            print(f"\n{Colors.BOLD}Entrando nos grupos...{Colors.ENDC}\n")
            
            for i, code in enumerate(codigos, 1):
                self.print_info(f"[{i}/{len(codigos)}] Entrando no grupo...")
                
                try:
                    result = self.make_request(
                        'GET',
                        f'group/acceptInviteCode/{instance_name}',
                        params={'inviteCode': code},
                        timeout=20
                    )
                    
                    if result and result.get('accepted'):
                        self.print_success(f"✓ Grupo {i}: Entrada aceita!")
                        success_count += 1
                    else:
                        self.print_warning(f"✗ Grupo {i}: Resposta inesperada")
                        failed_count += 1
                    
                except Exception as e:
                    self.print_error(f"✗ Grupo {i}: Erro - {str(e)}")
                    failed_count += 1
                
                # Delay entre grupos (exceto no último)
                if i < len(codigos):
                    self.print_info("Aguardando 10 segundos...")
                    time.sleep(10)
            
            # Resumo
            print(f"\n{Colors.BOLD}{'='*50}{Colors.ENDC}")
            self.print_success(f"✓ Sucessos: {success_count}")
            if failed_count > 0:
                self.print_error(f"✗ Falhas: {failed_count}")
            
            # Listar grupos
            if success_count > 0:
                print(f"\n{Colors.BOLD}Listando grupos...{Colors.ENDC}")
                try:
                    groups = self.make_request(
                        'GET',
                        f'group/fetchAllGroups/{instance_name}',
                        params={'getParticipants': 'false'},
                        timeout=15
                    )
                    
                    if groups and isinstance(groups, list):
                        self.print_success(f"Total de grupos: {len(groups)}")
                        for group in groups[-success_count:]:  # Mostrar últimos grupos
                            name = group.get('subject', 'Sem nome')
                            size = group.get('size', 0)
                            print(f"  • {name} ({size} membros)")
                except Exception as e:
                    self.print_warning(f"Não foi possível listar grupos: {str(e)}")
        
        except ImportError:
            self.print_error("Módulo scraper.py não encontrado!")
            self.print_info("Certifique-se de que o arquivo scraper.py está na mesma pasta do CLI")
        except Exception as e:
            self.print_error(f"Erro durante scraping: {str(e)}")
    
    def main_menu(self):
        """Menu principal"""
        while True:
            self.print_header("EVOLUTION API - CLI INTERATIVO")
            
            print(f"{Colors.BOLD}1.{Colors.ENDC} Criar nova instância e conectar")
            print(f"{Colors.BOLD}2.{Colors.ENDC} Listar instâncias")
            print(f"{Colors.BOLD}3.{Colors.ENDC} Configurar persona manualmente")
            print(f"{Colors.BOLD}4.{Colors.ENDC} Verificar status de conexão")
            print(f"{Colors.BOLD}5.{Colors.ENDC} Deletar instância")
            print(f"{Colors.BOLD}6.{Colors.ENDC} Testar conexão e sincronizar")
            print(f"{Colors.BOLD}7.{Colors.ENDC} Entrar em grupos via link")
            print(f"{Colors.BOLD}8.{Colors.ENDC} Entrar em grupos automaticamente (scraping)")
            print(f"{Colors.BOLD}9.{Colors.ENDC} Reconfigurar API Keys")
            print(f"{Colors.BOLD}10.{Colors.ENDC} Sair")
            
            choice = input(f"\n{Colors.OKCYAN}Escolha uma opção: {Colors.ENDC}").strip()
            
            if choice == '1':
                self.create_and_connect()
            elif choice == '2':
                self.list_instances()
            elif choice == '3':
                instance_name = input(f"{Colors.OKCYAN}Nome da instância: {Colors.ENDC}").strip()
                if instance_name in self.instances:
                    if self.instances[instance_name].get('connected'):
                        self.setup_persona(instance_name)
                    else:
                        self.print_error("Instância não está conectada!")
                else:
                    self.print_error("Instância não encontrada!")
            elif choice == '4':
                instance_name = input(f"{Colors.OKCYAN}Nome da instância: {Colors.ENDC}").strip()
                if instance_name in self.instances:
                    connected = self.check_connection_status(instance_name)
                    if connected:
                        self.print_success(f"Instância '{instance_name}' está conectada!")
                        if not self.instances[instance_name].get('connected'):
                            self.instances[instance_name]['connected'] = True
                            self.storage.save_instances(self.instances)
                    else:
                        self.print_warning(f"Instância '{instance_name}' está desconectada!")
                        if self.instances[instance_name].get('connected'):
                            self.instances[instance_name]['connected'] = False
                            self.storage.save_instances(self.instances)
                else:
                    self.print_error("Instância não encontrada!")
            elif choice == '5':
                self.delete_instance()
            elif choice == '6':
                self.test_connection_and_sync()
            elif choice == '7':
                self.join_groups()
            elif choice == '8':
                self.join_groups_auto()
            elif choice == '9':
                # Limpar config e solicitar novamente
                self.storage.save_config({})
                self.print_info("Configurações limpas. Reinicie o CLI para reconfigurar.")
            elif choice == '10':
                self.print_info("Até logo!")
                break
            else:
                self.print_error("Opção inválida!")
            
            input(f"\n{Colors.OKCYAN}Pressione ENTER para continuar...{Colors.ENDC}")

if __name__ == "__main__":
    try:
        cli = EvolutionCLI()
        cli.main_menu()
    except KeyboardInterrupt:
        print(f"\n{Colors.WARNING}Operação cancelada pelo usuário{Colors.ENDC}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Colors.FAIL}Erro fatal: {str(e)}{Colors.ENDC}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
