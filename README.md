# Assistente de Consultas da Ouvidoria

O governo disponibiliza um volume enorme de dados sobre a ouvidoria, mas consultá-los
exige conhecimento técnico e paciência para entender as APIs. 

O objetivo é criar um agente de IA conversacional que permite a qualquer cidadão ou
gestor fazer perguntas em linguagem natural sobre os dados da ouvidoria e receber
respostas precisas, sem precisar entender de código ou estrutura de banco de dados.

## 🚀 Quick Start com Docker

A forma mais fácil de rodar a aplicação:

```bash
cd ouvidorIA
./start.sh
```

Acesse: http://localhost:8501

Para mais detalhes, veja:
- **Quick Start:** [DOCKER-QUICKSTART.md](ouvidorIA/DOCKER-QUICKSTART.md)
- **Guia Completo:** [README-Docker.md](ouvidorIA/README-Docker.md)

## 📦 Instalação Manual

Se preferir rodar sem Docker:

```bash
cd ouvidorIA
pip install -r requirements.txt
streamlit run main.py
```

**Nota:** Você precisará ter Ollama instalado localmente.

