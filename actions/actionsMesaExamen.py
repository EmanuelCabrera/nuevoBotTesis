from builtins import print
from typing import Any, Text, Dict, List
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk import Action
from rasa_sdk.events import SlotSet
import json

import os
from dotenv import load_dotenv
from supabase import create_client, Client
import httpx

try:
    from .subject_catalog import SubjectCatalogRepository
    from .subject_resolver import SubjectResolver
except ImportError:  # Support direct loading by the action unit-test harness.
    from actions.subject_catalog import SubjectCatalogRepository
    from actions.subject_resolver import SubjectResolver

load_dotenv()
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)
subject_catalog = SubjectCatalogRepository(lambda: supabase, ttl_seconds=600)
subject_resolver = SubjectResolver()


def _registration_retry_events(clear_mesa=True):
    events = []
    if clear_mesa:
        events.extend([SlotSet("codigo_mesa_examen", None), SlotSet("fecha_mesa", None)])
    events.append(SlotSet("flujo_actual", "inscripcion_mesa_examen"))
    return events


def _resolve_registration_subject(materia):
    catalog = subject_catalog.get_subjects()
    return subject_resolver.resolve(catalog, materia)


def _subject_resolution_message(dispatcher, materia, status, resolution):
    if status == "not_found":
        dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
    elif status == "ambiguous":
        options = ", ".join(sorted({subject["nombre"] for subject in resolution}))
        dispatcher.utter_message(
            f"❓ Encontré varias materias que coinciden con '{materia}': {options}. "
            "Por favor, especifica cuál necesitas."
        )

class ActionVerMesasExamen(Action):

    def name(self):
        return "action_consultar_mesas_examen"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        is_authenticated = tracker.get_slot('is_authenticated')
        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar las mesas de examen. Por favor, inicia sesión primero.")
            return []

        materia = tracker.get_slot('materia')
        if not materia:
            dispatcher.utter_message("❌ No especificaste qué materia quieres consultar. Por favor, dime de qué materia necesitas ver las mesas de examen.")
            return []

        try:
            catalog = subject_catalog.get_subjects()
            resolution_status, resolution = subject_resolver.resolve(catalog, materia)

            if resolution_status == "not_found":
                dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                return []

            if resolution_status == "ambiguous":
                options = ", ".join(sorted({subject["nombre"] for subject in resolution}))
                dispatcher.utter_message(
                    f"❓ Encontré varias materias que coinciden con '{materia}': {options}. "
                    "Por favor, especifica cuál necesitas."
                )
                return [
                    SlotSet("flujo_actual", "consultar_fecha_mesas_examen_final"),
                    SlotSet("materia", None),
                ]

            materia_codigo = resolution["codigo"]
            nombre_materia = resolution["nombre"]

            # Buscar todas las mesas asociadas al código canónico de la materia.
            mesas_resp = supabase.table("MesaExamen").select('fecha, codigo').eq("materia_codigo", materia_codigo).execute()
            if not mesas_resp.data:
                dispatcher.utter_message(f"📅 No se encontraron mesas de examen para la materia '{nombre_materia}'.")
                return [SlotSet("materia", None), SlotSet("flujo_actual", None)]

            dispatcher.utter_message(f"📅 **Mesas de examen disponibles para {nombre_materia.upper()}:**")
            for idx, mesa in enumerate(mesas_resp.data, 1):
                codigo_mesa = mesa.get("codigo", "Sin código")
                fecha_mesa = mesa.get("fecha", "Fecha no disponible")
                dispatcher.utter_message(
                    f"-----------------------------\n"
                    f"📝 Mesa #{idx}\n"
                    f"📋 Código: `{codigo_mesa}`\n"
                    f"📅 Fecha: {fecha_mesa}\n"
                    f"-----------------------------"
                )
            dispatcher.utter_message(f"✅ Se encontraron {len(mesas_resp.data)} mesa(s) de examen para {nombre_materia.upper()}")
            dispatcher.utter_message("💡 **Nota:** Estas son las fechas disponibles para la materia consultada.")
            return [SlotSet("materia", None), SlotSet("flujo_actual", None)]

        except Exception as e:
            print(f"Error al consultar mesas de examen: {e}")
            dispatcher.utter_message("❌ Hubo un error al consultar las mesas de examen. Por favor, intenta nuevamente más tarde.")

        return []

class ValidateInscripcionMesaForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_inscripcion_mesa_form"

    def validate_matricula(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        is_authenticated = tracker.get_slot('is_authenticated')
        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para consultar e inscribirte a una mesa de examen. Por favor, inicia sesión primero.")
            return {"matricula": None}
            
        if not slot_value:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder continuar.")
            return {"matricula": None}
            
        return {"matricula": slot_value}

    def validate_materia(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: dict,
    ) -> Dict[Text, Any]:
        catalog = subject_catalog.get_subjects()
        resolution_status, resolution = SubjectResolver().resolve(catalog, slot_value)

        if resolution_status == "not_found":
            dispatcher.utter_message(f"😕 No se encontró la materia '{slot_value}' en la base de datos. Por favor, intenta ingresando otra materia.")
            return {"materia": None}

        if resolution_status == "ambiguous":
            options = ", ".join(subject["nombre"] for subject in resolution)
            dispatcher.utter_message(
                f"❓ Encontré varias materias que coinciden con '{slot_value}': {options}. "
                "Por favor, especifica cuál necesitas."
            )
            return {"materia": None}

        materia_codigo = resolution["codigo"]
        nombre_materia = resolution["nombre"]

        # Buscar mesas disponibles
        mesas_resp = supabase.table("MesaExamen").select('fecha, codigo').eq("materia_codigo", materia_codigo).order("fecha", desc=False).execute()
        
        if not mesas_resp.data:
            dispatcher.utter_message(f"📅 No se encontraron mesas de examen disponibles para la materia '{nombre_materia}'.")
            return {"materia": None}

        dispatcher.utter_message(f"📅 **Mesas de examen disponibles para {nombre_materia.upper()}:**")
        for idx, mesa in enumerate(mesas_resp.data, 1):
            codigo_mesa = mesa.get("codigo", "Sin código")
            fecha_mesa = mesa.get("fecha", "Fecha no disponible")
            dispatcher.utter_message(
                f"-----------------------------\n"
                f"📝 Mesa #{idx}\n"
                f"📋 Código: `{codigo_mesa}`\n"
                f"📅 Fecha: {fecha_mesa}\n"
                f"-----------------------------"
            )
        return {"materia": nombre_materia}

    def validate_fecha_mesa(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> Dict[Text, Any]:
        import re
        if slot_value:
            # Si el valor ingresado no parece una fecha (YYYY-MM-DD), asumimos que es el código de la mesa
            if not re.match(r'^\d{4}-\d{2}-\d{2}$', str(slot_value)):
                return {"fecha_mesa": slot_value, "codigo_mesa_examen": slot_value}
            
            return {"fecha_mesa": slot_value, "codigo_mesa_examen": None}
        return {"fecha_mesa": None}

# Modificar ActionInscripcionMesaExamen para solo inscribir si ya hay código de mesa seleccionado
def _find_mesa_by_codigo(codigo_mesa):
    mesa_response = supabase.table("MesaExamen").select('fecha, materia_codigo, Materia(nombre)').eq("codigo", codigo_mesa).execute()
    if mesa_response.data:
        return mesa_response.data[0]
    return None

class ActionInscripcionMesaExamen(Action):
    def name(self):
        return "action_inscripcion_mesa_examen"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        is_authenticated = tracker.get_slot('is_authenticated')
        if not is_authenticated:
            dispatcher.utter_message("❌ Necesitas estar autenticado para inscribirte a una mesa de examen. Por favor, inicia sesión primero.")
            return []
        matricula = tracker.get_slot('matricula')
        codigo_mesa = tracker.get_slot('codigo_mesa_examen')
        fecha_mesa = tracker.get_slot('fecha_mesa')
        materia = tracker.get_slot('materia')
        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder inscribirte a la mesa de examen.")
            return _registration_retry_events()
        # Si no hay código pero sí fecha, buscar el código de la mesa para esa fecha y materia
        if not codigo_mesa and fecha_mesa and materia:
            try:
                catalog = subject_catalog.get_subjects()
                resolution_status, resolution = SubjectResolver().resolve(catalog, materia)
                if resolution_status != "resolved":
                    dispatcher.utter_message(f"❌ No se encontró la materia '{materia}' en la base de datos.")
                    return []
                materia_codigo = resolution["codigo"]
                mesa_resp = supabase.table("MesaExamen").select('codigo').eq("materia_codigo", materia_codigo).eq("fecha", fecha_mesa).execute()
                if not mesa_resp.data:
                    dispatcher.utter_message(f"❌ No se encontró una mesa de examen para la materia '{resolution['nombre']}' en la fecha '{fecha_mesa}'.")
                    return _registration_retry_events()
                codigo_mesa = mesa_resp.data[0]["codigo"]
            except Exception as e:
                print(f"Error buscando mesa por fecha: {e}")
                dispatcher.utter_message("❌ Hubo un error al buscar la mesa de examen por fecha. Por favor, intenta nuevamente más tarde.")
                return _registration_retry_events()
        if not codigo_mesa:
            dispatcher.utter_message("❌ No tengo el código de la mesa de examen. Por favor, selecciona una mesa de examen para inscribirte (puedes consultarlas primero).")
            return _registration_retry_events()
        try:
            resolved_subject = None
            if materia:
                resolution_status, resolution = _resolve_registration_subject(materia)
                if resolution_status != "resolved":
                    _subject_resolution_message(dispatcher, materia, resolution_status, resolution)
                    return [SlotSet("materia", None)] + _registration_retry_events()
                resolved_subject = resolution

            mesa_info = _find_mesa_by_codigo(codigo_mesa)
            if not mesa_info:
                dispatcher.utter_message(f"❌ No se encontró una mesa de examen con el código '{codigo_mesa}'.")
                return _registration_retry_events()
            nombre_materia = mesa_info.get("Materia", {}).get("nombre", "Materia sin nombre")
            fecha_mesa_final = mesa_info.get("fecha", "Fecha no disponible")

            if resolved_subject:
                if mesa_info.get("materia_codigo") != resolved_subject["codigo"]:
                    dispatcher.utter_message(
                        f"❌ La mesa seleccionada no corresponde a la materia '{resolved_subject['nombre']}'. "
                        "Por favor, selecciona una mesa de esa materia."
                    )
                    return _registration_retry_events()
            # Verificar si ya está inscrito
            inscripcion_existente = supabase.table("Inscripcion").select('*').eq("estudiante", matricula).eq("codigo_mesa", codigo_mesa).execute()
            if inscripcion_existente.data:
                dispatcher.utter_message(f"⚠️ Ya estás inscrito a la mesa de examen de **{nombre_materia}** (código: {codigo_mesa}) que se realizará el {fecha_mesa_final}.")
                return [SlotSet("flujo_actual", None), SlotSet("materia", None), SlotSet("fecha_mesa", None), SlotSet("codigo_mesa_examen", None)]
            # Realizar la inscripción
            inscripcion_data = {
                "estudiante": matricula,
                "codigo_mesa": codigo_mesa,
                "fecha_inscripcion": "now()"
            }
            print(f"[LOG] matricula: {matricula}")
            print(f"[LOG] codigo_mesa: {codigo_mesa}")
            print(f"[LOG] fecha_inscripcion: {inscripcion_data['fecha_inscripcion']}")
            insert_response = supabase.table("Inscripcion").insert(inscripcion_data).execute()
            if insert_response.data:
                dispatcher.utter_message(f"✅ **¡Inscripción exitosa!**")
                dispatcher.utter_message(f"📚 Materia: **{nombre_materia}**")
                dispatcher.utter_message(f"📋 Código de mesa: `{codigo_mesa}`")
                dispatcher.utter_message(f"📅 Fecha del examen: {fecha_mesa_final}")
                dispatcher.utter_message(f"🎓 Matrícula: {matricula}")
                dispatcher.utter_message("📝 Recuerda presentarte con tu libreta y los materiales necesarios para el examen.")
                return [SlotSet("flujo_actual", None), SlotSet("materia", None), SlotSet("fecha_mesa", None), SlotSet("codigo_mesa_examen", None)]
            else:
                dispatcher.utter_message("❌ Hubo un problema al procesar tu inscripción. Por favor, intenta nuevamente.")
        except Exception as e:
            print(f"Error al inscribir a mesa de examen: {e}")
            dispatcher.utter_message("❌ Hubo un error al procesar tu inscripción. Por favor, intenta nuevamente más tarde.")
            return _registration_retry_events()
        return _registration_retry_events()

class ActionCancelarInscripcionMesa(Action):

    def name(self):
        return "action_cancelar_inscripcion_mesa_examen"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain):
        materia = tracker.get_slot('materia')
        matricula = tracker.get_slot('matricula')
        
        if not matricula:
            dispatcher.utter_message("❌ No tengo tu número de matrícula. Por favor, proporciona tu matrícula para poder cancelar la inscripción.")
            return []
        
        if not materia:
            dispatcher.utter_message("❌ No tengo la materia especificada. Por favor, dime de qué materia quieres cancelar la inscripción.")
            return []
        
        try:
            # Resolver la expresión contra el catálogo canónico completo.
            catalog = subject_catalog.get_subjects()
            resolution_status, resolution = SubjectResolver().resolve(catalog, materia)

            if resolution_status == "not_found":
                dispatcher.utter_message(f"😕 No se encontró la materia '{materia}' en la base de datos. Por favor, intenta ingresando otra materia.")
                return [SlotSet("materia", None)]

            if resolution_status == "ambiguous":
                options = ", ".join(subject["nombre"] for subject in resolution)
                dispatcher.utter_message(
                    f"❓ Encontré varias materias que coinciden con '{materia}': {options}. "
                    "Por favor, indica cuál necesitas."
                )
                return [SlotSet("materia", None)]
            materia_codigo = resolution["codigo"]
            nombre_materia = resolution["nombre"]
            
            # Buscar las mesas de examen para esa materia específica
            mesa_response = supabase.table("MesaExamen").select('codigo').eq("materia_codigo", materia_codigo).execute()
            
            print(f"Mesas encontradas para {nombre_materia}: {mesa_response.data}")
            if not mesa_response.data:
                dispatcher.utter_message(f"❌ No se encontraron mesas de examen para la materia '{materia}'.")
                return []
            
            # Buscar todas las inscripciones del estudiante para las mesas de esa materia
            inscripciones_canceladas = 0
            for mesa in mesa_response.data:
                codigo_mesa = mesa.get("codigo")
                
                # Buscar la inscripción específica
                inscripcion_response = supabase.table("Inscripcion").select('*').eq("estudiante", matricula).eq("codigo_mesa", codigo_mesa).execute()
                
                print(inscripcion_response.data)
                if inscripcion_response.data:
                    # Eliminar la inscripción
                    delete_response = supabase.table("Inscripcion").delete().eq("estudiante", matricula).eq("codigo_mesa", codigo_mesa).execute()
                    
                    if delete_response.data:
                        inscripciones_canceladas += 1
                        dispatcher.utter_message(f"✅ Tu inscripción a la mesa de examen de {nombre_materia} (código: {codigo_mesa}) ha sido cancelada exitosamente.")
            
            if inscripciones_canceladas == 0:
                dispatcher.utter_message(f"❌ No se encontró una inscripción activa para la matrícula {matricula} en ninguna mesa de examen de la materia '{materia}'.")
            elif inscripciones_canceladas == 1:
                dispatcher.utter_message("✅ Cancelación completada.")
            else:
                dispatcher.utter_message(f"✅ Se cancelaron {inscripciones_canceladas} inscripciones.")
                
        except Exception as e:
            print(f"Error al cancelar inscripción: {e}")
            dispatcher.utter_message("❌ Hubo un error al procesar la cancelación. Por favor, intenta nuevamente más tarde.")
        
        return []

