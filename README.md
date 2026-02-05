# 💰 Inver - Personal Investment Assistant

**Inver** es un asistente de inversiones personal potenciado por Inteligencia Artificial. Utiliza modelos avanzados de Google Gemini para analizar tu portafolio, el contexto del mercado y las noticias recientes para ofrecerte recomendaciones estratégicas de inversión personalizadas.

## 🚀 Características

- **Dashboard de Mercado**: Visualización en tiempo real de activos clave (SPY, GLD, MELI, GGAL).
- **Gestión de Portafolio**:
  - **Modo Simulación**: Datos de prueba para explorar la funcionalidad sin credenciales reales.
  - **Integración con IOL (InvertirOnline)**: Conexión directa para ver tu portafolio real (requiere credenciales).
- **Analista IA (Gemini)**:
  - Utiliza modelos de última generación (incluyendo modelos "Thinking" como Gemini 2.0 Flash Thinking).
  - Analiza la composición de tu cartera.
  - Considera el contexto global y noticias financieras recientes.
  - Permite personalizar el "System Prompt" para ajustar el perfil del asesor.
- **Noticias en Tiempo Real**: Obtención automática de titulares relevantes vía Yahoo Finance.

## 📋 Requisitos Previos

- Python 3.8 o superior.
- Una API Key de Google Gemini (puedes obtenerla en [Google AI Studio](https://aistudio.google.com/)).
- (Opcional) Cuenta en InvertirOnline si deseas conectar tu portafolio real.

## 🛠️ Instalación

1. **Clonar el repositorio**:
   ```bash
   git clone <URL_DEL_REPOSITORIO>
   cd Inver
   ```

2. **Crear un entorno virtual (recomendado)**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   ```

3. **Instalar dependencias**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuración de Variables de Entorno**:
   Crea un archivo `.env` en la raíz del proyecto (puedes usar `.env.example` como base):
   ```bash
   cp .env.example .env
   ```
   
   Edita el archivo `.env` y agrega tus claves:
   ```env
   # Obligatorio para el análisis IA
   GEMINI_API_KEY=tu_api_key_aqui

   # Obligatorio para guardar credenciales y cifrar datos sensibles
   # Genera una clave con:
   # python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ENCRYPTION_KEY=tu_clave_fernet_aqui

   # Obligatorio: clave para cookies de sesión
   COOKIE_KEY=tu_cookie_key_aqui

   # Recomendado: contraseña del usuario admin inicial
   # Si no se setea, se genera una temporal y se imprime en consola al iniciar
   ADMIN_PASSWORD=una_password_segura

   # Opcional: Solo si usas la integración con InvertirOnline
   IOL_USERNAME=tu_usuario_iol
   IOL_PASSWORD=tu_password_iol
   ```
   *Nota: Si no configuras las credenciales de IOL, la app funcionará en "Modo Simulación" por defecto.*
   *Nota: Si no configuras `ENCRYPTION_KEY` y `COOKIE_KEY`, la app se detendrá al iniciar.*

## ▶️ Ejecución

### Opción A: Ejecución Local (Normal)

Para iniciar la aplicación web:

```bash
streamlit run app.py
```

La aplicación se abrirá automáticamente en tu navegador (usualmente en `http://localhost:8501`).

### Opción B: Ejecución con Docker (Recomendado para 24/7)

Si quieres dejarlo corriendo en un servidor, Raspberry Pi o en tu PC sin depender de tener la terminal abierta:

1.  Asegúrate de tener Docker y Docker Compose instalados.
2.  Ejecuta:
    ```bash
    docker-compose up -d --build
    ```
3.  Esto levantará dos servicios:
    *   **inver-web**: La interfaz web en `http://localhost:8501`.
    *   **inver-scheduler**: Un proceso de fondo que actualiza tu portafolio **inmediatamente al iniciar y luego cada 60 minutos**. Esto asegura que siempre tengas el dato más reciente posible, incluso si apagas el equipo temprano.

Para ver los logs del actualizador automático:
```bash
docker logs -f inver-scheduler
```

Para detener todo:
```bash
docker-compose down
```

## 🧱 Estructura del Proyecto

```
app.py
src/
  __init__.py
  settings.py
  ui/
    app.py
  services/
    ai_analyst.py
    market_data.py
    iol_client.py
    cron_update.py
    scheduler.py
    list_models.py
  data/
    auth_manager.py
    portfolio_manager.py
    seed_history.py
```

**Descripción rápida**
- `app.py`: entrypoint para Streamlit (`streamlit run app.py`).
- `src/settings.py`: configuración central (Pydantic + `.env`).
- `src/ui/`: capa de interfaz (Streamlit).
- `src/services/`: lógica de negocio e integraciones externas.
- `src/data/`: acceso a datos y persistencia (SQLite).

## ⚠️ Disclaimer

Esta aplicación es una herramienta de asistencia y **NO** constituye asesoramiento financiero profesional vinculante. Las inversiones en mercados financieros con llevan riesgos. Siempre realiza tu propia investigación (DYOR) o consulta con un asesor matriculado antes de invertir.
