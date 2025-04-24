from typing import Any, Text, Dict, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import EventType
from transacciones_io import guardar_transaccion, cargar_transacciones
from rasa_sdk.events import SlotSet
from collections import defaultdict
import json
import os
import re
from datetime import datetime
from collections import Counter, defaultdict
from rasa_sdk.types import DomainDict
from dateparser import parse as parse_fecha_relativa
from transacciones_io import eliminar_transaccion_logicamente
from alertas_io import guardar_alerta, eliminar_alerta_logicamente, cargar_alertas, guardar_todas_las_alertas
import alertas_io

def construir_mensaje(*bloques: str) -> str:
    """Concatena bloques separados por doble salto, permitiendo saltos simples dentro de cada bloque."""
    return "\n\n".join(bloque.strip() for bloque in bloques if bloque)

def formatear_fecha(fecha: str) -> str:
    try:
        partes = fecha.strip().split("/")
        if len(partes) == 3:
            dia, mes, anio = partes
            meses = {
                "01": "enero", "02": "febrero", "03": "marzo", "04": "abril",
                "05": "mayo", "06": "junio", "07": "julio", "08": "agosto",
                "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"
            }
            mes_nombre = meses.get(mes.zfill(2), mes)
            return f"{int(dia)} de {mes_nombre} de {anio}"
    except:
        pass
    return fecha

def get_entity(tracker: Tracker, entity_name: str) -> Text:
    entity = next(tracker.get_latest_entity_values(entity_name), None)
    return entity if entity else ""

def parse_monto(monto_raw: str) -> float:
    try:
        monto_limpio = (
            monto_raw.lower()
            .replace("soles", "")
            .replace("sol", "")
            .replace("s/", "")
            .replace("s\\", "")
            .replace("s", "")
            .replace(",", "")
            .strip()
        )
        return float(monto_limpio)
    except Exception as e:
        print(f"[ERROR] No se pudo convertir el monto: '{monto_raw}' → {e}")
        return 0.0

class ActionRegistrarGasto(Action):
    def name(self) -> Text:
        return "action_registrar_gasto"

    def run(self, dispatcher, tracker, domain):
        try:
            texto_usuario = tracker.latest_message.get("text", "").lower()
            tipo_actual = tracker.get_slot("tipo") or "gasto"

            monto_raw = get_entity(tracker, "monto") or tracker.get_slot("monto")
            categoria = get_entity(tracker, "categoria") or tracker.get_slot("categoria")
            fecha_raw = get_entity(tracker, "fecha") or tracker.get_slot("fecha")
            medio = get_entity(tracker, "medio") or tracker.get_slot("medio")

            campos_faltantes = []
            if not monto_raw:
                campos_faltantes.append("monto")
            if not categoria:
                campos_faltantes.append("categoría")
            if not medio:
                campos_faltantes.append("medio")

            if campos_faltantes:
                mensaje = "❗ Para registrar tu gasto, necesito también:\n\n"
                for campo in campos_faltantes:
                    if campo == "medio":
                        mensaje += "• ¿Con qué medio realizaste el gasto? (efectivo, débito o crédito)\n"
                    elif campo == "monto":
                        mensaje += "• ¿Cuál fue el monto?\n"
                    elif campo == "categoría":
                        mensaje += "• ¿En qué categoría clasificarías este gasto?\n"

                dispatcher.utter_message(text=mensaje.strip())
                return [
                    SlotSet("tipo", "gasto"),
                    SlotSet("monto", monto_raw),
                    SlotSet("categoria", categoria),
                    SlotSet("fecha", fecha_raw),
                    SlotSet("medio", medio)
                ]

            monto = parse_monto(monto_raw)
            if monto == 0.0:
                dispatcher.utter_message(text="⚠️ El monto ingresado no es válido. Intenta nuevamente.")
                return []

            # 🗓️ Procesar fecha
            if not fecha_raw:
                fecha_raw = datetime.now().strftime("%d/%m/%Y")
            elif len(fecha_raw.split("/")) == 2:
                fecha_raw += f"/{datetime.now().year}"
            fecha = formatear_fecha(fecha_raw)

            transaccion = {
                "tipo": "gasto",
                "monto": monto,
                "categoria": categoria,
                "fecha": fecha,
                "medio": medio
            }

            guardar_transaccion(transaccion)
            mes_actual = transaccion.get("mes", "").lower()

            # 🚨 Verificar alertas activas
            alertas = cargar_alertas()
            alertas_activas = [
                a for a in alertas
                if a.get("categoria", "").lower() == categoria.lower()
                and a.get("periodo", "").lower() == mes_actual
            ]

            if alertas_activas:
                limite = float(alertas_activas[0].get("monto", 0))
                transacciones = cargar_transacciones()
                total_categoria = sum(
                    float(t["monto"]) for t in transacciones
                    if t.get("tipo") == "gasto"
                    and t.get("categoria", "").lower() == categoria.lower()
                    and t.get("mes", "").lower() == mes_actual
                )
                if total_categoria > limite:
                    exceso = total_categoria - limite
                    dispatcher.utter_message(
                        text=(
                            f"⚠️ *Atención*: Has superado el límite de *{limite:.2f} soles* en *{categoria}* "
                            f"para *{mes_actual}*. Te has excedido por *{exceso:.2f} soles*."
                        )
                    )

            # ✅ Confirmación de registro con formato optimizado
            mensaje = construir_mensaje(
                "💸 **Gasto registrado correctamente:**",
                f"💰 *Monto:* {monto:.2f} soles",
                f"📁 *Categoría:* {categoria}",
                f"📅 *Fecha:* {fecha}",
                f"💳 *Medio:* {medio}",
                "👉 ¿Deseas *registrar otro gasto* o *consultar tu saldo*?"
            )
            
            dispatcher.utter_message(text=mensaje)

            return [
                SlotSet("tipo", None),
                SlotSet("sugerencia_pendiente", "action_consultar_saldo"),
                SlotSet("categoria", None),
                SlotSet("monto", None),
                SlotSet("fecha", None),
                SlotSet("medio", None)
            ]

        except Exception as e:
            print(f"[ERROR] Fallo en action_registrar_gasto: {e}")
            dispatcher.utter_message(
                text="❌ Ocurrió un error al registrar tu gasto. Por favor, intenta nuevamente."
            )
            return []

from datetime import datetime, timedelta

from datetime import datetime, timedelta

