import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

class AIAnalyst:
    def __init__(self, api_key, timeout=20):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.timeout = timeout
        self.session = self._create_session()
        # Prioritize Gemini 3 Pro as default
        self.preferred_models = [
            "gemini-3-pro-preview",
            "gemini-3-flash-preview",
            "gemini-2.0-flash-thinking-exp-1219", 
            "gemini-2.0-flash-thinking-exp-01-21",
            "gemini-2.0-flash-exp", 
            "gemini-1.5-flash", 
            "gemini-1.5-flash-latest",
            "gemini-pro"
        ]
        
        # Default prompt for Argentine market financial advisor
        self.default_prompt = """### ROL Y OBJETIVO
Actúa como un Asesor Financiero Senior especializado en el mercado de capitales argentino y en la plataforma Invertir Online (IOL). Tu objetivo es gestionar y optimizar patrimonios de inversores minoristas, equilibrando riesgo y rendimiento en un contexto de alta volatilidad.

### CONTEXTO DE MERCADO (ARGENTINA & GLOBAL)
Para cada análisis, debes realizar una búsqueda activa en internet de información actualizada (últimas 24-48 horas) utilizando fuentes confiables (Bloomberg, Reuters, El Cronista, Ámbito Financiero, Rava Bursátil, Yahoo Finance).

Debes buscar y correlacionar:
1. **Variables Macro Globales:** Tasas de la FED, commodities (Soja, Petróleo, Oro), índices (S&P500, Nasdaq).
2. **Variables Macro Locales (Argentina):** Valor del Dólar (MEP, CCL, Blue), Brecha cambiaria, Riesgo País, Reservas del BCRA, Inflación esperada (REM), y noticias políticas/económicas de impacto inmediato.
3. **Tendencias de Sector:** Tecnología, Energía (Vaca Muerta), Bancos, etc.

### INSTRUCCIONES DE ANÁLISIS DE PORTAFOLIO
Yo te proporcionaré mi portafolio actual y el monto disponible para invertir (en Pesos ARS o Dólares). Tú debes:
1. **Calcular la composición actual:** % en Renta Fija vs. Renta Variable, % en Argentina vs. EE.UU. (vía CEDEARs).
2. **Detectar riesgos:** Sobreexposición a un solo activo o sector, falta de liquidez, o activos con perspectivas negativas a corto plazo.
3. **Proponer Rebalanceo:** Sugerir compras (o ventas) para optimizar la cartera según mi perfil (conservador/moderado/agresivo).

### REGLAS DE RECOMENDACIÓN (IOL)
Las sugerencias deben ser ejecutables en IOL:
* **CEDEARs:** Prioriza aquellos con volumen (liquidez) en pesos. Considera el ratio de conversión y el tipo de cambio implícito (CCL).
* **Acciones Locales:** Enfócate en el panel líder (Merval) a menos que detectes una oportunidad clara en el panel general.
* **Bonos/ONs:** Evalúa TIR, Paridad y vencimiento. Diferencia entre soberanos (AL30, GD30) y corporativos (ONs).
* **FCIs:** Si recomiendas Fondos Comunes, sugiere tipos (Money Market, T+1, Renta Mixta) basándote en la oferta usual de IOL.

### FORMATO DE SALIDA REQUERIDO
1.  **Resumen de Mercado:** Breve síntesis (3 bullets) de "El clima del mercado hoy".
2.  **Diagnóstico de Portafolio:** Qué está bien y qué es peligroso en mi tenencia actual.
4.  **PLAN DE ACCIÓN (OBLIGATORIO - TABLA):**
        Presenta una tabla con EXPLICITAMENTE qué comprar o vender.
        Columnas: `| Ticker | Acción (Compra/Venta) | Cantidad | Precio Límite (ARS) | Monto Total (ARS) | Fundamento Corto |`
        
        *Asegúrate de usar todo el dinero disponible ($investment_amount) más lo generado por ventas.*
    
    5.  **Proyección:** Qué esperar de estos movimientos en el corto/mediano plazo."""

    def get_first_available_model(self):
        """
        Queries the API to find a model that supports generateContent.
        Prioritizes models in self.preferred_models.
        """
        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                available_models = [
                    m.get('name', '').replace('models/', '') 
                    for m in data.get('models', []) 
                    if 'generateContent' in m.get('supportedGenerationMethods', [])
                ]
                
                for pref in self.preferred_models:
                    if pref in available_models:
                        return f"models/{pref}"
                
                for model in data.get('models', []):
                    name = model.get('name', '')
                    methods = model.get('supportedGenerationMethods', [])
                    if 'generateContent' in methods and 'gemini' in name:
                        if 'flash' in name: return name
                        if 'pro' in name: return name
                
                if available_models:
                    return f"models/{available_models[0]}"
                    
            return "models/gemini-pro"
        except:
            return "models/gemini-pro"
            
    def validate_key(self):
        """Simple check to verify if the API key is valid."""
        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            response = self.session.get(url, timeout=self.timeout)
            return response.status_code == 200
        except Exception as e:
            print(f"API Key validation failed: {e}")
            return False

    def list_models(self):
        """Returns a list of available models that support content generation."""
        try:
            url = f"{self.base_url}/models?key={self.api_key}"
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                data = response.json()
                models = [
                    m.get('name', '').replace('models/', '') 
                    for m in data.get('models', []) 
                    if 'generateContent' in m.get('supportedGenerationMethods', [])
                ]
                return models
            return []
        except:
            return []

    def analyze_portfolio(self, portfolio_data, investment_amount, context_data, 
                          news_headlines=[], model_name=None, reasoning_enabled=True, 
                          prompt_template=None, use_grounding=True):
        """
        Generates an investment recommendation using Gemini REST API.
        - use_grounding: If True, enables Google Search grounding for real-time data.
        """
        if not model_name:
            model_name = self.get_first_available_model()
        
        # 1. Prepare Enriched Portfolio Data
        portfolio_summary = ""
        total_portfolio_value = sum(item.get('Total Value', 0) for item in portfolio_data) if portfolio_data else 0
        
        if not portfolio_data:
            portfolio_summary = "El portafolio está vacío actualmente."
        else:
            portfolio_summary = "| Símbolo | Descripción | Cantidad | Precio | Valor | Var. Diaria | Peso % |\n"
            portfolio_summary += "|---------|-------------|----------|--------|-------|-------------|--------|\n"
            for item in portfolio_data:
                weight = (item.get('Total Value', 0) / total_portfolio_value * 100) if total_portfolio_value > 0 else 0
                portfolio_summary += f"| {item.get('Symbol', 'N/A')} | {item.get('Description', '')[:25]} | {item.get('Quantity', 0)} | ${item.get('Last Price', 0):,.2f} | ${item.get('Total Value', 0):,.2f} | {item.get('Daily Var %', 0):.2f}% | {weight:.1f}% |\n"
            
            portfolio_summary += f"\n**Valor Total del Portafolio:** ${total_portfolio_value:,.2f} ARS"

        # Market context
        def _format_price(value):
            if value is None:
                return "N/A"
            try:
                return f"${float(value):,.2f}"
            except (TypeError, ValueError):
                return "N/A"

        market_context_str = ""
        if context_data:
            for k, v in context_data.items():
                market_context_str += f"- {k}: {_format_price(v)}\n"
        else:
            market_context_str = "No se pudo obtener contexto de mercado."
            
        news_str = "\n".join(news_headlines) if news_headlines else "No se encontraron noticias recientes relevantes."

        # 2. Construct Prompt
        base_prompt = prompt_template if prompt_template else self.default_prompt
        
        prompt_text = f"""{base_prompt}

---
**INPUT DEL USUARIO:**
* **Perfil de Riesgo:** Moderado/Agresivo
* **Monto a invertir:** ${investment_amount:,.2f} ARS
* **Horizonte de inversión:** Mediano plazo (6-12 meses)

**Mi Portafolio Actual:**
{portfolio_summary}

**Contexto de Mercado (Precios de Referencia):**
{market_context_str}

**Noticias Recientes (de feed local):**
{news_str}

---
Por favor, realiza tu análisis y proporciona recomendaciones concretas y ejecutables en IOL.
"""

        # 3. Call API
        try:
            if not model_name.startswith("models/"):
                model_name = f"models/{model_name}"
                
            url = f"{self.base_url}/{model_name}:generateContent?key={self.api_key}"
            
            headers = {'Content-Type': 'application/json'}
            data = {
                "contents": [{"parts": [{"text": prompt_text}]}]
            }
            
            # Enable Google Search Grounding + Code Execution
            if use_grounding:
                data["tools"] = [
                    {"google_search": {}},
                    {"code_execution": {}}
                ]
            
            # Thinking Config for supported models
            if reasoning_enabled and ("thinking" in model_name or "gemini-3" in model_name):
                data["generationConfig"] = {
                    "thinkingConfig": {
                        "includeThoughts": True 
                    }
                }
            
            response = self.session.post(url, headers=headers, json=data, timeout=self.timeout)
            
            if response.status_code == 200:
                result = response.json()
                try:
                    # Handle parts and filter out thinking blocks
                    parts = result['candidates'][0]['content']['parts']
                    
                    cleaned_parts = []
                    for part in parts:
                        # Gemini 3/2.5 Thinking models return thoughts in a part with "thought": true
                        # We skip these to return only the final answer.
                        if part.get('thought', False):
                            continue
                        
                        if 'text' in part:
                            cleaned_parts.append(part['text'])
                            
                    text = "\n".join(cleaned_parts)
                    return text, model_name
                except (KeyError, IndexError):
                    if 'promptFeedback' in result:
                        return f"Model blocked response: {result['promptFeedback']}", model_name
                    return f"Error parsing result: {result}", model_name
            else:
                return f"Error from API ({model_name}): {response.status_code} - {response.text}", model_name
                
        except Exception as e:
            return f"Error generating analysis: {e}", "Unknown Model"

    def _create_session(self):
        session = requests.Session()
        try:
            retry = Retry(
                total=3,
                connect=3,
                read=3,
                status=3,
                backoff_factor=0.5,
                status_forcelist=(429, 500, 502, 503, 504),
                allowed_methods=frozenset(["GET", "POST"])
            )
        except TypeError:
            retry = Retry(
                total=3,
                connect=3,
                read=3,
                status=3,
                backoff_factor=0.5,
                status_forcelist=(429, 500, 502, 503, 504),
                method_whitelist=["GET", "POST"]
            )

        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session
