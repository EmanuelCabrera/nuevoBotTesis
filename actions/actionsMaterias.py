
from builtins import print
from typing import Any, Text, Dict, List
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action, Tracker
from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import json

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import httpx

from actions.subject_catalog import SubjectCatalogRepository
from actions.subject_resolver import SubjectResolver

load_dotenv()
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)
subject_catalog = SubjectCatalogRepository(lambda: supabase)

class ActionConsultarMaterias(Action):

    def name(self):
        return "action_consultar_materias"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Verificar si el usuario está autenticado
        is_authenticated = tracker.get_slot('is_authenticated')

        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar tus materias. Por favor, inicia sesión primero.")
            return []

        # Obtener la matrícula del slot
        matricula = tracker.get_slot('matricula')

        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder consultar tus materias.")
            return [SlotSet("flujo_actual", "consultar_materias")]

        try:
            response = supabase.table("MateriaCursada").select('fecha_cursada, Materia(nombre)').eq("estudiante", matricula).execute()

            if not response.data:
                dispatcher.utter_message(f"📚 No se encontraron materias cursadas para la matrícula {matricula}.")
                return [SlotSet("flujo_actual", None)]

            dispatcher.utter_message(f"📚 **Materias cursadas para la matrícula {matricula}:**")

            for materia in response.data:
                nombre_materia = materia.get("Materia", {}).get("nombre", "Materia sin nombre")
                fecha_cursada = materia.get("fecha_cursada", "Fecha no disponible")

                dispatcher.utter_message(f"• **{nombre_materia}** - Cursada el: {fecha_cursada}")

            dispatcher.utter_message(f"✅ Total de materias encontradas: {len(response.data)}")
            return [SlotSet("flujo_actual", None), SlotSet("materia", None)]
        except Exception as e:
            print(f"Error al consultar materias: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar tus materias. Por favor, intenta nuevamente más tarde.")

        return []

class ActionConsultarNotas(Action):

    def name(self):
        return "action_consultar_notas"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Verificar si el usuario está autenticado
        is_authenticated = tracker.get_slot('is_authenticated')

        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar tus notas. Por favor, inicia sesión primero.")
            return []

        # Obtener la matrícula del slot
        matricula = tracker.get_slot('matricula')

        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder consultar tus notas.")
            return [SlotSet("flujo_actual", "consultar_notas")]

        # Convertir matrícula a entero
        try:
            matricula = int(matricula)
        except ValueError:
            dispatcher.utter_message("❌ El número de matrícula debe ser un número válido.")
            return []

        # Obtener la materia del slot
        materia = tracker.get_slot('materia')
        if not materia:
            dispatcher.utter_message("❌ No tengo la materia especificada. Por favor, dime de qué materia quieres consultar las notas.")
            return [SlotSet("flujo_actual", "consultar_notas")]
        try:
            catalog = subject_catalog.get_subjects()
            resolution_status, resolution = SubjectResolver().resolve(catalog, materia)

            if resolution_status == "not_found":
                dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                return [SlotSet("flujo_actual", None)]

            if resolution_status == "ambiguous":
                options = ", ".join(subject["nombre"] for subject in resolution)
                dispatcher.utter_message(
                    f"❓ Encontré varias materias que coinciden con '{materia}': {options}. "
                    "Por favor, indica cuál necesitas."
                )
                return [SlotSet("flujo_actual", "consultar_notas")]

            canonical_code = resolution["codigo"]
            canonical_name = resolution["nombre"]
            response = (
                supabase.table("Notas")
                .select("*, Materia!inner(nombre, codigo)")
                .eq("estudiante_id", matricula)
                .eq("materia_codigo", canonical_code)
                .execute()
            )

            if not response.data:
                dispatcher.utter_message(
                    f"📊 No se encontraron notas registradas para la matrícula {matricula} en la materia '{canonical_name}'."
                )
                return [SlotSet("flujo_actual", None)]

            dispatcher.utter_message(f"📊 **Notas de {canonical_name.upper()} para la matrícula {matricula}:**")

            for nota in response.data:
                calificacion = nota.get("nota", "Sin calificar")
                fecha_raw = nota.get("created_at", "Fecha no disponible")
                # Formatear fecha a dd/mm/yyyy
                try:
                    from datetime import datetime
                    if fecha_raw != "Fecha no disponible":
                        # Parsear la fecha ISO (ej: 2024-07-25T10:30:00+00:00)
                        fecha_obj = datetime.fromisoformat(fecha_raw.replace('Z', '+00:00'))
                        fecha_nota = fecha_obj.strftime("%d/%m/%Y")
                    else:
                        fecha_nota = fecha_raw
                except Exception as e:
                    fecha_nota = fecha_raw
                descripcion = nota.get("descripcion", "Sin descripción")
                # Formatear la nota con emoji según la calificación
                if isinstance(calificacion, (int, float)):
                    if calificacion >= 7:
                        emoji = "🟢"
                    elif calificacion >= 4:
                        emoji = "🟡"
                    else:
                        emoji = "🔴"
                    nota_formateada = f"{emoji} {calificacion}/10"
                else:
                    nota_formateada = f"📝 {calificacion}"
                dispatcher.utter_message(f"• {nota_formateada} - {descripcion} - Fecha: {fecha_nota}")

            dispatcher.utter_message(f"✅ Total de notas encontradas: {len(response.data)}")
            return [SlotSet("flujo_actual", None), SlotSet("materia", None)]
        except Exception as e:
            print(f"Error al consultar notas: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar tus notas. Por favor, intenta nuevamente más tarde.")

        return []