class ActionRegistrarIngreso(Action):
    def name(self) -> Text:
        return "action_registrar_ingreso"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        try:
            texto_usuario = tracker.latest_message.get("text", "").lower()
            tipo_actual = tracker.get_slot("tipo") or "ingreso"

            monto_raw = get_entity(tracker, "monto") or tracker.get_slot("monto")
            categoria = get_entity(tracker, "categoria") or tracker.get_slot("categoria")
            fecha_raw = get_entity(tracker, "fecha") or tracker.get_slot("fecha")
            medio = get_entity(tracker, "medio") or tracker.get_slot("medio")

            campos_faltantes = []
            if not monto_raw:
                campos_faltantes.append("monto")
            if not categoria:
                campos_faltantes.append("categoría")
            if not medio:
                campos_faltantes.append("medio")

            if campos_faltantes:
                mensaje = "⚠️ **Faltan algunos datos para registrar tu ingreso:**\n\n"
                if "monto" in campos_faltantes:
                    mensaje += "- ¿Cuál fue el **monto** del ingreso?\n"
                if "categoría" in campos_faltantes:
                    mensaje += "- ¿Qué **tipo de ingreso** fue? (sueldo, venta, etc.)\n"
                if "medio" in campos_faltantes:
                    mensaje += "- ¿Con qué **medio** recibiste el ingreso? (efectivo, tarjeta de débito, etc.)\n"
                
                dispatcher.utter_message(text=mensaje)
                return [
                    SlotSet("tipo", "ingreso"),
                    SlotSet("monto", monto_raw),
                    SlotSet("categoria", categoria),
                    SlotSet("fecha", fecha_raw),
                    SlotSet("medio", medio)
                ]

            monto = parse_monto(monto_raw)
            if monto == 0.0:
                dispatcher.utter_message(text="❌ El monto ingresado no es válido. Intenta nuevamente.")
                return []

            # Procesamiento de fecha
            if not fecha_raw:
                fecha_raw = datetime.now().strftime("%d/%m/%Y")
            elif len(fecha_raw.split("/")) == 2:
                fecha_raw += f"/{datetime.now().year}"
            fecha = formatear_fecha(fecha_raw)

            transaccion = {
                "tipo": "ingreso",
                "monto": monto,
                "categoria": categoria,
                "fecha": fecha,
                "medio": medio
            }

            guardar_transaccion(transaccion)
            
            mensaje = construir_mensaje(
                "✅ **Ingreso registrado con éxito:**",
                f"💰 *Monto:* {monto:.2f} soles",
                f"📁 *Categoría:* {categoria}",
                f"📅 *Fecha:* {fecha}",
                f"💳 *Medio:* {medio}",
                "👉 ¿Deseas *registrar otro ingreso* o *consultar tu saldo*?"
            )

            dispatcher.utter_message(text=mensaje)

            return [
                SlotSet("tipo", None),
                SlotSet("sugerencia_pendiente", "action_consultar_saldo"),
                SlotSet("categoria", None),
                SlotSet("monto", None),
                SlotSet("fecha", None),
                SlotSet("medio", None)
            ]

        except Exception as e:
            print(f"[ERROR] Fallo en action_registrar_ingreso: {e}")
            dispatcher.utter_message(text="❌ Ocurrió un error al registrar tu ingreso. Por favor, intenta nuevamente.")
            return []

class ActionConsultarSaldo(Action):
    def name(self) -> Text:
        return "action_consultar_saldo"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        try:
            transacciones = cargar_transacciones()
            medio = next(tracker.get_latest_entity_values("medio"), None)

            if medio:
                transacciones = [t for t in transacciones if t.get("medio") == medio]

            total_ingresos = sum(float(t["monto"]) for t in transacciones if t["tipo"] == "ingreso")
            total_gastos = sum(float(t["monto"]) for t in transacciones if t["tipo"] == "gasto")
            saldo = total_ingresos - total_gastos

            if total_ingresos == 0 and total_gastos == 0:
                if medio:
                    mensaje = (
                        f"📭 *No se han registrado ingresos ni gastos con* **{medio}**.\n\n"
                        f"¿Deseas registrar uno ahora?"
                    )
                else:
                    mensaje = (
                        f"📭 *Aún no se han registrado ingresos ni gastos.*\n\n"
                        f"Puedes comenzar registrando tu primer ingreso o gasto."
                    )

                dispatcher.utter_message(text=mensaje)
                return []

            if medio:
                mensaje = (
                    f"🧮 **Saldo disponible en {medio}:**\n\n"
                    f"💰 *{saldo:.2f} soles*\n\n"
                    f"¿Deseas *ver tu historial* o *consultar tus ingresos*?"
                )
            else:
                mensaje = (
                    f"🧮 **Saldo total disponible:**\n\n"
                    f"💰 *{saldo:.2f} soles*\n\n"
                    f"¿Deseas *ver tu historial* o *consultar tus ingresos*?"
                )

            dispatcher.utter_message(text=mensaje)
            return [SlotSet("sugerencia_pendiente", "action_ver_historial_completo")]

        except Exception as e:
            print(f"[ERROR] Fallo en action_consultar_saldo: {e}")
            dispatcher.utter_message(text="❌ Ocurrió un error al consultar tu saldo. Por favor, intenta nuevamente.")
            return []

class ActionVerHistorialCompleto(Action):
    def name(self) -> Text:
        return "action_ver_historial_completo"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        try:
            from transacciones_io import cargar_transacciones

            transacciones = cargar_transacciones(filtrar_activos=True)
            periodo = get_entity(tracker, "periodo")

            # 🧠 Reconstruir periodo en todas las transacciones
            for t in transacciones:
                if not t.get("periodo"):
                    mes = t.get("mes", "").strip().lower()
                    año = str(t.get("año")).strip()
                    if mes and año:
                        t["periodo"] = f"{mes} de {año}"

            # 🎯 Filtrar solo ingresos/gastos
            transacciones_filtradas = [
                t for t in transacciones if t.get("tipo") in ["ingreso", "gasto"]
            ]

            # 📆 Filtrar por periodo si se indicó
            if periodo:
                periodo = periodo.lower().strip()
                transacciones_filtradas = [
                    t for t in transacciones_filtradas
                    if periodo == t.get("periodo", "").lower()
                ]

            if not transacciones_filtradas:
                mensaje = (
                    f"📭 *No se encontraron movimientos registrados*"
                    + (f" para el periodo **{periodo}**." if periodo else ".")
                )
                dispatcher.utter_message(text=mensaje)
                return []

            # 🧾 Construcción del mensaje
            mensaje = []
            encabezado = "📋 **Historial de transacciones**"
            if periodo:
                encabezado += f" para *{periodo}*"
            mensaje.append(encabezado + ":\n")

            for t in transacciones_filtradas:
                tipo = t.get("tipo", "transacción").capitalize()
                monto = float(t.get("monto", 0))
                categoria = t.get("categoria", "sin categoría").capitalize()
                fecha = formatear_fecha(t.get("fecha", "")) if t.get("fecha") else ""
                medio = t.get("medio", "")

                linea = f"🔸 *{tipo}* de *{monto:.2f} soles* en *{categoria}*"
                if fecha:
                    linea += f", el *{fecha}*"
                if medio and medio.lower() != "n/a":
                    linea += f", con *{medio}*"
                mensaje.append(linea)

            mensaje.append("\n📊 ¿Deseas *registrar algo nuevo* o *consultar tu resumen mensual*?")
            dispatcher.utter_message(text=construir_mensaje(*mensaje))
            return [SlotSet("sugerencia_pendiente", "action_consultar_resumen_mensual")]

        except Exception as e:
            print(f"[ERROR] Fallo en action_ver_historial_completo: {e}")
            dispatcher.utter_message(
                text="❌ Ocurrió un error al mostrar tu historial. Por favor, intenta nuevamente."
            )
            return []

