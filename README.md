# 🧐 Chatbot Financiero con Rasa y Streamlit

Este proyecto integra un asistente conversacional para la gestión de finanzas personales, construido con Rasa y una interfaz web desarrollada en Streamlit. Ambos servicios están desplegados en Render y Streamlit Community Cloud, permitiendo una interacción fluida y en línea.

---

## 📁 Tabla de Contenidos

- [📦 Estructura del Proyecto](#-estructura-del-proyecto)
- [⚙️ Requisitos Previos](#-requisitos-previos)
- [🚀 Despliegue en Producción](#-despliegue-en-producción)
- [📊 Instalación y Ejecución Local (Desarrollo)](#-instalación-y-ejecución-local-desarrollo)
- [💪 Funcionalidades del Asistente Financiero](#-funcionalidades-del-asistente-financiero)
- [🔄 Sincronización Automática con GitHub](#-sincronización-automática-con-github)
- [🌐 Resumen de URLs de Producción](#-resumen-de-urls-de-producción)
- [👨‍💻 Desarrolladores](#-desarrolladores)

---

## 📦 Estructura del Proyecto

```
chatbot-financiero/
├── actions/
│   ├── actions.py
│   ├── transacciones_io.py
│   ├── alertas_io.py
│   ├── requirements.txt
│   └── Dockerfile
├── data/
│   ├── nlu.yml
│   ├── rules.yml
│   └── stories.yml
├── models/
├── streamlit_app/
│   └── app.py
├── alertas.json
├── transacciones.json
├── config.yml
├── credentials.yml
├── endpoints.yml
├── README.md
└── requirements.txt
```

---

## ⚙️ Requisitos Previos

- Python 3.10
- pip
- Cuenta en Render
- Cuenta en Streamlit Community Cloud (opcional)

---

## 🚀 Despliegue en Producción

El chatbot financiero está desplegado utilizando **Render** como plataforma principal para ambos servidores (Rasa y Actions) y **Streamlit Community Cloud** como frontend de usuario.

### 1. Backend de Acciones Personalizadas (Actions Server)

- Carpeta utilizada: `actions/`
- Desplegado en Render como servicio Docker independiente.
- Puerto expuesto: `5055`
- URL pública generada:

```
https://actions-server-xxxx.onrender.com
```

### 2. Servidor Principal de Rasa (Chatbot)

- Editar `endpoints.yml`:

```yaml
action_endpoint:
  url: "https://actions-server-xxxx.onrender.com/webhook"
```

- Comando de ejecución en Render:

```
rasa run --enable-api --cors "*" --debug
```

- URL pública generada:

```
https://chatbot-financiero-xxxx.onrender.com
```

### 3. Frontend Streamlit

- Carpeta utilizada: `streamlit_app/`
- Archivo principal: `app.py`
- Configurar el endpoint de Rasa:

```python
RASA_ENDPOINT = "https://chatbot-financiero-xxxx.onrender.com/webhooks/rest/webhook"
```

- Desplegado en Streamlit Community Cloud:
  - [Chatbot Financiero - Streamlit](https://chatbot-financiero-pt77l48szdcbu6pxju2kvb.streamlit.app/)

### 4. Visor de Datos Financieros (Herramienta Auxiliar)

- Herramienta adicional para visualizar registros en tiempo real:
  - [Visor de Datos Financieros - Streamlit](https://visor-b2anm9fwizjlwa3b4skff2.streamlit.app/)

---

## 📊 Instalación y Ejecución Local (Desarrollo)

```
# Clonar el repositorio
git clone https://github.com/MaximoGuzmanH/chatbot-financiero.git
cd chatbot-financiero

# Crear entorno virtual
python -m venv venv
source venv/bin/activate       # Linux/Mac
venv\Scripts\activate          # Windows

# Instalar dependencias
pip install -r requirements.txt

# Entrenar el modelo
rasa train

# Ejecutar chatbot en terminal
rasa shell

# Ejecutar interfaz Streamlit
streamlit run streamlit_app/app.py
```

Accede desde el navegador:

```
http://localhost:8501
```

---

## 💪 Funcionalidades del Asistente Financiero

| Intent | Descripción |
|--------|-------------|
| `analizar_gastos` | Analiza todos los gastos registrados mostrando totales y porcentajes por categoría. |
| `comparar_meses` | Compara gastos o ingresos entre dos meses distintos. |
| `consultar_configuracion` | Consulta alertas presupuestarias activas configuradas. |
| `consultar_informacion_financiera` | Consulta ingresos o gastos registrados filtrando por tipo, categoría o periodo. |
| `crear_configuracion` | Crea nuevas alertas de presupuesto mensual por categoría. |
| `modificar_configuracion` | Modifica alertas existentes (monto y periodo). |
| `eliminar_configuracion` | Elimina configuraciones de alertas. |
| `registrar_gasto` | Registra un nuevo gasto. |
| `registrar_ingreso` | Registra un nuevo ingreso. |
| `resetear_categoria_gastos` | Borra todos los gastos de una categoría en un mes determinado. |
| `ver_historial_completo` | Muestra todo el historial de ingresos y gastos filtrado por mes. |
| `entrada_no_entendida` | Gestiona entradas ambiguas o incompletas. |

---

## 🔄 Sincronización Automática con GitHub

- Cada vez que se registra una nueva transacción o alerta, los archivos `transacciones.json` y `alertas.json` se sincronizan automáticamente con el repositorio de GitHub.
- Seguridad implementada mediante autenticación segura usando `GITHUB_TOKEN` como variable de entorno.

---

## 🌐 Resumen de URLs de Producción

| Servicio | URL |
|----------|-----|
| Chatbot Financiero (Rasa Render) | [https://chatbot-financiero-pt77l48szdcbu6pxju2kvb.streamlit.app/](https://chatbot-financiero-pt77l48szdcbu6pxju2kvb.streamlit.app/) |
| Actions Server (Render) | `https://actions-server-xxxx.onrender.com` |
| Frontend Usuario (Streamlit) | [https://chatbot-financiero-pt77l48szdcbu6pxju2kvb.streamlit.app/](https://chatbot-financiero-pt77l48szdcbu6pxju2kvb.streamlit.app/) |
| Visor de Datos Financieros | [https://visor-b2anm9fwizjlwa3b4skff2.streamlit.app/](https://visor-b2anm9fwizjlwa3b4skff2.streamlit.app/) |

---

## 👨‍💻 Desarrolladores

- Máximo Guzmán Huamán
- Sergio Renato Zegarra Villanueva

Proyecto de gestión financiera personal mediante inteligencia artificial conversacional.

---

# 📝 Repositorio Oficial

- [GitHub - Chatbot Financiero](https://github.com/MaximoGuzmanH/chatbot-financiero)

---

# 🚀 ¡Listo para Usarse y Escalar!

