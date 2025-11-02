#!/usr/bin/env python3
"""
Scraper Automático para gruposwhats.app
Extrai códigos de convite de grupos (22 caracteres)
"""

import requests
from bs4 import BeautifulSoup
import re
import time
import json
from typing import List

class GruposWhatsScraper:
    """Scraper para gruposwhats.app"""
    
    CATEGORIAS = {
        "amizade": "https://gruposwhats.app/category/amizade",
        "amor_e_romance": "https://gruposwhats.app/category/amor-e-romance"
    }
    
    GRUPOS_POR_CATEGORIA = 5
    
    def __init__(self):
        """Inicializa o scraper"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Connection': 'keep-alive',
        })
    
    def extrair_links_intermediarios(self, url_categoria: str) -> List[str]:
        """Extrai links das páginas de grupos"""
        try:
            response = self.session.get(url_categoria, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Encontrar links que contêm /group/
            links = soup.find_all('a', href=re.compile(r'/group/\d+'))
            
            links_unicos = []
            urls_vistas = set()
            
            for link in links:
                url = link.get('href')
                if url and url not in urls_vistas:
                    # Garantir URL completa
                    if url.startswith('/'):
                        url = 'https://gruposwhats.app' + url
                    
                    urls_vistas.add(url)
                    links_unicos.append(url)
                    
                    if len(links_unicos) >= self.GRUPOS_POR_CATEGORIA:
                        break
            
            return links_unicos
            
        except Exception as e:
            print(f"  Erro ao acessar categoria: {str(e)}")
            return []
    
    def extrair_codigo_whatsapp(self, url_intermediaria: str) -> str:
        """Extrai código do WhatsApp (22 caracteres) da página do grupo"""
        try:
            response = self.session.get(url_intermediaria, timeout=15)
            response.raise_for_status()
            
            # Procurar padrão: chat.whatsapp.com/CODIGO_22_CARACTERES
            match = re.search(r'chat\.whatsapp\.com/([A-Za-z0-9]{22})', response.text)
            
            if match:
                return match.group(1)
            
            return None
            
        except Exception as e:
            print(f"    Erro: {str(e)}")
            return None
    
    def coletar_codigos(self, verbose: bool = True) -> List[str]:
        """Coleta códigos de grupos"""
        todos_codigos = []
        
        for nome_cat, url_cat in self.CATEGORIAS.items():
            if verbose:
                print(f"\n{'='*50}")
                print(f"Categoria: {nome_cat.replace('_', ' ').title()}")
                print(f"{'='*50}")
            
            # Extrair links intermediários
            links_inter = self.extrair_links_intermediarios(url_cat)
            
            if verbose:
                print(f"  Encontrados: {len(links_inter)} grupos")
            
            # Extrair códigos do WhatsApp
            for i, link_inter in enumerate(links_inter, 1):
                if verbose:
                    print(f"  [{i}/{len(links_inter)}] Extraindo código...")
                
                codigo = self.extrair_codigo_whatsapp(link_inter)
                
                if codigo:
                    todos_codigos.append(codigo)
                    if verbose:
                        print(f"    ✓ {codigo}")
                else:
                    if verbose:
                        print(f"    ✗ Falhou")
                
                time.sleep(1)  # Delay entre requisições
        
        return todos_codigos
    
    def salvar_json(self, codigos: List[str], arquivo: str = "grupos_coletados.json"):
        """Salva códigos em arquivo JSON"""
        with open(arquivo, 'w', encoding='utf-8') as f:
            json.dump({"codigos": codigos, "total": len(codigos)}, f, indent=2, ensure_ascii=False)
    
    @staticmethod
    def carregar_json(arquivo: str = "grupos_coletados.json") -> List[str]:
        """Carrega códigos de arquivo JSON"""
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('codigos', [])
        except:
            return []

def main():
    """Teste do scraper"""
    print("="*60)
    print("SCRAPER AUTOMÁTICO - gruposwhats.app")
    print("="*60)
    
    scraper = GruposWhatsScraper()
    codigos = scraper.coletar_codigos(verbose=True)
    
    print(f"\n{'='*60}")
    print(f"RESULTADO FINAL")
    print(f"{'='*60}")
    print(f"Total de códigos coletados: {len(codigos)}")
    
    if codigos:
        scraper.salvar_json(codigos)
        print(f"Arquivo salvo: grupos_coletados.json")
        
        print(f"\nCódigos coletados:")
        for i, codigo in enumerate(codigos, 1):
            print(f"  {i}. {codigo}")
    else:
        print("\n⚠️  Nenhum código foi coletado!")

if __name__ == "__main__":
    main()