from collections import Counter, defaultdict

class ActionAnalizarGastos(Action):
    def name(self) -> Text:
        return "action_analizar_gastos"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        from datetime import datetime
        import re
        from collections import defaultdict

        transacciones = cargar_transacciones(filtrar_activos=True)
        texto_usuario = tracker.latest_message.get("text", "").lower()

        # 🔍 Extraer entidades
        periodo_raw = get_entity(tracker, "periodo")
        categoria = get_entity(tracker, "categoria")

        # 📆 Normalizar periodo
        periodo = None
        if "este mes" in texto_usuario and not periodo_raw:
            periodo = f"{datetime.now().strftime('%B').lower()} de {datetime.now().year}"
        elif periodo_raw:
            match = re.search(r"([a-záéíóúñ]+)(?:\s+de\s+)?(\d{4})?", periodo_raw.lower())
            if match:
                mes = match.group(1).strip()
                año = match.group(2) or str(datetime.now().year)
                periodo = f"{mes} de {año}"
            else:
                periodo = periodo_raw.strip().lower()

        # 🎯 Filtrar solo gastos válidos
        gastos = [
            t for t in transacciones
            if t.get("tipo") == "gasto" and t.get("monto") and t.get("categoria")
        ]
        if periodo:
            gastos = [g for g in gastos if g.get("periodo", "").lower() == periodo.lower()]

        if not gastos:
            mensaje = (
                f"📭 *No se encontraron gastos registrados*"
                + (f" para el periodo **{periodo}**." if periodo else ".")
                + "\n\n¿Deseas ingresar uno?"
            )
            dispatcher.utter_message(text=mensaje)
            return []

        sin_categoria = [g for g in gastos if not g.get("categoria")]

        # 📂 Si se indicó categoría específica
        if categoria:
            gastos_categoria = [g for g in gastos if categoria.lower() in g.get("categoria", "").lower()]
            total_categoria = sum(float(g["monto"]) for g in gastos_categoria)

            if not gastos_categoria:
                mensaje = construir_mensaje(
                    f"⚠️ Se encontraron {len(sin_categoria)} gasto(s) sin categoría. Esto podría afectar el análisis." if sin_categoria else "",
                    f"🔍 No se encontraron gastos en la categoría *{categoria}*" +
                    (f" durante *{periodo}*" if periodo else "") + "."
                )
            else:
                mensaje = construir_mensaje(
                    f"⚠️ Se encontraron {len(sin_categoria)} gasto(s) sin categoría. Esto podría afectar el análisis." if sin_categoria else "",
                    f"📂 Has gastado un total de *{total_categoria:.2f} soles* en *{categoria}*" +
                    (f" durante *{periodo}*" if periodo else "") + "."
                )

            dispatcher.utter_message(text=mensaje)
            return [SlotSet("sugerencia_pendiente", "action_consultar_resumen_mensual")]

        # 📊 Agrupar por categoría y calcular totales
        categorias_sumadas = defaultdict(float)
        for g in gastos:
            nombre = g.get("categoria", "Sin categoría").strip().lower()
            categorias_sumadas[nombre] += float(g.get("monto", 0))

        total_gasto = sum(categorias_sumadas.values())
        top_categorias = sorted(categorias_sumadas.items(), key=lambda x: x[1], reverse=True)[:3]

        # 🧾 Generar respuesta formateada
        mensaje = []

        titulo = "🧾 **Análisis de tus hábitos de consumo**"
        if periodo:
            titulo += f" durante *{periodo}*"
        mensaje.append(titulo)

        if sin_categoria:
            mensaje.append(f"⚠️ Se encontraron {len(sin_categoria)} gasto(s) sin categoría. Esto podría afectar el análisis.")

        resumen = "📊 **Categorías con mayor gasto:**"
        for cat, total in top_categorias:
            porcentaje = (total / total_gasto) * 100
            resumen += f"\n• {cat.title()}: {total:.2f} soles ({porcentaje:.1f}%)"
        mensaje.append(resumen)

        mensaje.append(f"💸 **Total gastado:** *{total_gasto:.2f} soles*")

        # 📋 Ejemplos recientes
        def parse_fecha(fecha_str):
            try:
                return datetime.strptime(fecha_str, "%Y-%m-%d")
            except:
                return datetime.min

        recientes = sorted(gastos, key=lambda x: parse_fecha(x.get("fecha", "")), reverse=True)[:5]
        detalles = "📋 **Ejemplos recientes:**"
        for g in recientes:
            fecha = g.get("fecha", "sin fecha")
            monto = g.get("monto", 0)
            cat = g.get("categoria", "Sin categoría")
            detalles += f"\n- {cat.title()}: {monto:.2f} soles ({fecha})"
        mensaje.append(detalles)

        mensaje.append("👉 ¿Quieres *comparar tus gastos entre meses* o *configurar una alerta*?")

        dispatcher.utter_message(text=construir_mensaje(*mensaje))

        return [SlotSet("sugerencia_pendiente", "action_comparar_meses")]

def extraer_mes(fecha: str) -> str:
    meses = {
        "01": "enero", "02": "febrero", "03": "marzo", "04": "abril",
        "05": "mayo", "06": "junio", "07": "julio", "08": "agosto",
        "09": "septiembre", "10": "octubre", "11": "noviembre", "12": "diciembre"
    }
    try:
        partes = fecha.strip().split("/")
        if len(partes) >= 2:
            mes = partes[1].lower().zfill(2)
            if mes in meses:
                return meses[mes]  # si es numérico
            return mes  # si ya está como nombre, lo devolvemos directamente
    except:
        pass
    return ""