class ActionConsultarRequerimientosMateria(Action):

    def name(self):
        return "action_consultar_requerimientos_materia"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        # Verificar si el usuario está autenticado
        is_authenticated = tracker.get_slot('is_authenticated')

        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar los requerimientos de las materias. Por favor, inicia sesión primero.")
            return []

        # Obtener la matrícula del slot
        matricula = tracker.get_slot('matricula')

        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder consultar los requerimientos de las materias.")
            return [SlotSet("flujo_actual", "consultar_requerimientos_materia")]

        # Obtener la materia del slot
        materia = tracker.get_slot('materia')

        if not materia:
            dispatcher.utter_message("❌ No tengo la materia especificada. Por favor, dime de qué materia quieres consultar los requerimientos.")
            return [SlotSet("flujo_actual", "consultar_requerimientos_materia")]

        try:
            # Resolver la expresión contra el catálogo canónico completo.
            catalog = subject_catalog.get_subjects()
            resolution_status, resolution = SubjectResolver().resolve(catalog, materia)

            if resolution_status == "not_found":
                dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                return [SlotSet("flujo_actual", None)]

            if resolution_status == "ambiguous":
                options = ", ".join(subject["nombre"] for subject in resolution)
                dispatcher.utter_message(
                    f"❓ Encontré varias materias que coinciden con '{materia}': {options}. "
                    "Por favor, indica cuál necesitas."
                )
                return [SlotSet("flujo_actual", "consultar_requerimientos_materia")]

            materia_codigo = resolution["codigo"]
            materia_nombre = resolution["nombre"]

            # Buscar únicamente las relaciones directas del registro canónico.
            requerimientos_resp = supabase.table("MateriaEquivalencia").select('*, Materia!MateriaEquivalencia_equivalencia_id_fkey(nombre)').eq("materia_codigo", materia_codigo).execute()

            if not requerimientos_resp.data:
                dispatcher.utter_message(f"❌ No se encontraron requerimientos para la materia '{materia_nombre}'.")
                return [SlotSet("flujo_actual", None)]

            dispatcher.utter_message(f"📊 **Requerimientos de {materia_nombre.upper()}:**")

            for requerimiento in requerimientos_resp.data:
                nombre_materia_equivalencia = requerimiento.get("Materia", {}).get("nombre", "Materia sin nombre")
                dispatcher.utter_message(f"• **{nombre_materia_equivalencia}**")

            dispatcher.utter_message(f"✅ Total de requerimientos encontrados: {len(requerimientos_resp.data)}")
            return [SlotSet("flujo_actual", None), SlotSet("materia", None)]
        except Exception as e:
            print(f"Error al consultar requerimientos de la materia: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar los requerimientos de la materia. Por favor, intenta nuevamente más tarde.")

        return []
