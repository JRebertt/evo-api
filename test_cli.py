#!/usr/bin/env python3
"""
Script de teste para verificar funcionalidades do CLI
"""

import json
from pathlib import Path

def test_structure():
    """Testa estrutura de arquivos"""
    print("🧪 Testando estrutura de arquivos...")
    
    required_files = [
        'cli.py',
        'config.json',
        'requirements.txt',
        'README.md',
        'QUICKSTART.md',
        'ai/prompt.txt',
        'models/README.md'
    ]
    
    base_dir = Path(__file__).parent
    
    for file_path in required_files:
        full_path = base_dir / file_path
        if full_path.exists():
            print(f"  ✓ {file_path}")
        else:
            print(f"  ✗ {file_path} - FALTANDO!")
            return False
    
    return True

def test_config():
    """Testa arquivo de configuração"""
    print("\n🧪 Testando config.json...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        required_keys = ['evolution_api', 'gemini', 'webhook', 'settings']
        
        for key in required_keys:
            if key in config:
                print(f"  ✓ {key}")
            else:
                print(f"  ✗ {key} - FALTANDO!")
                return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Erro ao ler config.json: {e}")
        return False

def test_photos():
    """Testa fotos na pasta models"""
    print("\n🧪 Testando fotos na pasta models...")
    
    models_dir = Path('models')
    photos = list(models_dir.glob('*.jpg')) + list(models_dir.glob('*.png'))
    
    if len(photos) > 0:
        print(f"  ✓ {len(photos)} fotos encontradas")
        for photo in photos:
            print(f"    - {photo.name}")
        return True
    else:
        print(f"  ✗ Nenhuma foto encontrada!")
        return False

def test_prompt():
    """Testa arquivo de prompt"""
    print("\n🧪 Testando ai/prompt.txt...")
    
    try:
        with open('ai/prompt.txt', 'r') as f:
            prompt = f.read()
        
        if len(prompt) > 100:
            print(f"  ✓ Prompt carregado ({len(prompt)} caracteres)")
            return True
        else:
            print(f"  ✗ Prompt muito curto!")
            return False
            
    except Exception as e:
        print(f"  ✗ Erro ao ler prompt: {e}")
        return False

def main():
    print("=" * 60)
    print("TESTE DO EVOLUTION CLI".center(60))
    print("=" * 60)
    
    tests = [
        test_structure,
        test_config,
        test_photos,
        test_prompt
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "=" * 60)
    print("RESULTADO DOS TESTES".center(60))
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n✓ Testes passados: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 Todos os testes passaram! CLI está pronto para uso.")
        return 0
    else:
        print("\n⚠️  Alguns testes falharam. Verifique os erros acima.")
        return 1

if __name__ == "__main__":
    exit(main())