class ActionCompararMeses(Action):
    def name(self) -> Text:
        return "action_comparar_meses"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        try:
            from datetime import datetime
            import re
            from collections import defaultdict

            transacciones = cargar_transacciones(filtrar_activos=True)
            texto = tracker.latest_message.get("text", "").lower()

            tipo = "ingreso" if "ingreso" in texto or "ingresos" in texto else "gasto"
            año_actual = str(datetime.now().year)

            posibles_meses = [
                "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
            ]

            texto_normalizado = texto
            for sep in [" y ", " o ", " vs ", " versus ", " entre ", "contra", "comparar "]:
                texto_normalizado = texto_normalizado.replace(sep, " y ")

            matches = re.findall(rf"({'|'.join(posibles_meses)})(?:\s+de)?\s+(\d{{4}})", texto_normalizado)

            if len(matches) == 2:
                periodo1 = f"{matches[0][0]} de {matches[0][1]}"
                periodo2 = f"{matches[1][0]} de {matches[1][1]}"

                if periodo1 == periodo2:
                    dispatcher.utter_message(text="⚠️ Por favor, proporciona *dos periodos diferentes* para la comparación.")
                    return []

                total = defaultdict(float)
                for t in transacciones:
                    if t.get("tipo") != tipo:
                        continue
                    if t.get("periodo", "").lower() == periodo1:
                        total[periodo1] += float(t.get("monto", 0))
                    elif t.get("periodo", "").lower() == periodo2:
                        total[periodo2] += float(t.get("monto", 0))

                v1, v2 = total.get(periodo1, 0), total.get(periodo2, 0)
                if v1 == 0 and v2 == 0:
                    dispatcher.utter_message(
                        text=f"📭 *No se encontraron {tipo}s registrados* para *{periodo1}* ni *{periodo2}*."
                    )
                    return []

                comparativa = (
                    f"⬅️ En *{periodo1}* tuviste más {tipo}s que en *{periodo2}*" if v1 > v2 else
                    f"➡️ En *{periodo2}* tuviste más {tipo}s que en *{periodo1}*" if v2 > v1 else
                    f"✅ Tus {tipo}s fueron iguales en ambos periodos."
                )

                mensaje = construir_mensaje(
                    f"📊 **Comparativa de {tipo}s:**",
                    f"• *{periodo1.capitalize()}*: {v1:.2f} soles",
                    f"• *{periodo2.capitalize()}*: {v2:.2f} soles",
                    comparativa,
                    "👉 ¿Quieres *configurar un presupuesto* o *consultar tus ingresos recientes*?"
                )
                dispatcher.utter_message(text=mensaje)
                return [SlotSet("sugerencia_pendiente", "action_crear_configuracion")]

            elif "en qué mes" in texto:
                totales_por_mes = defaultdict(float)
                for t in transacciones:
                    if t.get("tipo") != tipo:
                        continue
                    mes = t.get("mes", "").lower()
                    año = str(t.get("año"))
                    if mes in posibles_meses and año == año_actual:
                        totales_por_mes[mes] += float(t.get("monto", 0))

                if not totales_por_mes:
                    dispatcher.utter_message(
                        text=f"📭 No se encontraron {tipo}s registrados durante el año *{año_actual}*."
                    )
                    return []

                mes_max = max(totales_por_mes.items(), key=lambda x: x[1])[0]
                monto_max = totales_por_mes[mes_max]

                mensaje = construir_mensaje(
                    f"📅 **Mes con mayor {tipo} en {año_actual}:**",
                    f"• *{mes_max}* con *{monto_max:.2f} soles*",
                    "👉 ¿Deseas *comparar otros periodos* o *revisar tu historial completo*?"
                )
                dispatcher.utter_message(text=mensaje)
                return [SlotSet("sugerencia_pendiente", "action_ver_historial_completo")]

            else:
                dispatcher.utter_message(
                    text="ℹ️ Por favor, indícame *dos periodos válidos* con mes y año.\n\n*Ejemplo:* `marzo de 2024 y abril de 2024`"
                )
                return []

        except Exception as e:
            print(f"[ERROR] Fallo en action_comparar_meses: {e}")
            dispatcher.utter_message(
                text="❌ Ocurrió un error al comparar los meses. Intenta de nuevo usando dos periodos como *marzo de 2024 y abril de 2024*."
            )
            return []

class ActionConsultarInformacionFinanciera(Action):
    def name(self) -> Text:
        return "action_consultar_informacion_financiera"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        from datetime import datetime
        from collections import defaultdict
        import re

        transacciones = cargar_transacciones(filtrar_activos=True)
        texto = tracker.latest_message.get("text", "").strip().lower()
        tokens = texto.split()

        tipo = get_entity(tracker, "tipo") or tracker.get_slot("tipo")
        categoria = get_entity(tracker, "categoria") or tracker.get_slot("categoria")
        medio = get_entity(tracker, "medio") or tracker.get_slot("medio")
        fecha_raw = get_entity(tracker, "fecha") or tracker.get_slot("fecha")
        periodo_raw = get_entity(tracker, "periodo") or tracker.get_slot("periodo")

        # Verificación de ambigüedad o entrada muy breve
        verbos_clave = [
            "gasté", "gaste", "pagué", "ingresé", "recibí", "consulté", "usé",
            "muestra", "consultar", "ver", "registré", "gané", "cuánto", "invertí"
        ]
        contiene_verbo = any(v in texto for v in verbos_clave)
        if not contiene_verbo and len(tokens) <= 5:
            mensaje = construir_mensaje(
                f"❓ No logré entender tu intención con: “{texto}”. ¿Podrías reformularlo?",
                "🧠 Estoy aquí para ayudarte con tus finanzas. Puedes decir cosas como:",
                "- “¿Cuánto gasté en comida en abril?”",
                "- “Muéstrame mis ingresos por sueldo en marzo.”"
            )
            dispatcher.utter_message(text=mensaje)
            return [
                SlotSet("sugerencia_pendiente", "action_ayuda_general"),
                FollowupAction("action_entrada_no_entendida")
            ]

        # Procesar fecha relativa
        fecha = None
        if fecha_raw:
            try:
                fecha_parseada = parse_fecha_relativa(fecha_raw)
                fecha = fecha_parseada.strftime("%d/%m/%Y") if fecha_parseada else fecha_raw
            except:
                fecha = fecha_raw

        # Normalizar periodo
        periodo = None
        if periodo_raw:
            match = re.search(r"([a-záéíóúñ]+)(?:\s+de\s+)?(\d{4})?", periodo_raw.lower())
            if match:
                mes = match.group(1).strip()
                año = match.group(2) or str(datetime.now().year)
                periodo = f"{mes} de {año}"
            else:
                periodo = periodo_raw.strip().lower()

        # Filtrar transacciones
        resultados = []
        for t in transacciones:
            if tipo and t.get("tipo") != tipo:
                continue
            if medio and t.get("medio", "").lower() != medio.lower():
                continue
            if categoria and categoria.lower() not in t.get("categoria", "").lower():
                continue
            if periodo and periodo.lower() != t.get("periodo", "").lower():
                continue
            if fecha and fecha not in t.get("fecha", ""):
                continue
            resultados.append(t)

        total = sum(t["monto"] for t in resultados)

        if not resultados:
            mensaje = construir_mensaje(
                f"📭 *No se encontraron registros financieros* con los criterios proporcionados.",
                f"🧾 **Parámetros usados:**",
                f"- Tipo: *{tipo}*" if tipo else "",
                f"- Categoría: *{categoria}*" if categoria else "",
                f"- Medio: *{medio}*" if medio else "",
                f"- Fecha: *{fecha}*" if fecha else "",
                f"- Periodo: *{periodo}*" if periodo else ""
            )
            dispatcher.utter_message(text=mensaje)
            return []

        # Construir respuesta
        partes = []

        if categoria and periodo:
            partes.append(f"📌 Tu *{tipo}* total en la categoría *{categoria}* durante *{periodo}* es de *{total:.2f} soles*.")
        elif tipo and periodo:
            partes.append(f"📌 Tu *{tipo}* total durante *{periodo}* es de *{total:.2f} soles*.")
        elif tipo:
            resumen_cat = defaultdict(float)
            for t in resultados:
                resumen_cat[t.get("categoria", "Sin categoría")] += t["monto"]

            partes.append(f"📊 *Resumen de {tipo}s por categoría:*")
            for cat, monto in resumen_cat.items():
                partes.append(f"- {cat}: {monto:.2f} soles")
        elif medio:
            partes.append(f"📌 Total registrado usando *{medio}*: *{total:.2f} soles*.")
        else:
            partes.append(f"📊 *Total filtrado*: *{total:.2f} soles*.")

        partes.append("👉 ¿Deseas *ver tu historial* o *analizar tus gastos por categoría*?")
        dispatcher.utter_message(text=construir_mensaje(*partes))

        return [SlotSet("sugerencia_pendiente", "action_analizar_gastos")]
        
