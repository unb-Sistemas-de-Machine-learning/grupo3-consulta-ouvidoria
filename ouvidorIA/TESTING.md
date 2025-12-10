# 🧪 Testing Guide

## What Was Fixed

### Problem
The chatbot was returning the entire prompt/context instead of generating actual responses:
```
"Retorne APENAS um JSON neste formato: { "tipo": "CHAT" ..."
```

### Root Cause
The `analyze_demand()` method was using `query_engine.query()` which is designed for RAG (document retrieval), not direct LLM conversation.

### Solution
Changed to call the LLM directly using `self.llm.complete()` for classification tasks.

---

## How to Test

### 1. Rebuild & Start

```bash
cd /Users/paulo.goncalves/Documents/unb/grupo3-consulta-ouvidoria/ouvidorIA

# Rebuild the container with fixes
docker-compose up --build
```

### 2. Test Cases

Open http://localhost:8501 and click "💬 Ajuda" button.

#### Test 1: Simple Greeting (should return CHAT response)
```
User: Olá!
Expected: Friendly greeting in Portuguese (not JSON)
```

#### Test 2: Simple Question (should return CHAT response)
```
User: Como funciona a ouvidoria?
Expected: Informative response about ouvidoria
```

#### Test 3: Real Complaint (should return form suggestion)
```
User: Não consigo marcar consulta no posto de saúde há 3 meses
Expected: 
- Chat message acknowledging the issue
- Form widget showing:
  - Tipo: Reclamação
  - Órgão: Ministério da Saúde (MS)
  - Resumo técnico profissional
```

#### Test 4: Denunciation (should return form suggestion)
```
User: Vi funcionários dormindo durante expediente na repartição
Expected:
- Chat message
- Form widget showing:
  - Tipo: Denúncia
  - Appropriate órgão
  - Professional summary
```

#### Test 5: Service Request (should return form suggestion)
```
User: Preciso solicitar acesso aos dados de contratos públicos
Expected:
- Chat message
- Form widget showing:
  - Tipo: Solicitação
  - Appropriate órgão
  - Professional summary
```

---

## Expected Behavior

### ✅ For Greetings/Questions (CHAT):
- Should display a conversational response
- NO form widget appears
- Response is friendly and helpful

### ✅ For Real Demands (Reclamação/Denúncia/Solicitação):
- Chat message acknowledging the issue
- Form widget appears with:
  - **Tipo:** Classification
  - **Órgão:** Identified government agency
  - **Resumo qualificado:** Professional technical description
  - Button to auto-fill the form

---

## Debugging

### View Logs

```bash
# Watch logs in real-time
docker-compose logs -f streamlit

# Look for these lines:
# - "Ollama conectado: phi3 @ http://ollama:11434"
# - "LLM Response: {...}"
```

### Common Issues

#### Issue: Still seeing prompt as response
**Solution:** Make sure you rebuilt the container:
```bash
docker-compose down
docker-compose up --build
```

#### Issue: "Cannot connect to Ollama"
**Solution:** Check if Ollama is running:
```bash
docker-compose ps
docker-compose logs ollama
```

#### Issue: Very slow responses
**Solution:** Model is still loading. Wait 1-2 minutes after startup.

#### Issue: JSON parsing errors
**Check logs:**
```bash
docker-compose logs -f streamlit
```
Look for the actual LLM response to see if it's valid JSON.

---

## Performance Expectations

| Action | Expected Time |
|--------|---------------|
| First message (cold start) | 10-30 seconds |
| Subsequent messages | 3-10 seconds |
| Greeting response | 2-5 seconds |
| Complex analysis | 5-15 seconds |

---

## Architecture Overview

```
User Message
    ↓
analyze_demand() 
    ↓
self.llm.complete() ← Direct LLM call (not RAG)
    ↓
JSON Response
    ↓
Parse & Display
```

**Key Difference:**
- ❌ OLD: `query_engine.query()` → Goes through RAG pipeline
- ✅ NEW: `self.llm.complete()` → Direct LLM call

---

## Success Criteria

✅ Greetings return conversational responses (not JSON prompts)
✅ Real complaints generate structured JSON with form suggestions
✅ Response time is reasonable (< 15 seconds)
✅ No error messages in logs
✅ Form auto-fill button works when clicked

---

## Need More Help?

Check the logs and look for:
```bash
# Success indicators:
"Ollama conectado: phi3"
"LLM Response: {"

# Error indicators:
"Erro ao conectar Ollama"
"Erro ao processar JSON"
```

If you see errors, share the logs for more specific help!