class ActionEntradaNoEntendida(Action):
    def name(self) -> Text:
        return "action_entrada_no_entendida"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        try:
            from datetime import datetime

            texto = tracker.latest_message.get("text", "").strip()
            intent = tracker.latest_message.get("intent", {}).get("name", "")
            entidades = [e.get("entity") for e in tracker.latest_message.get("entities", [])]

            # ❌ No registrar saludos, afirmaciones o negaciones como entradas no entendidas
            if intent not in ["entrada_no_entendida", "nlu_fallback"]:
                dispatcher.utter_message(
                    text="❓ *No logré entender completamente tu mensaje.* ¿Podrías reformularlo o dar más detalles?"
                )
                return []

            # 🧠 Guardar entrada como no comprendida
            guardar_transaccion({
                "tipo": "entrada_no_entendida",
                "descripcion": texto,
                "timestamp": datetime.now().isoformat()
            })

            # 📌 Mensaje personalizado según si hubo detección parcial
            if entidades:
                mensaje = construir_mensaje(
                    f"🤔 *No logré comprender del todo tu mensaje:* “{texto}”.",
                    f"🔎 Detecté las siguientes entidades: *{', '.join(entidades)}*.",
                    f"¿Podrías darme más contexto o reformular tu solicitud?"
                )
            else:
                mensaje = construir_mensaje(
                    f"🤔 *No logré entender tu mensaje:* “{texto}”.",
                    "👉 *Ejemplos que puedes probar:*",
                    "- “Registré un gasto de 100 soles en comida”",
                    "- “¿Cuánto ingresé en marzo?”",
                    "- “Configura una alerta de 300 soles para abril”"
                )

            dispatcher.utter_message(text=mensaje)

            # Mensaje final de continuidad
            dispatcher.utter_message(
                text="🧠 *Estoy aquí para ayudarte con tus finanzas.* ¿Qué te gustaría hacer ahora?"
            )

            return [SlotSet("sugerencia_pendiente", "action_ayuda_general")]

        except Exception as e:
            print(f"[ERROR] Fallo en action_entrada_no_entendida: {e}")
            dispatcher.utter_message(
                text="❌ Ocurrió un error procesando tu mensaje. Por favor, intenta nuevamente."
            )
            return []

class ActionResetearCategoriaGastos(Action):
    def name(self) -> Text:
        return "action_resetear_categoria_gastos"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        from datetime import datetime
        import json
        import re

        categoria = get_entity(tracker, "categoria")
        periodo = get_entity(tracker, "periodo")
        texto_usuario = tracker.latest_message.get("text", "").lower()

        if not categoria or not periodo:
            dispatcher.utter_message(
                text="⚠️ Necesito tanto la *categoría* como el *mes con año* para poder resetear los gastos."
            )
            return []

        # Normalizar periodo
        match = re.search(r"([a-záéíóúñ]+)(?:\s+de\s+)?(\d{4})", periodo.lower())
        if not match:
            dispatcher.utter_message(
                text="🗓️ El periodo debe tener el formato *“marzo de 2025”*, por ejemplo."
            )
            return []

        mes = match.group(1).strip().lower()
        año = int(match.group(2))

        transacciones = cargar_transacciones()
        ahora = datetime.now().isoformat()
        modificadas = 0

        # Marcar gastos como eliminados (status 0)
        for t in transacciones:
            if (
                t.get("tipo") == "gasto"
                and t.get("categoria", "").lower() == categoria.lower()
                and t.get("mes", "").lower() == mes
                and t.get("año") == año
                and t.get("status", 1) == 1
            ):
                t["status"] = 0
                t["timestamp_modificacion"] = ahora
                modificadas += 1

        # Agregar registro del reinicio
        transacciones.append({
            "tipo": "reinicio",
            "categoria": categoria,
            "mes": mes,
            "año": año,
            "motivo": "reseteo de gastos",
            "timestamp": ahora,
            "status": 1
        })

        # Guardar cambios
        with open(RUTA_TRANSACCIONES, "w", encoding="utf-8") as f:
            json.dump(transacciones, f, ensure_ascii=False, indent=2)

        # Mensaje de confirmación
        if modificadas > 0:
            mensaje = construir_mensaje(
                f"🔄 *Se han reseteado {modificadas} registros de gasto* en la categoría *{categoria}* para *{mes} {año}*.",
                "📌 Estos registros ya no se considerarán en tus análisis financieros."
            )
        else:
            mensaje = construir_mensaje(
                f"ℹ️ *No se encontraron gastos activos* en *{categoria}* para *{mes} {año}*.",
                "📌 Aun así, se ha registrado el reinicio para dejar constancia del cambio."
            )

        dispatcher.utter_message(text=mensaje)
        return []

class ActionCrearConfiguracion(Action):
    def name(self) -> Text:
        return "action_crear_configuracion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            import re
            from datetime import datetime

            categoria = get_entity(tracker, "categoria")
            monto = get_entity(tracker, "monto")
            periodo = get_entity(tracker, "periodo")
            texto_usuario = tracker.latest_message.get("text", "").lower()

            if not categoria or not monto or not periodo:
                dispatcher.utter_message(text="⚠️ Necesito la *categoría*, el *monto* y el *mes con año* para poder crear una configuración.")
                return []

            try:
                monto_float = parse_monto(monto)
            except Exception:
                dispatcher.utter_message(text="❌ El monto ingresado no es válido. Intenta con un valor numérico.")
                return []

            if monto_float <= 0:
                dispatcher.utter_message(text="⚠️ El monto debe ser *mayor que cero*.")
                return []

            # 📆 Normalizar periodo
            periodo = periodo.lower().strip()
            match = re.search(r"([a-záéíóúñ]+)(?:\s+de\s+)?(\d{4})", periodo)
            if not match:
                dispatcher.utter_message(
                    text="📅 El formato del periodo debe ser *“abril de 2024”*, por ejemplo."
                )
                return []

            mes = match.group(1).strip().lower()
            año = int(match.group(2))
            periodo_normalizado = f"{mes} de {año}"

            # 🧠 Verificar si ya existe una alerta activa
            alertas = cargar_alertas()
            ya_existe = any(
                a.get("categoria", "").lower() == categoria.lower() and
                a.get("periodo", "").lower() == periodo_normalizado and
                a.get("status", 1) == 1
                for a in alertas
            )

            if ya_existe:
                dispatcher.utter_message(
                    text=f"🔔 Ya existe una *alerta activa* para *{categoria}* en *{periodo_normalizado}*.\n\n🛠️ Usa *modificar* si deseas actualizarla."
                )
                return []

            nueva_alerta = {
                "categoria": categoria,
                "monto": monto_float,
                "periodo": periodo_normalizado,
                "mes": mes,
                "año": año,
                "timestamp": datetime.now().isoformat(),
                "status": 1
            }

            guardar_alerta(nueva_alerta)

            mensaje = construir_mensaje(
                f"✅ *Presupuesto/Alerta registrada correctamente*",
                f"📌 Se ha creado una alerta de *{monto_float:.2f} soles* para *{categoria}* en *{periodo_normalizado}*.",
                "👉 Puedes modificarla más adelante si es necesario."
            )
            dispatcher.utter_message(text=mensaje)

            return []

        except Exception as e:
            print(f"[ERROR] Fallo en action_crear_configuracion: {e}")
            dispatcher.utter_message(text="❌ Ocurrió un error al crear la alerta. Por favor, intenta nuevamente.")
            return []
            
class ActionModificarConfiguracion(Action):
    def name(self) -> Text:
        return "action_modificar_configuracion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        import re
        import json
        from datetime import datetime

        categoria = get_entity(tracker, "categoria")
        monto = get_entity(tracker, "monto")
        periodo = get_entity(tracker, "periodo")
        texto_usuario = tracker.latest_message.get("text", "").lower()

        if not categoria or not monto or not periodo:
            dispatcher.utter_message(
                text="⚠️ Para *modificar una configuración*, necesito que me indiques la *categoría*, el *monto* y el *mes con año*."
            )
            return []

        try:
            monto_float = parse_monto(monto)
        except Exception:
            dispatcher.utter_message(
                text="❌ El monto proporcionado no es válido. Intenta con un valor numérico."
            )
            return []

        if monto_float <= 0:
            dispatcher.utter_message(
                text="⚠️ El monto debe ser *mayor a cero* para configurar una alerta."
            )
            return []

        # 📅 Normalizar periodo
        match = re.search(r"([a-záéíóúñ]+)(?:\s+de\s+)?(\d{4})", periodo.lower())
        if not match:
            dispatcher.utter_message(
                text="📅 El formato del periodo debe ser *“abril de 2024”*, por ejemplo."
            )
            return []

        mes = match.group(1).strip().lower()
        año = int(match.group(2))
        periodo_normalizado = f"{mes} de {año}"

        # 🔍 Buscar si existe una alerta activa
        alertas = cargar_alertas()
        alerta_existente = next((
            a for a in alertas
            if a.get("categoria", "").lower() == categoria.lower()
            and a.get("periodo", "").lower() == periodo_normalizado
            and a.get("status", 1) == 1
        ), None)

        if alerta_existente:
            # ✅ Hay una alerta activa: proponer modificación
            dispatcher.utter_message(
                text=construir_mensaje(
                    f"✏️ Se encontró una alerta activa para *{categoria}* en *{periodo_normalizado}*.",
                    f"¿Deseas actualizarla al nuevo monto de *{monto_float:.2f} soles*?"
                )
            )
            return [
                SlotSet("categoria", categoria),
                SlotSet("monto", monto_float),
                SlotSet("periodo", periodo_normalizado),
                SlotSet("mes", mes),
                SlotSet("año", año),
                SlotSet("alerta_original", json.dumps(alerta_existente)),
                SlotSet("sugerencia_pendiente", "confirmar_modificacion_alerta")
            ]

        else:
            # ❌ No existe: sugerir creación
            dispatcher.utter_message(
                text=construir_mensaje(
                    f"🔍 *No encontré una alerta activa* para *{categoria}* en *{periodo_normalizado}*.",
                    "¿Deseas crear una nueva alerta con esa información?"
                )
            )
            return [
                SlotSet("categoria", categoria),
                SlotSet("monto", monto_float),
                SlotSet("periodo", periodo_normalizado),
                SlotSet("mes", mes),
                SlotSet("año", año),
                SlotSet("sugerencia_pendiente", "action_crear_configuracion")
            ]

class ActionConfirmarModificacionAlerta(Action):
    def name(self) -> Text:
        return "confirmar_modificacion_alerta"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        import json

        categoria = tracker.get_slot("categoria")
        monto = tracker.get_slot("monto")
        periodo = tracker.get_slot("periodo")

        # 🔍 Verificar si la alerta aún existe y está activa
        alertas = cargar_alertas()
        alerta_existente = next((
            a for a in alertas
            if a.get("categoria", "").lower() == categoria.lower()
            and a.get("periodo", "").lower() == periodo.lower()
            and a.get("status", 1) == 1
        ), None)

        if not alerta_existente:
            dispatcher.utter_message(
                text="⚠️ *La alerta que intentas modificar ya no está activa o no existe.*"
            )
            return []

        # ✅ Preparar mensaje de confirmación
        mensaje = construir_mensaje(
            "✏️ *Esta es la alerta que tienes activa:*",
            f"• Categoría: *{alerta_existente['categoria']}*",
            f"• Monto actual: *{alerta_existente['monto']:.2f} soles*",
            f"• Periodo: *{alerta_existente['periodo']}*",
            "🔄 ¿Deseas actualizarla a:",
            f"• *{monto:.2f} soles*?",
            "✉️ *Responde con “sí” para confirmar* o *“no” para cancelar* la modificación."
        )

        dispatcher.utter_message(text=mensaje)

        return [
            SlotSet("alerta_original", json.dumps(alerta_existente))  # Para su uso posterior
        ]

class ActionEjecutarModificacionAlerta(Action):
    def name(self) -> Text:
        return "action_ejecutar_modificacion_alerta"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        import json
        from datetime import datetime

        try:
            categoria = tracker.get_slot("categoria")
            monto = tracker.get_slot("monto")
            periodo = tracker.get_slot("periodo")
            alerta_json = tracker.get_slot("alerta_original")

            if not (categoria and monto and periodo and alerta_json):
                dispatcher.utter_message(
                    text="⚠️ *No se pudo completar la modificación* porque faltan datos importantes."
                )
                return []

            alerta_original = json.loads(alerta_json)
            alertas = cargar_alertas()
            ahora = datetime.now()

            # 🚫 Desactivar alerta anterior
            for alerta in alertas:
                if (
                    alerta.get("categoria", "").lower() == alerta_original.get("categoria", "").lower() and
                    alerta.get("periodo", "").lower() == alerta_original.get("periodo", "").lower() and
                    alerta.get("status", 1) == 1
                ):
                    alerta["status"] = 0
                    alerta["timestamp_modificacion"] = ahora.isoformat()

            # 🆕 Crear alerta actualizada
            nueva_alerta = {
                "categoria": categoria,
                "monto": float(monto),
                "periodo": periodo,
                "status": 1,
                "timestamp": ahora.isoformat()
            }
            alertas.append(nueva_alerta)

            # 💾 Guardar cambios
            with open(RUTA_ALERTAS, "w", encoding="utf-8") as f:
                json.dump(alertas, f, ensure_ascii=False, indent=2)

            # ✅ Confirmación final
            mensaje = construir_mensaje(
                f"✅ *Alerta modificada correctamente*",
                f"• Categoría: *{categoria}*",
                f"• Nuevo monto: *{float(monto):.2f} soles*",
                f"• Periodo: *{periodo}*",
                "👉 Puedes consultar o modificarla nuevamente cuando lo necesites."
            )
            dispatcher.utter_message(text=mensaje)

            return [
                SlotSet("categoria", None),
                SlotSet("monto", None),
                SlotSet("periodo", None),
                SlotSet("alerta_original", None),
                SlotSet("sugerencia_pendiente", None),
            ]

        except Exception as e:
            print(f"[ERROR] Fallo en action_ejecutar_modificacion_alerta: {e}")
            dispatcher.utter_message(
                text="❌ *Hubo un error al intentar modificar la alerta.* Por favor, intenta nuevamente."
            )
            return []

def desactivar_alerta(categoria: str, periodo: str):
    alertas = cargar_alertas()
    for alerta in alertas:
        if alerta["categoria"].lower() == categoria.lower() and alerta["periodo"].lower() == periodo.lower():
            alerta["status"] = 0
    guardar_todas_las_alertas(alertas)

class ActionEliminarConfiguracion(Action):
    def name(self) -> Text:
        return "action_eliminar_configuracion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        import re

        categoria = get_entity(tracker, "categoria")
        periodo = get_entity(tracker, "periodo")
        texto_usuario = tracker.latest_message.get("text", "").lower()

        if not categoria or not periodo:
            dispatcher.utter_message(
                text="⚠️ Necesito la *categoría* y el *mes con año* para poder eliminar una configuración."
            )
            return []

        # 📆 Normalizar periodo
        periodo = periodo.lower().strip()

        # 🔍 Buscar alerta activa
        alertas = cargar_alertas()
        alerta = next((
            a for a in alertas
            if a.get("categoria", "").lower() == categoria.lower()
            and a.get("periodo", "").lower() == periodo
            and a.get("status", 1) == 1
        ), None)

        if not alerta:
            dispatcher.utter_message(
                text=f"📭 *No se encontró ninguna alerta activa* para *{categoria}* en *{periodo}*."
            )
            return []

        mensaje = construir_mensaje(
            f"🔔 *Se encontró una alerta activa:*",
            f"• Categoría: *{alerta['categoria']}*",
            f"• Monto: *{alerta['monto']:.2f} soles*",
            f"• Periodo: *{alerta['periodo']}*",
            "⚠️ ¿Estás seguro de que deseas eliminar esta alerta?",
            "✉️ *Responde con “sí” para confirmar* o *“no” para cancelar* la eliminación."
        )
        dispatcher.utter_message(text=mensaje)

        return [
            SlotSet("categoria", categoria),
            SlotSet("periodo", periodo),
            SlotSet("sugerencia_pendiente", "confirmar_eliminacion_alerta")
        ]

class ActionConfirmarEliminacionAlerta(Action):
    def name(self) -> Text:
        return "confirmar_eliminacion_alerta"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        import json
        from datetime import datetime

        intent_confirmacion = tracker.latest_message.get("intent", {}).get("name")
        categoria = tracker.get_slot("categoria")
        periodo = tracker.get_slot("periodo")

        if intent_confirmacion != "affirm":
            dispatcher.utter_message(
                text="👍 Perfecto, *no se ha eliminado la alerta*. Si deseas realizar otro cambio, solo dímelo."
            )
            return [SlotSet("sugerencia_pendiente", None)]

        # 🔍 Buscar y desactivar alerta
        alertas = cargar_alertas()
        encontrado = False

        for alerta in alertas:
            if (
                alerta.get("categoria", "").lower() == categoria.lower()
                and alerta.get("periodo", "").lower() == periodo.lower()
                and alerta.get("status", 1) == 1
            ):
                alerta["status"] = 0
                alerta["timestamp_modificacion"] = datetime.now().isoformat()
                encontrado = True

        if encontrado:
            # 💾 Guardar cambios
            with open(RUTA_ALERTAS, "w", encoding="utf-8") as f:
                json.dump(alertas, f, ensure_ascii=False, indent=2)

            mensaje = construir_mensaje(
                f"🗑️ *Alerta eliminada correctamente*",
                f"• Categoría: *{categoria}*",
                f"• Periodo: *{periodo}*",
                "👉 Ya no será tenida en cuenta en tus análisis ni alertas futuras."
            )
            dispatcher.utter_message(text=mensaje)
        else:
            dispatcher.utter_message(
                text="⚠️ *No se encontró una alerta activa* para eliminar con esos datos."
            )

        return [
            SlotSet("categoria", None),
            SlotSet("periodo", None),
            SlotSet("sugerencia_pendiente", None)
        ]

class ActionConsultarConfiguracion(Action):
    def name(self) -> Text:
        return "action_consultar_configuracion"

    def run(self, dispatcher, tracker, domain):
        import re
        from datetime import datetime

        alertas = cargar_alertas()
        if not alertas:
            dispatcher.utter_message(
                text="📭 *No tienes configuraciones de alertas registradas actualmente.*"
            )
            return []

        texto_usuario = tracker.latest_message.get("text", "").lower()

        # 🔍 Capturar entidad periodo (normalizado)
        periodo_raw = get_entity(tracker, "periodo")
        periodo_normalizado = None
        if "este mes" in texto_usuario:
            mes_actual_en = datetime.now().strftime("%B").lower()
            meses_es = {
                "january": "enero", "february": "febrero", "march": "marzo", "april": "abril",
                "may": "mayo", "june": "junio", "july": "julio", "august": "agosto",
                "september": "septiembre", "october": "octubre", "november": "noviembre", "december": "diciembre"
            }
            mes_actual = meses_es.get(mes_actual_en, mes_actual_en)
            año_actual = datetime.now().year
            periodo_normalizado = f"{mes_actual} de {año_actual}"
        elif periodo_raw:
            match = re.search(r"([a-záéíóúñ]+)(?:\s+de\s+)?(\d{4})?", periodo_raw.lower())
            if match:
                mes = match.group(1).strip()
                año = match.group(2) or str(datetime.now().year)
                periodo_normalizado = f"{mes} de {año}"

        # 🔍 Capturar entidad categoria
        categoria_raw = None
        for ent in tracker.latest_message.get("entities", []):
            if ent.get("entity") == "categoria":
                categoria_raw = ent.get("value").lower()
                break
        if not categoria_raw:
            categoria_raw = tracker.get_slot("categoria")

        # 📌 Filtrar alertas activas, y por periodo o categoría si aplica
        ultimas_alertas = {}
        for alerta in sorted(alertas, key=lambda x: x.get("timestamp", ""), reverse=True):
            if alerta.get("status", 1) != 1:
                continue

            periodo_alerta = alerta.get("periodo", "").lower()
            categoria_alerta = alerta.get("categoria", "").lower()
            clave = f"{categoria_alerta}_{periodo_alerta}"

            if periodo_normalizado and periodo_alerta != periodo_normalizado:
                continue
            if categoria_raw and categoria_alerta != categoria_raw:
                continue

            if clave not in ultimas_alertas:
                ultimas_alertas[clave] = alerta

        if not ultimas_alertas:
            texto = f"📭 *No se encontraron alertas activas"
            if categoria_raw:
                texto += f" para la categoría *{categoria_raw}*"
            if periodo_normalizado:
                texto += f" en el periodo **{periodo_normalizado}**"
            texto += ".*"
            dispatcher.utter_message(text=texto)
            return []

        mensaje = ["🔔 **Estas son tus configuraciones de alerta activas:**"]
        for alerta in ultimas_alertas.values():
            categoria = alerta.get("categoria", "desconocida").capitalize()
            monto = alerta.get("monto", "?")
            periodo = alerta.get("periodo", "")
            fecha = ""
            if alerta.get("timestamp"):
                try:
                    fecha = datetime.fromisoformat(alerta["timestamp"]).strftime(" _(registrado el %d/%m/%Y)_")
                except:
                    fecha = ""
            linea = f"• *{categoria}*: {monto} soles"
            if periodo:
                linea += f" para *{periodo}*"
            linea += f"{fecha}"
            mensaje.append(linea)

        mensaje.append("👉 ¿Deseas *modificar o eliminar* alguna de estas configuraciones?")
        dispatcher.utter_message(text=construir_mensaje(*mensaje))
        return []

class ActionEliminarAlerta(Action):
    def name(self) -> Text:
        return "action_eliminar_alerta"

    def run(self, dispatcher, tracker, domain):
        categoria = get_entity(tracker, "categoria")
        periodo = get_entity(tracker, "periodo")

        if not categoria or not periodo:
            dispatcher.utter_message(
                text="⚠️ Necesito saber qué *alerta deseas eliminar*. Por favor, indícame la *categoría* y el *mes con año*."
            )
            return []

        condiciones = {
            "categoria": categoria.lower(),
            "periodo": periodo.lower()
        }

        alertas = cargar_alertas()
        coincidencias = [
            a for a in alertas
            if a.get("categoria", "").lower() == condiciones["categoria"]
            and a.get("periodo", "").lower() == condiciones["periodo"]
            and a.get("status", 1) == 1
        ]

        if not coincidencias:
            dispatcher.utter_message(
                text=f"📭 *No encontré ninguna alerta activa* para *{categoria}* en *{periodo}*."
            )
            return []

        # 🗑️ Eliminar lógicamente
        eliminar_alerta_logicamente(condiciones)

        mensaje = construir_mensaje(
            f"🗑️ *Alerta eliminada correctamente*",
            f"• Categoría: *{categoria}*",
            f"• Periodo: *{periodo}*",
            "👉 Ya no será considerada en tus análisis ni alertas futuras."
        )

        dispatcher.utter_message(text=mensaje)
        return []
    
from rasa_sdk.events import FollowupAction

class ActionFollowSuggestion(Action):
    def name(self) -> Text:
        return "action_follow_suggestion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        sugerencia = tracker.get_slot("sugerencia_pendiente")

        # ✅ Si hay una sugerencia pendiente, la ejecutamos
        if sugerencia:
            dispatcher.utter_message(
                text="✅ *Perfecto*, procedo con tu solicitud..."
            )
            return [
                FollowupAction(sugerencia),
                SlotSet("sugerencia_pendiente", None)
            ]

        # ❌ Si no hay sugerencia válida
        dispatcher.utter_message(
            text="⚠️ *No tengo ninguna acción pendiente por ejecutar.*\n\n👉 ¿Te gustaría *registrar algo* o *hacer una consulta*?"
        )
        return []

class ActionBienvenida(Action):
    def name(self) -> Text:
        return "action_bienvenida"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        from datetime import datetime

        meses_es = {
            "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
            "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
            "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
        }

        ahora = datetime.now()
        nombre_mes_en = ahora.strftime("%B")
        nombre_mes_es = meses_es.get(nombre_mes_en, nombre_mes_en).capitalize()
        fecha_formateada = f"{ahora.day} de {nombre_mes_es} de {ahora.year}"

        mensaje = construir_mensaje(
            "💼 **¡Hola! Bienvenido 👋**",
            f"📅 Hoy es *{fecha_formateada}* y estoy listo para ayudarte con tus finanzas.",
            "🛠️ **Puedo ayudarte a:**",
            "- Registrar ingresos y gastos",
            "- Ver tu historial o saldo",
            "- Configurar alertas",
            "- Comparar tus gastos entre meses",
            "💡 *Ejemplo:* `Muéstrame mis gastos de abril`",
            "👉 ¿Qué deseas hacer hoy?"
        )

        dispatcher.utter_message(text=mensaje)
        return []

class ActionAyudaGeneral(Action):
    def name(self) -> Text:
        return "action_ayuda_general"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        mensaje = construir_mensaje(
            "🧭 **Aquí tienes algunas cosas que puedo hacer por ti:**",
            "- Registrar *ingresos* o *gastos*",
            "- Consultar tu *saldo* o tu *historial financiero*",
            "- Configurar, modificar o eliminar *alertas* por categoría",
            "- *Analizar* tus hábitos de consumo",
            "- *Comparar* tus gastos entre distintos meses",
            "💡 *Ejemplo útil:* `Gasté 80 soles en comida con débito el 2 de abril`",
            "👉 ¿Con qué te gustaría comenzar?"
        )

        dispatcher.utter_message(text=mensaje)
        return []

from rasa_sdk.events import SessionStarted, ActionExecuted, EventType

class ActionSessionStart(Action):
    def name(self) -> Text:
        return "action_session_start"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> List[EventType]:

        # 🟢 Evento estándar de inicio de sesión en Rasa
        events = [SessionStarted(), ActionExecuted("action_listen")]

        # 📣 Ejecutar la acción de bienvenida personalizada (manual)
        bienvenida = ActionBienvenida()
        await bienvenida.run(dispatcher, tracker, domain)

        # Retornar eventos para continuar con el flujo estándar
        return events

class ActionNegacion(Action):
    def name(self) -> Text:
        return "action_negacion"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[EventType]:

        sugerencia = tracker.get_slot("sugerencia_pendiente")

        if sugerencia:
            dispatcher.utter_message(
                text="🙅‍♂️ *Perfecto, no se realizará la acción pendiente.*\n\n✅ Si deseas hacer otra consulta más adelante, estaré aquí para ayudarte."
            )
            return [SlotSet("sugerencia_pendiente", None)]

        dispatcher.utter_message(
            text="👍 Entendido.\n\n🧠 Si necesitas *registrar algo* o *consultar tus finanzas*, solo dímelo."
        )
        return []
